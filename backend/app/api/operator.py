from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import User, ProduceListing, AuditLog
from app.schemas import ProduceListingResponse, AuditLogResponse
from app.services.audit_service import AuditService
from app.api.deps import get_optional_current_user

router = APIRouter(prefix="/api/operator", tags=["operator"])

class OperatorListingCreate(BaseModel):
    farmer_name: str
    consent_method: str  # 'verbal' or 'written'
    crop_name: str
    quantity: float
    expected_price: float
    minimum_price: float
    location: str
    harvest_date: str
    freshness_status: Optional[str] = "fresh"
    operator_notes: Optional[str] = None

@router.post("/listings", response_model=ProduceListingResponse)
def create_proxy_listing(
    payload: OperatorListingCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    operator = current_user or db.query(User).filter(User.role == "operator").first()
    if not operator or operator.role != "operator":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only certified FPO village operators can create proxy listings."
        )

    # 1. Enforce explicit farmer consent logging
    AuditService.verify_and_log_operator_consent(
        db=db,
        operator_user=operator,
        farmer_name=payload.farmer_name,
        consent_method=payload.consent_method,
        action="CREATE_LISTING",
        details=f"Listed {payload.quantity} kg {payload.crop_name} on behalf of farmer {payload.farmer_name}. Notes: {payload.operator_notes or 'None'}"
    )

    # 2. Find or register representative farmer
    farmer = db.query(User).filter(User.name == payload.farmer_name, User.role == "farmer").first()
    if not farmer:
        farmer = db.query(User).filter(User.role == "farmer").first()
        farmer_id = farmer.id if farmer else 1
    else:
        farmer_id = farmer.id

    # 3. Create listing
    listing = ProduceListing(
        farmer_id=farmer_id,
        crop_name=payload.crop_name,
        quantity=payload.quantity,
        available_quantity=payload.quantity,
        unit="kg",
        expected_price=payload.expected_price,
        minimum_price=payload.minimum_price,
        location=payload.location,
        harvest_date=payload.harvest_date,
        freshness_status=payload.freshness_status or "fresh",
        listing_status="active"
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(db: Session = Depends(get_db)):
    return db.query(AuditLog).order_by(AuditLog.id.desc()).all()
