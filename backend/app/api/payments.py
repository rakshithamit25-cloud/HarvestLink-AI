from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import Order, Payment, User, MatchResult
from app.schemas import PayPalCreateOrderResponse, PayPalCaptureRequest, PaymentResponse
from app.services.paypal_service import PayPalService
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.post("/create-order/{order_id}", response_model=PayPalCreateOrderResponse)
def create_paypal_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Only the authenticated buyer associated with the order can create payment
    if current_user.role != "buyer" or order.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the designated buyer for this order can initiate payment."
        )

    # Reject cancelled, rejected, delivered or invalid orders
    if order.order_status in ["cancelled", "delivered", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create payment for order in status '{order.order_status}'."
        )

    # Validate order state: payment creation permitted only after both farmer and buyer approvals
    if order.match_id:
        match = db.query(MatchResult).filter(MatchResult.id == order.match_id).first()
        if not match or match.status != "confirmed":
            current_status = match.status if match else "missing"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment creation is permitted only after both farmer and buyer approvals. Deal status is '{current_status}'."
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment creation is permitted only after both farmer and buyer approvals. Order has no associated confirmed match."
        )

    payment, approval_url = PayPalService.create_order(db, order)

    mock_notice = (
        "MOCK MODE - no real PayPal call. Real Sandbox Orders v2 will activate when PAYPAL_CLIENT_ID & SECRET are configured."
        if payment.is_mock else None
    )

    return {
        "order_id": order.id,
        "paypal_order_id": payment.paypal_order_id,
        "status": payment.status,
        "approval_url": approval_url,
        "is_mock": payment.is_mock,
        "mock_mode_notice": mock_notice
    }

@router.post("/capture/{order_id}", response_model=PaymentResponse)
def capture_paypal_order(
    order_id: int,
    request: PayPalCaptureRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Only the authenticated buyer associated with the order can capture payment
    if current_user.role != "buyer" or order.buyer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the designated buyer for this order can capture payment."
        )

    # Reject cancelled, rejected, delivered or invalid orders during capture
    if order.order_status in ["cancelled", "delivered", "rejected"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot capture payment for order in status '{order.order_status}'."
        )

    payment = PayPalService.capture_and_verify(
        db=db,
        order_id=order_id,
        paypal_order_id=request.paypal_order_id
    )
    return payment

@router.get("/{order_id}", response_model=PaymentResponse)
def get_payment_status(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if current_user.id not in [order.buyer_id, order.farmer_id]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view payment details for this order."
        )

    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return payment
