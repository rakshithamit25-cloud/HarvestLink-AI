import pytest
from app.models import ProduceListing, BuyerRequirement, MatchResult, Order, User
from app.agents.workflow import execute_matching_pipeline
from app.services.order_service import OrderService
from app.services.paypal_service import PayPalService

def test_complete_kumar_scenario(db_session):
    # 1. Setup Kumar's produce listing (500 kg Tomatoes)
    kumar = db_session.query(User).filter(User.role == "farmer").first()
    listing = ProduceListing(
        farmer_id=kumar.id,
        crop_name="Tomato",
        quantity=500.0,
        available_quantity=500.0,
        unit="kg",
        expected_price=1.00,
        minimum_price=0.90,
        location="Salem",
        harvest_date="2026-11-08",
        freshness_status="fresh",
        listing_status="active"
    )
    db_session.add(listing)

    # 2. Setup 3 buyers
    buyers = db_session.query(User).filter(User.role == "buyer").all()
    req_a = BuyerRequirement(
        buyer_id=buyers[0].id,
        buyer_name="Restaurant A",
        crop_name="Tomato",
        required_quantity=100.0,
        maximum_price=1.20,
        location="Salem",
        required_date="2026-11-10",
        status="open"
    )
    req_b = BuyerRequirement(
        buyer_id=buyers[1].id,
        buyer_name="Supermarket B",
        crop_name="Tomato",
        required_quantity=200.0,
        maximum_price=1.05,
        location="Erode",
        required_date="2026-11-11",
        status="open"
    )
    req_c = BuyerRequirement(
        buyer_id=buyers[2].id,
        buyer_name="Food Processor C",
        crop_name="Tomato",
        required_quantity=150.0,
        maximum_price=0.95,
        location="Namakkal",
        required_date="2026-11-12",
        status="open"
    )
    db_session.add_all([req_a, req_b, req_c])
    db_session.commit()

    # 3. Execute Multi-Agent pipeline
    state = execute_matching_pipeline(db_session, listing, mode="rule-based")
    
    # Check matching proposals
    matches = db_session.query(MatchResult).filter(
        MatchResult.listing_id == listing.id,
        MatchResult.allocated_quantity > 0
    ).all()
    
    assert len(matches) == 3, f"Expected 3 matches, got {len(matches)}"
    total_allocated = sum(m.allocated_quantity for m in matches)
    assert total_allocated == 450.0, f"Expected 450 kg allocated, got {total_allocated}"
    
    # Check remaining inventory
    db_session.refresh(listing)
    assert listing.available_quantity == 50.0, f"Expected 50 kg remaining, got {listing.available_quantity}"
    assert listing.listing_status == "partially_matched"

    # 4. Consent and Order Creation
    orders = []
    for m in matches:
        # Farmer approves
        OrderService.approve_match_by_farmer(db_session, m.id, kumar, consent_method="verbal", operator_farmer_name="Kumar")
        # Buyer approves
        buyer_user = db_session.query(User).filter(User.id == m.buyer_requirement.buyer_id).first()
        OrderService.approve_match_by_buyer(db_session, m.id, buyer_user)
        
        # Order generated
        order = OrderService.create_order_from_confirmed_match(db_session, m.id)
        assert order is not None
        assert order.payment_status == "pending"
        
        # PayPal Sandbox checkout & capture
        payment, approval_url = PayPalService.create_order(db_session, order)
        assert payment is not None
        assert payment.status == "created"
        
        verified_payment = PayPalService.capture_and_verify(db_session, order.id, payment.paypal_order_id)
        assert verified_payment.status == "completed"
        assert order.payment_status == "completed"
        orders.append(order)

    assert len(orders) == 3
    assert sum(o.quantity for o in orders) == 450.0
    
    # Verify accurate totals (quantity * agreed_price)
    for o in orders:
        assert round(o.quantity * o.agreed_price, 2) == round(o.total_amount, 2)
