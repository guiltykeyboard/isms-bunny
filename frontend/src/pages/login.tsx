import { useEffect, useState } from "react";
import { apiFetch } from "../lib/api";
import { palette, resolveMode, getInitialMode, ThemeMode } from "../styles/theme";

type Provider = { id: string; name: string; type: string; tenant_id?: string };

export default function Login() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [totp, setTotp] = useState("");
  const [providers, setProviders] = useState<Provider[]>([]);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    apiFetch("/providers/public")
      .then((p) => setProviders(p))
      .catch(() => setProviders([]));
  }, []);

  const loginPassword = async () => {
    setStatus("Signing in…");
    try {
      await apiFetch("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password, totp_code: totp || undefined }),
      });
      setStatus("Signed in");
      window.location.href = "/";
    } catch (e: any) {
      setStatus(e.message || "Login failed");
    }
  };

  const loginPasskey = async () => {
    if (!email) {
      setStatus("Email required to find your passkeys");
      return;
    }
    setStatus("Starting passkey sign-in…");
    try {
      const options = await apiFetch("/webauthn/login/options", {
        method: "POST",
        body: JSON.stringify({ email }),
      });
      const publicKey: PublicKeyCredentialRequestOptions = {
        ...options,
        challenge: base64urlToBuffer(options.challenge),
        allowCredentials: options.allowCredentials?.map((c: any) => ({
          ...c,
          id: base64urlToBuffer(c.id),
        })),
      } as any;
      const cred = (await navigator.credentials.get({ publicKey })) as PublicKeyCredential;
      if (!cred) throw new Error("No credential");
      const resp = cred.response as AuthenticatorAssertionResponse;
      await apiFetch("/webauthn/login/verify", {
        method: "POST",
        body: JSON.stringify({
          user_id: options.user_id || undefined,
          credential: {
            id: cred.id,
            raw_id: bufferToBase64url(cred.rawId),
            type: cred.type,
            response: {
              clientDataJSON: bufferToBase64url(resp.clientDataJSON),
              authenticatorData: bufferToBase64url(resp.authenticatorData),
              signature: bufferToBase64url(resp.signature),
              userHandle: resp.userHandle ? bufferToBase64url(resp.userHandle) : undefined,
            },
          },
        }),
      });
      setStatus("Signed in with passkey");
      window.location.href = "/";
    } catch (err: any) {
      setStatus(err.message || "Passkey login failed");
    }
  };

  const startOidc = async (name: string) => {
    setStatus("Redirecting to provider…");
    try {
      const { auth_url } = await apiFetch(`/auth/oidc/${encodeURIComponent(name)}/start`);
      window.location.href = auth_url;
    } catch (e: any) {
      setStatus(e.message || "OIDC start failed");
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: colors.background, color: colors.text, padding: "2rem" }}>
      <h1>Sign in</h1>
      <div style={{ display: "grid", gap: "1rem", maxWidth: 420 }}>
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="email"
          style={input(colors)}
          autoComplete="email"
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="password"
          style={input(colors)}
        />
        <input
          value={totp}
          onChange={(e) => setTotp(e.target.value)}
          placeholder="TOTP (if enabled)"
          style={input(colors)}
        />
        <button style={btn(colors)} onClick={loginPassword}>
          Sign in with password
        </button>
        <button style={btn(colors)} onClick={loginPasskey}>
          Sign in with passkey
        </button>
        {providers.filter((p) => p.type === "oidc").length > 0 && (
          <div>
            <p style={{ color: colors.muted, marginBottom: "0.3rem" }}>Single Sign-On</p>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              {providers
                .filter((p) => p.type === "oidc")
                .map((p) => (
                  <button key={p.id} style={btn(colors)} onClick={() => startOidc(p.name)}>
                    {p.name}
                  </button>
                ))}
            </div>
          </div>
        )}
      </div>
      {status && <p style={{ marginTop: "1rem", color: colors.muted }}>{status}</p>}
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

const input = (colors: any) => ({
  padding: "0.7rem",
  borderRadius: 10,
  border: `1px solid ${colors.surface}`,
  background: colors.surface,
  color: colors.text,
});

const btn = (colors: any) => ({
  padding: "0.7rem 1.1rem",
  borderRadius: 10,
  border: "none",
  background: colors.primary,
  color: colors.text,
  cursor: "pointer",
  fontWeight: 600,
});
