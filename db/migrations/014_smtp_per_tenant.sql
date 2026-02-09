-- Per-tenant SMTP configuration with MSP fallback
ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS smtp_config jsonb DEFAULT '{}'::jsonb;
