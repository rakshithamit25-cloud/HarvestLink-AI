import pytest
import time
from fastapi import HTTPException
from app.core.config import settings
from app.services.otp_service import otp_store
from app.api.auth import request_otp, verify_otp
from app.schemas import OTPRequest, OTPVerifyRequest

@pytest.fixture(autouse=True)
def clean_otp_store():
    otp_store.clear()
    yield
    otp_store.clear()

def test_correct_otp_succeeds(db_session, monkeypatch):
    """Correct 6-digit OTP verification returns JWT and user profile."""
    monkeypatch.setattr(settings, "OTP_DEMO_MODE", True)
    
    # 1. Request OTP
    req_resp = request_otp(OTPRequest(phone="+91-9876543210"), db=db_session)
    assert req_resp["delivery"] == "demo-not-sent"
    assert req_resp["demo_otp"] is not None
    assert len(req_resp["demo_otp"]) == 6
    otp = req_resp["demo_otp"]

    # 2. Verify OTP
    verify_resp = verify_otp(OTPVerifyRequest(phone="+91-9876543210", otp=otp), db=db_session)
    assert "access_token" in verify_resp
    assert verify_resp["token_type"] == "bearer"
    assert verify_resp["user"].name == "Kumar"
    assert verify_resp["user"].phone == "+91-9876543210"

def test_incorrect_otp_fails(db_session, monkeypatch):
    """Incorrect OTP attempt raises HTTP 400 with remaining attempts count."""
    monkeypatch.setattr(settings, "OTP_DEMO_MODE", True)
    
    req_resp = request_otp(OTPRequest(phone="+91-9876543210"), db=db_session)
    correct_otp = req_resp["demo_otp"]

    wrong_otp = "000000" if correct_otp != "000000" else "111111"
    with pytest.raises(HTTPException) as exc_info:
        verify_otp(OTPVerifyRequest(phone="+91-9876543210", otp=wrong_otp), db=db_session)
    assert exc_info.value.status_code == 400
    assert "Incorrect OTP" in exc_info.value.detail

def test_expired_otp_fails(db_session, monkeypatch):
    """Expired OTP (past 5 minutes) raises HTTP 400."""
    monkeypatch.setattr(settings, "OTP_DEMO_MODE", True)
    
    req_resp = request_otp(OTPRequest(phone="+91-9876543210"), db=db_session)
    otp = req_resp["demo_otp"]

    phone_key = "+91-9876543210"
    assert phone_key in otp_store._store
    # Fast forward OTP expiry past 300 seconds
    otp_store._store[phone_key].expires_at = time.time() - 10

    with pytest.raises(HTTPException) as exc_info:
        verify_otp(OTPVerifyRequest(phone=phone_key, otp=otp), db=db_session)
    assert exc_info.value.status_code == 400
    assert "expired" in exc_info.value.detail.lower()

def test_sixth_attempt_is_blocked(db_session, monkeypatch):
    """Maximum 5 incorrect attempts allowed; 6th attempt is blocked."""
    monkeypatch.setattr(settings, "OTP_DEMO_MODE", True)
    
    req_resp = request_otp(OTPRequest(phone="+91-9876543210"), db=db_session)
    correct_otp = req_resp["demo_otp"]
    wrong_otp = "000000" if correct_otp != "000000" else "111111"

    # Make 5 wrong attempts
    for attempt in range(1, 6):
        with pytest.raises(HTTPException) as exc_info:
            verify_otp(OTPVerifyRequest(phone="+91-9876543210", otp=wrong_otp), db=db_session)
        assert exc_info.value.status_code == 400

    # 6th attempt must be blocked
    with pytest.raises(HTTPException) as exc_info_6:
        verify_otp(OTPVerifyRequest(phone="+91-9876543210", otp=correct_otp), db=db_session)
    assert exc_info_6.value.status_code == 400
    assert "Maximum verification attempts exceeded" in exc_info_6.value.detail

def test_cooldown_is_enforced(db_session, monkeypatch):
    """Resend request within 30 seconds raises HTTP 429 Too Many Requests."""
    monkeypatch.setattr(settings, "OTP_DEMO_MODE", True)
    
    first_resp = request_otp(OTPRequest(phone="+91-9876543210"), db=db_session)
    assert first_resp["delivery"] == "demo-not-sent"

    with pytest.raises(HTTPException) as exc_info:
        request_otp(OTPRequest(phone="+91-9876543210"), db=db_session)
    assert exc_info.value.status_code == 429
    assert "seconds before requesting a new OTP" in exc_info.value.detail

def test_unknown_number_rejected(db_session):
    """Requesting OTP for an unregistered phone number raises HTTP 404."""
    with pytest.raises(HTTPException) as exc_info:
        request_otp(OTPRequest(phone="+91-0000000000"), db=db_session)
    assert exc_info.value.status_code == 404
    assert "Phone number not registered" in exc_info.value.detail

def test_otp_not_returned_when_demo_mode_false(db_session, monkeypatch):
    """When OTP_DEMO_MODE=False, demo_otp is None in response and no OTP is exposed."""
    monkeypatch.setattr(settings, "OTP_DEMO_MODE", False)
    
    resp = request_otp(OTPRequest(phone="+91-9876543210"), db=db_session)
    assert resp["demo_otp"] is None
    assert resp["delivery"] == "demo-not-sent"
