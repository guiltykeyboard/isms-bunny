from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import enforce_current_tenant, require_msp_admin
from app.context import current_tenant
from app.db import get_session
from app.deps import get_current_user_jwt
from app.models import Tenant, User

router = APIRouter(tags=["trust"])


@router.get("/trust")
async def trust_page(session: Annotated[AsyncSession, Depends(get_session)]):
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Tenant not resolved")
    t = await session.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = t.scalar_one_or_none()
    return {
        "tenant": str(tenant_id),
        "name": tenant.name if tenant else "unknown",
    }


@router.get("/trust/content")
async def trust_content(session: Annotated[AsyncSession, Depends(get_session)]):
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=404, detail="Tenant not resolved")
    result = await session.execute(
        """
        SELECT overview_md, policies, attestations, subprocessors, status_banner
        FROM trust_pages
        WHERE tenant_id = :tid
        """,
        {"tid": tenant_id},
    )
    row = result.fetchone()
    if not row:
        return {"tenant": str(tenant_id), "content": None}
    keys = ["overview_md", "policies", "attestations", "subprocessors", "status_banner"]
    return {"tenant": str(tenant_id), **dict(zip(keys, row, strict=False))}


@router.put("/trust/content")
async def update_trust_content(
    payload: dict,
    user: Annotated[User, Depends(get_current_user_jwt)],
    session: Annotated[AsyncSession, Depends(get_session)],
):
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    enforce_current_tenant(tenant_id)
    require_msp_admin(user.is_msp_admin)
    stmt = update(Tenant.__table__.metadata.tables["trust_pages"]).where(
        Tenant.__table__.metadata.tables["trust_pages"].c.tenant_id == tenant_id
    ).values(
        overview_md=payload.get("overview_md"),
        policies=payload.get("policies", []),
        attestations=payload.get("attestations", []),
        subprocessors=payload.get("subprocessors", []),
        status_banner=payload.get("status_banner", {}),
    )
    await session.execute(stmt)
    await session.commit()
    return {"detail": "updated"}
