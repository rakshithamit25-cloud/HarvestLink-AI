import pytest
from fastapi import HTTPException
from app.models import User, AuditLog, MatchResult, ProduceListing, BuyerRequirement
from app.services.order_service import OrderService
from app.services.audit_service import AuditService

def test_fpo_operator_action_without_consent_rejected(db_session):
    operator = db_session.query(User).filter(User.role == "operator").first()
    farmer = db_session.query(User).filter(User.role == "farmer").first()
    buyer = db_session.query(User).filter(User.role == "buyer").first()

    listing = ProduceListing(
        farmer_id=farmer.id,
        crop_name="Tomato",
        quantity=50.0,
        available_quantity=50.0,
        unit="kg",
        expected_price=1.00,
        minimum_price=0.90,
        location="Salem",
        harvest_date="2026-11-08",
        freshness_status="fresh",
        listing_status="active"
    )
    req = BuyerRequirement(
        buyer_id=buyer.id,
        buyer_name="Restaurant A",
        crop_name="Tomato",
        required_quantity=50.0,
        maximum_price=1.20,
        location="Salem",
        required_date="2026-11-10",
        status="open"
    )
    db_session.add_all([listing, req])
    db_session.commit()

    match = MatchResult(
        listing_id=listing.id,
        buyer_requirement_id=req.id,
        allocated_quantity=50.0,
        farmer_asking_price=1.00,
        ai_suggested_price=1.10,
        agreed_price=None,
        match_reason="Matches criteria",
        status="proposed"
    )
    db_session.add(match)
    db_session.commit()
    db_session.refresh(match)

    # 1. Attempt operator action without valid consent_method -> MUST BE REJECTED
    with pytest.raises(HTTPException) as exc_missing_consent:
        OrderService.approve_match_by_farmer(
            db=db_session,
            match_id=match.id,
            farmer_user=operator,
            consent_method="",  # Missing consent!
            operator_farmer_name="Kumar"
        )
    assert exc_missing_consent.value.status_code == 400
    assert "Explicit farmer consent is required" in exc_missing_consent.value.detail

    # 2. Attempt operator action with invalid consent method (e.g. 'telepathy') -> MUST BE REJECTED
    with pytest.raises(HTTPException) as exc_invalid_method:
        OrderService.approve_match_by_farmer(
            db=db_session,
            match_id=match.id,
            farmer_user=operator,
            consent_method="unverified",
            operator_farmer_name="Kumar"
        )
    assert exc_invalid_method.value.status_code == 400

    # 3. Attempt operator action without farmer name -> MUST BE REJECTED
    with pytest.raises(HTTPException) as exc_missing_name:
        OrderService.approve_match_by_farmer(
            db=db_session,
            match_id=match.id,
            farmer_user=operator,
            consent_method="verbal",
            operator_farmer_name=""  # Missing farmer name!
        )
    assert exc_missing_name.value.status_code == 400
    assert "Farmer name is required" in exc_missing_name.value.detail

    # 4. Valid operator action with verbal consent -> MUST SUCCEED AND WRITE TO AUDIT LOG
    approved_match = OrderService.approve_match_by_farmer(
        db=db_session,
        match_id=match.id,
        farmer_user=operator,
        consent_method="verbal",
        operator_farmer_name="Kumar"
    )
    assert approved_match.status == "farmer_approved"

    # Verify audit log entry
    audit_entry = db_session.query(AuditLog).filter(
        AuditLog.actor_id == operator.id,
        AuditLog.consent_method == "verbal",
        AuditLog.farmer_name == "Kumar"
    ).first()
    assert audit_entry is not None
    assert "OPERATOR_PROXY_ACCEPT_MATCH" in audit_entry.action
