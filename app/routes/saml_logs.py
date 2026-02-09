from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import assert_tenant_access, require_msp_admin
from app.context import current_tenant
from app.db import get_session
from app.deps import get_current_user_jwt

router = APIRouter(prefix="/saml/logs", tags=["saml"])

async def log_saml_event(
    session: AsyncSession,
    tenant_id: str,
    level: str,
    message: str,
    details: dict | None = None,
):
    await session.execute(
        text(
            """
            INSERT INTO saml_logs (tenant_id, level, message, details)
            VALUES (:tid, :level, :message, COALESCE(:details, '{}'::jsonb))
            """
        ),
        {"tid": tenant_id, "level": level, "message": message, "details": details or {}},
    )
    await session.commit()


@router.get("")
async def list_logs(
    user: Annotated[object, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
    tenant_id: str | None = None,
    limit: int = 50,
):
    """
    Tenant admins: view their own tenant logs.
    MSP admins: can query any tenant_id.
    """
    effective_tenant = tenant_id or current_tenant()
    if not effective_tenant:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    await assert_tenant_access(session, user.id, effective_tenant, user.is_msp_admin)

    rows = await session.execute(
        text(
            """
            SELECT level, message, details, created_at
            FROM saml_logs
            WHERE tenant_id=:tid
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {"tid": effective_tenant, "limit": limit},
    )
    return [dict(r) for r in rows.mappings().all()]


@router.delete("/{tenant_id}")
async def clear_logs(
    tenant_id: str,
    user: Annotated[object, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    require_msp_admin(user.is_msp_admin)
    await session.execute(text("DELETE FROM saml_logs WHERE tenant_id=:tid"), {"tid": tenant_id})
    await session.commit()
    return {"detail": "cleared"}
