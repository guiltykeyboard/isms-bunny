import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { palette, resolveMode, getInitialMode, ThemeMode } from "../../styles/theme";

interface Credential {
  id?: string;
  nickname?: string;
  sign_count?: number;
}

export default function WebAuthnAdmin() {
  const [mode] = useState<ThemeMode>(getInitialMode());
  const colors = palette[resolveMode(mode)];
  const [creds, setCreds] = useState<Credential[]>([]);
  const [status, setStatus] = useState<string | null>(null);

  const load = async () => {
    // Placeholder: server list endpoint not yet implemented; show static note
    setStatus("Register passkeys from your profile. Admin listing TODO.");
  };

  useEffect(() => {
    load().catch((e) => setStatus(e.message));
  }, []);

  return (
    <div style={{ padding: "1.5rem", color: colors.text, background: colors.background, minHeight: "100vh" }}>
      <h1>Passkeys</h1>
      <p style={{ color: colors.muted, maxWidth: 720 }}>
        Register security keys or platform passkeys in your profile. This admin page will later list device
        registrations per user for audit visibility.
      </p>
      {creds.length === 0 && (
        <div style={{ padding: "1rem", border: `1px dashed ${colors.surface}`, borderRadius: 8 }}>
          No passkeys listed yet. Use the user profile UI to register; audit view coming soon.
        </div>
      )}
      {status && <p style={{ marginTop: "0.5rem", color: colors.muted }}>{status}</p>}
    </div>
  );
}
