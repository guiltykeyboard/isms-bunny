import os

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
    if os.getenv("SKIP_RLS_CONTEXT") == "1":
        return
    def _literal(val):
        if val is None:
            return None
        if isinstance(val, bool):
            return "true" if val else "false"
        return "'" + str(val).replace("'", "''") + "'"

    tenant = _literal(current_tenant())
    user = _literal(current_user())
    is_admin = _literal(current_is_msp_admin())
    is_public = _literal(current_public())

    if tenant:
        await session.execute(text(f"set local app.current_tenant_id = {tenant}"))
    if user:
        await session.execute(text(f"set local app.current_user_id = {user}"))
    if is_admin:
        await session.execute(text(f"set local app.current_is_msp_admin = {is_admin}"))
    if is_public:
        await session.execute(text(f"set local app.public = {is_public}"))


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        await _set_rls(session)
        yield session
