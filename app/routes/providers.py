from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import require_msp_admin
from app.db import get_session
from app.deps import get_current_user_jwt
from app.settings_store import get_setting, set_setting

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/oidc")
async def list_oidc(
    user=Depends(get_current_user_jwt),
    session: Annotated[AsyncSession, Depends(get_session)],
):
    require_msp_admin(user.is_msp_admin)
    cfg = await get_setting(session, "oidc_providers")
    return cfg or []


@router.put("/oidc")
async def upsert_oidc(
    payload: list[dict],
    user=Depends(get_current_user_jwt),
    session: Annotated[AsyncSession, Depends(get_session)],
):
    require_msp_admin(user.is_msp_admin)
    await set_setting(session, "oidc_providers", payload)
    return {"detail": "saved"}


@router.get("/saml")
async def list_saml(
    user=Depends(get_current_user_jwt),
    session: Annotated[AsyncSession, Depends(get_session)],
):
    require_msp_admin(user.is_msp_admin)
    cfg = await get_setting(session, "saml_providers")
    return cfg or []


@router.put("/saml")
async def upsert_saml(
    payload: list[dict],
    user=Depends(get_current_user_jwt),
    session: Annotated[AsyncSession, Depends(get_session)],
):
    require_msp_admin(user.is_msp_admin)
    await set_setting(session, "saml_providers", payload)
    return {"detail": "saved"}
