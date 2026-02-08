from functools import lru_cache

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = "ISMS-Bunny"
    environment: str = Field(default="development")
    secret_key: str = Field(default="change-me")

    default_tenant_fqdn: str = Field(default="localhost")
    default_tenant_id: str | None = Field(default="00000000-0000-0000-0000-000000000001")

    database_url: str = Field(default="postgresql+asyncpg://isms:isms@db:5432/isms")
    redis_url: str = Field(default="redis://cache:6379/0")

    storage_backend: str = Field(default="s3")
    s3_bucket: str = Field(default="isms-bunny-dev")
    s3_region: str = Field(default="us-east-1")
    s3_endpoint: str = Field(default="https://s3.wasabisys.com")
    s3_access_key_id: str = Field(default="changeme")
    s3_secret_access_key: str = Field(default="changeme")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
