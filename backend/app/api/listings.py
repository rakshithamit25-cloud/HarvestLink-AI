from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import ProduceListing, User
from app.schemas import (
    ProduceListingCreate,
    ProduceListingResponse,
    TamilParseRequest,
    TamilParseResponse
)
from app.services.tamil_parser import parse_tamil_or_english_text
from app.api.deps import get_current_user, get_optional_current_user

router = APIRouter(prefix="/api/listings", tags=["listings"])

@router.post("/parse-text", response_model=TamilParseResponse)
def parse_voice_or_manual_text(request: TamilParseRequest):
    """
    Parses voice-transcribed or typed Tamil / English text to extract
    crop name, quantity, price, and location.
    Missing fields are returned in missing_fields so the UI can request them.
    Farmer must confirm before publishing.
    """
    parsed = parse_tamil_or_english_text(request.text)
    return parsed

@router.post("", response_model=ProduceListingResponse)
def create_listing(
    listing_in: ProduceListingCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user)
):
    # Default to farmer Kumar (id 1) if not logged in or during quick demo creation
    farmer_id = current_user.id if current_user and current_user.role == "farmer" else 1

    listing = ProduceListing(
        farmer_id=farmer_id,
        crop_name=listing_in.crop_name,
        quantity=listing_in.quantity,
        available_quantity=listing_in.quantity,
        unit="kg",
        expected_price=listing_in.expected_price,
        minimum_price=listing_in.minimum_price,
        location=listing_in.location,
        harvest_date=listing_in.harvest_date,
        freshness_status=listing_in.freshness_status or "fresh",
        listing_status="active"
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing

@router.get("", response_model=List[ProduceListingResponse])
def get_listings(
    farmer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ProduceListing)
    if farmer_id:
        query = query.filter(ProduceListing.farmer_id == farmer_id)
    return query.order_by(ProduceListing.id.desc()).all()

@router.get("/{listing_id}", response_model=ProduceListingResponse)
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.query(ProduceListing).filter(ProduceListing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Produce listing not found")
    return listing
