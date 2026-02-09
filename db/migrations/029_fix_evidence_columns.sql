-- Ensure legacy evidence table has control linkage before indexing
ALTER TABLE evidence
  ADD COLUMN IF NOT EXISTS control_id uuid REFERENCES controls(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS name text,
  ADD COLUMN IF NOT EXISTS url text,
  ADD COLUMN IF NOT EXISTS s3_key text,
  ADD COLUMN IF NOT EXISTS added_by uuid REFERENCES users(id),
  ADD COLUMN IF NOT EXISTS added_at timestamptz NOT NULL DEFAULT now();

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = 'evidence'
      AND column_name = 'control_id'
  ) THEN
    CREATE INDEX IF NOT EXISTS evidence_control_tenant_idx
      ON evidence(tenant_id, control_id, added_at DESC);
  END IF;
END $$;
