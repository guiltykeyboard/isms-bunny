from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth_utils import hash_password
from app.config import get_settings
from app.db import get_session
from app.settings_store import is_initialized, set_setting

router = APIRouter(prefix="/setup", tags=["setup"])
settings = get_settings()


@router.get("/status")
async def setup_status(session: Annotated[AsyncSession, Depends(get_session)]):
    initialized = await is_initialized(session)
    return {"initialized": initialized}


@router.post("/initialize")
async def setup_initialize(
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    if await is_initialized(session):
        raise HTTPException(status_code=400, detail="Already initialized")

    company = payload.get("company_name", "MSP Tenant")
    fqdn = payload.get("fqdn", settings.default_tenant_fqdn)
    admin_email = payload.get("admin_email")
    admin_password = payload.get("admin_password")
    storage_cfg = payload.get("storage", {})

    if not admin_email or not admin_password:
        raise HTTPException(status_code=400, detail="admin_email and admin_password required")

    # Create tenant
    result = await session.execute(
        """
        INSERT INTO tenants (name, fqdn, type, storage_config)
        VALUES (:name, :fqdn, 'internal_msp', :storage)
        RETURNING id
        """,
        {"name": company, "fqdn": fqdn.lower(), "storage": storage_cfg},
    )
    tenant_id = result.scalar_one()

    # Create admin user
    result = await session.execute(
        """
        INSERT INTO users (email, full_name, is_msp_admin, status)
        VALUES (:email, :name, true, 'active')
        RETURNING id
        """,
        {"email": admin_email.lower(), "name": "MSP Admin"},
    )
    user_id = result.scalar_one()

    await session.execute(
        """
        INSERT INTO memberships (user_id, tenant_id, roles)
        VALUES (:uid, :tid, ARRAY['msp_admin'])
        """,
        {"uid": user_id, "tid": tenant_id},
    )

    await session.execute(
        """
        INSERT INTO local_credentials (user_id, password_hash, mfa_enabled)
        VALUES (:uid, :pwd, false)
        """,
        {"uid": user_id, "pwd": hash_password(admin_password)},
    )

    # store defaults
    await set_setting(session, "initialized", True)
    await set_setting(session, "default_tenant_id", str(tenant_id))
    await set_setting(session, "default_tenant_fqdn", fqdn.lower())

    await session.commit()
    return {"detail": "initialized", "tenant_id": str(tenant_id), "admin_user_id": str(user_id)}
