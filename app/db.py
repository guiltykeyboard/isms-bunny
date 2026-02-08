from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

from app.config import get_settings
from app.context import (
    current_tenant,
    current_user,
    current_is_msp_admin,
    current_public,
)

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    future=True,
    echo=False,
    pool_pre_ping=True,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def _set_rls(session: AsyncSession):
    """Push per-request context into Postgres for RLS policies."""
    await session.execute(
        text("set local app.current_tenant_id = :tenant_id"),
        {"tenant_id": current_tenant()},
    )
    await session.execute(
        text("set local app.current_user_id = :user_id"),
        {"user_id": current_user()},
    )
    await session.execute(
        text("set local app.current_is_msp_admin = :is_admin"),
        {"is_admin": current_is_msp_admin()},
    )
    await session.execute(
        text("set local app.public = :is_public"),
        {"is_public": current_public()},
    )


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        await _set_rls(session)
        yield session
