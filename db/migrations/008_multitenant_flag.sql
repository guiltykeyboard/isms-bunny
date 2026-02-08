ALTER TABLE system_settings ADD COLUMN IF NOT EXISTS dummy text; -- no-op to keep migration system consistent
-- store multitenant flag in settings
-- (value stored as boolean in system_settings.value)
