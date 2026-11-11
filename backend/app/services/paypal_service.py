import json
import uuid
import datetime
import logging
import httpx
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.config import settings
from app.models import Order, Payment

logger = logging.getLogger(__name__)

class PayPalService:
    @staticmethod
    def _is_mock() -> bool:
        return settings.PAYPAL_MODE == "mock"

    @staticmethod
    def get_access_token() -> str:
        """
        Retrieves OAuth2 Bearer token from PayPal Sandbox REST API
        using client_id and client_secret.
        Fails fast if Sandbox configuration is missing or invalid.
        """
        if PayPalService._is_mock():
            return "mock_sandbox_access_token"

        if (
            not settings.PAYPAL_CLIENT_ID or
            settings.PAYPAL_CLIENT_ID == "mock_client_id" or
            not settings.PAYPAL_CLIENT_SECRET
        ):
            logger.error("PayPal Sandbox is enabled, but valid client credentials are not configured.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="PayPal Sandbox configuration error: missing or invalid credentials."
            )

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
                logger.error(f"PayPal OAuth token request failed with HTTP {resp.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Unable to authenticate with payment processor."
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

        frontend_base = settings.FRONTEND_URL.split(",")[0].strip()
        if existing_payment and existing_payment.paypal_order_id:
            approval_url = (
                f"https://www.sandbox.paypal.com/checkoutnow?token={existing_payment.paypal_order_id}"
                if not existing_payment.is_mock else
                f"{frontend_base}/checkout?order_id={order.id}&paypal_order_id={existing_payment.paypal_order_id}&mock=true"
            )
            return existing_payment, approval_url

        idempotency_key = f"HL-PAY-{order.id}-{uuid.uuid4().hex[:12]}"
        ret_url = return_url or f"{frontend_base}/checkout/success?order_id={order.id}"
        can_url = cancel_url or f"{frontend_base}/checkout/cancel?order_id={order.id}"
        
        is_mock_flow = PayPalService._is_mock()
        
        if is_mock_flow:
            paypal_order_id = f"MOCK-PAYPAL-{uuid.uuid4().hex[:12].upper()}"
            approval_url = f"{frontend_base}/checkout?order_id={order.id}&paypal_order_id={paypal_order_id}&mock=true"
            
            payment = existing_payment or Payment(order_id=order.id)
            payment.paypal_order_id = paypal_order_id
            payment.amount = order.total_amount
            payment.currency = "USD"
            payment.status = "created"
            payment.idempotency_key = idempotency_key
            payment.is_mock = True
            payment.raw_response_json = json.dumps({
                "id": paypal_order_id,
                "status": "CREATED",
                "intent": "CAPTURE",
                "mock_mode": True,
                "notice": "MOCK MODE - no real PayPal call. For real Sandbox, configure credentials in .env"
            })
            if not existing_payment:
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
                logger.error(f"PayPal create order failed with HTTP {resp.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Payment processor error during order creation."
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

            payment = existing_payment or Payment(order_id=order.id)
            payment.paypal_order_id = paypal_order_id
            payment.amount = order.total_amount
            payment.currency = "USD"
            payment.status = "created"
            payment.idempotency_key = idempotency_key
            payment.is_mock = False
            payment.raw_response_json = json.dumps(paypal_data)
            if not existing_payment:
                db.add(payment)
            order.payment_status = "created"
            db.commit()
            db.refresh(payment)
            return payment, approval_url

    @staticmethod
    def _finalize_capture(
        db: Session,
        payment: Payment,
        order: Order,
        capture_data: Dict[str, Any]
    ) -> Payment:
        """
        Validates capture details (status, amount, currency, capture ID)
        and finalizes the payment and order records.
        Used by both the normal capture response and HTTP 422 recovery.
        """
        if capture_data.get("status") != "COMPLETED":
            payment.status = "failed"
            order.payment_status = "failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"PayPal order not completed. Status: {capture_data.get('status')}"
            )

        purchase_unit = capture_data.get("purchase_units", [{}])[0]
        payments_obj = purchase_unit.get("payments", {})
        captures = payments_obj.get("captures", [])
        capture_obj = captures[0] if captures else {}

        capture_id = capture_obj.get("id")
        if not capture_id:
            payment.status = "failed"
            order.payment_status = "failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment verification failed: No valid capture ID found in processor response."
            )

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

        # Fix 1: Validate stored PayPal order ID exists and matches supplied ID
        if not payment.paypal_order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No PayPal order ID stored for this payment record."
            )

        if not paypal_order_id or payment.paypal_order_id != paypal_order_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplied PayPal order ID does not match the payment record for this order."
            )
            
        if payment.status == "completed":
            return payment

        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Fix 3: Reject ineligible orders (cancelled, delivered, rejected)
        if order.order_status in ["cancelled", "delivered", "rejected"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot capture payment for order in status '{order.order_status}'."
            )

        # Fix 5: Apply business validation (amount & currency) in MOCK mode too
        if abs(payment.amount - order.total_amount) > 0.05 or payment.currency != "USD":
            payment.status = "failed"
            order.payment_status = "failed"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Payment verification failed: Amount or currency mismatch. Expected {order.total_amount} USD, got {payment.amount} {payment.currency}"
            )

        # Mock mode capture
        if payment.is_mock or PayPalService._is_mock():
            payment.status = "completed"
            payment.paypal_capture_id = f"MOCK-CAP-{uuid.uuid4().hex[:12].upper()}"
            payment.verified_at = datetime.datetime.utcnow()
            payment.raw_response_json = json.dumps({
                "id": payment.paypal_order_id,
                "status": "COMPLETED",
                "mock_mode": True,
                "capture_id": payment.paypal_capture_id,
                "amount": payment.amount,
                "currency": payment.currency
            })
            
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

            # Fix 2: If already captured on PayPal (422), fetch order details and verify fully
            if capture_resp.status_code == 422:
                logger.info(f"Capture returned 422 for order {order_id}; attempting recovery via order query.")
                verify_resp = client.get(
                    f"{settings.PAYPAL_API_BASE_URL}/v2/checkout/orders/{paypal_order_id}",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if verify_resp.status_code == 200:
                    order_details = verify_resp.json()
                    return PayPalService._finalize_capture(db, payment, order, order_details)
                else:
                    logger.error(f"PayPal order details recovery query failed with HTTP {verify_resp.status_code}")

            # Fix 6: Sanitize provider error response (do not expose raw capture_resp.text)
            if capture_resp.status_code not in [200, 201]:
                payment.status = "failed"
                order.payment_status = "failed"
                db.commit()
                logger.error(f"PayPal capture failed with HTTP {capture_resp.status_code}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Payment processor error during payment capture."
                )

            capture_data = capture_resp.json()
            return PayPalService._finalize_capture(db, payment, order, capture_data)

