from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routes import (
    auth,
    memberships,
    oidc,
    providers,
    saml_logs,
    setup,
    tenants,
    trust,
    users,
    webauthn,
)
from app.tenancy import resolve_tenant

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")


@app.middleware("http")
async def tenancy_middleware(request: Request, call_next):
    if request.url.path in {"/health", "/setup/status"}:
        return await call_next(request)
    try:
        await resolve_tenant(request)
    except HTTPException as exc:
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    return await call_next(request)


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


app.include_router(users.router)
app.include_router(trust.router)
app.include_router(tenants.router)
app.include_router(auth.router)
app.include_router(oidc.router)
app.include_router(memberships.router)
app.include_router(setup.router)
app.include_router(webauthn.router)
app.include_router(providers.router)
app.include_router(saml_logs.router)
