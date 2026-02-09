from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.alerts import dispatch_alert
from app.context import current_tenant
from app.db import get_session
from app.deps import get_current_user_jwt

router = APIRouter(prefix="/risks", tags=["risks"])


@router.get("/assets")
async def list_assets(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    rows = await session.execute(
        text(
            """
            SELECT id, name, category, owner_user_id, criticality, notes
            FROM assets
            WHERE tenant_id=:tid
            ORDER BY created_at DESC
            """
        ),
        {"tid": tid},
    )
    return [dict(r) for r in rows.mappings().all()]


@router.post("/assets")
async def add_asset(
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    await session.execute(
        text(
            """
            INSERT INTO assets (tenant_id, name, category, owner_user_id, criticality, notes)
            VALUES (:tid, :name, :category, :owner, :crit, :notes)
            """
        ),
        {
            "tid": tid,
            "name": name,
            "category": payload.get("category"),
            "owner": payload.get("owner_user_id"),
            "crit": payload.get("criticality"),
            "notes": payload.get("notes"),
        },
    )
    await session.commit()
    return {"detail": "asset added"}


@router.get("")
async def list_risks(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    rows = await session.execute(
        text(
            """
            SELECT id, title, threat, vulnerability, impact, likelihood,
                   status, treatment, asset_id, owner_user_id
            FROM risks
            WHERE tenant_id=:tid
            ORDER BY created_at DESC
            """
        ),
        {"tid": tid},
    )
    return [dict(r) for r in rows.mappings().all()]


@router.post("")
async def add_risk(
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    title = payload.get("title")
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    await session.execute(
        text(
            """
            INSERT INTO risks (
                tenant_id, asset_id, title, threat, vulnerability, impact,
                likelihood, status, treatment, owner_user_id
            )
            VALUES (
                :tid, :asset, :title, :threat, :vuln, :impact,
                :likelihood, :status, :treatment, :owner
            )
            """
        ),
        {
            "tid": tid,
            "asset": payload.get("asset_id"),
            "title": title,
            "threat": payload.get("threat"),
            "vuln": payload.get("vulnerability"),
            "impact": payload.get("impact"),
            "likelihood": payload.get("likelihood"),
            "status": payload.get("status", "open"),
            "treatment": payload.get("treatment"),
            "owner": payload.get("owner_user_id"),
        },
    )
    await session.commit()
    await dispatch_alert(
        session,
        tid,
        "risk_created",
        subject=f"[ISMS-Bunny] New risk: {title}",
        body_text=f"Risk created: {title}",
        webhook_payload={"title": title, "risk_id": None, "type": "risk_created"},
    )
    return {"detail": "risk added"}
