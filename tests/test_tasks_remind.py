import uuid
from typing import List

import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import get_settings
from app.db import SessionLocal
from app.main import app


async def _seed_user_and_membership(user_id: uuid.UUID):
    settings = get_settings()
    async with SessionLocal() as session:
        await session.execute(
            text(
                """
                INSERT INTO users (id, email, full_name, status, is_msp_admin)
                VALUES (:id, :email, 'Tester', 'active', true)
                ON CONFLICT (id) DO UPDATE SET is_msp_admin = EXCLUDED.is_msp_admin
                """
            ),
            {"id": user_id, "email": f"{user_id}@example.com"},
        )
        await session.execute(
            text(
                """
                INSERT INTO memberships (user_id, tenant_id, roles)
                VALUES (:uid, :tid, ARRAY['msp_admin']::member_role[])
                ON CONFLICT DO NOTHING
                """
            ),
            {"uid": user_id, "tid": settings.default_tenant_id},
        )
        await session.commit()


async def _clear_user(user_id: uuid.UUID):
    async with SessionLocal() as session:
        await session.execute(text("DELETE FROM memberships WHERE user_id=:uid"), {"uid": user_id})
        await session.execute(text("DELETE FROM users WHERE id=:uid"), {"uid": user_id})
        await session.commit()


@pytest.mark.asyncio
async def test_task_remind_webhook(monkeypatch):
    settings = get_settings()
    user_id = uuid.uuid4()
    await _seed_user_and_membership(user_id)

    called: List[dict] = []

    def fake_post(url, json=None, timeout=8):
        called.append({"url": url, "json": json, "timeout": timeout})

        class Resp:
            def raise_for_status(self):
                return None

        return Resp()

    monkeypatch.setattr(requests, "post", fake_post)

    async def seed():
        async with SessionLocal() as session:
            await session.execute(
                text("UPDATE tenants SET reminder_webhook_url=:u WHERE id=:tid"),
                {"u": "https://webhook.example/test", "tid": settings.default_tenant_id},
            )
            await session.execute(
                text(
                    """
                    INSERT INTO tenant_alert_prefs (tenant_id, alert_type, channel, recipients)
                    VALUES (:tid, 'task_due', 'webhook', '{}')
                    ON CONFLICT (tenant_id, alert_type)
                    DO UPDATE SET channel='webhook', recipients='{}'
                    """
                ),
                {"tid": settings.default_tenant_id},
            )
            await session.execute(
                text(
                    """
                    INSERT INTO tasks (id, tenant_id, title, status, due_date)
                    VALUES (:id, :tid, 'Test task', 'open', CURRENT_DATE)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"id": uuid.uuid4(), "tid": settings.default_tenant_id},
            )
            await session.commit()

    await seed()

    client = TestClient(app, headers={"host": settings.default_tenant_fqdn or "localhost"})
    resp = client.post("/tasks/remind", headers={"X-User-Id": str(user_id)})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["webhook"] is True
    assert body.get("last_sent_at")
    assert called and called[0]["url"] == "https://webhook.example/test"

    await _clear_user(user_id)


@pytest.mark.asyncio
async def test_task_remind_email(monkeypatch):
    settings = get_settings()
    user_id = uuid.uuid4()
    await _seed_user_and_membership(user_id)

    sent = []

    def fake_send_email(cfg, to, subject, body, sender=None):
        sent.append({"to": to, "subject": subject, "body": body})

    monkeypatch.setattr("app.routes.tasks.send_email", fake_send_email)

    async def seed():
        async with SessionLocal() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO tenant_alert_prefs (tenant_id, alert_type, channel, recipients)
                    VALUES (:tid, 'task_due', 'email', ARRAY['ops@example.com'])
                    ON CONFLICT (tenant_id, alert_type)
                    DO UPDATE SET channel='email', recipients=ARRAY['ops@example.com']
                    """
                ),
                {"tid": settings.default_tenant_id},
            )
            await session.execute(
                text(
                    """
                    INSERT INTO tasks (id, tenant_id, title, status, due_date)
                    VALUES (:id, :tid, 'Email task', 'open', CURRENT_DATE)
                    ON CONFLICT DO NOTHING
                    """
                ),
                {"id": uuid.uuid4(), "tid": settings.default_tenant_id},
            )
            await session.commit()

    await seed()

    client = TestClient(app, headers={"host": settings.default_tenant_fqdn or "localhost"})
    resp = client.post("/tasks/remind", headers={"X-User-Id": str(user_id)})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["email"] is True
    assert body.get("last_sent_at")
    assert sent and sent[0]["to"] == "ops@example.com"

    await _clear_user(user_id)
