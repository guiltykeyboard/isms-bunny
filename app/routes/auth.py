from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth_utils
from app.config import get_settings
from app.db import get_session
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


@router.post("/login")
async def login(
    response: Response,
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    email = (payload.get("email") or "").lower().strip()
    password = payload.get("password")
    totp_code = payload.get("totp_code")

    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password required")

    user = await get_user_by_email(session, email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    cred = await session.execute(
        """
        SELECT password_hash, mfa_enabled, totp_secret
        FROM local_credentials
        WHERE user_id = :uid
        """,
        {"uid": user.id},
    )
    row = cred.fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Local login not configured")

    password_hash, mfa_enabled, totp_secret = row
    if not auth_utils.verify_password(password, password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if mfa_enabled:
        if not totp_code or not auth_utils.verify_totp(totp_secret, totp_code):
            raise HTTPException(status_code=401, detail="Invalid or missing TOTP code")

    token = auth_utils.create_access_token(user.id)
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
    )
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(settings.cookie_name)
    return {"detail": "logged out"}
