from fastapi import FastAPI, Request

from app.config import get_settings
from app.routes import auth, memberships, setup, tenants, trust, users, webauthn
from app.tenancy import resolve_tenant

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")


@app.middleware("http")
async def tenancy_middleware(request: Request, call_next):
    await resolve_tenant(request)
    response = await call_next(request)
    return response


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.app_name}


app.include_router(users.router)
app.include_router(trust.router)
app.include_router(tenants.router)
app.include_router(auth.router)
app.include_router(memberships.router)
app.include_router(setup.router)
app.include_router(webauthn.router)
