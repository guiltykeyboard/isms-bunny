-- Risk register: assets, threats, vulnerabilities, risks, treatments

CREATE TABLE IF NOT EXISTS assets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    name text NOT NULL,
    category text,
    owner_user_id uuid REFERENCES users(id),
    criticality text,
    notes text,
    created_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS assets_tenant_idx ON assets(tenant_id);

CREATE TABLE IF NOT EXISTS risks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE,
    asset_id uuid REFERENCES assets(id) ON DELETE SET NULL,
    title text NOT NULL,
    threat text,
    vulnerability text,
    impact numeric,
    likelihood numeric,
    status text DEFAULT 'open', -- open|treated|accepted
    treatment text,
    owner_user_id uuid REFERENCES users(id),
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS risks_tenant_idx ON risks(tenant_id, status);
