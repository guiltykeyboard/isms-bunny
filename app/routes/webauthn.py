from base64 import urlsafe_b64decode
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_utils import (
    build_webauthn_authentication_options,
    build_webauthn_registration_options,
    verify_webauthn_authentication,
    verify_webauthn_registration,
)
from app.db import get_session
from app.deps import get_current_user_jwt
from app.settings_store import get_setting, set_setting

router = APIRouter(prefix="/webauthn", tags=["webauthn"])


def _b64decode_bytes(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return urlsafe_b64decode(value + padding)


@router.post("/register/options")
async def registration_options(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    existing = await session.execute(
        text(
            """
            SELECT credential_id
            FROM webauthn_credentials
            WHERE user_id=:uid
            ORDER BY created_at ASC
            """
        ),
        {"uid": user.id},
    )
    exclude = [{"type": "public-key", "id": row[0]} for row in existing.fetchall()]
    options = build_webauthn_registration_options(UUID(user.id), user.email)
    options.exclude_credentials = exclude
    await set_setting(
        session,
        f"webauthn_reg_{user.id}",
        {"challenge": options.challenge.decode()},
    )
    return options


@router.post("/register/verify")
async def registration_verify(
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    stored = await get_setting(session, f"webauthn_reg_{user.id}")
    if not stored or "challenge" not in stored:
        raise HTTPException(status_code=400, detail="No pending registration challenge")
    credential = payload.get("credential")
    if not credential:
        raise HTTPException(status_code=400, detail="Missing credential")
    try:
        verified = verify_webauthn_registration(credential, stored["challenge"].encode())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Verification failed: {exc}") from None

    cred_id = _b64decode_bytes(credential["id"])
    public_key = verified.credential_public_key
    sign_count = verified.sign_count
    await session.execute(
        text(
            """
            INSERT INTO webauthn_credentials
                (user_id, credential_id, public_key, sign_count, nickname)
            VALUES (:uid, :cid, :pub, :sc, :nick)
            ON CONFLICT (credential_id) DO UPDATE
            SET public_key = EXCLUDED.public_key, sign_count = EXCLUDED.sign_count
            """
        ),
        {
            "uid": user.id,
            "cid": cred_id,
            "pub": public_key,
            "sc": sign_count,
            "nick": payload.get("nickname"),
        },
    )
    await session.commit()
    return {"detail": "registered", "sign_count": sign_count}


@router.post("/login/options")
async def login_options(
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    cred_rows = await session.execute(
        text(
            """
            SELECT credential_id
            FROM webauthn_credentials
            WHERE user_id=:uid
            ORDER BY created_at ASC
            LIMIT 1
            """
        ),
        {"uid": user_id},
    )
    cred_row = cred_rows.fetchone()
    if not cred_row:
        raise HTTPException(status_code=404, detail="No credential stored")
    options = build_webauthn_authentication_options(cred_row[0])
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
    if not stored_chal:
        raise HTTPException(status_code=404, detail="No pending auth challenge")

    raw_id = credential.get("raw_id") or credential.get("rawId") or credential.get("id")
    if not raw_id:
        raise HTTPException(status_code=400, detail="Missing credential id")
    cred_id_bytes = _b64decode_bytes(raw_id)
    row = await session.execute(
        text(
            """
            SELECT public_key, sign_count
            FROM webauthn_credentials
            WHERE credential_id=:cid AND user_id=:uid
            """
        ),
        {"cid": cred_id_bytes, "uid": user_id},
    )
    stored_cred = row.fetchone()
    if not stored_cred:
        raise HTTPException(status_code=404, detail="Unknown credential")

    try:
        verified = verify_webauthn_authentication(
            credential,
            stored_chal["challenge"].encode(),
            stored_cred.public_key,
            stored_cred.sign_count or 0,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Verification failed: {exc}") from None

    await session.execute(
        text("UPDATE webauthn_credentials SET sign_count=:sc WHERE credential_id=:cid"),
        {
            "sc": getattr(verified, "new_sign_count", (stored_cred.sign_count or 0) + 1),
            "cid": cred_id_bytes,
        },
    )
    await session.commit()
    return {"detail": "webauthn ok", "user_id": user_id}
