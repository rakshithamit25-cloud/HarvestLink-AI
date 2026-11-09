from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import Order, User
from app.schemas import OrderResponse, DeliveryConfirmRequest
from app.services.order_service import OrderService
from app.api.deps import get_current_user, get_optional_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.get("", response_model=List[OrderResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Order)
    if current_user.role == "farmer":
        query = query.filter(Order.farmer_id == current_user.id)
    elif current_user.role == "buyer":
        query = query.filter(Order.buyer_id == current_user.id)
    elif current_user.role == "operator":
        # No registered_by_operator_id column exists in schema,
        # so operators currently see no orders (cannot determine ownership).
        # A future schema migration would add this link.
        query = query.filter(Order.id == None)  # returns empty set
    
    orders = query.order_by(Order.id.desc()).all()
    results = []
    for o in orders:
        b_name = o.match.buyer_requirement.buyer_name if o.match and o.match.buyer_requirement else "Buyer"
        c_name = o.listing.crop_name if o.listing else "Produce"
        results.append({
            "id": o.id,
            "listing_id": o.listing_id,
            "match_id": o.match_id,
            "farmer_id": o.farmer_id,
            "buyer_id": o.buyer_id,
            "buyer_name": b_name,
            "crop_name": c_name,
            "quantity": o.quantity,
            "agreed_price": o.agreed_price,
            "total_amount": o.total_amount,
            "payment_status": o.payment_status,
            "order_status": o.order_status,
            "delivery_verified_at": o.delivery_verified_at,
            "created_at": o.created_at
        })
    return results

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    b_name = order.match.buyer_requirement.buyer_name if order.match and order.match.buyer_requirement else "Buyer"
    c_name = order.listing.crop_name if order.listing else "Produce"
    return {
        "id": order.id,
        "listing_id": order.listing_id,
        "match_id": order.match_id,
        "farmer_id": order.farmer_id,
        "buyer_id": order.buyer_id,
        "buyer_name": b_name,
        "crop_name": c_name,
        "quantity": order.quantity,
        "agreed_price": order.agreed_price,
        "total_amount": order.total_amount,
        "payment_status": order.payment_status,
        "order_status": order.order_status,
        "delivery_verified_at": order.delivery_verified_at,
        "created_at": order.created_at
    }

@router.put("/{order_id}/status")
@router.patch("/{order_id}")
def direct_order_status_update():
    """
    STRICT SECURITY RULE:
    Clients/frontends cannot directly mutate payment_status or mark an order paid.
    Payment success is determined solely by backend server-side PayPal capture verification.
    """
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Direct client payment status updates are strictly prohibited. Payments must be verified via PayPal capture."
    )

@router.post("/{order_id}/confirm-delivery", response_model=OrderResponse)
def confirm_delivery(
    order_id: int,
    request: DeliveryConfirmRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    actor = current_user or db.query(User).filter(User.role == "buyer").first()
    order = OrderService.confirm_delivery(
        db=db,
        order_id=order_id,
        actor_user=actor,
        consent_method=request.consent_method,
        farmer_name=request.farmer_name,
        notes=request.notes or ""
    )
    b_name = order.match.buyer_requirement.buyer_name if order.match and order.match.buyer_requirement else "Buyer"
    c_name = order.listing.crop_name if order.listing else "Produce"
    return {
        "id": order.id,
        "listing_id": order.listing_id,
        "match_id": order.match_id,
        "farmer_id": order.farmer_id,
        "buyer_id": order.buyer_id,
        "buyer_name": b_name,
        "crop_name": c_name,
        "quantity": order.quantity,
        "agreed_price": order.agreed_price,
        "total_amount": order.total_amount,
        "payment_status": order.payment_status,
        "order_status": order.order_status,
        "delivery_verified_at": order.delivery_verified_at,
        "created_at": order.created_at
    }
