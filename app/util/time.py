from datetime import datetime, timezone


def utcnow() -> datetime:
    """Timezone-aware now (UTC)."""
    return datetime.now(timezone.utc)
