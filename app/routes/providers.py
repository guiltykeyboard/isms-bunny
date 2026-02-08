from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import require_msp_admin
from app.db import get_session
from app.deps import get_current_user_jwt

router = APIRouter(prefix="/providers", tags=["providers"])


async def _list(session: AsyncSession, provider_type: str) -> list[dict]:
    result = await session.execute(
        text(
            """
            SELECT id, name, type, config, enabled, tenant_id
            FROM idp_connections
            WHERE type = :type
            ORDER BY name
            """
        ),
        {"type": provider_type},
    )
    rows = result.mappings().all()
    return [dict(r) for r in rows]


async def _upsert_many(session: AsyncSession, provider_type: str, payload: list[dict]):
    for item in payload:
        name = item.get("name")
        config = item.get("config") or {}
        enabled = bool(item.get("enabled", True))
        tenant_id = item.get("tenant_id")
        provider_id = item.get("id")

        if not name:
            raise HTTPException(status_code=400, detail="name is required for providers")

        params = {
            "id": UUID(provider_id) if provider_id else None,
            "name": name,
            "type": provider_type,
            "config": config,
            "enabled": enabled,
            "tenant_id": UUID(tenant_id) if tenant_id else None,
        }

        if provider_id:
            await session.execute(
                text(
                    """
                    UPDATE idp_connections
                    SET name=:name, config=:config, enabled=:enabled,
                        tenant_id=:tenant_id, updated_at=now()
                    WHERE id=:id AND type=:type
                    """
                ),
                params,
            )
        else:
            await session.execute(
                text(
                    """
                    INSERT INTO idp_connections (name, type, config, enabled, tenant_id)
                    VALUES (:name, :type, :config, :enabled, :tenant_id)
                    """
                ),
                params,
            )
    await session.commit()


@router.get("/oidc")
async def list_oidc(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    require_msp_admin(user.is_msp_admin)
    return await _list(session, "oidc")


@router.put("/oidc")
async def upsert_oidc(
    payload: list[dict],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    require_msp_admin(user.is_msp_admin)
    await _upsert_many(session, "oidc", payload)
    return {"detail": "saved"}


@router.get("/saml")
async def list_saml(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    require_msp_admin(user.is_msp_admin)
    return await _list(session, "saml")


@router.put("/saml")
async def upsert_saml(
    payload: list[dict],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    require_msp_admin(user.is_msp_admin)
    await _upsert_many(session, "saml", payload)
    return {"detail": "saved"}


@router.delete("/{provider_id}")
async def delete_provider(
    provider_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    require_msp_admin(user.is_msp_admin)
    await session.execute(
        text("DELETE FROM idp_connections WHERE id=:id"),
        {"id": provider_id},
    )
    await session.commit()
    return {"detail": "deleted"}
