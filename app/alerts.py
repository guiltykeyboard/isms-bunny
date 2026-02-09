from datetime import datetime, timezone
from typing import Iterable, Optional

import requests
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.emailer import resolve_smtp_config, send_email


async def dispatch_alert(
    session: AsyncSession,
    tenant_id,
    alert_type: str,
    subject: str,
    body_text: str,
    webhook_payload: Optional[dict] = None,
    webhook_override: Optional[str] = None,
):
    """
    Send an alert using tenant_alert_prefs settings:
      - channel: webhook|email|both|none
      - recipients: array of emails for email channel
      - reminder_webhook_url used for webhook delivery
    """
    # Load tenant + prefs
    res = await session.execute(
        text(
            """
            SELECT t.name,
                   t.reminder_webhook_url,
                   t.smtp_config,
                   p.channel AS alert_channel,
                   p.recipients AS alert_recipients
            FROM tenants t
            LEFT JOIN tenant_alert_prefs p
              ON p.tenant_id = t.id AND p.alert_type = :atype
            WHERE t.id = :tid
            """
        ),
        {"tid": tenant_id, "atype": alert_type},
    )
    row = res.mappings().first()
    if not row:
        return {"detail": "tenant not found"}

    tenant_name = row["name"]
    tenant_webhook = row["reminder_webhook_url"]
    tenant_smtp = row["smtp_config"]
    channel = row["alert_channel"] or "webhook"
    recipients: Iterable[str] = row["alert_recipients"] or []

    sent_webhook = False
    sent_email = False
    now = datetime.now(timezone.utc)

    # webhook
    if channel in {"webhook", "both"}:
        url = webhook_override or tenant_webhook
        if url:
            payload = webhook_payload or {}
            payload.setdefault("alert_type", alert_type)
            payload.setdefault("tenant_id", str(tenant_id))
            payload.setdefault("tenant_name", tenant_name)
            try:
                resp = requests.post(url, json=payload, timeout=8)
                resp.raise_for_status()
                sent_webhook = True
            except Exception:  # pragma: no cover
                # don't raise; report in response
                sent_webhook = False
        # if no url, we just skip webhook

    # email
    if channel in {"email", "both"} and recipients:
        smtp_cfg = resolve_smtp_config(tenant_smtp)
        for email in recipients:
            send_email(smtp_cfg, email, subject, body_text)
        sent_email = True

    # record last sent
    await session.execute(
        text(
            """
            INSERT INTO tenant_alert_prefs (tenant_id, alert_type, last_sent_at)
            VALUES (:tid, :atype, :now)
            ON CONFLICT (tenant_id, alert_type)
            DO UPDATE SET last_sent_at = :now
            """
        ),
        {"tid": tenant_id, "atype": alert_type, "now": now},
    )
    await session.commit()

    return {
        "webhook": sent_webhook,
        "email": sent_email,
        "last_sent_at": now.isoformat(),
    }
