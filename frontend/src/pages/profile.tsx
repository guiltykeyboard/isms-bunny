import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import { palette, resolveMode, getInitialMode, ThemeMode } from "../styles/theme";

export default function Profile() {
  const [mode] = useState<ThemeMode>(getInitialMode());
  const colors = palette[resolveMode(mode)];
  const [email, setEmail] = useState("");
  const [creds, setCreds] = useState<any[]>([]);
  const [status, setStatus] = useState<string | null>(null);

  const loadCreds = async () => {
    try {
      const data = await apiFetch("/webauthn/credentials/me");
      setCreds(data);
    } catch (e: any) {
      setStatus(e.message);
    }
  };

  const registerPasskey = async () => {
    setStatus("Starting passkey registration…");
    try {
      const options = await apiFetch("/webauthn/register/options");
      const publicKey: PublicKeyCredentialCreationOptions = {
        ...options,
        challenge: base64urlToBuffer(options.challenge),
        user: {
          ...options.user,
          id: base64urlToBuffer(options.user.id || options.user.idBytes || options.user.id),
        },
      } as any;

      const cred = (await navigator.credentials.create({ publicKey })) as PublicKeyCredential;
      if (!cred) throw new Error("No credential created");
      const response = cred.response as AuthenticatorAttestationResponse;
      const payload = {
        credential: {
          id: cred.id,
          raw_id: bufferToBase64url(cred.rawId),
          type: cred.type,
          response: {
            clientDataJSON: bufferToBase64url(response.clientDataJSON),
            attestationObject: bufferToBase64url(response.attestationObject),
          },
        },
        nickname: `Device ${new Date().toISOString()}`,
      };
      await apiFetch("/webauthn/register/verify", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setStatus("Passkey registered.");
      loadCreds();
    } catch (err: any) {
      setStatus(err.message || "Failed to register passkey");
    }
  };

  const deleteCred = async (id: string) => {
    await apiFetch(`/webauthn/credentials/me/${id}`, { method: "DELETE" });
    loadCreds();
  };

  useEffect(() => {
    loadCreds();
  }, []);

  return (
    <div style={{ padding: "2rem", background: colors.background, color: colors.text, minHeight: "100vh" }}>
      <h1>My Profile</h1>
      <p style={{ color: colors.muted }}>Register a passkey for passwordless login.</p>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", marginTop: "1rem" }}>
        <button onClick={registerPasskey} style={btn(colors)}>
          Register Passkey
        </button>
      </div>
      {creds.length > 0 && (
        <div style={{ marginTop: "1.5rem" }}>
          <h3>My Passkeys</h3>
          <ul style={{ paddingLeft: "1rem" }}>
            {creds.map((c) => (
              <li key={c.id} style={{ marginBottom: "0.4rem" }}>
                {c.nickname || "Passkey"} — sign count {c.sign_count ?? 0}
                <button
                  style={{ marginLeft: "0.6rem", ...btn(colors), padding: "0.3rem 0.6rem" }}
                  onClick={() => deleteCred(c.id)}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      {status && <p style={{ marginTop: "0.75rem", color: colors.muted }}>{status}</p>}
    </div>
  );
}

function bufferToBase64url(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let str = "";
  bytes.forEach((b) => (str += String.fromCharCode(b)));
  return btoa(str).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64urlToBuffer(base64url: string): ArrayBuffer {
  const pad = "=".repeat((4 - (base64url.length % 4)) % 4);
  const base64 = (base64url + pad).replace(/-/g, "+").replace(/_/g, "/");
  const str = atob(base64);
  const buffer = new ArrayBuffer(str.length);
  const view = new Uint8Array(buffer);
  for (let i = 0; i < str.length; i++) view[i] = str.charCodeAt(i);
  return buffer;
}

const btn = (colors: any) => ({
  padding: "0.7rem 1.1rem",
  borderRadius: 10,
  border: "none",
  background: colors.primary,
  color: colors.text,
  cursor: "pointer",
  fontWeight: 600,
});
