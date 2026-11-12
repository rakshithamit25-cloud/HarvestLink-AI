import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db, Base, engine
from app.models import User, ProduceListing, BuyerRequirement, MatchResult, Order, Payment, AgentLog, AuditLog
from app.core.security import hash_password
from app.core.config import settings
from app.agents.workflow import execute_matching_pipeline
from app.services.order_service import OrderService
from app.services.paypal_service import PayPalService

router = APIRouter(prefix="/api/demo", tags=["demo"])

def _require_demo_mode():
    """Raise 403 if DEMO_MODE is not enabled."""
    if not settings.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Demo mode is disabled")

def seed_database(db: Session):
    """
    Idempotently seeds demo users, listings, buyer requirements, and match proposals
    for Tomato, Onion, Potato, and Carrot.
    Safe to run repeatedly on startup or reset without duplicating records.
    """
    # 1. Seed Users if not present
    farmer_kumar = db.query(User).filter(User.email == "kumar@harvestlink.org").first()
    if not farmer_kumar:
        farmer_kumar = User(
            name="Kumar",
            email="kumar@harvestlink.org",
            hashed_password=hash_password("farmer123"),
            role="farmer",
            phone="+91-9876543210",
            preferred_language="ta"
        )
        db.add(farmer_kumar)

    buyer_restaurant_a = db.query(User).filter(User.email == "restaurant_a@harvestlink.org").first()
    if not buyer_restaurant_a:
        buyer_restaurant_a = User(
            name="Restaurant A (Salem)",
            email="restaurant_a@harvestlink.org",
            hashed_password=hash_password("buyer123"),
            role="buyer",
            phone="+91-9876543211",
            preferred_language="en"
        )
        db.add(buyer_restaurant_a)

    buyer_supermarket_b = db.query(User).filter(User.email == "supermarket_b@harvestlink.org").first()
    if not buyer_supermarket_b:
        buyer_supermarket_b = User(
            name="Supermarket B (Erode)",
            email="supermarket_b@harvestlink.org",
            hashed_password=hash_password("buyer123"),
            role="buyer",
            phone="+91-9876543212",
            preferred_language="en"
        )
        db.add(buyer_supermarket_b)

    buyer_processor_c = db.query(User).filter(User.email == "processor_c@harvestlink.org").first()
    if not buyer_processor_c:
        buyer_processor_c = User(
            name="Food Processor C (Namakkal)",
            email="processor_c@harvestlink.org",
            hashed_password=hash_password("buyer123"),
            role="buyer",
            phone="+91-9876543213",
            preferred_language="en"
        )
        db.add(buyer_processor_c)

    operator_selvi = db.query(User).filter(User.email == "selvi@harvestlink.org").first()
    if not operator_selvi:
        operator_selvi = User(
            name="Selvi (FPO Operator)",
            email="selvi@harvestlink.org",
            hashed_password=hash_password("operator123"),
            role="operator",
            phone="+91-9876543214",
            preferred_language="ta"
        )
        db.add(operator_selvi)

    db.commit()
    db.refresh(farmer_kumar)
    db.refresh(buyer_restaurant_a)
    db.refresh(buyer_supermarket_b)
    db.refresh(buyer_processor_c)
    db.refresh(operator_selvi)

    # 2. Seed Demo Produce Listings & Buyer Requirements for 4 core crops
    demo_crops = [
        {
            "crop_name": "Tomato",
            "quantity": 500.0,
            "expected_price": 1.00,
            "minimum_price": 0.90,
            "location": "Salem",
            "harvest_date": "2026-11-08",
            "freshness_status": "fresh",
            "requirements": [
                {
                    "buyer_id": buyer_restaurant_a.id,
                    "buyer_name": "Restaurant A",
                    "quantity": 100.0,
                    "max_price": 1.20,
                    "location": "Salem",
                    "date": "2026-11-10",
                },
                {
                    "buyer_id": buyer_supermarket_b.id,
                    "buyer_name": "Supermarket B",
                    "quantity": 200.0,
                    "max_price": 1.05,
                    "location": "Erode",
                    "date": "2026-11-11",
                },
                {
                    "buyer_id": buyer_processor_c.id,
                    "buyer_name": "Food Processor C",
                    "quantity": 150.0,
                    "max_price": 0.95,
                    "location": "Namakkal",
                    "date": "2026-11-12",
                },
            ],
        },
        {
            "crop_name": "Onion",
            "quantity": 600.0,
            "expected_price": 0.80,
            "minimum_price": 0.70,
            "location": "Salem",
            "harvest_date": "2026-11-08",
            "freshness_status": "fresh",
            "requirements": [
                {
                    "buyer_id": buyer_restaurant_a.id,
                    "buyer_name": "Restaurant A",
                    "quantity": 150.0,
                    "max_price": 0.90,
                    "location": "Salem",
                    "date": "2026-11-10",
                },
                {
                    "buyer_id": buyer_supermarket_b.id,
                    "buyer_name": "Supermarket B",
                    "quantity": 250.0,
                    "max_price": 0.85,
                    "location": "Erode",
                    "date": "2026-11-11",
                },
                {
                    "buyer_id": buyer_processor_c.id,
                    "buyer_name": "Food Processor C",
                    "quantity": 200.0,
                    "max_price": 0.75,
                    "location": "Namakkal",
                    "date": "2026-11-12",
                },
            ],
        },
        {
            "crop_name": "Potato",
            "quantity": 800.0,
            "expected_price": 0.70,
            "minimum_price": 0.60,
            "location": "Salem",
            "harvest_date": "2026-11-08",
            "freshness_status": "fresh",
            "requirements": [
                {
                    "buyer_id": buyer_restaurant_a.id,
                    "buyer_name": "Restaurant A",
                    "quantity": 200.0,
                    "max_price": 0.80,
                    "location": "Salem",
                    "date": "2026-11-10",
                },
                {
                    "buyer_id": buyer_supermarket_b.id,
                    "buyer_name": "Supermarket B",
                    "quantity": 300.0,
                    "max_price": 0.75,
                    "location": "Erode",
                    "date": "2026-11-11",
                },
                {
                    "buyer_id": buyer_processor_c.id,
                    "buyer_name": "Food Processor C",
                    "quantity": 300.0,
                    "max_price": 0.65,
                    "location": "Namakkal",
                    "date": "2026-11-12",
                },
            ],
        },
        {
            "crop_name": "Carrot",
            "quantity": 400.0,
            "expected_price": 1.20,
            "minimum_price": 1.00,
            "location": "Salem",
            "harvest_date": "2026-11-08",
            "freshness_status": "fresh",
            "requirements": [
                {
                    "buyer_id": buyer_restaurant_a.id,
                    "buyer_name": "Restaurant A",
                    "quantity": 100.0,
                    "max_price": 1.35,
                    "location": "Salem",
                    "date": "2026-11-10",
                },
                {
                    "buyer_id": buyer_supermarket_b.id,
                    "buyer_name": "Supermarket B",
                    "quantity": 150.0,
                    "max_price": 1.25,
                    "location": "Erode",
                    "date": "2026-11-11",
                },
                {
                    "buyer_id": buyer_processor_c.id,
                    "buyer_name": "Food Processor C",
                    "quantity": 150.0,
                    "max_price": 1.10,
                    "location": "Namakkal",
                    "date": "2026-11-12",
                },
            ],
        },
    ]

    for crop_data in demo_crops:
        # Idempotently check listing
        listing = db.query(ProduceListing).filter(
            ProduceListing.farmer_id == farmer_kumar.id,
            ProduceListing.crop_name == crop_data["crop_name"]
        ).first()

        if not listing:
            listing = ProduceListing(
                farmer_id=farmer_kumar.id,
                crop_name=crop_data["crop_name"],
                quantity=crop_data["quantity"],
                available_quantity=crop_data["quantity"],
                unit="kg",
                expected_price=crop_data["expected_price"],
                minimum_price=crop_data["minimum_price"],
                location=crop_data["location"],
                harvest_date=crop_data["harvest_date"],
                freshness_status=crop_data["freshness_status"],
                listing_status="active"
            )
            db.add(listing)
            db.commit()
            db.refresh(listing)

        # Idempotently check requirements — with deduplication guard
        for req_data in crop_data["requirements"]:
            # Fetch ALL rows for this (buyer_id, crop_name) pair to catch legacy duplicates
            all_matching = db.query(BuyerRequirement).filter(
                BuyerRequirement.buyer_id == req_data["buyer_id"],
                BuyerRequirement.crop_name == crop_data["crop_name"]
            ).order_by(BuyerRequirement.id).all()

            if not all_matching:
                # Create the canonical requirement
                new_req = BuyerRequirement(
                    buyer_id=req_data["buyer_id"],
                    buyer_name=req_data["buyer_name"],
                    crop_name=crop_data["crop_name"],
                    required_quantity=req_data["quantity"],
                    maximum_price=req_data["max_price"],
                    location=req_data["location"],
                    required_date=req_data["date"],
                    status="open"
                )
                db.add(new_req)
            else:
                # Keep the first (lowest-id = earliest canonical) row; remove any extras
                canonical = all_matching[0]
                for extra in all_matching[1:]:
                    # Only remove extras that have no completed payment-linked MatchResult
                    extra_matches = db.query(MatchResult).filter(
                        MatchResult.buyer_requirement_id == extra.id,
                        MatchResult.status == "confirmed"
                    ).count()
                    if extra_matches == 0:
                        # Delete any unconfirmed MatchResults for this extra req first
                        db.query(MatchResult).filter(
                            MatchResult.buyer_requirement_id == extra.id,
                            MatchResult.status != "confirmed"
                        ).delete()
                        db.delete(extra)

                # Normalize buyer_name and location on the canonical row
                canonical.buyer_name = req_data["buyer_name"]
                canonical.location = req_data["location"]
        db.commit()

        # Idempotently execute matching pipeline if no matches exist yet for this listing
        match_count = db.query(MatchResult).filter(MatchResult.listing_id == listing.id).count()
        if match_count == 0:
            execute_matching_pipeline(db, listing, mode="rule-based")

