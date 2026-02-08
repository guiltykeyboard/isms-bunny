from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
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
        "auth_preference": user.auth_preference,
        "allow_local_fallback": user.allow_local_fallback,
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


@router.patch("/me/auth")
async def update_auth_pref(
    payload: dict,
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    auth_pref = payload.get("auth_preference")
    allow_local = payload.get("allow_local_fallback")
    updates = {}
    if auth_pref in {"external", "local", "either"}:
        updates["auth_preference"] = auth_pref
    if allow_local is not None:
        updates["allow_local_fallback"] = bool(allow_local)
    if not updates:
        return {"error": "nothing to update"}
    await session.execute(
        update(User)
        .where(User.id == user.id)
        .values(**updates)
    )
    await session.commit()
    return {
        "auth_preference": updates.get("auth_preference", user.auth_preference),
        "allow_local_fallback": updates.get("allow_local_fallback", user.allow_local_fallback),
    }


@router.patch("/{user_id}/auth")
async def admin_update_auth_pref(
    user_id: str,
    payload: dict,
    current: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if not current.is_msp_admin:
        raise HTTPException(status_code=403, detail="MSP admin required")
    auth_pref = payload.get("auth_preference")
    allow_local = payload.get("allow_local_fallback")
    updates = {}
    if auth_pref in {"external", "local", "either"}:
        updates["auth_preference"] = auth_pref
    if allow_local is not None:
        updates["allow_local_fallback"] = bool(allow_local)
    if not updates:
        return {"error": "nothing to update"}
    result = await session.execute(
        update(User)
        .where(User.id == user_id)
        .values(**updates)
        .returning(User.id, User.auth_preference, User.allow_local_fallback)
    )
    row = result.fetchone()
    await session.commit()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(row.id),
        "auth_preference": row.auth_preference,
        "allow_local_fallback": row.allow_local_fallback,
    }
