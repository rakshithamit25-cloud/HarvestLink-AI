from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import Order, Payment
from app.schemas import PayPalCreateOrderResponse, PayPalCaptureRequest, PaymentResponse
from app.services.paypal_service import PayPalService

router = APIRouter(prefix="/api/payments", tags=["payments"])

@router.post("/create-order/{order_id}", response_model=PayPalCreateOrderResponse)
def create_paypal_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

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
    db: Session = Depends(get_db)
):
    payment = PayPalService.capture_and_verify(
        db=db,
        order_id=order_id,
        paypal_order_id=request.paypal_order_id
    )
    return payment

@router.get("/{order_id}", response_model=PaymentResponse)
def get_payment_status(order_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")
    return payment
