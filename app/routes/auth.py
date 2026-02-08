import secrets
import urllib.parse
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from itsdangerous import BadSignature, URLSafeTimedSerializer
from jwt import PyJWKClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app import auth_utils
from app.config import get_settings
from app.context import current_tenant
from app.db import get_session
from app.models import User
from app.tokens import create_refresh_token, decode_refresh_token

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
    tenant_id = current_tenant()
    if tenant_id:
        allow = await session.execute(
            "SELECT allow_local_login FROM tenants WHERE id=:tid",
            {"tid": tenant_id},
        )
        row = allow.fetchone()
        if row and row[0] is False:
            raise HTTPException(status_code=403, detail="Local login disabled for this tenant")
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
    refresh = create_refresh_token(user.id)
    auth_utils.set_auth_cookies(response, token, refresh)
    return {"access_token": token, "refresh_token": refresh, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(settings.cookie_name)
    response.delete_cookie(settings.refresh_cookie_name)
    return {"detail": "logged out"}


@router.post("/refresh")
async def refresh_token(
    response: Response,
    payload: dict,
):
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="refresh_token required")
    user_id = decode_refresh_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="invalid refresh token")
    access = auth_utils.create_access_token(user_id)
    auth_utils.set_auth_cookies(response, access, token)
    return {"access_token": access, "token_type": "bearer"}


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str):
    response.set_cookie(
        key=settings.cookie_name,
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.refresh_token_expiry_days * 24 * 3600,
        path="/",
    )


# ---------- OIDC ----------
@router.get("/oidc/{provider}/start")
async def oidc_start(provider: str, session: Annotated[AsyncSession, Depends(get_session)]):
    """
    Build an authorization URL for a configured OIDC provider.
    Expects provider config (auth_url, token_url, userinfo_url, client_id,
    client_secret, redirect_uri, scopes[]) stored in idp_connections.
    """
    cfg = await _load_provider(session, provider, "oidc")
    nonce = secrets.token_urlsafe(16)
    serializer = URLSafeTimedSerializer(settings.jwt_secret)
    state = serializer.dumps({"p": cfg["id"], "t": cfg.get("tenant_id"), "n": nonce})
    params = {
        "response_type": "code",
        "client_id": cfg["config"]["client_id"],
        "redirect_uri": cfg["config"]["redirect_uri"],
        "scope": " ".join(cfg["config"].get("scopes", ["openid", "email", "profile"])),
        "state": state,
        "nonce": nonce,
    }
    url = cfg["config"]["auth_url"] + "?" + urllib.parse.urlencode(params)
    return {"auth_url": url, "state": state}


