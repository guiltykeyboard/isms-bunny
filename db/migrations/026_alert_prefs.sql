-- Per-tenant alert preferences (channel and recipients) per alert type
CREATE TABLE IF NOT EXISTS tenant_alert_prefs (
  tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
  alert_type text NOT NULL,
  channel text NOT NULL DEFAULT 'webhook' CHECK (channel IN ('webhook','email','both','none')),
  recipients text[] DEFAULT '{}',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (tenant_id, alert_type)
);

-- Useful index for lookups by tenant/type
CREATE INDEX IF NOT EXISTS idx_alert_prefs_tenant_type ON tenant_alert_prefs(tenant_id, alert_type);
