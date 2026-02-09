from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.context import current_tenant
from app.db import get_session
from app.deps import get_current_user_jwt

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
async def list_tasks(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    res = await session.execute(
        text(
            """
            SELECT id, title, status, due_date, control_id, risk_id, assignee, created_at, updated_at
            FROM tasks
            WHERE tenant_id=:tid
            ORDER BY status, due_date NULLS LAST, created_at DESC
            """
        ),
        {"tid": tid},
    )
    return [dict(r) for r in res.mappings().all()]


@router.post("")
async def add_task(
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
            INSERT INTO tasks (tenant_id, title, status, due_date, control_id, assignee)
            VALUES (:tid, :title, :status, :due, :control, :assignee)
            """
        ),
        {
            "tid": tid,
            "title": title,
            "status": payload.get("status", "open"),
            "due": payload.get("due_date"),
            "control": payload.get("control_id"),
            "risk": payload.get("risk_id"),
            "assignee": payload.get("assignee"),
        },
    )
    await session.commit()
    return {"detail": "task added"}


@router.get("/due-soon")
async def due_soon(
    days: int = 7,
    session: Annotated[AsyncSession, Depends(get_session)] = Depends(),
    user: Annotated[object, Depends(get_current_user_jwt)] = Depends(),
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    res = await session.execute(
        text(
            """
            SELECT id, title, status, due_date, control_id, risk_id, assignee, created_at
            FROM tasks
            WHERE tenant_id=:tid
              AND status <> 'done'
              AND due_date IS NOT NULL
              AND due_date <= (CURRENT_DATE + (:days || ' days')::interval)
            ORDER BY due_date ASC
            """
        ),
        {"tid": tid, "days": days},
    )
    return [dict(r) for r in res.mappings().all()]


@router.patch("/{task_id}")
async def update_task(
    task_id: str,
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    fields = {
        k: payload.get(k)
        for k in ["title", "status", "due_date", "control_id", "risk_id", "assignee"]
        if k in payload
    }
    if not fields:
        return {"detail": "nothing to update"}
    sets = ", ".join([f"{k} = :{k}" for k in fields.keys()])
    params = {**fields, "tid": tid, "id": task_id}
    await session.execute(
        text(
            f"""
            UPDATE tasks
            SET {sets}, updated_at = now()
            WHERE id=:id AND tenant_id=:tid
            """
        ),
        params,
    )
    await session.commit()
    return {"detail": "updated"}