@router.get("/oidc/{provider}/callback")
async def oidc_callback(
    provider: str,
    code: str,
    state: str,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    serializer = URLSafeTimedSerializer(settings.jwt_secret)
    try:
        data = serializer.loads(state, max_age=600)
    except BadSignature:
        raise HTTPException(status_code=400, detail="invalid state") from None

    cfg = await _load_provider(session, provider, "oidc")
    if str(cfg["id"]) != str(data.get("p")):
        raise HTTPException(status_code=400, detail="state provider mismatch")

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
    email = None
    if "id_token" in token_data:
        claims = await _verify_id_token(token_data["id_token"], cfg, data.get("n"))
        email = claims.get("email") or claims.get("preferred_username")
    if not email:
        # fallback to userinfo
        bearer = token_data.get("access_token", "")
        async with httpx.AsyncClient(timeout=10) as client:
            ui_resp = await client.get(
                cfg["config"]["userinfo_url"],
                headers={"Authorization": f"Bearer {bearer}"},
            )
            if ui_resp.status_code < 400:
                email = ui_resp.json().get("email")
    if not email:
        raise HTTPException(status_code=400, detail="email not returned by provider")

    user = await get_user_by_email(session, email.lower())
    if not user:
        # auto-provision minimal user
        result = await session.execute(
            """
            INSERT INTO users (email, full_name, status)
            VALUES (:email, :name, 'active')
            RETURNING id
            """,
            {"email": email.lower(), "name": email.split("@")[0]},
        )
        user_id = result.scalar_one()
        # attach to tenant if scoped
        tenant_id = data.get("t") or cfg.get("tenant_id")
        if tenant_id:
            await session.execute(
                """
                INSERT INTO memberships (user_id, tenant_id, roles)
                VALUES (:uid, :tid, ARRAY['viewer'])
                ON CONFLICT DO NOTHING
                """,
                {"uid": user_id, "tid": tenant_id},
            )
        user = await get_user_by_email(session, email.lower())
    token = auth_utils.create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    auth_utils.set_auth_cookies(response, token, refresh)
    await session.commit()
    return {"access_token": token, "refresh_token": refresh, "token_type": "bearer"}


@router.get("/saml/metadata")
async def saml_metadata(
    request: Request,
    provider: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    cfg = await _load_provider(session, provider, "saml")
    settings = _build_saml_settings(cfg, request)
    from onelogin.saml2.settings import OneLogin_Saml2_Settings

    saml_settings = OneLogin_Saml2_Settings(settings=settings, sp_validation_only=True)
    metadata = saml_settings.get_sp_metadata()
    return Response(content=metadata, media_type="application/xml")


@router.get("/saml/{provider}/login")
async def saml_login(
    request: Request, provider: str, session: Annotated[AsyncSession, Depends(get_session)]
):
    cfg = await _load_provider(session, provider, "saml")
    auth = _build_saml_auth(cfg, request)
    return {"redirect": auth.login()}


@router.post("/saml/{provider}/acs")
async def saml_acs(
    request: Request,
    provider: str,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    cfg = await _load_provider(session, provider, "saml")
    form = await request.form()
    auth = _build_saml_auth(cfg, request, dict(form))
    auth.process_response()
    errors = auth.get_errors()
    if errors:
        await _log_saml(
            session, cfg.get("tenant_id"), "error", "SAML ACS error", {"errors": errors}
        )
        raise HTTPException(status_code=400, detail=f"SAML error: {errors}")
    email = auth.get_nameid() or auth.get_attribute("email") or auth.get_attribute("mail")
    if isinstance(email, list):
        email = email[0]
    if not email:
        await _log_saml(
            session, cfg.get("tenant_id"), "error", "SAML assertion missing email", {}
        )
        raise HTTPException(status_code=400, detail="email not found in assertion")
    user = await get_user_by_email(session, str(email).lower())
    if not user:
        result = await session.execute(
            """
            INSERT INTO users (email, full_name, status)
            VALUES (:email, :name, 'active')
            RETURNING id
            """,
            {"email": str(email).lower(), "name": str(email).split("@")[0]},
        )
        user_id = result.scalar_one()
        tenant_id = cfg.get("tenant_id")
        if tenant_id:
            await session.execute(
                """
                INSERT INTO memberships (user_id, tenant_id, roles)
                VALUES (:uid, :tid, ARRAY['viewer'])
                ON CONFLICT DO NOTHING
                """,
                {"uid": user_id, "tid": tenant_id},
            )
        user = await get_user_by_email(session, str(email).lower())
    token = auth_utils.create_access_token(user.id)
    refresh = create_refresh_token(user.id)
    auth_utils.set_auth_cookies(response, token, refresh)
    await session.commit()
    await _log_saml(
        session, cfg.get("tenant_id"), "info", "SAML login success", {"email": str(email)}
    )
    return {"access_token": token, "refresh_token": refresh, "token_type": "bearer"}


async def _load_provider(session: AsyncSession, name: str, ptype: str) -> dict:
    result = await session.execute(
        """
        SELECT id, name, type, config, enabled, tenant_id
        FROM idp_connections
        WHERE lower(name)=lower(:name) AND type=:type AND enabled=true
        LIMIT 1
        """,
        {"name": name, "type": ptype},
    )
    cfg = result.mappings().first()
    if not cfg:
        raise HTTPException(status_code=404, detail=f"{ptype} provider not found or disabled")
    return dict(cfg)


async def _verify_id_token(id_token: str, cfg: dict, expected_nonce: str | None) -> dict:
    jwks_url = cfg["config"].get("jwks_url")
    issuer = cfg["config"].get("issuer")
    audience = cfg["config"].get("client_id")
    if not jwks_url:
        raise HTTPException(status_code=400, detail="jwks_url not configured for provider")
    try:
        jwk_client = PyJWKClient(jwks_url)
        signing_key = jwk_client.get_signing_key_from_jwt(id_token).key
        import jwt

        claims = jwt.decode(
            id_token,
            signing_key,
            algorithms=["RS256", "ES256", "RS512", "ES512"],
            audience=audience,
            issuer=issuer,
        )
        if expected_nonce and claims.get("nonce") != expected_nonce:
            raise HTTPException(status_code=400, detail="nonce mismatch")
        return claims
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"id_token validation failed: {exc}") from None


def _saml_request_data(request: Request, post_data: dict) -> dict:
    # Minimal ASGI -> WSGI adapter fields for python3-saml
    url = str(request.url)
    return {
        "https": "on" if request.url.scheme == "https" else "off",
        "http_host": request.headers.get("host", ""),
        "server_port": request.url.port or (443 if request.url.scheme == "https" else 80),
        "script_name": request.url.path,
        "get_data": dict(request.query_params),
        "post_data": post_data,
        "url": url,
    }


def _build_saml_settings(cfg: dict, request: Request) -> dict:
    sp_acs = cfg["config"].get("sp_acs_url") or str(
        request.url_for("saml_acs", provider=cfg["name"])
    )
    sp_entity = cfg["config"].get("sp_entity_id") or sp_acs
    want_assertions_signed = cfg["config"].get("want_assertions_signed", True)
    want_messages_signed = cfg["config"].get("want_messages_signed", False)
    requested_context = cfg["config"].get("requested_authn_context", [])
    return {
        "strict": True,
        "debug": False,
        "sp": {
            "entityId": sp_entity,
            "assertionConsumerService": {
                "url": sp_acs,
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
            },
        },
        "idp": {
            "entityId": cfg["config"]["idp_entity_id"],
            "singleSignOnService": {
                "url": cfg["config"]["idp_sso_url"],
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": cfg["config"]["idp_x509cert"],
        },
        "security": {
            "authnRequestsSigned": want_messages_signed,
            "logoutRequestSigned": want_messages_signed,
            "logoutResponseSigned": want_messages_signed,
            "wantAssertionsSigned": want_assertions_signed,
            "wantMessagesSigned": want_messages_signed,
        },
        "requestedAuthnContext": requested_context,
    }


def _build_saml_auth(cfg: dict, request: Request, post_data: dict | None = None):
    from onelogin.saml2.auth import OneLogin_Saml2_Auth

    req_data = _saml_request_data(request, post_data or {})
    return OneLogin_Saml2_Auth(req_data, old_settings=_build_saml_settings(cfg, request))


async def _log_saml(session: AsyncSession, tenant_id, level: str, message: str, details: dict):
    if not tenant_id:
        return
    await session.execute(
        text(
            """
            INSERT INTO saml_logs (tenant_id, level, message, details)
            VALUES (:tid, :lvl, :msg, :det)
            """
        ),
        {"tid": tenant_id, "lvl": level, "msg": message, "det": details or {}},
    )
    await session.commit()
