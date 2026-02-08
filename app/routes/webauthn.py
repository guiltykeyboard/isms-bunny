from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth_utils
from app.db import get_session
from app.deps import get_current_user_jwt
from app.settings_store import get_setting, set_setting
from app.auth_utils import (
    build_webauthn_registration_options,
    verify_webauthn_registration,
    build_webauthn_authentication_options,
    verify_webauthn_authentication,
)

router = APIRouter(prefix="/webauthn", tags=["webauthn"])


@router.post("/register/options")
async def registration_options(
    user=Depends(get_current_user_jwt),
    session: Annotated[AsyncSession, Depends(get_session)],
):
    options = build_webauthn_registration_options(UUID(user.id), user.email)
    await set_setting(
        session,
        f"webauthn_reg_{user.id}",
        {
            "challenge": options.challenge.decode(),
        },
    )
    return options


@router.post("/register/verify")
async def registration_verify(
    payload: dict,
    user=Depends(get_current_user_jwt),
    session: Annotated[AsyncSession, Depends(get_session)],
):
    stored = await get_setting(session, f"webauthn_reg_{user.id}")
    if not stored or "challenge" not in stored:
        raise HTTPException(status_code=400, detail="No pending registration challenge")
    credential = payload.get("credential")
    if not credential:
        raise HTTPException(status_code=400, detail="Missing credential")
    try:
        verify_webauthn_registration(credential, stored["challenge"].encode())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Verification failed: {exc}")
    await set_setting(
        session,
        f"webauthn_cred_{user.id}",
        {"id": credential["id"], "public_key": credential.get("public_key", b"")},
    )
    return {"detail": "registered"}


@router.post("/login/options")
async def login_options(
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    cred = await get_setting(session, f"webauthn_cred_{user_id}")
    if not cred:
        raise HTTPException(status_code=404, detail="No credential stored")
    options = build_webauthn_authentication_options(cred["id"])
    await set_setting(
        session,
        f"webauthn_auth_{user_id}",
        {"challenge": options.challenge.decode()},
    )
    return options


@router.post("/login/verify")
async def login_verify(
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    user_id = payload.get("user_id")
    credential = payload.get("credential")
    if not user_id or not credential:
        raise HTTPException(status_code=400, detail="user_id and credential required")
    stored_chal = await get_setting(session, f"webauthn_auth_{user_id}")
    stored_cred = await get_setting(session, f"webauthn_cred_{user_id}")
    if not stored_chal or not stored_cred:
        raise HTTPException(status_code=404, detail="No pending auth challenge")
    verify_webauthn_authentication(
        credential,
        stored_chal["challenge"].encode(),
        stored_cred["public_key"],
    )
    return {"detail": "webauthn ok", "user_id": user_id}
