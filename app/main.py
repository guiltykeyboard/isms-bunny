from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from uuid import UUID

from app.config import get_settings
from app.tenancy import resolve_tenant
from app.context import current_tenant

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


@app.get("/whoami")
async def whoami():
    return {"tenant": str(current_tenant()) if current_tenant() else None}


@app.get("/trust")
async def trust_page():
    # Placeholder public trust page payload
    return {
        "tenant": str(current_tenant()) if current_tenant() else "public",
        "sections": {
            "overview": "ISMS-Bunny trust page placeholder",
            "status": "draft",
        },
    }
