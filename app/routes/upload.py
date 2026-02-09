from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.context import current_tenant
from app.db import get_session
from app.deps import get_current_user_jwt
from app.storage import build_storage_client
from app.config import get_settings

router = APIRouter(prefix="/upload", tags=["upload"])
settings = get_settings()


@router.post("/evidence")
async def presign_evidence(
    payload: dict,
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[object, Depends(get_current_user_jwt)],
):
    tenant_id = current_tenant()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant not resolved")
    filename = payload.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="filename required")

    # Build storage client using tenant storage_config (if any)
    defaults = {
        "default_bucket": settings.s3_bucket,
        "default_region": settings.s3_region,
        "default_endpoint": settings.s3_endpoint,
        "default_access_key": settings.s3_access_key_id,
        "default_secret": settings.s3_secret_access_key,
    }
    storage_cfg = payload.get("storage_config") or {"use_msp_storage": True}
    client = build_storage_client(
        storage_cfg,
        tenant_prefix=str(tenant_id),
        tenant_type=None,
        **defaults,
    )
    key = f"{client.config.prefix or tenant_id}/evidence/{filename}"
    url = client.client.generate_presigned_url(
        "put_object",
        Params={"Bucket": client.config.bucket, "Key": key, "ContentType": payload.get("content_type", "application/octet-stream")},
        ExpiresIn=900,
    )
    return {"upload_url": url, "s3_key": key}
