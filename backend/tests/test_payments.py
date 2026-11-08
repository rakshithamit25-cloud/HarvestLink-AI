from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from app.models import Order, Payment, ProduceListing, User
from app.services.paypal_service import PayPalService

def test_failed_or_error_payment_leaves_order_unpaid(db_session):
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

    # 1. Create PayPal Order
    payment, approval_url = PayPalService.create_order(db_session, order)
    payment.is_mock = False
    db_session.commit()
    assert payment.status == "created"
    assert order.payment_status == "created"

    # 2. Simulate PayPal error / failure during capture (mocking a PayPal API error)
    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.text = '{"name":"UNPROCESSABLE_ENTITY","message":"The requested action could not be performed"}'
        mock_post.return_value = mock_resp

        with patch.object(PayPalService, "_is_mock", return_value=False):
            with patch.object(PayPalService, "get_access_token", return_value="fake_token"):
                try:
                    PayPalService.capture_and_verify(db_session, order.id, payment.paypal_order_id)
                    assert False, "Expected HTTPException 502"
                except HTTPException as exc_info:
                    assert exc_info.status_code == 502

    # Verify order state remained failed/unpaid
    db_session.refresh(order)
    db_session.refresh(payment)
    assert order.payment_status == "failed"
    assert payment.status == "failed"
    assert order.order_status == "created"

def test_duplicate_capture_idempotency(db_session):
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

    payment, approval_url = PayPalService.create_order(db_session, order)
    
    # First capture
    verified_1 = PayPalService.capture_and_verify(db_session, order.id, payment.paypal_order_id)
    assert verified_1.status == "completed"

    # Repeated capture request (simulating double-click or network retry)
    verified_2 = PayPalService.capture_and_verify(db_session, order.id, payment.paypal_order_id)
    assert verified_2.id == verified_1.id
    assert verified_2.status == "completed"

    # Verify that only ONE payment record exists in DB for this order
    payment_records = db_session.query(Payment).filter(Payment.order_id == order.id).all()
    assert len(payment_records) == 1, "Only one payment record must exist per order (duplicate protection)."
