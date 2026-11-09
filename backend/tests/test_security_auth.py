"""
Phase 3 Task 1 — Security & Auth Tests (Pure synchronous, no socket dependency).
Requirements:
  1. Unauthenticated request / missing token -> 401
  2. POST /api/demo/reset with DEMO_MODE=false -> 403
  3. Farmer A cannot see farmer B's orders
  4. CORS rejects unlisted origin (no wildcard, strictly FRONTEND_URL)
"""
import pytest
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.main import app
from app.api.deps import get_current_user
from app.api.demo import reset_database
from app.api.orders import get_orders
from app.api.listings import create_listing
from app.schemas import ProduceListingCreate
from app.models import User, Order, ProduceListing
from app.core.config import settings


def test_unauthenticated_request_raises_401(db_session):
    """Missing or invalid Authorization header raises HTTP 401 Unauthorized."""
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(authorization=None, db=db_session)
    assert exc_info.value.status_code == 401
    assert "Missing Authorization header" in exc_info.value.detail

    with pytest.raises(HTTPException) as exc_info_invalid:
        get_current_user(authorization="Bearer invalid.token.payload", db=db_session)
    assert exc_info_invalid.value.status_code == 401


def test_demo_reset_forbidden_when_demo_mode_false(db_session, monkeypatch):
    """POST /api/demo/reset raises HTTP 403 Forbidden when DEMO_MODE=False."""
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    with pytest.raises(HTTPException) as exc_info:
        reset_database(db=db_session)
    assert exc_info.value.status_code == 403
    assert "Demo mode is disabled" in exc_info.value.detail


def test_farmer_a_cannot_see_farmer_b_orders(db_session):
    """Farmer B querying orders must not see Farmer A's orders."""
    farmer_a = db_session.query(User).filter(User.role == "farmer", User.name == "Kumar").first()
    buyer = db_session.query(User).filter(User.role == "buyer").first()

    # Create farmer B
    farmer_b = User(
        name="Farmer B",
        email="farmer_b@test.org",
        hashed_password="hashed_pw",
        role="farmer",
        phone="+91-9999999999",
        preferred_language="ta"
    )
    db_session.add(farmer_b)
    db_session.commit()
    db_session.refresh(farmer_b)

    # Create a listing and order for Farmer A
    listing_a = ProduceListing(
        farmer_id=farmer_a.id,
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
    db_session.add(listing_a)
    db_session.commit()

    order_a = Order(
        listing_id=listing_a.id,
        farmer_id=farmer_a.id,
        buyer_id=buyer.id,
        quantity=50.0,
        agreed_price=1.00,
        total_amount=50.00,
        payment_status="pending",
        order_status="created"
    )
    db_session.add(order_a)
    db_session.commit()

    # Farmer A querying orders gets 1 order
    orders_a = get_orders(db=db_session, current_user=farmer_a)
    assert len(orders_a) == 1
    assert orders_a[0]["farmer_id"] == farmer_a.id

    # Farmer B querying orders gets 0 orders (cannot see Farmer A's orders)
    orders_b = get_orders(db=db_session, current_user=farmer_b)
    assert len(orders_b) == 0


def test_cors_rejects_unlisted_origin():
    """CORS middleware must not allow wildcard origins and must reject unlisted origins."""
    cors_middleware = next((m for m in app.user_middleware if m.cls == CORSMiddleware), None)
    assert cors_middleware is not None, "CORSMiddleware not found on app"
    
    allowed_origins = cors_middleware.kwargs.get("allow_origins", [])
    assert "*" not in allowed_origins, "Wildcard '*' origin is strictly forbidden"
    assert "https://evil-unlisted-origin.com" not in allowed_origins
    
    expected_origins = [url.strip() for url in settings.FRONTEND_URL.split(",") if url.strip()]
    assert set(allowed_origins) == set(expected_origins)
