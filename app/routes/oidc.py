from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from itsdangerous import BadSignature, URLSafeTimedSerializer
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_utils import create_access_token
from app.config import get_settings
from app.db import get_session
from app.routes.auth import _verify_id_token

router = APIRouter(prefix="/oidc", tags=["oidc"])
settings = get_settings()


async def _load_provider(session: AsyncSession, provider_id: str) -> dict:
    res = await session.execute(
        text(
            """
            SELECT id, name, config, tenant_id
            FROM idp_connections
            WHERE id=:id AND type='oidc' AND enabled=true
            """
        ),
        {"id": provider_id},
    )
    row = res.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="provider not found")
    return dict(row)


@router.get("/start/{provider_id}")
async def start(provider_id: str, session: Annotated[AsyncSession, Depends(get_session)]):
    cfg = await _load_provider(session, provider_id)
    serializer = URLSafeTimedSerializer(settings.jwt_secret)
    nonce = serializer.dumps({"p": str(cfg["id"])})
    params = {
        "response_type": "code",
        "client_id": cfg["config"]["client_id"],
        "redirect_uri": cfg["config"]["redirect_uri"],
        "scope": " ".join(cfg["config"].get("scopes", ["openid", "email", "profile"])),
        "state": nonce,
        "nonce": nonce,
    }
    return {"auth_url": cfg["config"]["auth_url"], "params": params}


@router.get("/callback/{provider_id}")
async def callback(
    provider_id: str,
    code: str,
    state: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    serializer = URLSafeTimedSerializer(settings.jwt_secret)
    try:
        data = serializer.loads(state, max_age=600)
    except BadSignature as exc:
        raise HTTPException(status_code=400, detail="invalid state") from exc
    cfg = await _load_provider(session, provider_id)
    if str(cfg["id"]) != str(data.get("p")):
        raise HTTPException(status_code=400, detail="state mismatch")
    async with httpx.AsyncClient(timeout=10) as client:
        token_resp = await client.post(
            cfg["config"]["token_url"],
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": cfg["config"]["redirect_uri"],
                "client_id": cfg["config"]["client_id"],
                "client_secret": cfg["config"]["client_secret"],
            },
            headers={"Accept": "application/json"},
        )
    if token_resp.status_code >= 400:
        raise HTTPException(status_code=400, detail="token exchange failed")
    token_data = token_resp.json()
    claims = await _verify_id_token(token_data["id_token"], cfg, data.get("nonce"))
    email = claims.get("email") or claims.get("preferred_username")
    if not email:
        raise HTTPException(status_code=400, detail="email not present in id_token")
    # Issue access token (user provisioning handled in auth.py route)
    from app.routes.auth import get_user_by_email
    user = await get_user_by_email(session, str(email).lower())
    if not user:
        raise HTTPException(status_code=403, detail="user not provisioned")
    token = create_access_token(user.id)
    resp = {"access_token": token, "token_type": "bearer"}
    return resp
