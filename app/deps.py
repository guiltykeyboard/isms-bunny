from typing import Annotated, Optional
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_utils import decode_access_token
from app.config import get_settings
from app.context import current_user, set_msp_admin, set_user
from app.db import get_session
from app.models import User

settings = get_settings()


async def inject_user(
    x_user_id: str | None = Header(default=None, convert_underscores=False),
    x_is_msp_admin: str | None = Header(default=None, convert_underscores=False),
) -> UUID | None:
    """
    Development-only user injection. Replace with real auth later.
    Accepts:
      - X-User-Id: UUID string
      - X-Is-Msp-Admin: "true"/"false"
    """
    user_id: UUID | None = None
    if x_user_id:
        try:
            user_id = UUID(x_user_id)
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid X-User-Id header"
            ) from None
    is_admin = (x_is_msp_admin or "").lower() == "true"

    set_user(user_id)
    set_msp_admin(is_admin)
    return user_id


async def get_current_user(
    _user_injected: Annotated[UUID | None, Depends(inject_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if current_user() is None:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    result = await session.execute(select(User).where(User.id == current_user()))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def extract_token(request: Request, cookie_token: Optional[str]) -> Optional[str]:
    # Prefer Authorization bearer header
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    # Fallback to cookie
    if cookie_token:
        return cookie_token
    return None


async def auth_or_header_user(
    request: Request,
    cookie_token: Optional[str] = Cookie(default=None, alias=settings.cookie_name),
) -> UUID | None:
    token = extract_token(request, cookie_token)
    if token:
        user_id = decode_access_token(token)
        if user_id:
            set_user(user_id)
            # msp admin flag will be set after user lookup
            return user_id
    # fall back to dev header injection
    return await inject_user(
        x_user_id=request.headers.get("X-User-Id"),
        x_is_msp_admin=request.headers.get("X-Is-Msp-Admin"),
    )


async def get_current_user_jwt(
    _user_id: Annotated[UUID | None, Depends(auth_or_header_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    if current_user() is None:
        raise HTTPException(status_code=401, detail="Unauthenticated")
    result = await session.execute(select(User).where(User.id == current_user()))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    set_msp_admin(user.is_msp_admin)
    return user
