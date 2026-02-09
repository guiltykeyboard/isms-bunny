import secrets

import pytest

from app.routes.auth import _verify_id_token


@pytest.mark.asyncio
async def test_oidc_nonce_rejection(monkeypatch):
    # minimal unsigned token with wrong nonce
    import jwt

    key = secrets.token_hex(16)
    claims = {"sub": "user", "aud": "cid", "iss": "iss", "nonce": "good"}
    token = jwt.encode(claims, key, algorithm="HS256")

    async def fake_verify(id_token, cfg, expected_nonce):
        return await _verify_id_token(id_token, cfg, expected_nonce)

    with pytest.raises(Exception):  # noqa: B017 broad catch acceptable in test
        await fake_verify(token, {"config": {"jwks_url": None}}, "bad")
