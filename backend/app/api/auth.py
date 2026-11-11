from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models import User
from app.schemas import UserLogin, TokenResponse, UserResponse, OTPRequest, OTPRequestResponse, OTPVerifyRequest
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.api.deps import get_current_user
from app.services.otp_service import otp_store, find_user_by_phone

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    access_token = create_access_token({"sub": str(user.id), "role": user.role, "name": user.name})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/otp/request", response_model=OTPRequestResponse)
def request_otp(req: OTPRequest, db: Session = Depends(get_db)):
    user = find_user_by_phone(db, req.phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not registered. Please use an existing registered user."
        )

    cooldown = otp_store.get_cooldown_remaining(user.phone)
    if cooldown > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Please wait {cooldown} seconds before requesting a new OTP"
        )

    raw_otp = otp_store.generate_otp(user.phone)

    if settings.OTP_DEMO_MODE:
        return {
            "message": "DEMO OTP: SMS not connected",
            "delivery": "demo-not-sent",
            "demo_otp": raw_otp,
            "expires_in_seconds": 300,
            "cooldown_seconds": 30
        }
    else:
        return {
            "message": "OTP generated. SMS delivery not connected.",
            "delivery": "demo-not-sent",
            "demo_otp": None,
            "expires_in_seconds": 300,
            "cooldown_seconds": 30
        }

@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(req: OTPVerifyRequest, db: Session = Depends(get_db)):
    user = find_user_by_phone(db, req.phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not registered"
        )

    is_valid, err_reason = otp_store.verify_otp(user.phone, req.otp)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_reason
        )

    access_token = create_access_token({"sub": str(user.id), "role": user.role, "name": user.name})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
