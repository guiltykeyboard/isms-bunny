import { useState } from "react";
import { apiFetch } from "../lib/api";
import { palette, ThemeMode, getInitialMode, resolveMode } from "../styles/theme";

const defaultStorage = {
  bucket: "isms-bunny-dev",
  region: "us-east-1",
  endpoint: "https://s3.wasabisys.com",
  access_key: "",
  secret_key: "",
};

export default function Setup() {
  const [company, setCompany] = useState("MSP Tenant");
  const [fqdn, setFqdn] = useState("localhost");
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("");
  const [storage, setStorage] = useState(defaultStorage);
  const [status, setStatus] = useState<string | null>(null);
  const [mode, setMode] = useState<ThemeMode>(getInitialMode());
  const resolved = resolveMode(mode);
  const colors = palette[resolved];

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus("Initializing…");
    try {
      await apiFetch("/setup/initialize", {
        method: "POST",
        body: JSON.stringify({
          company_name: company,
          fqdn,
          admin_email: email,
          admin_password: password,
          storage,
        }),
      });
      setStatus("Initialized! You can now log in.");
    } catch (err: any) {
      setStatus(`Error: ${err.message}`);
    }
  };

  return (
    <div
      style={{
        background: colors.background,
        color: colors.text,
        minHeight: "100vh",
        padding: "2rem",
        fontFamily: "Inter, system-ui, -apple-system, sans-serif",
      }}
    >
      <h1>ISMS-Bunny Setup</h1>
      <p style={{ color: colors.muted }}>First-time configuration for the MSP tenant.</p>

      <form
        onSubmit={submit}
        style={{ display: "grid", gap: "1rem", maxWidth: 520, marginTop: "1rem" }}
      >
        <label>
          Company / Tenant Name
          <input
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            required
            style={inputStyle(colors)}
          />
        </label>
        <label>
          Default FQDN (host)
          <input
            value={fqdn}
            onChange={(e) => setFqdn(e.target.value)}
            required
            style={inputStyle(colors)}
          />
        </label>
        <label>
          Admin Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={inputStyle(colors)}
          />
        </label>
        <label>
          Admin Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={inputStyle(colors)}
          />
        </label>
        <fieldset style={{ border: `1px solid ${colors.surface}`, padding: "1rem" }}>
          <legend>Object Storage (S3-compatible)</legend>
          {["bucket", "region", "endpoint", "access_key", "secret_key"].map((field) => (
            <label key={field} style={{ display: "block", marginBottom: "0.5rem" }}>
              {field}
              <input
                value={(storage as any)[field]}
                onChange={(e) => setStorage({ ...storage, [field]: e.target.value })}
                style={inputStyle(colors)}
              />
            </label>
          ))}
        </fieldset>

        <button
          type="submit"
          style={{
            background: colors.primary,
            color: colors.text,
            border: "none",
            padding: "0.8rem 1.2rem",
            borderRadius: 10,
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          Run setup
        </button>
      </form>

      {status && <p style={{ marginTop: "1rem", color: colors.muted }}>{status}</p>}
    </div>
  );
}

const inputStyle = (colors: any) => ({
  width: "100%",
  padding: "0.6rem",
  borderRadius: 8,
  border: `1px solid ${colors.surface}`,
  background: colors.surface,
  color: colors.text,
  marginTop: 4,
});
