from base64 import urlsafe_b64decode
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth_utils
from app.auth_utils import (
    build_webauthn_authentication_options,
    build_webauthn_registration_options,
    verify_webauthn_authentication,
    verify_webauthn_registration,
)
from app.authz import require_msp_admin
from app.db import get_session
from app.deps import get_current_user_jwt
from app.settings_store import get_setting, set_setting
from app.tokens import create_refresh_token

router = APIRouter(prefix="/webauthn", tags=["webauthn"])


def _b64decode_bytes(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return urlsafe_b64decode(value + padding)


def _b64encode_bytes(data: bytes) -> str:
    import base64

    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


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
    email = payload.get("email")
    if not user_id and not email:
        raise HTTPException(status_code=400, detail="user_id or email required")
    if not user_id and email:
        row = await session.execute(
            text("SELECT id FROM users WHERE lower(email)=lower(:email)"),
            {"email": email},
        )
        found = row.scalar_one_or_none()
        if not found:
            raise HTTPException(status_code=404, detail="User not found")
        user_id = found
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
    response: Response,
):
    user_id = payload.get("user_id")
    credential = payload.get("credential")
    if not credential:
        raise HTTPException(status_code=400, detail="credential required")

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
            SELECT public_key, sign_count, user_id
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
    # issue login tokens
    token_row = await session.execute(
        text("SELECT id FROM users WHERE id=:uid"), {"uid": stored_cred.user_id}
        if hasattr(stored_cred, "user_id")
        else {"uid": user_id}
    )
    user_row = token_row.scalar_one_or_none()
    final_user_id = user_row or user_id
    access = auth_utils.create_access_token(final_user_id)
    refresh = create_refresh_token(final_user_id)
    auth_utils.set_auth_cookies(response, access, refresh)
    await session.commit()
    return {
        "detail": "webauthn ok",
        "user_id": str(final_user_id),
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    }


@router.get("/credentials/me")
async def list_my_credentials(
    user: Annotated[object, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    rows = await session.execute(
        text(
            """
            SELECT credential_id, nickname, sign_count, created_at
            FROM webauthn_credentials
            WHERE user_id = :uid
            ORDER BY created_at DESC
            """
        ),
        {"uid": user.id},
    )
    creds = [
        {
            "id": _b64encode_bytes(r.credential_id),
            "nickname": r.nickname,
            "sign_count": r.sign_count,
            "created_at": r.created_at,
        }
        for r in rows.fetchall()
    ]
    return creds


@router.delete("/credentials/me/{cred_id}")
async def delete_my_credential(
    cred_id: str,
    user: Annotated[object, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    await session.execute(
        text(
            "DELETE FROM webauthn_credentials WHERE credential_id=:cid AND user_id=:uid"
        ),
        {"cid": _b64decode_bytes(cred_id), "uid": user.id},
    )
    await session.commit()
    return {"detail": "deleted"}


@router.get("/credentials/user/{user_id}")
async def admin_list_credentials(
    user_id: UUID,
    user: Annotated[object, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    require_msp_admin(user.is_msp_admin)
    rows = await session.execute(
        text(
            """
            SELECT credential_id, nickname, sign_count, created_at
            FROM webauthn_credentials
            WHERE user_id = :uid
            ORDER BY created_at DESC
            """
        ),
        {"uid": user_id},
    )
    return [
        {
            "id": _b64encode_bytes(r.credential_id),
            "nickname": r.nickname,
            "sign_count": r.sign_count,
            "created_at": r.created_at,
        }
        for r in rows.fetchall()
    ]


@router.delete("/credentials/user/{user_id}/{cred_id}")
async def admin_delete_credential(
    user_id: UUID,
    cred_id: str,
    user: Annotated[object, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    require_msp_admin(user.is_msp_admin)
    await session.execute(
        text(
            "DELETE FROM webauthn_credentials WHERE credential_id=:cid AND user_id=:uid"
        ),
        {"cid": _b64decode_bytes(cred_id), "uid": user_id},
    )
    await session.commit()
    return {"detail": "deleted"}
