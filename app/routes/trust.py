from fastapi import APIRouter

from app.context import current_tenant

router = APIRouter(tags=["trust"])


@router.get("/trust")
async def trust_page():
    # Placeholder public trust page payload
    return {
        "tenant": str(current_tenant()) if current_tenant() else "public",
        "sections": {
            "overview": "ISMS-Bunny trust page placeholder",
            "status": "draft",
        },
    }
