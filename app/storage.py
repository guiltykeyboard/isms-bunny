from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.client import Config


@dataclass
class StorageConfig:
    backend: str = "s3"
    bucket: str = ""
    region: str = ""
    endpoint: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    prefix: Optional[str] = None  # tenant-specific prefix


class StorageClient:
    def __init__(self, config: StorageConfig):
        self.config = config
        session = boto3.session.Session(
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            region_name=config.region,
        )
        self.client = session.client(
            "s3",
            endpoint_url=config.endpoint,
            config=Config(signature_version="s3v4"),
        )

    async def health(self) -> bool:
        try:
            await self._head_bucket()
            return True
        except Exception:
            return False

    async def generate_signed_url(self, key: str, expires: int = 900) -> str:
        full_key = f"{self.config.prefix}/{key}" if self.config.prefix else key
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.config.bucket, "Key": full_key},
            ExpiresIn=expires,
        )

    async def _head_bucket(self):
        return self.client.head_bucket(Bucket=self.config.bucket)


def build_storage_client(
    tenant_storage: Optional[dict],
    default_bucket: str,
    default_region: str,
    default_endpoint: Optional[str],
    default_access_key: Optional[str],
    default_secret: Optional[str],
    tenant_prefix: Optional[str],
    tenant_type: Optional[str] = None,
) -> StorageClient:
    """
    Select between MSP shared bucket (with per-tenant prefixes) or BYO S3 config.
    tenant_storage may include:
      - use_msp_storage: bool
      - bucket/region/endpoint/access_key/secret_key
    """
    use_msp = tenant_storage.get("use_msp_storage", False) if tenant_storage else False
    effective_prefix = tenant_prefix
    if use_msp and tenant_prefix:
        effective_prefix = f"tenants/{tenant_prefix}"
        if tenant_type == "internal_msp":
            effective_prefix = f"msp/{tenant_prefix}"
    cfg = StorageConfig(
        bucket=(
            default_bucket
            if use_msp
            else tenant_storage.get("bucket", default_bucket)
            if tenant_storage
            else default_bucket
        ),
        region=(
            default_region
            if use_msp
            else tenant_storage.get("region", default_region)
            if tenant_storage
            else default_region
        ),
        endpoint=(
            tenant_storage.get("endpoint", default_endpoint)
            if (tenant_storage and not use_msp)
            else default_endpoint
        ),
        access_key=(
            tenant_storage.get("access_key")
            if (tenant_storage and not use_msp)
            else default_access_key
        ),
        secret_key=(
            tenant_storage.get("secret_key")
            if (tenant_storage and not use_msp)
            else default_secret
        ),
        prefix=effective_prefix,
    )
    return StorageClient(cfg)