@router.post("/reset")
def reset_database(db: Session = Depends(get_db)):
    """
    Clears all tables and reseeds pristine Kumar demo data.
    Requires DEMO_MODE=true.
    """
    _require_demo_mode()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database(db)
    return {"status": "success", "message": "Demo data reset successfully."}

@router.post("/run-scenario")
async def run_kumar_demo_scenario(db: Session = Depends(get_db)):
    """
    Runs the complete Kumar end-to-end demo scenario.
    Requires DEMO_MODE=true.
    """
    _require_demo_mode()
    # 1. Reset first for deterministic replay
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_database(db)

    # 2. Retrieve Kumar's Tomato listing
    listing = db.query(ProduceListing).filter(ProduceListing.crop_name == "Tomato").first()
    farmer = db.query(User).filter(User.role == "farmer").first()

    # Reset Tomato listing matches and stock so the scenario replays deterministically
    db.query(MatchResult).filter(MatchResult.listing_id == listing.id).delete()
    listing.available_quantity = listing.quantity
    listing.listing_status = "active"
    db.commit()
    
    # 3. Execute Multi-Agent Pipeline
    agent_state = execute_matching_pipeline(db, listing, mode="rule-based")

    # 4. Approve all proposed matches by both farmer and buyers
    matches = db.query(MatchResult).filter(MatchResult.listing_id == listing.id, MatchResult.allocated_quantity > 0).all()
    created_orders = []

    for match in matches:
        # Farmer approves
        OrderService.approve_match_by_farmer(db, match.id, farmer, consent_method="verbal", operator_farmer_name="Kumar")
        
        # Buyer approves
        buyer = db.query(User).filter(User.id == match.buyer_requirement.buyer_id).first()
        OrderService.approve_match_by_buyer(db, match.id, buyer)
        
        # Order generated from confirmed match
        order = OrderService.create_order_from_confirmed_match(db, match.id)
        
        # PayPal Sandbox order create + capture verification
        payment, approval_url = PayPalService.create_order(db, order)
        verified_payment = PayPalService.capture_and_verify(db, order.id, payment.paypal_order_id)
        
        created_orders.append({
            "order_id": order.id,
            "buyer": buyer.name,
            "quantity_kg": order.quantity,
            "agreed_price": order.agreed_price,
            "total_usd": order.total_amount,
            "payment_status": order.payment_status,
            "paypal_order_id": verified_payment.paypal_order_id,
            "paypal_capture_id": verified_payment.paypal_capture_id,
            "is_mock": verified_payment.is_mock
        })

    # 5. Check remaining inventory
    db.refresh(listing)

    return {
        "scenario": "Kumar 500kg Tomato Allocation & PayPal Sandbox Settlement",
        "initial_quantity_kg": listing.quantity,
        "total_allocated_kg": sum(o["quantity_kg"] for o in created_orders),
        "remaining_inventory_kg": listing.available_quantity,
        "is_inventory_consistent": (listing.quantity - sum(o["quantity_kg"] for o in created_orders)) == listing.available_quantity,
        "orders_count": len(created_orders),
        "orders": created_orders,
        "agent_logs": agent_state["agent_logs"]
    }
