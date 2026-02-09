import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { getInitialMode, palette, resolveMode, ThemeMode } from "../../styles/theme";

type SmtpConfig = {
  host?: string;
  port?: number;
  username?: string;
  password?: string;
  use_tls?: boolean;
};

export default function SmtpPage() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const [cfg, setCfg] = useState<SmtpConfig>({});
  const [status, setStatus] = useState<string | null>(null);
  const [tenantId, setTenantId] = useState<string>("");

  const load = async () => {
    setStatus("Loading…");
    try {
      const t = await apiFetch("/tenants/current");
      setTenantId(t.id);
      setCfg(t.smtp_config || {});
      setStatus(null);
    } catch (e: any) {
      setStatus(e.message || "Failed to load");
    }
  };

  const save = async () => {
    if (!tenantId) return;
    setStatus("Saving…");
    try {
      await apiFetch(`/tenants/${tenantId}/smtp`, {
        method: "PATCH",
        body: JSON.stringify({ smtp_config: cfg }),
      });
      setStatus("Saved. Update SPF to include this SMTP host/IP.");
    } catch (e: any) {
      setStatus(e.message || "Save failed");
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div style={{ padding: "2rem", minHeight: "100vh", background: colors.background, color: colors.text }}>
      <h1>SMTP Settings</h1>
      <p style={{ color: colors.muted }}>
        Configure per-tenant SMTP. Leave blank to use the MSP default. Remember to add this host/IP to your SPF record.
      </p>
      <div style={{ display: "grid", gap: "0.6rem", maxWidth: 520, marginTop: "1rem" }}>
        <input
          placeholder="Host"
          value={cfg.host || ""}
          onChange={(e) => setCfg({ ...cfg, host: e.target.value })}
          style={input(colors)}
        />
        <input
          type="number"
          placeholder="Port"
          value={cfg.port || ""}
          onChange={(e) => setCfg({ ...cfg, port: Number(e.target.value) || undefined })}
          style={input(colors)}
        />
        <input
          placeholder="Username"
          value={cfg.username || ""}
          onChange={(e) => setCfg({ ...cfg, username: e.target.value })}
          style={input(colors)}
        />
        <input
          placeholder="Password"
          type="password"
          value={cfg.password || ""}
          onChange={(e) => setCfg({ ...cfg, password: e.target.value })}
          style={input(colors)}
        />
        <label style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <input
            type="checkbox"
            checked={cfg.use_tls ?? true}
            onChange={(e) => setCfg({ ...cfg, use_tls: e.target.checked })}
          />
          Use TLS/STARTTLS
        </label>
        <button style={btn(colors)} onClick={save}>
          Save
        </button>
      </div>
      {status && <p style={{ color: colors.muted, marginTop: "0.75rem" }}>{status}</p>}
    </div>
  );
}

const input = (colors: any) => ({
  padding: "0.6rem",
  borderRadius: 8,
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
