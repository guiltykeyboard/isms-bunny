from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.context import current_user, set_msp_admin, set_user
from app.db import get_session
from app.models import User


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
        raise HTTPException(status_code=401, detail="Unauthenticated (dev stub)")
    result = await session.execute(select(User).where(User.id == current_user()))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
