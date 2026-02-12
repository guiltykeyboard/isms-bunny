-- Add missing task linkage columns referenced by reminders and trust views
ALTER TABLE tasks
    ADD COLUMN IF NOT EXISTS control_id uuid REFERENCES controls(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS risk_id uuid REFERENCES risks(id) ON DELETE SET NULL,
    ADD COLUMN IF NOT EXISTS assignee text;
