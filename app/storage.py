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
