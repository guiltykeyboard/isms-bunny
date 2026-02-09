from typing import Annotated

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.context import current_tenant
from app.db import get_session
from app.deps import get_current_user_jwt
from app.emailer import resolve_smtp_config, send_email

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
            SELECT id, title, status, due_date, control_id, risk_id, assignee,
                   created_at, updated_at
            FROM tasks
            WHERE tenant_id=:tid
            ORDER BY status, due_date NULLS LAST, created_at DESC
            """
        ),
        {"tid": tid},
    )
    return [dict(r) for r in res.mappings().all()]


@router.post("/remind")
async def send_reminders(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
    payload: dict | None = None,
    days: int = 7,
):
    """
    Send due-soon task reminders to the tenant's configured webhook.
    Optional override: {"webhook_url": "..."}.
    """
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")

    # Load tenant info + alert pref
    result = await session.execute(
        text(
            """
            SELECT t.name,
                   t.reminder_webhook_url,
                   t.smtp_config,
                   p.channel AS alert_channel,
                   p.recipients AS alert_recipients
            FROM tenants t
            LEFT JOIN tenant_alert_prefs p
              ON p.tenant_id = t.id AND p.alert_type = 'task_due'
            WHERE t.id=:tid
            """
        ),
        {"tid": tid},
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Tenant not found")
    tenant_name = row["name"]
    tenant_webhook = row["reminder_webhook_url"]
    tenant_smtp = row["smtp_config"]
    channel = row["alert_channel"] or "webhook"
    recipients = row["alert_recipients"] or []

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
    tasks = [dict(r) for r in res.mappings().all()]
    if not tasks:
        return {"detail": "no tasks due soon", "count": 0}

    body = {
        "tenant_id": str(tid),
        "tenant_name": tenant_name,
        "days": days,
        "task_count": len(tasks),
        "tasks": tasks,
    }
    sent_webhook = False
    sent_email = False

    webhook_url = (payload or {}).get("webhook_url") or tenant_webhook
    if channel in {"webhook", "both"} and webhook_url:
        try:
            resp = requests.post(webhook_url, json=body, timeout=8)
            resp.raise_for_status()
            sent_webhook = True
        except Exception as exc:  # pragma: no cover
            raise HTTPException(
                status_code=502, detail=f"Webhook delivery failed: {exc}"
            ) from exc

    if channel in {"email", "both"} and recipients:
        smtp_cfg = resolve_smtp_config(tenant_smtp)
        subject = f"[ISMS-Bunny] {len(tasks)} tasks due in next {days} days"
        lines = [
            f"Tenant: {tenant_name}",
            f"Due within {days} days:",
            "",
        ]
        for t in tasks:
            lines.append(
                "- {title} (status {status}, due {due}, control {control}, risk {risk})".format(
                    title=t["title"],
                    status=t["status"],
                    due=t["due_date"],
                    control=t.get("control_id") or "-",
                    risk=t.get("risk_id") or "-",
                )
            )
        body_text = "\n".join(lines)
        for email in recipients:
            send_email(smtp_cfg, email, subject, body_text)
        sent_email = True

    if channel in {"webhook", "both"} and not sent_webhook and webhook_url is None:
        raise HTTPException(status_code=400, detail="No reminder webhook configured")

    await session.execute(
        text(
            """
            INSERT INTO tenant_alert_prefs (tenant_id, alert_type, last_sent_at)
            VALUES (:tid, 'task_due', now())
            ON CONFLICT (tenant_id, alert_type)
            DO UPDATE SET last_sent_at = now()
            """
        ),
        {"tid": tid},
    )
    await session.commit()

    return {
        "detail": "reminders sent",
        "count": len(tasks),
        "webhook": sent_webhook,
        "email": sent_email,
    }


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
            INSERT INTO tasks (tenant_id, title, status, due_date, control_id, risk_id, assignee)
            VALUES (:tid, :title, :status, :due, :control, :risk, :assignee)
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
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
    days: int = 7,
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
