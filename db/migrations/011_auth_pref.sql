-- Per-user auth preference / break-glass flag
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_preference text DEFAULT 'external'; -- external|local|either
ALTER TABLE users ADD COLUMN IF NOT EXISTS allow_local_fallback boolean DEFAULT false;
