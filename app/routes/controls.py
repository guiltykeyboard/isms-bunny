from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.authz import require_msp_admin
from app.context import current_tenant
from app.db import get_session
from app.deps import get_current_user_jwt

router = APIRouter(prefix="/controls", tags=["controls"])


@router.get("")
async def list_controls(
    session: Annotated[AsyncSession, Depends(get_session)],
    standard: str | None = None,
) -> list[dict]:
    rows = await session.execute(
        text(
            """
            SELECT id, standard, ref, title, description, tags
            FROM controls
            WHERE (:std IS NULL OR standard = :std)
            ORDER BY standard, ref
            """
        ),
        {"std": standard},
    )
    return [dict(r) for r in rows.mappings().all()]


@router.get("/soa")
async def soa(
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
) -> list[dict]:
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    rows = await session.execute(
        text(
            """
            SELECT c.id, c.standard, c.ref, c.title, c.description, c.tags,
                   cs.status, cs.rationale, cs.owner_user_id, cs.last_reviewed_at
            FROM controls c
            LEFT JOIN control_states cs
              ON cs.control_id = c.id AND cs.tenant_id = :tid
            ORDER BY c.standard, c.ref
            """
        ),
        {"tid": tenant_id},
    )
    return [dict(r) for r in rows.mappings().all()]


@router.patch("/{control_id}/state")
async def upsert_state(
    control_id: str,
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    status_val = payload.get("status")
    if status_val not in {"not_started", "in_progress", "implemented", "not_applicable"}:
        raise HTTPException(status_code=400, detail="Invalid status")
    await session.execute(
        text(
            """
            INSERT INTO control_states (control_id, tenant_id, status, rationale, owner_user_id, last_reviewed_at)
            VALUES (:cid, :tid, :status, :rationale, :owner, now())
            ON CONFLICT (control_id, tenant_id)
              DO UPDATE SET status = EXCLUDED.status,
                            rationale = EXCLUDED.rationale,
                            owner_user_id = EXCLUDED.owner_user_id,
                            last_reviewed_at = now()
            """
        ),
        {
            "cid": control_id,
            "tid": tenant_id,
            "status": status_val,
            "rationale": payload.get("rationale"),
            "owner": payload.get("owner_user_id"),
        },
    )
    await session.commit()
    return {"detail": "updated"}


@router.post("/{control_id}/evidence")
async def add_evidence(
    control_id: str,
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    await session.execute(
        text(
            """
            INSERT INTO evidence (control_id, tenant_id, name, url, s3_key, added_by)
            VALUES (:cid, :tid, :name, :url, :s3, :user)
            """
        ),
        {
            "cid": control_id,
            "tid": tenant_id,
            "name": name,
            "url": payload.get("url"),
            "s3": payload.get("s3_key"),
            "user": getattr(user, "id", None),
        },
    )
    await session.commit()
    return {"detail": "added"}


@router.get("/{control_id}/evidence")
async def list_evidence(
    control_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    rows = await session.execute(
        text(
            """
            SELECT id, name, url, s3_key, added_by, added_at
            FROM evidence
            WHERE control_id=:cid AND tenant_id=:tid
            ORDER BY added_at DESC
            """
        ),
        {"cid": control_id, "tid": tenant_id},
    )
    return [dict(r) for r in rows.mappings().all()]


@router.post("/{control_id}/evidence/upload")
async def upload_evidence(
    control_id: str,
    file: UploadFile = File(...),
    session: Annotated[AsyncSession, Depends(get_session)] = Depends(),
    user: Annotated[object, Depends(get_current_user_jwt)] = Depends(),
):
    """
    Stub for evidence upload: records metadata; assumes frontend handles actual S3 upload and passes s3_key.
    """
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    if not file:
        raise HTTPException(status_code=400, detail="file required")
    # In this stub, we just record metadata; actual upload should be done client-side with a presigned URL.
    s3_key = f"evidence/{tenant_id}/{control_id}/{file.filename}"
    await session.execute(
        text(
            """
            INSERT INTO evidence_files (tenant_id, control_id, filename, s3_key, size_bytes, content_type, added_by)
            VALUES (:tid, :cid, :fn, :s3, :size, :ct, :user)
            """
        ),
        {
            "tid": tenant_id,
            "cid": control_id,
            "fn": file.filename,
            "s3": s3_key,
            "size": file.size if hasattr(file, "size") else None,
            "ct": file.content_type,
            "user": getattr(user, "id", None),
        },
    )
    await session.commit()
    return {"detail": "recorded", "s3_key": s3_key}


@router.post("/seed/iso27001")
async def seed_iso27001(session: Annotated[AsyncSession, Depends(get_session)], user: Annotated[object, Depends(get_current_user_jwt)]):
    # MSP admin only to avoid duplicates
    require_msp_admin(user.is_msp_admin)
    controls = [
        ("ISO27001:2022", "A.5.1", "Policies for information security", "Provide management direction for information security."),
        ("ISO27001:2022", "A.5.7", "Threat intelligence", "Collect and analyze threat intelligence to improve security posture."),
        ("ISO27001:2022", "A.8.1", "User endpoint devices", "Protect endpoint devices with appropriate controls."),
        ("ISO27001:2022", "A.12.1", "Logging and monitoring", "Log and monitor activities to identify events."),
        ("ISO27001:2022", "A.17.1", "Information security continuity", "Ensure information security during disruptions."),
    ]
    for std, ref, title, desc in controls:
        await session.execute(
            text(
                """
                INSERT INTO controls (standard, ref, title, description)
                VALUES (:std, :ref, :title, :desc)
                ON CONFLICT (standard, ref) DO NOTHING
                """
            ),
            {"std": std, "ref": ref, "title": title, "desc": desc},
        )
    await session.commit()
    return {"detail": "seeded"}
