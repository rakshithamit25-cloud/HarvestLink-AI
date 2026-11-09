import json
import uuid
import datetime
import httpx
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.config import settings
from app.models import Order, Payment

class PayPalService:
    @staticmethod
    def _is_mock() -> bool:
        return (
            settings.PAYPAL_MODE == "mock" or
            not settings.PAYPAL_CLIENT_ID or
            settings.PAYPAL_CLIENT_ID == "mock_client_id" or
            not settings.PAYPAL_CLIENT_SECRET
        )

    @staticmethod
    def get_access_token() -> str:
        """
        Retrieves OAuth2 Bearer token from PayPal Sandbox REST API
        using client_id and client_secret.
        """
        if PayPalService._is_mock():
            return "mock_sandbox_access_token"

        auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET)
        data = {"grant_type": "client_credentials"}
        headers = {"Accept": "application/json", "Accept-Language": "en_US"}
        
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{settings.PAYPAL_API_BASE_URL}/v1/oauth2/token",
                auth=auth,
                data=data,
                headers=headers
            )
            if resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to obtain PayPal OAuth token: {resp.text}"
                )
            token_data = resp.json()
            return token_data.get("access_token", "")

    @staticmethod
    def create_order(
        db: Session,
        order: Order,
        return_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Tuple[Payment, str]:
        """
        Creates a PayPal Order v2 with intent CAPTURE.
        Uses idempotency header PayPal-Request-Id.
        Guarantees duplicate protection: 1 payment record per order.
        """
        existing_payment = db.query(Payment).filter(Payment.order_id == order.id).first()
        if existing_payment and existing_payment.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment for this order has already been completed."
            )
            
        if order.order_status in ["cancelled", "delivered", "rejected"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot create payment for order in status '{order.order_status}'."
            )

        if order.match and order.match.status != "confirmed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment creation is permitted only after both farmer and buyer approvals. Deal status is '{order.match.status}'."
            )

        if existing_payment and existing_payment.paypal_order_id:
            approval_url = (
                f"https://www.sandbox.paypal.com/checkoutnow?token={existing_payment.paypal_order_id}"
                if not existing_payment.is_mock else
                f"{settings.FRONTEND_URL}/checkout?order_id={order.id}&paypal_order_id={existing_payment.paypal_order_id}&mock=true"
            )
            return existing_payment, approval_url

        idempotency_key = f"HL-PAY-{order.id}-{uuid.uuid4().hex[:12]}"
        ret_url = return_url or f"{settings.FRONTEND_URL}/checkout/success?order_id={order.id}"
        can_url = cancel_url or f"{settings.FRONTEND_URL}/checkout/cancel?order_id={order.id}"
        
        is_mock_flow = PayPalService._is_mock()
        
        if is_mock_flow:
            paypal_order_id = f"MOCK-PAYPAL-{uuid.uuid4().hex[:12].upper()}"
            approval_url = f"{settings.FRONTEND_URL}/checkout?order_id={order.id}&paypal_order_id={paypal_order_id}&mock=true"
            
            payment = Payment(
                order_id=order.id,
                paypal_order_id=paypal_order_id,
                amount=order.total_amount,
                currency="USD",
                status="created",
                idempotency_key=idempotency_key,
                is_mock=True,
                raw_response_json=json.dumps({
                    "id": paypal_order_id,
                    "status": "CREATED",
                    "intent": "CAPTURE",
                    "mock_mode": True,
                    "notice": "MOCK MODE - no real PayPal call. For real Sandbox, configure credentials in .env"
                })
            )
            db.add(payment)
            order.payment_status = "created"
            db.commit()
            db.refresh(payment)
            return payment, approval_url

        # Real PayPal Sandbox REST API call
        token = PayPalService.get_access_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "PayPal-Request-Id": idempotency_key
        }
        
        body = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": f"ORDER_{order.id}",
                    "description": f"HarvestLink AI Produce Order #{order.id} ({order.quantity} kg)",
                    "amount": {
                        "currency_code": "USD",
                        "value": f"{order.total_amount:.2f}"
                    }
                }
            ],
            "application_context": {
                "brand_name": "HarvestLink AI",
                "landing_page": "NO_PREFERENCE",
                "user_action": "PAY_NOW",
                "return_url": ret_url,
                "cancel_url": can_url
            }
        }
        
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(
                f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders",
                json=body,
                headers=headers
            )
            
            if resp.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"PayPal API error on Create Order: {resp.text}"
                )
                
            paypal_data = resp.json()
            paypal_order_id = paypal_data.get("id")
            
            approval_url = ""
            for link in paypal_data.get("links", []):
                if link.get("rel") == "approve":
                    approval_url = link.get("href")
                    break
                    
            if not approval_url:
                approval_url = f"https://www.sandbox.paypal.com/checkoutnow?token={paypal_order_id}"

            payment = Payment(
                order_id=order.id,
                paypal_order_id=paypal_order_id,
                amount=order.total_amount,
                currency="USD",
                status="created",
                idempotency_key=idempotency_key,
                is_mock=False,
                raw_response_json=json.dumps(paypal_data)
            )
            db.add(payment)
            order.payment_status = "created"
            db.commit()
            db.refresh(payment)
            return payment, approval_url

    @staticmethod
    def capture_and_verify(
        db: Session,
        order_id: int,
        paypal_order_id: str
    ) -> Payment:
        payment = db.query(Payment).filter(Payment.order_id == order_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment record not found for this order."
            )
            
        if payment.status == "completed":
            return payment

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Mock mode capture
        if payment.is_mock or PayPalService._is_mock():
            payment.status = "completed"
            payment.paypal_capture_id = f"MOCK-CAP-{uuid.uuid4().hex[:12].upper()}"
            payment.verified_at = datetime.datetime.utcnow()
            
            order.payment_status = "completed"
            order.order_status = "processing"
            db.commit()
            db.refresh(payment)
            return payment

        # Real PayPal Sandbox Capture
        token = PayPalService.get_access_token()
        capture_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "PayPal-Request-Id": f"CAP-{payment.idempotency_key}"
        }

        with httpx.Client(timeout=15.0) as client:
            capture_resp = client.post(
                f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders/{paypal_order_id}/capture",
                headers=capture_headers
            )

            # If already captured on PayPal, fetch order details to verify
            if capture_resp.status_code == 422:
                verify_resp = client.get(
                    f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders/{paypal_order_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if verify_resp.status_code == 200:
                    order_details = verify_resp.json()
                    if order_details.get("status") == "COMPLETED":
                        payment.status = "completed"
                        payment.verified_at = datetime.datetime.utcnow()
                        order.payment_status = "completed"
                        order.order_status = "processing"
                        db.commit()
                        db.refresh(payment)
                        return payment

            if capture_resp.status_code not in [200, 201]:
                payment.status = "failed"
                order.payment_status = "failed"
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"PayPal Capture failed: {capture_resp.text}"
                )

            capture_data = capture_resp.json()
            if capture_data.get("status") != "COMPLETED":
                payment.status = "failed"
                order.payment_status = "failed"
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"PayPal order not completed. Status: {capture_data.get('status')}"
                )

            # Verify amount and currency
            purchase_unit = capture_data.get("purchase_units", [{}])[0]
            payments_obj = purchase_unit.get("payments", {})
            captures = payments_obj.get("captures", [{}])
            capture_obj = captures[0] if captures else {}
            
            capture_id = capture_obj.get("id")
            cap_amount = float(capture_obj.get("amount", {}).get("value", 0.0))
            cap_currency = capture_obj.get("amount", {}).get("currency_code", "")

            if abs(cap_amount - order.total_amount) > 0.05 or cap_currency != "USD":
                payment.status = "failed"
                order.payment_status = "failed"
                db.commit()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Payment verification failed: Amount or currency mismatch. Expected {order.total_amount} USD, got {cap_amount} {cap_currency}"
                )

            payment.status = "completed"
            payment.paypal_capture_id = capture_id
            payment.verified_at = datetime.datetime.utcnow()
            payment.raw_response_json = json.dumps(capture_data)

            order.payment_status = "completed"
            order.order_status = "processing"
            db.commit()
            db.refresh(payment)
            return payment
