-- Track when an alert type was last sent for a tenant
ALTER TABLE tenant_alert_prefs
  ADD COLUMN IF NOT EXISTS last_sent_at timestamptz;

CREATE INDEX IF NOT EXISTS idx_alert_prefs_last_sent
  ON tenant_alert_prefs(tenant_id, alert_type, last_sent_at);
