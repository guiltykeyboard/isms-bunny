from fastapi import Request, HTTPException
from uuid import UUID

from app.context import set_tenant, set_public


async def resolve_tenant(request: Request):
    """
    Resolve tenant based on Host header.
    In a real implementation, look up the host in the tenants table.
    For now, accept any host and set tenant_id to None (public).
    """
    host = request.headers.get("host", "").lower()
    if not host:
        raise HTTPException(status_code=400, detail="Missing Host header")

    # TODO: replace with DB lookup
    tenant_id: UUID | None = None

    set_tenant(tenant_id)
    set_public(request.url.path.startswith("/trust"))
