-- Per-tenant storage config to support MSP bucket or BYO S3
-- Fields stored as jsonb:
--   use_msp_storage: bool
--   bucket, region, endpoint, access_key, secret_key, prefix

ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS storage_config jsonb DEFAULT '{}'::jsonb;
