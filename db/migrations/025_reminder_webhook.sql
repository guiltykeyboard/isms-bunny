-- Allow per-tenant reminder webhook
ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS reminder_webhook_url text;
