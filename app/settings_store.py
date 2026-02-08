from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_setting(session: AsyncSession, key: str) -> Optional[dict]:
    result = await session.execute(
        text("SELECT value FROM system_settings WHERE key = :key"),
        {"key": key},
    )
    row = result.scalar_one_or_none()
    return row


async def set_setting(session: AsyncSession, key: str, value) -> None:
    await session.execute(
        text(
            """
            INSERT INTO system_settings (key, value)
            VALUES (:key, :value)
            ON CONFLICT (key) DO UPDATE SET value = :value, updated_at = now()
            """
        ),
        {"key": key, "value": value},
    )
    await session.commit()


async def is_initialized(session: AsyncSession) -> bool:
    result = await session.execute(
        text("SELECT value FROM system_settings WHERE key = 'initialized'")
    )
    row = result.scalar_one_or_none()
    return bool(row)
