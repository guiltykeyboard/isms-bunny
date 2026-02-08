-- Add per-user theme preference (system/dark/light)
ALTER TABLE users
ADD COLUMN theme_preference text NOT NULL DEFAULT 'system'
  CHECK (theme_preference IN ('system','dark','light'));
