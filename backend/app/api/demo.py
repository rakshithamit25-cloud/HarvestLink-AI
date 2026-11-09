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
    # Check if already seeded
    if db.query(User).count() > 0:
        return

    # Seed Users
    farmer_kumar = User(
        name="Kumar",
        email="kumar@harvestlink.org",
        hashed_password=hash_password("farmer123"),
        role="farmer",
        phone="+91-9876543210",
        preferred_language="ta"
    )
    buyer_restaurant_a = User(
        name="Restaurant A (Salem)",
        email="restaurant_a@harvestlink.org",
        hashed_password=hash_password("buyer123"),
        role="buyer",
        phone="+91-9876543211",
        preferred_language="en"
    )
    buyer_supermarket_b = User(
        name="Supermarket B (Erode)",
        email="supermarket_b@harvestlink.org",
        hashed_password=hash_password("buyer123"),
        role="buyer",
        phone="+91-9876543212",
        preferred_language="en"
    )
    buyer_processor_c = User(
        name="Food Processor C (Namakkal)",
        email="processor_c@harvestlink.org",
        hashed_password=hash_password("buyer123"),
        role="buyer",
        phone="+91-9876543213",
        preferred_language="en"
    )
    operator_selvi = User(
        name="Selvi (FPO Operator)",
        email="selvi@harvestlink.org",
        hashed_password=hash_password("operator123"),
        role="operator",
        phone="+91-9876543214",
        preferred_language="ta"
    )

    db.add_all([farmer_kumar, buyer_restaurant_a, buyer_supermarket_b, buyer_processor_c, operator_selvi])
    db.commit()
    db.refresh(farmer_kumar)
    db.refresh(buyer_restaurant_a)
    db.refresh(buyer_supermarket_b)
    db.refresh(buyer_processor_c)

    # Seed Buyer Requirements
    req_a = BuyerRequirement(
        buyer_id=buyer_restaurant_a.id,
        buyer_name="Restaurant A",
        crop_name="Tomato",
        required_quantity=100.0,
        maximum_price=1.20,
        location="Salem",
        required_date="2026-11-10",
        status="open"
    )
    req_b = BuyerRequirement(
        buyer_id=buyer_supermarket_b.id,
        buyer_name="Supermarket B",
        crop_name="Tomato",
        required_quantity=200.0,
        maximum_price=1.05,
        location="Erode",
        required_date="2026-11-11",
        status="open"
    )
    req_c = BuyerRequirement(
        buyer_id=buyer_processor_c.id,
        buyer_name="Food Processor C",
        crop_name="Tomato",
        required_quantity=150.0,
        maximum_price=0.95,
        location="Namakkal",
        required_date="2026-11-12",
        status="open"
    )
    db.add_all([req_a, req_b, req_c])
    db.commit()

    # Seed Farmer Kumar's Produce Listing
    listing_kumar = ProduceListing(
        farmer_id=farmer_kumar.id,
        crop_name="Tomato",
        quantity=500.0,
        available_quantity=500.0,
        unit="kg",
        expected_price=1.00,
        minimum_price=0.90,  # Kumar minimum $0.90 enables genuine overlap with Buyer C (max $0.95)
        location="Salem",
        harvest_date="2026-11-08",
        freshness_status="fresh",
        listing_status="active"
    )
    db.add(listing_kumar)
    db.commit()

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

    # 2. Retrieve Kumar's listing
    listing = db.query(ProduceListing).first()
    farmer = db.query(User).filter(User.role == "farmer").first()
    
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
