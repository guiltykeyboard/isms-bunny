from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import require_msp_admin
from app.db import get_session
from app.deps import get_current_user_jwt
from app.models import Membership, User

router = APIRouter(prefix="/memberships", tags=["memberships"])


@router.get("")
async def list_memberships(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user_jwt)],
):
    require_msp_admin(user.is_msp_admin)
    result = await session.execute(
        """
        SELECT m.user_id, m.tenant_id, m.roles, t.name, t.fqdn
        FROM memberships m
        JOIN tenants t ON t.id = m.tenant_id
        """
    )
    rows = result.fetchall()
    return [
        {
            "user_id": str(r[0]),
            "tenant_id": str(r[1]),
            "roles": r[2],
            "tenant_name": r[3],
            "tenant_fqdn": r[4],
        }
        for r in rows
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_membership(
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user_jwt)],
):
    require_msp_admin(user.is_msp_admin)
    user_id = payload.get("user_id")
    tenant_id = payload.get("tenant_id")
    roles = payload.get("roles", [])
    if not user_id or not tenant_id or not roles:
        raise HTTPException(status_code=400, detail="user_id, tenant_id, roles required")
    await session.execute(
        insert(Membership).values(
            user_id=UUID(user_id),
            tenant_id=UUID(tenant_id),
            roles=roles,
        )
        .on_conflict_do_update(
            index_elements=[Membership.user_id, Membership.tenant_id],
            set_={"roles": roles},
        )
    )
    await session.commit()
    return {"detail": "upserted"}


@router.delete("")
async def delete_membership(
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user_jwt)],
):
    require_msp_admin(user.is_msp_admin)
    user_id = payload.get("user_id")
    tenant_id = payload.get("tenant_id")
    if not user_id or not tenant_id:
        raise HTTPException(status_code=400, detail="user_id and tenant_id required")
    await session.execute(
        delete(Membership).where(
            Membership.user_id == UUID(user_id), Membership.tenant_id == UUID(tenant_id)
        )
    )
    await session.commit()
    return {"detail": "deleted"}
