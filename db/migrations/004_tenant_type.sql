ALTER TABLE tenants
  ADD COLUMN IF NOT EXISTS type text NOT NULL DEFAULT 'customer'
    CHECK (type IN ('internal_msp','customer'));

-- Backfill existing rows to customer if null (in case of prior data)
UPDATE tenants SET type = 'customer' WHERE type IS NULL;
