-- Add risk_id to tasks for linking risks
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS risk_id uuid REFERENCES risks(id);
