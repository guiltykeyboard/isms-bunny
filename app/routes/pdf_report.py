from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.context import current_tenant
from app.db import get_session
from app.deps import get_current_user_jwt

router = APIRouter(prefix="/reports", tags=["reports-pdf"])


def _simple_pdf(title: str, subtitle: str, body_lines: list[str]) -> bytes:
    # Minimal text-only PDF
    lines = [title, subtitle, ""] + body_lines
    content = "\\n".join(lines)
    buf = BytesIO()
    pdf = f"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length {len(content)+200}>>stream
BT /F1 14 Tf 72 760 Td ({title}) T* /F1 10 Tf ({subtitle}) T* T* ({content}) Tj ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000060 00000 n 
0000000111 00000 n 
0000000338 00000 n 
0000000456 00000 n 
trailer<</Root 1 0 R/Size 6>>
startxref
558
%%EOF"""
    buf.write(pdf.encode("utf-8"))
    return buf.getvalue()


@router.get("/soa.pdf")
async def soa_pdf(
    session: AsyncSession = Depends(get_session),
    user: object = Depends(get_current_user_jwt),
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    res = await session.execute(
        text(
            """
            SELECT c.standard, c.ref, c.title, coalesce(cs.status,'not_started') as status
            FROM controls c
            LEFT JOIN control_states cs
              ON cs.control_id = c.id AND cs.tenant_id = :tid
            ORDER BY c.standard, c.ref
            """
        ),
        {"tid": tid},
    )
    rows = res.mappings().all()
    body = [f"{r['ref']} - {r['title']} [{r['status']}]" for r in rows]
    subtitle = f"Tenant: {tid}"
    pdf_bytes = _simple_pdf("Statement of Applicability", subtitle, body)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=soa.pdf"},
    )


@router.get("/risks.pdf")
async def risks_pdf(
    session: AsyncSession = Depends(get_session),
    user: object = Depends(get_current_user_jwt),
):
    tid = current_tenant()
    if not tid:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    res = await session.execute(
        text(
            """
            SELECT title, threat, vulnerability, impact, likelihood, status, treatment
            FROM risks
            WHERE tenant_id=:tid
            ORDER BY created_at DESC
            """
        ),
        {"tid": tid},
    )
    rows = res.mappings().all()
    body = [
        f"{r['title']} [status: {r['status']}] threat: {r['threat'] or '-'} vuln: {r['vulnerability'] or '-'} "
        f"impact {r['impact'] or '-'} likelihood {r['likelihood'] or '-'} treatment: {r['treatment'] or '-'}"
        for r in rows
    ]
    subtitle = f"Tenant: {tid}"
    pdf_bytes = _simple_pdf("Risk Register", subtitle, body or ["No risks recorded."])
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=risks.pdf"},
    )
