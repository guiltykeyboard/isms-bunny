-- Add sub_msp_admin role and ensure tenant hierarchy support for ancestor checks

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_type t
    JOIN pg_enum e ON t.oid = e.enumtypid
    WHERE t.typname = 'member_role' AND e.enumlabel = 'sub_msp_admin'
  ) THEN
    ALTER TYPE member_role ADD VALUE 'sub_msp_admin';
  END IF;
END$$;

-- Ensure parent_tenant_id exists (added earlier), but keep for safety
ALTER TABLE IF EXISTS tenants
  ADD COLUMN IF NOT EXISTS parent_tenant_id uuid REFERENCES tenants(id);

-- Convenience view for ancestor lookups (used by the app)
CREATE OR REPLACE VIEW tenant_ancestry AS
WITH RECURSIVE tree AS (
    SELECT id AS tenant_id, parent_tenant_id, id AS descendant
    FROM tenants
    UNION ALL
    SELECT t.id, t.parent_tenant_id, tree.descendant
    FROM tenants t
    JOIN tree ON t.parent_tenant_id = tree.tenant_id
)
SELECT descendant, tenant_id AS ancestor
FROM tree;
