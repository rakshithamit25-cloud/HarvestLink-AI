import pytest
from app.models import ProduceListing, BuyerRequirement, MatchResult, Order, User
from app.api.demo import seed_database
from app.agents.workflow import execute_matching_pipeline
from app.services.order_service import OrderService

def test_seed_database_creates_all_four_crops(db_session):
    """Verify that seed_database populates Tomato, Onion, Potato, and Carrot with listings and >=3 buyer requirements."""
    seed_database(db_session)

    expected_crops = ["Tomato", "Onion", "Potato", "Carrot"]
    for crop in expected_crops:
        listing = db_session.query(ProduceListing).filter(ProduceListing.crop_name == crop).first()
        assert listing is not None, f"Expected listing for {crop} to exist"
        assert listing.quantity > 0
        assert listing.listing_status in ["active", "partially_matched", "fully_matched"]

        reqs = db_session.query(BuyerRequirement).filter(BuyerRequirement.crop_name == crop).all()
        assert len(reqs) >= 3, f"Expected at least 3 buyer requirements for {crop}, got {len(reqs)}"

        matches = db_session.query(MatchResult).filter(MatchResult.listing_id == listing.id).all()
        assert len(matches) >= 3, f"Expected at least 3 match proposals for {crop}, got {len(matches)}"
        for m in matches:
            assert m.buyer_requirement.crop_name == crop
            assert m.allocated_quantity > 0
            assert m.ai_suggested_price > 0
            assert m.status == "proposed"

def test_seed_database_is_idempotent(db_session):
    """Verify restarting/re-running seed_database does not create duplicate listings or requirements."""
    seed_database(db_session)

    initial_users = db_session.query(User).count()
    initial_listings = db_session.query(ProduceListing).count()
    initial_reqs = db_session.query(BuyerRequirement).count()
    initial_matches = db_session.query(MatchResult).count()

    # Re-run seed_database
    seed_database(db_session)

    assert db_session.query(User).count() == initial_users
    assert db_session.query(ProduceListing).count() == initial_listings
    assert db_session.query(BuyerRequirement).count() == initial_reqs
    assert db_session.query(MatchResult).count() == initial_matches

def test_crop_matching_isolation_no_cross_pollution(db_session):
    """Verify each crop's matches only link to that specific crop's requirements."""
    seed_database(db_session)

    for crop in ["Tomato", "Onion", "Potato", "Carrot"]:
        listing = db_session.query(ProduceListing).filter(ProduceListing.crop_name == crop).first()
        matches = db_session.query(MatchResult).filter(MatchResult.listing_id == listing.id).all()
        for m in matches:
            assert m.listing.crop_name == crop
            assert m.buyer_requirement.crop_name == crop
            assert crop.lower() in m.match_reason.lower()

def test_farmer_and_buyer_approval_on_non_tomato_crop(db_session):
    """Verify Farmer Accept and Buyer Approve actions work on Onion and create a valid Order."""
    seed_database(db_session)

    onion_listing = db_session.query(ProduceListing).filter(ProduceListing.crop_name == "Onion").first()
    farmer = db_session.query(User).filter(User.role == "farmer").first()
    
    onion_match = db_session.query(MatchResult).filter(
        MatchResult.listing_id == onion_listing.id,
        MatchResult.allocated_quantity > 0
    ).first()
    assert onion_match is not None

    buyer_user = db_session.query(User).filter(User.id == onion_match.buyer_requirement.buyer_id).first()

    # Farmer approves
    approved_by_farmer = OrderService.approve_match_by_farmer(
        db_session, onion_match.id, farmer, consent_method="verbal", operator_farmer_name="Kumar"
    )
    assert approved_by_farmer.status == "farmer_approved"

    # Buyer approves
    approved_by_buyer = OrderService.approve_match_by_buyer(
        db_session, onion_match.id, buyer_user
    )
    assert approved_by_buyer.status == "confirmed"

    # Order generated from confirmed match
    order = OrderService.create_order_from_confirmed_match(db_session, onion_match.id)
    assert order is not None
    assert order.listing.crop_name == "Onion"
    assert order.quantity == onion_match.allocated_quantity
    assert order.agreed_price == onion_match.agreed_price
    assert order.payment_status == "pending"

from app.api.matching import run_matching

def test_run_matching_refreshes_proposed_matches(db_session):
    """Verify executing matching pipeline on a listing with unconfirmed proposed matches refreshes cleanly."""
    seed_database(db_session)

    carrot_listing = db_session.query(ProduceListing).filter(ProduceListing.crop_name == "Carrot").first()
    initial_matches = db_session.query(MatchResult).filter(MatchResult.listing_id == carrot_listing.id).all()
    assert len(initial_matches) == 3

    # Re-run matching API endpoint
    result = run_matching(listing_id=carrot_listing.id, mode="rule-based", db=db_session)
    assert result["status"] == "success"
    assert result["proposals_count"] == 3

    refreshed_matches = db_session.query(MatchResult).filter(MatchResult.listing_id == carrot_listing.id).all()
    assert len(refreshed_matches) == 3
