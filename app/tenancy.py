from fastapi import Request, HTTPException
from uuid import UUID

from app.context import set_tenant, set_public


async def resolve_tenant(request: Request):
    """
    Resolve tenant based on Host header.
    For now this is a stub; in production, look up host in the tenants table.
    """
    host = request.headers.get("host", "").lower()
    if not host:
        raise HTTPException(status_code=400, detail="Missing Host header")

    # TODO: replace with DB lookup on tenants.fqdn
    tenant_id: UUID | None = None

    set_tenant(tenant_id)
    set_public(request.url.path.startswith("/trust"))
