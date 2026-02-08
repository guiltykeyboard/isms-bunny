import datetime
from typing import Optional
from uuid import UUID

import jwt
import pyotp
from argon2 import PasswordHasher
from fastapi import Response
from webauthn import verify_authentication_response, verify_registration_response
from webauthn.helpers.structs import (
    AuthenticationCredential,
    PublicKeyCredentialCreationOptions,
    PublicKeyCredentialRequestOptions,
    RegistrationCredential,
)

from app.config import get_settings

settings = get_settings()
ph = PasswordHasher()

# WebAuthn relying party defaults
RP_ID = "localhost"
RP_NAME = "ISMS-Bunny"


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


def jwt_decode_no_verify(token: str) -> dict:
    try:
        return jwt.decode(token, options={"verify_signature": False})
    except Exception:
        return {}


# WebAuthn helpers (minimal stubs)
def build_webauthn_registration_options(
    user_id: UUID, username: str
) -> PublicKeyCredentialCreationOptions:
    return PublicKeyCredentialCreationOptions(
        rp={"id": RP_ID, "name": RP_NAME},
        user={
            "id": str(user_id).encode(),
            "name": username,
            "displayName": username,
        },
        challenge=pyotp.random_base32().encode(),
        pub_key_cred_params=[{"type": "public-key", "alg": -7}],
    )


def verify_webauthn_registration(credential: RegistrationCredential, expected_challenge: bytes):
    return verify_registration_response(
        credential=credential,
        expected_challenge=expected_challenge,
        expected_origin=f"https://{RP_ID}",
        expected_rp_id=RP_ID,
    )


def build_webauthn_authentication_options(
    credential_id: bytes,
) -> PublicKeyCredentialRequestOptions:
    return PublicKeyCredentialRequestOptions(
        challenge=pyotp.random_base32().encode(),
        rp_id=RP_ID,
        allow_credentials=[{"type": "public-key", "id": credential_id}],
    )


def verify_webauthn_authentication(
    credential: AuthenticationCredential,
    expected_challenge: bytes,
    stored_public_key: bytes,
):
    origin = f"https://{RP_ID}"
    return verify_authentication_response(
        credential=credential,
        expected_challenge=expected_challenge,
        expected_rp_id=RP_ID,
        expected_origin=origin,
        credential_public_key=stored_public_key,
        credential_current_sign_count=0,
    )


def set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    """
    Centralised cookie setter for access/refresh tokens.
    Keeps cookies httpOnly/secure and aligned with config defaults.
    """
    response.set_cookie(
        key=settings.cookie_name,
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=settings.access_token_expiry_minutes * 60,
    )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.refresh_token_expiry_days * 24 * 3600,
        path="/",
    )
