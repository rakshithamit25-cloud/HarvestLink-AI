from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import ProduceListing, MatchResult, User
from app.schemas import MatchResultResponse, MatchApprovalRequest
from app.agents.workflow import execute_matching_pipeline
from app.services.order_service import OrderService
from app.api.deps import get_optional_current_user

router = APIRouter(prefix="/api/matching", tags=["matching"])

@router.post("/run/{listing_id}")
def run_matching(
    listing_id: int,
    mode: str = "rule-based",
    db: Session = Depends(get_db)
):
    listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Produce listing not found")

    # If unconfirmed 'proposed' matches exist on this listing, release their stock and refresh proposals
    unconfirmed = db.query(MatchResult).filter(
        MatchResult.listing_id == listing_id,
        MatchResult.status == "proposed"
    ).all()
    if unconfirmed:
        for m in unconfirmed:
            listing.available_quantity += m.allocated_quantity
            db.delete(m)
        listing.listing_status = "active"
        db.commit()

    result_state = execute_matching_pipeline(db, listing, mode=mode)
    
    # Fetch updated matches
    matches = db.query(MatchResult).filter(MatchResult.listing_id == listing_id).all()
    
    return {
        "status": "success",
        "listing_id": listing_id,
        "available_quantity": result_state["available_quantity"],
        "proposals_count": len(result_state["proposals"]),
        "agent_logs": result_state["agent_logs"]
    }

@router.get("/results/{listing_id}", response_model=List[MatchResultResponse])
def get_match_results(listing_id: int, db: Session = Depends(get_db)):
    matches = db.query(MatchResult).filter(MatchResult.listing_id == listing_id).all()
    results = []
    for m in matches:
        b_name = m.buyer_requirement.buyer_name if m.buyer_requirement else "Buyer"
        c_name = m.buyer_requirement.crop_name if m.buyer_requirement else m.listing.crop_name
        results.append({
            "id": m.id,
            "listing_id": m.listing_id,
            "buyer_requirement_id": m.buyer_requirement_id,
            "buyer_name": b_name,
            "crop_name": c_name,
            "allocated_quantity": m.allocated_quantity,
            "farmer_asking_price": m.farmer_asking_price,
            "ai_suggested_price": m.ai_suggested_price,
            "agreed_price": m.agreed_price,
            "match_reason": m.match_reason,
            "status": m.status,
            "created_at": m.created_at
        })
    return results

@router.post("/{match_id}/approve-farmer", response_model=MatchResultResponse)
def approve_match_farmer(
    match_id: int,
    approval_data: Optional[MatchApprovalRequest] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user = current_user or db.query(User).filter(User.role == "farmer").first()
    consent = approval_data.consent_method if approval_data else "verbal"
    farmer_name = approval_data.farmer_name if approval_data else "Kumar"

    match = OrderService.approve_match_by_farmer(
        db=db,
        match_id=match_id,
        farmer_user=user,
        consent_method=consent,
        operator_farmer_name=farmer_name
    )
    
    # If confirmed by both, auto-create Order
    if match.status == "confirmed":
        OrderService.create_order_from_confirmed_match(db, match.id)

    b_name = match.buyer_requirement.buyer_name if match.buyer_requirement else "Buyer"
    return {
        "id": match.id,
        "listing_id": match.listing_id,
        "buyer_requirement_id": match.buyer_requirement_id,
        "buyer_name": b_name,
        "crop_name": match.listing.crop_name,
        "allocated_quantity": match.allocated_quantity,
        "farmer_asking_price": match.farmer_asking_price,
        "ai_suggested_price": match.ai_suggested_price,
        "agreed_price": match.agreed_price,
        "match_reason": match.match_reason,
        "status": match.status,
        "created_at": match.created_at
    }

@router.post("/{match_id}/approve-buyer", response_model=MatchResultResponse)
def approve_match_buyer(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    match = db.query(MatchResult).filter(MatchResult.id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    user = current_user or db.query(User).filter(User.id == match.buyer_requirement.buyer_id).first()

    match = OrderService.approve_match_by_buyer(db=db, match_id=match_id, buyer_user=user)
    
    # If confirmed by both, auto-create Order
    if match.status == "confirmed":
        OrderService.create_order_from_confirmed_match(db, match.id)

    b_name = match.buyer_requirement.buyer_name if match.buyer_requirement else "Buyer"
    return {
        "id": match.id,
        "listing_id": match.listing_id,
        "buyer_requirement_id": match.buyer_requirement_id,
        "buyer_name": b_name,
        "crop_name": match.listing.crop_name,
        "allocated_quantity": match.allocated_quantity,
        "farmer_asking_price": match.farmer_asking_price,
        "ai_suggested_price": match.ai_suggested_price,
        "agreed_price": match.agreed_price,
        "match_reason": match.match_reason,
        "status": match.status,
        "created_at": match.created_at
    }

@router.post("/{match_id}/reject", response_model=MatchResultResponse)
def reject_match(
    match_id: int,
    reason: str = "Decline terms",
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    user = current_user or db.query(User).first()
    match = OrderService.reject_match(db=db, match_id=match_id, actor_user=user, reason=reason)
    b_name = match.buyer_requirement.buyer_name if match.buyer_requirement else "Buyer"
    return {
        "id": match.id,
        "listing_id": match.listing_id,
        "buyer_requirement_id": match.buyer_requirement_id,
        "buyer_name": b_name,
        "crop_name": match.listing.crop_name,
        "allocated_quantity": match.allocated_quantity,
        "farmer_asking_price": match.farmer_asking_price,
        "ai_suggested_price": match.ai_suggested_price,
        "agreed_price": match.agreed_price,
        "match_reason": match.match_reason,
        "status": match.status,
        "created_at": match.created_at
    }
