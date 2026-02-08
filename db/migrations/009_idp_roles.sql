-- RBAC and IdP refinements

-- tenant hierarchy (optional child/customer tenants)
ALTER TABLE tenants ADD COLUMN IF NOT EXISTS parent_tenant_id uuid REFERENCES tenants(id) ON DELETE SET NULL;

-- scope IdP connections per-tenant and prevent duplicate names per type
ALTER TABLE idp_connections ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE;
CREATE UNIQUE INDEX IF NOT EXISTS idp_connections_unique_per_tenant ON idp_connections(tenant_id, name, type);

-- membership roles lookup speed
CREATE INDEX IF NOT EXISTS memberships_roles_gin ON memberships USING gin(roles);

-- trust page lookup by fqdn
CREATE INDEX IF NOT EXISTS tenants_fqdn_idx ON tenants (lower(fqdn));
ALTER TABLE idp_connections ADD COLUMN IF NOT EXISTS updated_at timestamptz NOT NULL DEFAULT now();
