import hashlib
import hmac
import base64
import json
import time
from typing import Optional
from app.core.config import settings

def hash_password(password: str) -> str:
    salt = "harvestlink_salt_2026"
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(plain_password), hashed_password)

def create_access_token(data: dict, expires_in_seconds: int = 86400 * 7) -> str:
    payload = data.copy()
    payload["exp"] = int(time.time()) + expires_in_seconds
    raw_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    b64_payload = base64.urlsafe_b64encode(raw_json).decode('utf-8').rstrip('=')
    signature = hmac.new(settings.SECRET_KEY.encode('utf-8'), b64_payload.encode('utf-8'), hashlib.sha256).hexdigest()
    return f"{b64_payload}.{signature}"

def decode_access_token(token: str) -> Optional[dict]:
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None
        b64_payload, signature = parts
        expected_sig = hmac.new(settings.SECRET_KEY.encode('utf-8'), b64_payload.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return None
        # Add back padding
        padded = b64_payload + '=' * (-len(b64_payload) % 4)
        raw_json = base64.urlsafe_b64decode(padded.encode('utf-8'))
        payload = json.loads(raw_json.decode('utf-8'))
        if payload.get("exp", 0) < int(time.time()):
            return None
        return payload
    except Exception:
        return None
