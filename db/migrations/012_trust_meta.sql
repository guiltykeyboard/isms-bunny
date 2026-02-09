-- Trust page metadata and gated access requests
ALTER TABLE trust_pages
  ADD COLUMN IF NOT EXISTS last_generated_at timestamptz,
  ADD COLUMN IF NOT EXISTS last_generated_by uuid,
  ADD COLUMN IF NOT EXISTS gated_policies jsonb DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS gated_attestations jsonb DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS trust_access_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    name text NOT NULL,
    email text NOT NULL,
    company text NOT NULL,
    justification text NOT NULL,
    status text NOT NULL DEFAULT 'new',
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS trust_access_requests_tenant_idx ON trust_access_requests(tenant_id, created_at DESC);
