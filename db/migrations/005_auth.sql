-- Auth and IdP tables

CREATE TABLE local_credentials (
    user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    password_hash text NOT NULL,
    mfa_enabled boolean DEFAULT false,
    totp_secret text,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE webauthn_credentials (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    credential_id bytea NOT NULL,
    public_key bytea NOT NULL,
    sign_count bigint DEFAULT 0,
    nickname text,
    transports text[],
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE idp_connections (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name text NOT NULL,
    type text NOT NULL CHECK (type IN ('oidc','saml')),
    config jsonb NOT NULL,
    enabled boolean DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE user_idp_links (
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    idp_id uuid REFERENCES idp_connections(id) ON DELETE CASCADE,
    external_id text NOT NULL,
    PRIMARY KEY (user_id, idp_id)
);
