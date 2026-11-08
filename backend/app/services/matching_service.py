from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import ProduceListing, BuyerRequirement, MatchResult
from app.core.geo import calculate_approx_distance_km
from app.services.inventory_service import InventoryService, InsufficientStockException

class MatchingService:
    @staticmethod
    def find_matches_for_listing(db: Session, listing_id: int) -> List[MatchResult]:
        listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id).first()
        if not listing:
            return []

        # Find open buyer requirements for this crop
        requirements = db.query(BuyerRequirement).filter(
            BuyerRequirement.crop_name.ilike(listing.crop_name),
            BuyerRequirement.status == "open"
        ).all()

        matches = []
        # Sort buyers by compatibility:
        # Priority to buyers whose maximum_price >= listing.minimum_price, sorted by distance
        scored_requirements = []
        for req in requirements:
            # Overlap check: buyer max price must be >= listing minimum price
            has_price_overlap = req.maximum_price >= listing.minimum_price
            distance_km = calculate_approx_distance_km(listing.location, req.location)
            
            # Shelf-life urgency weight: 'critical_surplus' > 'moderate' > 'fresh'
            urgency_score = 3 if listing.freshness_status == "critical_surplus" else (2 if listing.freshness_status == "moderate" else 1)
            
            scored_requirements.append({
                "req": req,
                "has_overlap": has_price_overlap,
                "distance_km": distance_km,
                "urgency": urgency_score
            })

        # Sort: first price overlap, then shortest distance
        scored_requirements.sort(key=lambda x: (not x["has_overlap"], x["distance_km"]))

        # Allocate stock atomically
        remaining_avail = listing.available_quantity
        for item in scored_requirements:
            req = item["req"]
            dist_km = item["distance_km"]
            has_overlap = item["has_overlap"]

            if not has_overlap:
                # Mark as no overlap and continue
                no_overlap_reason = (
                    f"No price overlap: Farmer minimum ${listing.minimum_price:.2f}/kg exceeds "
                    f"buyer maximum ${req.maximum_price:.2f}/kg ({dist_km} km away)."
                )
                match = MatchResult(
                    listing_id=listing.id,
                    buyer_requirement_id=req.id,
                    allocated_quantity=0,
                    farmer_asking_price=listing.expected_price,
                    ai_suggested_price=0.0,
                    agreed_price=None,
                    match_reason=no_overlap_reason,
                    status="no_overlap"
                )
                db.add(match)
                continue

            if remaining_avail <= 0.001:
                break

            alloc_qty = min(remaining_avail, req.required_quantity)
            if alloc_qty <= 0:
                continue

            # Calculate suggested price within both parties' limits (never call it fair)
            # If buyer max >= asking price: middle ground between asking price and buyer max
            # If buyer max < asking price: between minimum price and buyer max
            if req.maximum_price >= listing.expected_price:
                suggested_price = round((listing.expected_price + req.maximum_price) / 2.0, 2)
            else:
                suggested_price = round(req.maximum_price, 2)

            match_reason = (
                f"Needs {req.crop_name}, {alloc_qty:.0f} kg of {listing.quantity:.0f} kg allocated. "
                f"Located in {req.location} (~{dist_km} km away, approximate distance). "
                f"Suggested price ${suggested_price:.2f}/kg within both parties' limits "
                f"(farmer asked ${listing.expected_price:.2f}, min ${listing.minimum_price:.2f}; buyer max ${req.maximum_price:.2f})."
            )

            # Atomically reserve stock in inventory
            try:
                InventoryService.reserve_stock(db, listing.id, alloc_qty)
                remaining_avail -= alloc_qty

                match = MatchResult(
                    listing_id=listing.id,
                    buyer_requirement_id=req.id,
                    allocated_quantity=alloc_qty,
                    farmer_asking_price=listing.expected_price,
                    ai_suggested_price=suggested_price,
                    agreed_price=None,
                    match_reason=match_reason,
                    status="proposed"
                )
                db.add(match)
                matches.append(match)
            except InsufficientStockException:
                break

        db.commit()
        return matches
