-- Audit gated trust content access
CREATE TABLE IF NOT EXISTS trust_access_audit (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    email text NOT NULL,
    action text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS trust_access_audit_tenant_idx
  ON trust_access_audit (tenant_id, created_at DESC);
