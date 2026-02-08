from typing import Optional
from uuid import UUID

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.config import get_settings

settings = get_settings()
serializer = URLSafeTimedSerializer(settings.jwt_secret)


def create_refresh_token(user_id: UUID) -> str:
    return serializer.dumps(str(user_id))


def decode_refresh_token(token: str) -> Optional[UUID]:
    try:
        user = serializer.loads(
            token, max_age=settings.refresh_token_expiry_days * 24 * 3600
        )
        return UUID(user)
    except (BadSignature, SignatureExpired):
        return None
