import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import MatchResult, Order, User, ProduceListing, BuyerRequirement
from app.services.inventory_service import InventoryService
from app.services.audit_service import AuditService

class OrderService:
    @staticmethod
    def approve_match_by_farmer(
        db: Session,
        match_id: int,
        farmer_user: User,
        consent_method: str = "verbal",
        operator_farmer_name: str = None
    ) -> MatchResult:
        match = db.query(MatchResult).filter(MatchResult.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        listing = db.query(ProduceListing).filter(ProduceListing.id == match.listing_id).first()
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        # Authorization check: farmer themselves or operator on farmer's behalf
        if farmer_user.role == "operator":
            # Must record explicit consent
            farmer_target_name = operator_farmer_name if operator_farmer_name is not None else (listing.farmer.name if listing.farmer else None)
            AuditService.verify_and_log_operator_consent(
                db=db,
                operator_user=farmer_user,
                farmer_name=farmer_target_name,
                consent_method=consent_method,
                action="ACCEPT_MATCH",
                details=f"Operator accepted match {match_id} ({match.allocated_quantity} kg) on behalf of farmer {farmer_target_name}"
            )
        elif farmer_user.id != listing.farmer_id and farmer_user.role != "farmer":
            raise HTTPException(status_code=403, detail="Not authorized to approve this match for the farmer.")

        # State transition
        if match.status == "proposed":
            match.status = "farmer_approved"
        elif match.status == "buyer_approved":
            match.status = "confirmed"
            match.agreed_price = match.ai_suggested_price
        elif match.status in ["confirmed", "farmer_approved"]:
            pass # already approved
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve match in status '{match.status}'."
            )

        db.commit()
        db.refresh(match)
        return match

    @staticmethod
    def approve_match_by_buyer(
        db: Session,
        match_id: int,
        buyer_user: User
    ) -> MatchResult:
        match = db.query(MatchResult).filter(MatchResult.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        req = db.query(BuyerRequirement).filter(BuyerRequirement.id == match.buyer_requirement_id).first()
        if not req:
            raise HTTPException(status_code=404, detail="Buyer requirement not found")

        if buyer_user.id != req.buyer_id and buyer_user.role not in ["buyer", "operator"]:
            raise HTTPException(status_code=403, detail="Not authorized to approve for this buyer.")

        # State transition
        if match.status == "proposed":
            match.status = "buyer_approved"
        elif match.status == "farmer_approved":
            match.status = "confirmed"
            match.agreed_price = match.ai_suggested_price
        elif match.status in ["confirmed", "buyer_approved"]:
            pass
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve match in status '{match.status}'."
            )

        db.commit()
        db.refresh(match)
        return match

    @staticmethod
    def reject_match(db: Session, match_id: int, actor_user: User, reason: str = "") -> MatchResult:
        match = db.query(MatchResult).filter(MatchResult.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        if match.status == "rejected":
            return match

        # Release stock back to inventory atomically
        if match.allocated_quantity > 0:
            InventoryService.release_stock(db, match.listing_id, match.allocated_quantity)

        match.status = "rejected"
        match.match_reason += f" | Rejected by {actor_user.role} ({actor_user.name}): {reason}"
        db.commit()
        db.refresh(match)
        return match

    @staticmethod
    def create_order_from_confirmed_match(db: Session, match_id: int) -> Order:
        """
        Creates an Order strictly from a 'confirmed' match.
        Guarantees that both farmer and buyer have approved.
        """
        match = db.query(MatchResult).filter(MatchResult.id == match_id).first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")

        if match.status != "confirmed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Order cannot be created: deal status is '{match.status}'. Both farmer and buyer approval are required."
            )

        # Check if order already exists for this match
        existing_order = db.query(Order).filter(Order.match_id == match.id).first()
        if existing_order:
            return existing_order

        listing = db.query(ProduceListing).filter(ProduceListing.id == match.listing_id).first()
        req = db.query(BuyerRequirement).filter(BuyerRequirement.id == match.buyer_requirement_id).first()

        total_amount = round(match.allocated_quantity * match.agreed_price, 2)
        
        order = Order(
            listing_id=listing.id,
            match_id=match.id,
            farmer_id=listing.farmer_id,
            buyer_id=req.buyer_id,
            quantity=match.allocated_quantity,
            agreed_price=match.agreed_price,
            total_amount=total_amount,
            payment_status="pending",
            order_status="created",
            created_at=datetime.datetime.utcnow()
        )
        db.add(order)
        db.commit()
        db.refresh(order)
        return order

    @staticmethod
    def confirm_delivery(
        db: Session,
        order_id: int,
        actor_user: User,
        consent_method: str = None,
        farmer_name: str = None,
        notes: str = ""
    ) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.payment_status != "completed":
            raise HTTPException(
                status_code=400,
                detail="Cannot confirm delivery on an unpaid order."
            )

        if actor_user.role == "operator":
            AuditService.verify_and_log_operator_consent(
                db=db,
                operator_user=actor_user,
                farmer_name=farmer_name or "Farmer",
                consent_method=consent_method or "verbal",
                action="CONFIRM_DELIVERY",
                details=f"Operator verified delivery for Order #{order_id}: {notes}"
            )

        order.order_status = "delivered"
        order.delivery_verified_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(order)
        return order
