-- Control catalog, SoA, evidence, and tasks (initial)

CREATE TABLE IF NOT EXISTS controls (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    standard text NOT NULL, -- e.g., ISO27001:2022
    ref text NOT NULL,      -- e.g., A.5.1
    title text NOT NULL,
    description text,
    tags text[] DEFAULT '{}'
);
CREATE UNIQUE INDEX IF NOT EXISTS controls_standard_ref_idx ON controls(standard, ref);

CREATE TABLE IF NOT EXISTS control_states (
    control_id uuid REFERENCES controls(id) ON DELETE CASCADE,
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'not_started', -- not_started|in_progress|implemented|not_applicable
    rationale text,
    owner_user_id uuid REFERENCES users(id),
    last_reviewed_at timestamptz DEFAULT now(),
    PRIMARY KEY (control_id, tenant_id)
);
CREATE INDEX IF NOT EXISTS control_states_tenant_idx ON control_states(tenant_id);

CREATE TABLE IF NOT EXISTS evidence (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    control_id uuid REFERENCES controls(id) ON DELETE CASCADE,
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    name text NOT NULL,
    url text,
    s3_key text,
    added_by uuid REFERENCES users(id),
    added_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS evidence_control_tenant_idx ON evidence(tenant_id, control_id, added_at DESC);

-- Tasks linked to controls/risks (risks to be added later)
CREATE TABLE IF NOT EXISTS tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    title text NOT NULL,
    status text NOT NULL DEFAULT 'open', -- open|in_progress|done
    due_date date,
    control_id uuid REFERENCES controls(id),
    assignee uuid REFERENCES users(id),
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS tasks_tenant_idx ON tasks(tenant_id, status);
