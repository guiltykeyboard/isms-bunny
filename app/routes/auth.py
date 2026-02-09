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


@router.get("/method")
async def auth_method(
    email: str,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    user = await get_user_by_email(session, email.lower().strip())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    providers = await session.execute(
        text(
            """
            SELECT id, name, type
            FROM idp_connections
            WHERE tenant_id=:tid AND enabled=true
            ORDER BY name
            """
        ),
        {"tid": tenant_id},
    )
    prov_list = [dict(r) for r in providers.mappings().all()]
    has_idp = len(prov_list) > 0
    recommendation = "local"
    enforce_external = False
    allow_local = bool(user.allow_local_fallback)
    if has_idp:
        first_type = prov_list[0]["type"]
        if user.auth_preference == "external" and not allow_local:
            recommendation = first_type
            enforce_external = True
        elif user.auth_preference == "local":
            recommendation = "local"
        else:
            recommendation = first_type
    return {
        "recommendation": recommendation,
        "enforce_external": enforce_external,
        "allow_local_fallback": allow_local,
        "auth_preference": user.auth_preference,
        "providers": prov_list,
    }


@router.post("/login")
async def login(
    response: Response,
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    tenant_id = current_tenant()
    idp_configured = False
    tenant_local_allowed = True
    if tenant_id:
        allow = await session.execute(
            "SELECT allow_local_login FROM tenants WHERE id=:tid",
            {"tid": tenant_id},
        )
        row = allow.fetchone()
        tenant_local_allowed = bool(row[0]) if row else True
        idp = await session.execute(
            "SELECT count(*) FROM idp_connections WHERE tenant_id=:tid AND enabled=true",
            {"tid": tenant_id},
        )
        idp_configured = (idp.scalar() or 0) > 0
    email = (payload.get("email") or "").lower().strip()
    password = payload.get("password")
    totp_code = payload.get("totp_code")

    if not email or not password:
        raise HTTPException(status_code=400, detail="email and password required")

    user = await get_user_by_email(session, email)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    break_glass = bool(payload.get("allow_break_glass", False)) or bool(user.allow_local_fallback)
    if idp_configured and user.auth_preference == "external" and not break_glass:
        raise HTTPException(status_code=403, detail="Use single sign-on for this account")
    if not tenant_local_allowed and not break_glass:
        raise HTTPException(status_code=403, detail="Local login disabled for this tenant")

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

    # External-first users must have TOTP enabled as a break-glass control when local auth is used.
    if user.auth_preference == "external" and not mfa_enabled:
        raise HTTPException(status_code=403, detail="TOTP is required for this account")

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
    if not auth.is_authenticated():
        await _log_saml(
            session,
            cfg.get("tenant_id"),
            "error",
            "SAML authentication failed",
            {"attributes": auth.get_attributes()},
        )
        raise HTTPException(status_code=401, detail="SAML authentication failed")
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
            options={"verify_at_hash": False, "require": ["exp", "iat", "iss", "aud"]},
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
    sp_acs = (
        cfg.get("saml_sp_acs_override")
        or cfg["config"].get("sp_acs_url")
        or str(request.url_for("saml_acs", provider=cfg["name"]))
    )
    sp_entity = cfg["config"].get("sp_entity_id") or sp_acs
    want_assertions_signed = cfg.get("saml_require_signed_assertions") or cfg["config"].get(
        "want_assertions_signed", True
    )
    want_messages_signed = cfg.get("saml_require_signed_messages") or cfg["config"].get(
        "want_messages_signed", False
    )
    sp_x509 = cfg["config"].get("sp_x509cert")
    sp_key = cfg["config"].get("sp_private_key")
    metadata_url = cfg["config"].get("idp_metadata_url")
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
            **({"x509cert": sp_x509, "privateKey": sp_key} if sp_x509 and sp_key else {}),
        },
        "idp": {
            "entityId": cfg["config"].get("idp_entity_id"),
            "singleSignOnService": {
                "url": cfg["config"].get("idp_sso_url"),
                "binding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect",
            },
            "x509cert": cfg["config"].get("idp_x509cert"),
            **({"metadataUrl": metadata_url} if metadata_url else {}),
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


@router.get("/login/auto")
async def login_auto(email: str, session: Annotated[AsyncSession, Depends(get_session)]):
    """
    Determine auth path by email: returns external provider info or local/passkey.
    """
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    user = await get_user_by_email(session, email.lower().strip())
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Prefer configured IdP if present and user is external-first
    providers = await session.execute(
        text(
            """
            SELECT id, name, type
            FROM idp_connections
            WHERE tenant_id=:tid AND enabled=true
            ORDER BY name
            """
        ),
        {"tid": tenant_id},
    )
    prov_list = [dict(r) for r in providers.mappings().all()]
    has_idp = len(prov_list) > 0
    if has_idp and user.auth_preference == "external" and not user.allow_local_fallback:
        return {"route": "external", "provider": prov_list[0], "providers": prov_list}
    return {
        "route": "local",
        "allow_webauthn": True,
        "require_totp": user.auth_preference == "external",
        "providers": prov_list,
    }
