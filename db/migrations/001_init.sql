-- ISMS-Bunny initial schema and RLS
-- Run with a superuser; app connections should be limited-role users.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Session context variables set by the app:
-- SET LOCAL app.current_user_id = 'uuid';
-- SET LOCAL app.current_tenant_id = 'uuid';
-- SET LOCAL app.current_is_msp_admin = 'true'/'false';
-- SET LOCAL app.public = 'true'/'false';

CREATE TYPE member_role AS ENUM ('msp_admin', 'tenant_ciso', 'auditor', 'manager');

CREATE TABLE tenants (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name          text NOT NULL,
    fqdn          text UNIQUE NOT NULL,
    storage_config jsonb DEFAULT '{}'::jsonb, -- bucket, region, endpoint, access/secret (encrypted upstream)
    status        text DEFAULT 'active',
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email         citext UNIQUE NOT NULL,
    full_name     text,
    is_msp_admin  boolean NOT NULL DEFAULT false,
    auth_provider text DEFAULT 'local',
    status        text DEFAULT 'active',
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE memberships (
    user_id   uuid REFERENCES users(id) ON DELETE CASCADE,
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    roles     member_role[] NOT NULL,
    PRIMARY KEY (user_id, tenant_id)
);

CREATE TABLE frameworks (
    id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    code      text NOT NULL, -- e.g., ISO27001
    version   text NOT NULL,
    title     text NOT NULL
);

CREATE TABLE controls (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    framework_id uuid REFERENCES frameworks(id) ON DELETE CASCADE,
    code        text NOT NULL, -- e.g., A.5.1
    title       text NOT NULL,
    description text,
    UNIQUE (framework_id, code)
);

CREATE TABLE assets (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid REFERENCES tenants(id) ON DELETE CASCADE,
    name        text NOT NULL,
    owner_id    uuid REFERENCES users(id),
    category    text,
    criticality text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE risks (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid REFERENCES tenants(id) ON DELETE CASCADE,
    title       text NOT NULL,
    description text,
    impact      text,
    likelihood  text,
    score       numeric,
    status      text DEFAULT 'open',
    owner_id    uuid REFERENCES users(id),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE treatments (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    risk_id     uuid REFERENCES risks(id) ON DELETE CASCADE,
    tenant_id   uuid REFERENCES tenants(id) ON DELETE CASCADE,
    plan        text,
    status      text DEFAULT 'planned',
    target_date date,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE statements_of_applicability (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     uuid REFERENCES tenants(id) ON DELETE CASCADE,
    control_id    uuid REFERENCES controls(id) ON DELETE CASCADE,
    status        text NOT NULL, -- implemented, planned, not_applicable
    justification text,
    evidence_id   uuid,
    UNIQUE (tenant_id, control_id)
);

CREATE TABLE evidence (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid REFERENCES tenants(id) ON DELETE CASCADE,
    object_key  text NOT NULL, -- path in S3/MinIO
    description text,
    uploaded_by uuid REFERENCES users(id),
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE tasks (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   uuid REFERENCES tenants(id) ON DELETE CASCADE,
    title       text NOT NULL,
    description text,
    due_date    date,
    status      text DEFAULT 'open',
    assignee_id uuid REFERENCES users(id),
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE trust_pages (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id    uuid REFERENCES tenants(id) ON DELETE CASCADE,
    overview_md  text,
    policies     jsonb DEFAULT '[]'::jsonb,
    attestations jsonb DEFAULT '[]'::jsonb,
    subprocessors jsonb DEFAULT '[]'::jsonb,
    status_banner jsonb DEFAULT '{}'::jsonb,
    updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE audit_logs (
    id           bigserial PRIMARY KEY,
    tenant_id    uuid,
    actor_user_id uuid,
    action       text NOT NULL,
    entity_type  text,
    entity_id    uuid,
    data         jsonb,
    created_at   timestamptz NOT NULL DEFAULT now()
);

-- Enable RLS
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE memberships ENABLE ROW LEVEL SECURITY;
ALTER TABLE assets ENABLE ROW LEVEL SECURITY;
ALTER TABLE risks ENABLE ROW LEVEL SECURITY;
ALTER TABLE treatments ENABLE ROW LEVEL SECURITY;
ALTER TABLE statements_of_applicability ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE trust_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Helper expressions
-- current_setting returns text; coalesce to avoid errors when unset.
CREATE OR REPLACE FUNCTION app_is_msp_admin() RETURNS boolean AS $$
BEGIN
  RETURN coalesce(current_setting('app.current_is_msp_admin', true)::boolean, false);
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION app_current_tenant() RETURNS uuid AS $$
BEGIN
  RETURN current_setting('app.current_tenant_id', true)::uuid;
EXCEPTION
  WHEN others THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

CREATE OR REPLACE FUNCTION app_public() RETURNS boolean AS $$
BEGIN
  RETURN coalesce(current_setting('app.public', true)::boolean, false);
END;
$$ LANGUAGE plpgsql STABLE;

-- Policies
CREATE POLICY tenants_admin_only ON tenants
  USING (app_is_msp_admin())
  WITH CHECK (app_is_msp_admin());

CREATE POLICY memberships_owner_or_admin ON memberships
  USING (app_is_msp_admin() OR user_id = current_setting('app.current_user_id', true)::uuid)
  WITH CHECK (app_is_msp_admin());

-- Generic per-tenant policy helper applied to multiple tables
DO $$
DECLARE tbl text;
BEGIN
  FOR tbl IN SELECT unnest(ARRAY['assets','risks','treatments','statements_of_applicability','evidence','tasks','trust_pages','audit_logs'])
  LOOP
    EXECUTE format('CREATE POLICY %I_tenant_isolation ON %I USING (app_is_msp_admin() OR %I.tenant_id = app_current_tenant() OR app_public()) WITH CHECK (app_is_msp_admin() OR %I.tenant_id = app_current_tenant());', tbl, tbl, tbl, tbl);
  END LOOP;
END$$;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_memberships_user ON memberships(user_id);
CREATE INDEX IF NOT EXISTS idx_memberships_tenant ON memberships(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenants_fqdn ON tenants(fqdn);
CREATE INDEX IF NOT EXISTS idx_evidence_tenant ON evidence(tenant_id);
CREATE INDEX IF NOT EXISTS idx_risks_tenant ON risks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tasks_tenant ON tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_trust_pages_tenant ON trust_pages(tenant_id);

COMMENT ON TABLE trust_pages IS 'Public-facing trust center content per tenant';
COMMENT ON TABLE audit_logs IS 'Immutable-ish audit log; consider shipping to external sink';
-- Enable pgcrypto for gen_random_uuid
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
