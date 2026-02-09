from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.context import (
    current_is_msp_admin,
    current_public,
    current_tenant,
    current_user,
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
    def _literal(val):
        if val is None:
            return "NULL"
        if isinstance(val, bool):
            return "true" if val else "false"
        return "'" + str(val).replace("'", "''") + "'"

    await session.execute(
        text(f"set local app.current_tenant_id = {_literal(current_tenant())}")
    )
    await session.execute(
        text(f"set local app.current_user_id = {_literal(current_user())}")
    )
    await session.execute(
        text(f"set local app.current_is_msp_admin = {_literal(current_is_msp_admin())}")
    )
    await session.execute(text(f"set local app.public = {_literal(current_public())}"))


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        await _set_rls(session)
        yield session
