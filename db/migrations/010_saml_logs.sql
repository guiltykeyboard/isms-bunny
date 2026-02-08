-- SAML logging + break-glass toggle

ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS allow_local_login boolean DEFAULT true;

CREATE TABLE IF NOT EXISTS saml_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    level text NOT NULL,
    message text NOT NULL,
    details jsonb DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS saml_logs_tenant_created_idx
  ON saml_logs (tenant_id, created_at DESC);
