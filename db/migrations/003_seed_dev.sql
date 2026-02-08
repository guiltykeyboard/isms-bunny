-- Seed a default tenant and MSP admin for local development
-- Safe to rerun; uses fixed UUIDs.

INSERT INTO tenants (id, name, fqdn, status, type)
VALUES ('00000000-0000-0000-0000-000000000001', 'Dev Tenant', 'localhost', 'active', 'internal_msp')
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, email, full_name, is_msp_admin, status, theme_preference)
VALUES ('00000000-0000-0000-0000-000000000002', 'admin@example.com', 'Dev Admin', true, 'active', 'system')
ON CONFLICT (id) DO NOTHING;

-- Give admin membership to dev tenant (roles array includes msp_admin for clarity)
INSERT INTO memberships (user_id, tenant_id, roles)
VALUES ('00000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000001', ARRAY['msp_admin'])
ON CONFLICT (user_id, tenant_id) DO NOTHING;
