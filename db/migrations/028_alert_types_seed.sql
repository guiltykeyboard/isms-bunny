-- Seed alert types table for future use (simple lookup)
CREATE TABLE IF NOT EXISTS alert_types (
  id text PRIMARY KEY,
  description text
);

INSERT INTO alert_types (id, description) VALUES
  ('task_due', 'Task due soon'),
  ('evidence_uploaded', 'New evidence uploaded'),
  ('risk_created', 'New risk created'),
  ('trust_request', 'Trust access request')
ON CONFLICT (id) DO NOTHING;
