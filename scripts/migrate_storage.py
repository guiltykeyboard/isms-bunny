"""Utility to migrate a tenant's objects between MSP shared S3 and BYO S3.

Usage (local):
  DATABASE_URL=... python scripts/migrate_storage.py --tenant TENANT_ID --direction to_byo \
      --bucket target-bucket --region us-east-1 --endpoint https://s3.example.com \
      --access-key AKIA --secret-key SECRET

Direction options:
  to_byo   - copies from MSP shared bucket/prefix into a BYO bucket (config supplied
             via flags) and updates tenants.storage_config to use the BYO bucket.
  to_msp   - copies from the tenant's BYO bucket back into the MSP shared bucket/prefix
             and flips storage_config.use_msp_storage=true.

Notes:
- This is a blocking, best-effort copy using boto3; for large datasets, consider running
  from a worker host with proper IAM and add retries/multipart if needed.
- Objects are copied under the per-tenant prefix (tenants/<tenant_id> or msp/<tenant_id>
  for the MSP internal tenant) to preserve isolation.
"""

import argparse
import asyncio
import os
from uuid import UUID

import boto3
from botocore.client import Config
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings
from app.storage import StorageConfig, build_storage_client


def _s3_client(cfg: StorageConfig):
    session = boto3.session.Session(
        aws_access_key_id=cfg.access_key,
        aws_secret_access_key=cfg.secret_key,
        region_name=cfg.region,
    )
    return session.client(
        "s3",
        endpoint_url=cfg.endpoint,
        config=Config(signature_version="s3v4"),
    )


def _iter_keys(client, bucket: str, prefix: str):
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            yield obj["Key"]


def copy_prefix(src_cfg: StorageConfig, dst_cfg: StorageConfig, prefix: str):
    src = _s3_client(src_cfg)
    dst = _s3_client(dst_cfg)
    for key in _iter_keys(src, src_cfg.bucket, prefix):
        dst_key = key
        dst.copy({"Bucket": src_cfg.bucket, "Key": key}, dst_cfg.bucket, dst_key)


async def update_tenant_storage(session: AsyncSession, tenant_id: UUID, new_cfg: dict):
    await session.execute(
        text("UPDATE tenants SET storage_config=:cfg WHERE id=:tid"),
        {"cfg": new_cfg, "tid": tenant_id},
    )
    await session.commit()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tenant", required=True, help="Tenant UUID")
    parser.add_argument("--direction", choices=["to_byo", "to_msp"], required=True)
    parser.add_argument("--bucket")
    parser.add_argument("--region")
    parser.add_argument("--endpoint")
    parser.add_argument("--access-key")
    parser.add_argument("--secret-key")
    args = parser.parse_args()

    settings = get_settings()
    db_url = os.getenv("DATABASE_URL", settings.database_url)
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        session = AsyncSession(bind=conn)

        row = await session.execute(
            text("SELECT storage_config, type FROM tenants WHERE id=:tid"),
            {"tid": args.tenant},
        )
        cfg_row = row.first()
        if not cfg_row:
            raise SystemExit("Tenant not found")
        current_cfg, tenant_type = cfg_row

        tenant_prefix = str(args.tenant)
        msp_default = {
            "bucket": settings.s3_bucket,
            "region": settings.s3_region,
            "endpoint": settings.s3_endpoint,
            "access_key": settings.s3_access_key_id,
            "secret_key": settings.s3_secret_access_key,
        }

        if args.direction == "to_byo":
            if not all([args.bucket, args.region, args.access_key, args.secret_key]):
                raise SystemExit("BYO target bucket/region/access/secret are required for to_byo")
            dst_cfg = {
                "bucket": args.bucket,
                "region": args.region,
                "endpoint": args.endpoint or None,
                "access_key": args.access_key,
                "secret_key": args.secret_key,
                "prefix": tenant_prefix,
                "use_msp_storage": False,
            }
            src_client = build_storage_client(current_cfg or {"use_msp_storage": True}, **msp_default, tenant_prefix=tenant_prefix, tenant_type=tenant_type)
            dst_client = build_storage_client(dst_cfg, **msp_default, tenant_prefix=tenant_prefix, tenant_type=tenant_type)
            copy_prefix(src_client.config, dst_client.config, src_client.config.prefix or tenant_prefix)
            await update_tenant_storage(session, args.tenant, dst_cfg)
        else:  # to_msp
            dst_cfg_dict = {"use_msp_storage": True}
            src_client = build_storage_client(current_cfg or {}, **msp_default, tenant_prefix=tenant_prefix, tenant_type=tenant_type)
            dst_client = build_storage_client(dst_cfg_dict, **msp_default, tenant_prefix=tenant_prefix, tenant_type=tenant_type)
            copy_prefix(src_client.config, dst_client.config, src_client.config.prefix or tenant_prefix)
            await update_tenant_storage(session, args.tenant, dst_cfg_dict)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
