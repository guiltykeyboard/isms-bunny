-- Track status/notes on trust access requests
ALTER TABLE trust_access_requests
  ADD COLUMN IF NOT EXISTS note text,
  ADD COLUMN IF NOT EXISTS updated_at timestamptz;
