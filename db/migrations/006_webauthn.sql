-- Store WebAuthn challenges (registration/auth) for verification
CREATE TABLE IF NOT EXISTS webauthn_challenges (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    challenge bytea NOT NULL,
    purpose text NOT NULL CHECK (purpose IN ('registration','authentication')),
    created_at timestamptz NOT NULL DEFAULT now()
);
