import pytest
from fastapi import HTTPException
from app.models import Order, ProduceListing, User
from app.api.orders import direct_order_status_update

def test_frontend_cannot_mark_order_paid(db_session):
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
    db_session.add(listing)
    db_session.commit()

    order = Order(
        listing_id=listing.id,
        farmer_id=farmer.id,
        buyer_id=buyer.id,
        quantity=50.0,
        agreed_price=1.00,
        total_amount=50.00,
        payment_status="pending",
        order_status="created"
    )
    db_session.add(order)
    db_session.commit()

    # Attempt to directly mutate order payment_status to 'completed'
    # Backend strictly prohibits direct status updates and raises HTTP 403 Forbidden
    with pytest.raises(HTTPException) as exc_info:
        direct_order_status_update()
    
    assert exc_info.value.status_code == 403
    assert "strictly prohibited" in exc_info.value.detail

    # Verify database was completely unaffected
    db_session.refresh(order)
    assert order.payment_status == "pending"
