from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas import ImpactMetricsResponse
from app.services.impact_service import ImpactService

router = APIRouter(prefix="/api/impact", tags=["impact"])

@router.get("/metrics", response_model=ImpactMetricsResponse)
def get_impact_metrics(db: Session = Depends(get_db)):
    """
    Returns verified impact metrics calculated from real database records.
    Never blends matched, confirmed, or delivered amounts.
    Waste prevented is strictly equal to delivered_quantity.
    """
    return ImpactService.get_metrics(db)
