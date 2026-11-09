from unittest.mock import patch, MagicMock
import pytest
from fastapi import HTTPException
from app.models import Order, Payment, ProduceListing, User, MatchResult, BuyerRequirement
from app.services.paypal_service import PayPalService
from app.api.payments import create_paypal_order, capture_paypal_order
from app.schemas import PayPalCaptureRequest
from app.api.deps import get_current_user

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


def _setup_test_order_with_match(db_session, buyer_user, match_status="confirmed", order_status="created"):
    farmer = db_session.query(User).filter(User.role == "farmer").first()
    listing = ProduceListing(
        farmer_id=farmer.id,
        crop_name="Tomato",
        quantity=100.0,
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

    req = BuyerRequirement(
        buyer_id=buyer_user.id,
        buyer_name=buyer_user.name,
        crop_name="Tomato",
        required_quantity=50.0,
        maximum_price=1.20,
        location="Salem",
        required_date="2026-11-10",
        status="open"
    )
    db_session.add(req)
    db_session.commit()

    match = MatchResult(
        listing_id=listing.id,
        buyer_requirement_id=req.id,
        allocated_quantity=50.0,
        farmer_asking_price=1.00,
        ai_suggested_price=1.00,
        agreed_price=1.00 if match_status == "confirmed" else None,
        match_reason="Direct match",
        status=match_status
    )
    db_session.add(match)
    db_session.commit()

    order = Order(
        listing_id=listing.id,
        match_id=match.id,
        farmer_id=farmer.id,
        buyer_id=buyer_user.id,
        quantity=50.0,
        agreed_price=1.00,
        total_amount=50.00,
        payment_status="pending",
        order_status=order_status
    )
    db_session.add(order)
    db_session.commit()
    db_session.refresh(order)
    return order, match


def test_unauthenticated_payment_creation_rejected(db_session):
    """Unauthenticated access to payment creation must be rejected with HTTP 401."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization=None, db=db_session)
    assert exc_info.value.status_code == 401
    assert "Missing Authorization header" in exc_info.value.detail


def test_unauthenticated_capture_rejected(db_session):
    """Unauthenticated access to payment capture must be rejected with HTTP 401."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization="", db=db_session)
    assert exc_info.value.status_code == 401


def test_buyer_a_cannot_create_payment_for_buyer_b_order(db_session):
    """Buyer A cannot create payment for Buyer B's order (HTTP 403 Forbidden)."""
    buyers = db_session.query(User).filter(User.role == "buyer").all()
    buyer_a = buyers[0]
    buyer_b = buyers[1]

    order_b, _ = _setup_test_order_with_match(db_session, buyer_b, match_status="confirmed")

    with pytest.raises(HTTPException) as exc_info:
        create_paypal_order(order_id=order_b.id, db=db_session, current_user=buyer_a)
    assert exc_info.value.status_code == 403
    assert "Only the designated buyer" in exc_info.value.detail


def test_buyer_a_cannot_capture_buyer_b_order(db_session):
    """Buyer A cannot capture payment for Buyer B's order (HTTP 403 Forbidden)."""
    buyers = db_session.query(User).filter(User.role == "buyer").all()
    buyer_a = buyers[0]
    buyer_b = buyers[1]

    order_b, _ = _setup_test_order_with_match(db_session, buyer_b, match_status="confirmed")
    payment_b, _ = PayPalService.create_order(db_session, order_b)

    with pytest.raises(HTTPException) as exc_info:
        capture_paypal_order(
            order_id=order_b.id,
            request=PayPalCaptureRequest(paypal_order_id=payment_b.paypal_order_id),
            db=db_session,
            current_user=buyer_a
        )
    assert exc_info.value.status_code == 403
    assert "Only the designated buyer" in exc_info.value.detail


def test_unapproved_order_cannot_create_payment(db_session):
    """Unapproved order (unconfirmed match or cancelled status) cannot create payment (HTTP 400)."""
    buyer = db_session.query(User).filter(User.role == "buyer").first()

    # Case 1: Match is still 'proposed' (neither approved)
    order_unapproved, _ = _setup_test_order_with_match(db_session, buyer, match_status="proposed")
    with pytest.raises(HTTPException) as exc_info:
        create_paypal_order(order_id=order_unapproved.id, db=db_session, current_user=buyer)
    assert exc_info.value.status_code == 400
    assert "both farmer and buyer approvals" in exc_info.value.detail

    # Case 2: Order is cancelled
    order_cancelled, _ = _setup_test_order_with_match(db_session, buyer, match_status="confirmed", order_status="cancelled")
    with pytest.raises(HTTPException) as exc_info_cancel:
        create_paypal_order(order_id=order_cancelled.id, db=db_session, current_user=buyer)
    assert exc_info_cancel.value.status_code == 400
    assert "Cannot create payment for order in status 'cancelled'" in exc_info_cancel.value.detail


def test_approved_buyer_can_create_payment(db_session):
    """Approved buyer with confirmed order can successfully create and capture payment."""
    buyer = db_session.query(User).filter(User.role == "buyer").first()
    order, _ = _setup_test_order_with_match(db_session, buyer, match_status="confirmed")

    # 1. Create PayPal Order
    response = create_paypal_order(order_id=order.id, db=db_session, current_user=buyer)
    assert response["order_id"] == order.id
    assert response["status"] == "created"
    assert response["is_mock"] is True
    assert "paypal_order_id" in response

    # 2. Capture PayPal Order
    captured = capture_paypal_order(
        order_id=order.id,
        request=PayPalCaptureRequest(paypal_order_id=response["paypal_order_id"]),
        db=db_session,
        current_user=buyer
    )
    assert captured.status == "completed"
    assert captured.paypal_capture_id is not None
    db_session.refresh(order)
    assert order.payment_status == "completed"
    assert order.order_status == "processing"

