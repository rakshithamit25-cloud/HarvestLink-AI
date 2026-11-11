import secrets
import hashlib
import hmac
import time
import re
from typing import Optional, Dict, Tuple
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models import User

def normalize_phone(phone: str) -> str:
    """Strips formatting characters like spaces, dashes, parentheses."""
    if not phone:
        return ""
    return re.sub(r'[\s\-\(\)]', '', phone.strip())

def find_user_by_phone(db: Session, input_phone: str) -> Optional[User]:
    """Finds existing user by exact or normalized phone number. Never creates users."""
    if not input_phone:
        return None
    raw_clean = input_phone.strip()
    norm_input = normalize_phone(raw_clean)
    
    # 1. Exact match
    user = db.query(User).filter(User.phone == raw_clean).first()
    if user:
        return user
        
    # 2. Normalized match against all existing users
    all_users = db.query(User).filter(User.phone.isnot(None)).all()
    for u in all_users:
        if normalize_phone(u.phone) == norm_input:
            return u
            
    # 3. Last 10 digits match (for handling country code variations like +91)
    digits_input = re.sub(r'\D', '', raw_clean)
    if len(digits_input) >= 10:
        suffix_10 = digits_input[-10:]
        for u in all_users:
            digits_u = re.sub(r'\D', '', u.phone)
            if len(digits_u) >= 10 and digits_u[-10:] == suffix_10:
                return u
                
    return None

class OTPRecord:
    def __init__(self, otp_hash: str, salt: str):
        self.otp_hash = otp_hash
        self.salt = salt
        self.created_at = time.time()
        self.expires_at = self.created_at + 300  # 5 minutes
        self.last_requested_at = self.created_at
        self.attempts = 0

class InMemoryOTPStore:
    def __init__(self):
        self._store: Dict[str, OTPRecord] = {}

    def get_cooldown_remaining(self, phone_key: str) -> int:
        record = self._store.get(phone_key)
        if not record:
            return 0
        elapsed = time.time() - record.last_requested_at
        if elapsed < 30:
            return int(30 - elapsed)
        return 0

    def generate_otp(self, phone_key: str) -> str:
        """
        Generates a 6-digit OTP, stores only its SHA-256 hash with salt in memory.
        Returns the raw OTP string so the caller can conditionally provide it in demo mode.
        The OTP is never logged.
        """
        salt = secrets.token_hex(16)
        raw_otp = f"{secrets.randbelow(1_000_000):06d}"
        otp_hash = hashlib.sha256((raw_otp + salt).encode('utf-8')).hexdigest()
        
        record = OTPRecord(otp_hash=otp_hash, salt=salt)
        self._store[phone_key] = record
        return raw_otp

    def verify_otp(self, phone_key: str, input_otp: str) -> Tuple[bool, str]:
        """
        Verifies input_otp using constant-time HMAC comparison.
        Enforces 5-minute expiry and max 5 attempts.
        """
        record = self._store.get(phone_key)
        if not record:
            return False, "No active OTP found. Please request a new OTP."

        now = time.time()
        if now > record.expires_at:
            self._store.pop(phone_key, None)
            return False, "OTP has expired. Please request a new OTP."

        if record.attempts >= 5:
            return False, "Maximum verification attempts exceeded. Please request a new OTP."

        # Constant-time comparison
        input_hash = hashlib.sha256((input_otp.strip() + record.salt).encode('utf-8')).hexdigest()
        is_match = hmac.compare_digest(input_hash, record.otp_hash)

        if not is_match:
            record.attempts += 1
            if record.attempts >= 5:
                return False, "Maximum verification attempts exceeded. Please request a new OTP."
            remaining = 5 - record.attempts
            return False, f"Incorrect OTP. {remaining} attempt(s) remaining."

        # Successful verification: remove OTP from in-memory store
        self._store.pop(phone_key, None)
        return True, ""

    def clear(self):
        """Helper for unit tests."""
        self._store.clear()

otp_store = InMemoryOTPStore()
