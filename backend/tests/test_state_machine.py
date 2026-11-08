import pytest
from fastapi import HTTPException
from app.models import ProduceListing, BuyerRequirement, MatchResult, User
from app.services.order_service import OrderService

def test_order_cannot_be_created_without_both_approvals(db_session):
    farmer = db_session.query(User).filter(User.role == "farmer").first()
    buyer = db_session.query(User).filter(User.role == "buyer").first()

    listing = ProduceListing(
        farmer_id=farmer.id,
        crop_name="Tomato",
        quantity=50.0,
        available_quantity=50.0,
        unit="kg",
        expected_price=1.00,
        minimum_price=0.90,
        location="Salem",
        harvest_date="2026-11-08",
        freshness_status="fresh",
        listing_status="active"
    )
    req = BuyerRequirement(
        buyer_id=buyer.id,
        buyer_name="Restaurant A",
        crop_name="Tomato",
        required_quantity=50.0,
        maximum_price=1.20,
        location="Salem",
        required_date="2026-11-10",
        status="open"
    )
    db_session.add_all([listing, req])
    db_session.commit()

    match = MatchResult(
        listing_id=listing.id,
        buyer_requirement_id=req.id,
        allocated_quantity=50.0,
        farmer_asking_price=1.00,
        ai_suggested_price=1.10,
        agreed_price=None,
        match_reason="Matches criteria",
        status="proposed"
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)

    # 1. Attempt to create order while still in 'proposed' status -> MUST FAIL
    with pytest.raises(HTTPException) as exc_1:
        OrderService.create_order_from_confirmed_match(db_session, match.id)
    assert exc_1.value.status_code == 400
    assert "Both farmer and buyer approval are required" in exc_1.value.detail

    # 2. Farmer approves -> status becomes 'farmer_approved'
    OrderService.approve_match_by_farmer(db_session, match.id, farmer, consent_method="verbal", operator_farmer_name="Kumar")
    db_session.refresh(match)
    assert match.status == "farmer_approved"
    assert match.agreed_price is None

    # Attempt to create order with only farmer approval -> MUST STILL FAIL
    with pytest.raises(HTTPException) as exc_2:
        OrderService.create_order_from_confirmed_match(db_session, match.id)
    assert exc_2.value.status_code == 400

    # 3. Buyer approves -> status becomes 'confirmed' and agreed_price is locked
    OrderService.approve_match_by_buyer(db_session, match.id, buyer)
    db_session.refresh(match)
    assert match.status == "confirmed"
    assert match.agreed_price == 1.10

    # 4. Now order creation MUST SUCCEED
    order = OrderService.create_order_from_confirmed_match(db_session, match.id)
    assert order is not None
    assert order.quantity == 50.0
    assert order.agreed_price == 1.10
    assert order.total_amount == 55.00
