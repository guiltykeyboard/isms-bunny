from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.context import current_tenant
from app.db import get_session
from app.deps import get_current_user_jwt

router = APIRouter(prefix="/reports", tags=["reports"])


def _to_csv(rows, headers):
    yield ",".join(headers) + "\n"
    for r in rows:
        line = []
        for h in headers:
            val = r.get(h, "")
            if val is None:
                val = ""
            s = str(val).replace('"', '""')
            line.append(f'"{s}"')
        yield ",".join(line) + "\n"


@router.get("/soa.csv")
async def soa_csv(
    session: AsyncSession = Depends(get_session),
    user: object = Depends(get_current_user_jwt),
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    res = await session.execute(
        text(
            """
            SELECT c.standard, c.ref, c.title, cs.status, cs.rationale, cs.owner_user_id, cs.last_reviewed_at
            FROM controls c
            LEFT JOIN control_states cs
              ON cs.control_id = c.id AND cs.tenant_id = :tid
            ORDER BY c.standard, c.ref
            """
        ),
        {"tid": tid},
    )
    rows = [dict(r) for r in res.mappings().all()]
    headers = ["standard", "ref", "title", "status", "rationale", "owner_user_id", "last_reviewed_at"]
    return StreamingResponse(_to_csv(rows, headers), media_type="text/csv")


@router.get("/risks.csv")
async def risks_csv(
    session: AsyncSession = Depends(get_session),
    user: object = Depends(get_current_user_jwt),
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    res = await session.execute(
        text(
            """
            SELECT title, threat, vulnerability, impact, likelihood, status, treatment, asset_id, owner_user_id
            FROM risks
            WHERE tenant_id=:tid
            ORDER BY created_at DESC
            """
        ),
        {"tid": tid},
    )
    rows = [dict(r) for r in res.mappings().all()]
    headers = ["title", "threat", "vulnerability", "impact", "likelihood", "status", "treatment", "asset_id", "owner_user_id"]
    return StreamingResponse(_to_csv(rows, headers), media_type="text/csv")


@router.get("/tasks.csv")
async def tasks_csv(
    session: AsyncSession = Depends(get_session),
    user: object = Depends(get_current_user_jwt),
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    res = await session.execute(
        text(
            """
            SELECT title, status, due_date, control_id, risk_id, assignee, created_at, updated_at
            FROM tasks
            WHERE tenant_id=:tid
            ORDER BY status, due_date NULLS LAST, created_at DESC
            """
        ),
        {"tid": tid},
    )
    rows = [dict(r) for r in res.mappings().all()]
    headers = ["title", "status", "due_date", "control_id", "risk_id", "assignee", "created_at", "updated_at"]
    return StreamingResponse(_to_csv(rows, headers), media_type="text/csv")
