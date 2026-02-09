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

-- Seed a broader subset of ISO27001:2022 controls
INSERT INTO controls (standard, ref, title, description)
SELECT *
FROM (VALUES
    ('ISO27001:2022', 'A.5.1', 'Policies for information security', 'Provide management direction for information security.'),
    ('ISO27001:2022', 'A.5.7', 'Threat intelligence', 'Collect and analyze threat intelligence to improve security posture.'),
    ('ISO27001:2022', 'A.5.12', 'Classification of information', 'Ensure information is classified based on value and sensitivity.'),
    ('ISO27001:2022', 'A.5.23', 'Information security for use of cloud services', 'Establish processes to select, use, manage, and exit cloud services securely.'),
    ('ISO27001:2022', 'A.6.2', 'Mobile device and teleworking', 'Apply security measures for mobile devices and remote work.'),
    ('ISO27001:2022', 'A.8.1', 'User endpoint devices', 'Protect endpoint devices with appropriate controls.'),
    ('ISO27001:2022', 'A.8.8', 'Management of technical vulnerabilities', 'Establish vulnerability management to remediate in a timely manner.'),
    ('ISO27001:2022', 'A.12.1', 'Logging and monitoring', 'Log and monitor activities to identify events.'),
    ('ISO27001:2022', 'A.12.4', 'Event logging', 'Produce, store, and regularly review logs.'),
    ('ISO27001:2022', 'A.14.1', 'Information security requirements in projects', 'Integrate security into project management.'),
    ('ISO27001:2022', 'A.17.1', 'Information security continuity', 'Ensure information security during disruptions.'),
    ('ISO27001:2022', 'A.18.1', 'Compliance with legal and contractual requirements', 'Identify and meet all applicable requirements.')
) AS seed(standard, ref, title, description)
ON CONFLICT (standard, ref) DO NOTHING;
