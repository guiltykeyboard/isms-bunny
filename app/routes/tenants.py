from typing import Annotated
from uuid import UUID

import boto3
from botocore.client import Config as BotoConfig
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import insert, select, update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import assert_tenant_access, enforce_current_tenant, require_msp_admin
from app.config import get_settings
from app.context import current_tenant
from app.db import get_session
from app.deps import get_current_user_jwt
from app.models import Tenant, User
from app.storage import StorageConfig, build_storage_client

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
        {
            "id": str(t.id),
            "name": t.name,
            "fqdn": t.fqdn,
            "type": t.type,
            "parent_tenant_id": t.parent_tenant_id,
            "reminder_webhook_url": getattr(t, "reminder_webhook_url", None),
        }
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
    parent_tenant_id = payload.get("parent_tenant_id")
    if not name or not fqdn:
        raise HTTPException(status_code=400, detail="name and fqdn are required")
    stmt = (
        insert(Tenant)
        .values(
            name=name,
            fqdn=fqdn.lower(),
            type=tenant_type,
            parent_tenant_id=parent_tenant_id,
        )
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
    return {
        "id": str(t.id),
        "name": t.name,
        "fqdn": t.fqdn,
        "type": t.type,
        "parent_tenant_id": t.parent_tenant_id,
        "reminder_webhook_url": getattr(t, "reminder_webhook_url", None),
    }


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
            parent_tenant_id=payload.get("parent_tenant_id"),
        )
        .returning(Tenant)
    )
    result = await session.execute(stmt)
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    await session.commit()
    return {
        "id": str(t.id),
        "name": t.name,
        "fqdn": t.fqdn,
        "type": t.type,
        "parent_tenant_id": t.parent_tenant_id,
        "reminder_webhook_url": getattr(t, "reminder_webhook_url", None),
    }


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
        "reminder_webhook_url": getattr(t, "reminder_webhook_url", None),
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


def _s3_client(cfg: StorageConfig):
    session = boto3.session.Session(
        aws_access_key_id=cfg.access_key,
        aws_secret_access_key=cfg.secret_key,
        region_name=cfg.region,
    )
    return session.client(
        "s3", endpoint_url=cfg.endpoint, config=BotoConfig(signature_version="s3v4")
    )


def _iter_keys(client, bucket: str, prefix: str):
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            yield obj["Key"]


def _copy_prefix(src_cfg: StorageConfig, dst_cfg: StorageConfig, prefix: str):
    src = _s3_client(src_cfg)
    dst = _s3_client(dst_cfg)
    copied = 0
    for key in _iter_keys(src, src_cfg.bucket, prefix):
        dst.copy({"Bucket": src_cfg.bucket, "Key": key}, dst_cfg.bucket, key)
        copied += 1
    return copied


@router.post("/{tenant_id}/storage/migrate")
async def migrate_storage(
    tenant_id: UUID,
    payload: dict,
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Copy tenant objects between MSP shared storage and BYO S3, then update storage_config.
    direction: to_byo | to_msp
    For to_byo, include bucket/region/(endpoint/access_key/secret_key).
    """
    require_msp_admin(user.is_msp_admin)
    direction = payload.get("direction")
    if direction not in {"to_byo", "to_msp"}:
        raise HTTPException(status_code=400, detail="direction must be to_byo or to_msp")

    # Load tenant
    result = await session.execute(
        select(Tenant.storage_config, Tenant.type).where(Tenant.id == tenant_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")
    current_cfg, tenant_type = row

    settings_defaults = {
        "default_bucket": get_settings().s3_bucket,
        "default_region": get_settings().s3_region,
        "default_endpoint": get_settings().s3_endpoint,
        "default_access_key": get_settings().s3_access_key_id,
        "default_secret": get_settings().s3_secret_access_key,
    }
    tenant_prefix = str(tenant_id)

    if direction == "to_byo":
        target = payload.get("target") or {}
        required = ["bucket", "region", "access_key", "secret_key"]
        if any(not target.get(k) for k in required):
            raise HTTPException(
                status_code=400,
                detail="bucket, region, access_key, secret_key required",
            )
        dst_cfg_dict = {
            "bucket": target["bucket"],
            "region": target["region"],
            "endpoint": target.get("endpoint"),
            "access_key": target["access_key"],
            "secret_key": target["secret_key"],
            "prefix": tenant_prefix,
            "use_msp_storage": False,
        }
        src_client = build_storage_client(
            current_cfg or {"use_msp_storage": True},
            tenant_prefix=tenant_prefix,
            tenant_type=tenant_type,
            **settings_defaults,
        )
        dst_client = build_storage_client(
            dst_cfg_dict,
            tenant_prefix=tenant_prefix,
            tenant_type=tenant_type,
            **settings_defaults,
        )
        copied = _copy_prefix(
            src_client.config, dst_client.config, src_client.config.prefix or tenant_prefix
        )
        await session.execute(
            sql_update(Tenant)
            .where(Tenant.id == tenant_id)
            .values(storage_config=dst_cfg_dict)
        )
        await session.commit()
        return {
            "detail": "migrated to BYO",
            "storage_config": dst_cfg_dict,
            "copied": copied,
        }
    else:  # to_msp
        src_client = build_storage_client(
            current_cfg or {},
            tenant_prefix=tenant_prefix,
            tenant_type=tenant_type,
            **settings_defaults,
        )
        dst_cfg_dict = {"use_msp_storage": True}
        dst_client = build_storage_client(
            dst_cfg_dict,
            tenant_prefix=tenant_prefix,
            tenant_type=tenant_type,
            **settings_defaults,
        )
        copied = _copy_prefix(
            src_client.config, dst_client.config, src_client.config.prefix or tenant_prefix
        )
        await session.execute(
            sql_update(Tenant).where(Tenant.id == tenant_id).values(storage_config=dst_cfg_dict)
        )
        await session.commit()
        return {
            "detail": "migrated to MSP storage",
            "storage_config": dst_cfg_dict,
            "copied": copied,
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


@router.patch("/{tenant_id}/reminders/webhook")
async def update_tenant_reminder_webhook(
    tenant_id: UUID,
    payload: dict,
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    """
    Update per-tenant reminder webhook URL. Empty payload clears it.
    """
    await assert_tenant_access(session, user.id, tenant_id, user.is_msp_admin)
    url = payload.get("reminder_webhook_url")
    result = await session.execute(
        sql_update(Tenant)
        .where(Tenant.id == tenant_id)
        .values(reminder_webhook_url=url)
        .returning(Tenant)
    )
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tenant not found")
    await session.commit()
    return {
        "id": str(t.id),
        "reminder_webhook_url": getattr(t, "reminder_webhook_url", None),
    }


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
