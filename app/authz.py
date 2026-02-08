from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Membership
from app.context import current_tenant


def require_msp_admin(is_admin: bool):
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="MSP admin role required",
        )


async def assert_tenant_access(session: AsyncSession, user_id, tenant_id, is_admin: bool):
    """Allow if MSP admin or membership exists for tenant."""
    if is_admin:
        return

    if tenant_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant required")

    result = await session.execute(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.tenant_id == tenant_id,
        )
    )
    membership = result.scalar_one_or_none()
    if membership is None:
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
