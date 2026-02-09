import smtplib
from email.message import EmailMessage
from typing import Optional

from app.config import get_settings


class SMTPConfig:
    def __init__(
        self,
        host: Optional[str],
        port: Optional[int],
        username: Optional[str],
        password: Optional[str],
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port or 587
        self.username = username
        self.password = password
        self.use_tls = use_tls


def resolve_smtp_config(tenant_smtp: Optional[dict]) -> SMTPConfig:
    settings = get_settings()
    cfg = tenant_smtp or {}
    return SMTPConfig(
        host=cfg.get("host") or settings.smtp_host,
        port=cfg.get("port") or settings.smtp_port,
        username=cfg.get("username") or settings.smtp_username,
        password=cfg.get("password") or settings.smtp_password,
        use_tls=cfg.get("use_tls", settings.smtp_use_tls),
    )


def send_email(cfg: SMTPConfig, to: str, subject: str, body: str, sender: Optional[str] = None):
    if not cfg.host:
        return
    msg = EmailMessage()
    msg["To"] = to
    msg["From"] = sender or (cfg.username or "noreply@isms-bunny.local")
    msg["Subject"] = subject
    msg.set_content(body)

    if cfg.use_tls:
        with smtplib.SMTP(cfg.host, cfg.port) as smtp:
            smtp.starttls()
            if cfg.username and cfg.password:
                smtp.login(cfg.username, cfg.password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(cfg.host, cfg.port) as smtp:
            if cfg.username and cfg.password:
                smtp.login(cfg.username, cfg.password)
            smtp.send_message(msg)
