from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import BuyerRequirement, User
from app.schemas import BuyerRequirementCreate, BuyerRequirementResponse
from app.api.deps import get_optional_current_user

router = APIRouter(prefix="/api/buyers", tags=["buyers"])

@router.post("/requirements", response_model=BuyerRequirementResponse)
def create_requirement(
    req_in: BuyerRequirementCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    buyer_id = current_user.id if current_user and current_user.role == "buyer" else 2
    buyer_name = current_user.name if current_user else "Buyer"

    requirement = BuyerRequirement(
        buyer_id=buyer_id,
        buyer_name=buyer_name,
        crop_name=req_in.crop_name,
        required_quantity=req_in.required_quantity,
        maximum_price=req_in.maximum_price,
        location=req_in.location,
        required_date=req_in.required_date,
        status="open"
    )
    db.add(requirement)
    db.commit()
    db.refresh(requirement)
    return requirement

@router.get("/requirements", response_model=List[BuyerRequirementResponse])
def get_requirements(
    buyer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(BuyerRequirement)
    if buyer_id:
        query = query.filter(BuyerRequirement.buyer_id == buyer_id)
    return query.order_by(BuyerRequirement.id.desc()).all()
