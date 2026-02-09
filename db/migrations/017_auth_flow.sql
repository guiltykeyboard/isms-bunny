-- Auth flow tweaks: per-user SSO default, break-glass, and tenant-level allow_local_login clarified
ALTER TABLE tenants
  ALTER COLUMN allow_local_login SET DEFAULT true;

-- Ensure auth_preference has only expected values; no-op if already correct
UPDATE users SET auth_preference='external' WHERE auth_preference NOT IN ('external','local','either');

