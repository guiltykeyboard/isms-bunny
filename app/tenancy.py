from fastapi import Request, HTTPException
from uuid import UUID
from sqlalchemy import select

from app.context import set_tenant, set_public
from app.db import SessionLocal
from app.models import Tenant
from app.config import get_settings


async def resolve_tenant(request: Request):
    """
    Resolve tenant based on Host header.
    - Lookup host (sans port) in tenants.fqdn.
    - Fallback to DEFAULT_TENANT_ID for dev if host matches DEFAULT_TENANT_FQDN/localhost.
    """
    host_header = request.headers.get("host", "")
    if not host_header:
        raise HTTPException(status_code=400, detail="Missing Host header")

    host = host_header.split(":")[0].lower()
    settings = get_settings()

    tenant_id: UUID | None = None

    async with SessionLocal() as session:
        result = await session.execute(select(Tenant.id).where(Tenant.fqdn == host))
        tenant_id = result.scalar_one_or_none()

    if tenant_id is None and host in {
        settings.default_tenant_fqdn.lower(),
        "localhost",
        "127.0.0.1",
    }:
        if settings.default_tenant_id:
            try:
                tenant_id = UUID(settings.default_tenant_id)
            except ValueError:
                tenant_id = None

    set_tenant(tenant_id)
    set_public(request.url.path.startswith("/trust"))
