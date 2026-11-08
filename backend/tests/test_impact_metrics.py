from app.models import ProduceListing, MatchResult, Order, User
from app.services.impact_service import ImpactService
from app.services.order_service import OrderService

def test_impact_metrics_separation_and_delivery_verification(db_session):
    farmer = db_session.query(User).filter(User.role == "farmer").first()
    buyer = db_session.query(User).filter(User.role == "buyer").first()

    # Create listing of 100 kg
    listing = ProduceListing(
        farmer_id=farmer.id,
        crop_name="Tomato",
        quantity=100.0,
        available_quantity=60.0,
        unit="kg",
        expected_price=1.00,
        minimum_price=0.90,
        location="Salem",
        harvest_date="2026-11-08",
        freshness_status="fresh",
        listing_status="partially_matched"
    )
    db_session.add(listing)
    db_session.commit()

    # Proposed match of 40 kg (matched but NOT delivered)
    match = MatchResult(
        listing_id=listing.id,
        buyer_requirement_id=1,
        allocated_quantity=40.0,
        farmer_asking_price=1.00,
        ai_suggested_price=1.05,
        agreed_price=1.05,
        match_reason="Proposed match",
        status="confirmed"
    )
    db_session.add(match)
    db_session.commit()

    # Step 1: Verify metrics with only matched produce
    metrics_step1 = ImpactService.get_metrics(db_session)
    assert metrics_step1["listed_quantity"] == 100.0
    assert metrics_step1["matched_quantity"] == 40.0
    assert metrics_step1["confirmed_quantity"] == 0.0
    # Strict rule: matched produce must NOT be counted as delivered or waste prevented!
    assert metrics_step1["delivered_quantity"] == 0.0
    assert metrics_step1["waste_prevented_verified_kg"] == 0.0
    assert metrics_step1["remaining_unsold_quantity"] == 60.0

    # Step 2: Order created and paid
    order = Order(
        listing_id=listing.id,
        match_id=match.id,
        farmer_id=farmer.id,
        buyer_id=buyer.id,
        quantity=40.0,
        agreed_price=1.05,
        total_amount=42.00,
        payment_status="completed",
        order_status="processing"
    )
    db_session.add(order)
    db_session.commit()

    metrics_step2 = ImpactService.get_metrics(db_session)
    assert metrics_step2["confirmed_quantity"] == 40.0
    # Paid produce is NOT yet delivered: waste prevented must still be 0.0
    assert metrics_step2["delivered_quantity"] == 0.0
    assert metrics_step2["waste_prevented_verified_kg"] == 0.0

    # Step 3: Explicit Delivery Verification
    OrderService.confirm_delivery(
        db=db_session,
        order_id=order.id,
        actor_user=buyer,
        notes="Produce inspected and verified at restaurant kitchen"
    )

    metrics_step3 = ImpactService.get_metrics(db_session)
    # ONLY now does delivered_quantity and waste prevented increase!
    assert metrics_step3["delivered_quantity"] == 40.0
    assert metrics_step3["waste_prevented_verified_kg"] == 40.0
