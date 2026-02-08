from dataclasses import dataclass
from typing import Optional


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
    """
    Placeholder storage client.
    TODO: implement S3-compatible client (boto3/aioboto3) with:
      - shared bucket + prefix default
      - per-tenant BYO bucket/credentials
      - signed URL generation for trust page gates
    """

    def __init__(self, config: StorageConfig):
        self.config = config

    async def health(self) -> bool:
        # TODO: implement real health check
        return True

    async def generate_signed_url(self, key: str, expires: int = 900) -> str:
        raise NotImplementedError("S3 client not wired yet")
