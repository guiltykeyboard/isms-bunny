from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import assert_tenant_access, enforce_current_tenant, require_msp_admin
from app.context import current_tenant
from app.db import get_session
from app.deps import get_current_user_jwt
from app.models import Tenant, User

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.get("")
async def list_tenants(
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    require_msp_admin(user.is_msp_admin)
    result = await session.execute(select(Tenant))
    tenants = result.scalars().all()
    return [
        {"id": str(t.id), "name": t.name, "fqdn": t.fqdn, "type": t.type}
        for t in tenants
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: dict,
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    require_msp_admin(user.is_msp_admin)
    name = payload.get("name")
    fqdn = payload.get("fqdn")
    tenant_type = payload.get("type", "customer")
    if not name or not fqdn:
        raise HTTPException(status_code=400, detail="name and fqdn are required")
    stmt = (
        insert(Tenant)
        .values(name=name, fqdn=fqdn.lower(), type=tenant_type)
        .returning(Tenant)
    )
    result = await session.execute(stmt)
    await session.commit()
    t = result.scalar_one()
    return {"id": str(t.id), "name": t.name, "fqdn": t.fqdn, "type": t.type}


@router.get("/{tenant_id}")
async def get_tenant(
    tenant_id: UUID,
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    await assert_tenant_access(session, user.id, tenant_id, user.is_msp_admin)
    enforce_current_tenant(tenant_id)
    result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"id": str(t.id), "name": t.name, "fqdn": t.fqdn, "type": t.type}


@router.patch("/{tenant_id}")
async def update_tenant(
    tenant_id: UUID,
    payload: dict,
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    require_msp_admin(user.is_msp_admin)
    stmt = (
        sql_update(Tenant)
        .where(Tenant.id == tenant_id)
        .values(
            name=payload.get("name"),
            fqdn=payload.get("fqdn"),
            type=payload.get("type", "customer"),
        )
        .returning(Tenant)
    )
    result = await session.execute(stmt)
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    await session.commit()
    return {"id": str(t.id), "name": t.name, "fqdn": t.fqdn, "type": t.type}


@router.get("/current")
async def current_tenant_info(
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Tenant not resolved")
    await assert_tenant_access(session, user.id, tenant_id, user.is_msp_admin)
    result = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {
        "id": str(t.id),
        "name": t.name,
        "fqdn": t.fqdn,
        "type": t.type,
        "storage_config": getattr(t, "storage_config", None),
        "smtp_config": getattr(t, "smtp_config", None),
    }


@router.patch("/{tenant_id}/storage")
async def update_tenant_storage(
    tenant_id: UUID,
    payload: dict,
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Update per-tenant storage configuration (BYO S3-compatible).
    """
    require_msp_admin(user.is_msp_admin)
    storage_cfg = payload.get("storage_config") or payload
    result = await session.execute(
        sql_update(Tenant)
        .where(Tenant.id == tenant_id)
        .values(storage_config=storage_cfg)
        .returning(Tenant)
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    await session.commit()
    return {
        "id": str(t.id),
        "storage_config": storage_cfg,
    }


@router.patch("/{tenant_id}/smtp")
async def update_tenant_smtp(
    tenant_id: UUID,
    payload: dict,
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Update per-tenant SMTP configuration. Empty payload clears to MSP default.
    """
    require_msp_admin(user.is_msp_admin)
    smtp_cfg = payload.get("smtp_config") or payload
    result = await session.execute(
        sql_update(Tenant)
        .where(Tenant.id == tenant_id)
        .values(smtp_config=smtp_cfg)
        .returning(Tenant)
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    await session.commit()
    return {"id": str(t.id), "smtp_config": smtp_cfg}


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(
    tenant_id: UUID,
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    require_msp_admin(user.is_msp_admin)
    await session.execute(
        "DELETE FROM tenants WHERE id = :tid",
        {"tid": tenant_id},
    )
    await session.commit()
    return {}
