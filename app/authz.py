from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.context import current_tenant
from app.models import Membership


def require_msp_admin(is_admin: bool):
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MSP admin role required",
        )


async def _is_ancestor(session: AsyncSession, ancestor: str, tenant_id: str) -> bool:
    result = await session.execute(
        """
        WITH RECURSIVE tree AS (
            SELECT id, parent_tenant_id FROM tenants WHERE id = :tid
            UNION ALL
            SELECT t.id, t.parent_tenant_id FROM tenants t
            JOIN tree ON t.id = tree.parent_tenant_id
        )
        SELECT 1 FROM tree WHERE id = :ancestor LIMIT 1
        """,
        {"tid": tenant_id, "ancestor": ancestor},
    )
    return result.first() is not None


async def assert_tenant_access(session: AsyncSession, user_id, tenant_id, is_admin: bool):
    """
    Allow if MSP admin, direct membership, or sub_msp_admin on an ancestor tenant.
    """
    if is_admin:
        return

    if tenant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant required")

    # Direct membership
    result = await session.execute(
        select(Membership.roles).where(
            Membership.user_id == user_id,
            Membership.tenant_id == tenant_id,
        )
    )
    membership = result.first()
    if membership:
        return

    # Sub-MSP admin on ancestor tenant
    ancestor_rows = await session.execute(
        select(Membership.tenant_id).where(
            Membership.user_id == user_id,
            Membership.roles.any("sub_msp_admin"),
        )
    )
    ancestors = [str(r[0]) for r in ancestor_rows.fetchall()]
    for anc in ancestors:
        if await _is_ancestor(session, anc, str(tenant_id)):
            return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized for this tenant",
    )


def enforce_current_tenant(tenant_id):
    """Verify the route tenant_id matches the resolved tenant (for non-admins)."""
    current = current_tenant()
    if current is not None and tenant_id != current:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant mismatch with host",
        )
