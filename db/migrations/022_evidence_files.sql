-- Evidence files table for uploaded artifacts
CREATE TABLE IF NOT EXISTS evidence_files (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    control_id uuid REFERENCES controls(id) ON DELETE CASCADE,
    filename text NOT NULL,
    s3_key text NOT NULL,
    size_bytes bigint,
    content_type text,
    added_by uuid REFERENCES users(id),
    added_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS evidence_files_tenant_idx ON evidence_files(tenant_id, control_id, added_at DESC);
