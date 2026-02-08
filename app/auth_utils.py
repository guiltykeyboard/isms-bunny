import datetime
from typing import Optional
from uuid import UUID

import pyotp
from argon2 import PasswordHasher
from jose import jwt

from app.config import get_settings

settings = get_settings()
ph = PasswordHasher()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return ph.verify(password_hash, password)
    except Exception:
        return False


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    try:
        return totp.verify(code, valid_window=1)
    except Exception:
        return False


def create_access_token(user_id: UUID, expires_minutes: Optional[int] = None) -> str:
    exp_minutes = expires_minutes or settings.access_token_expiry_minutes
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=exp_minutes)
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> Optional[UUID]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        sub = payload.get("sub")
        return UUID(sub) if sub else None
    except Exception:
        return None
