from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.deps import get_current_user_jwt
from app.models import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def me(user: Annotated[User, Depends(get_current_user_jwt)]):
    return {
        "id": str(user.id),
        "email": user.email,
        "is_msp_admin": user.is_msp_admin,
        "theme_preference": user.theme_preference,
    }


@router.patch("/me/theme")
async def update_theme(
    payload: dict,
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    new_pref = payload.get("theme_preference")
    if new_pref not in {"system", "dark", "light"}:
        return {"error": "theme_preference must be system|dark|light"}

    await session.execute(
        update(User)
        .where(User.id == user.id)
        .values(theme_preference=new_pref)
    )
    await session.commit()
    return {"theme_preference": new_pref}
