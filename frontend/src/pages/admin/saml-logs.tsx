import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { getInitialMode, palette, resolveMode, ThemeMode } from "../../styles/theme";

export default function SamlLogs() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const [logs, setLogs] = useState<any[]>([]);
  const [tenantId, setTenantId] = useState<string>("");
  const [status, setStatus] = useState<string | null>(null);
  const [limit, setLimit] = useState<number>(50);

  const load = async () => {
    setStatus("Loading...");
    try {
      const qs = new URLSearchParams();
      if (tenantId) qs.set("tenant_id", tenantId);
      qs.set("limit", String(limit));
      const data = await apiFetch(`/saml/logs?${qs.toString()}`);
      setLogs(data);
      setStatus(null);
    } catch (e: any) {
      setStatus(e.message || "Failed to load logs");
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const clearLogs = async () => {
    if (!tenantId) {
      setStatus("Tenant ID required to clear logs (MSP only).");
      return;
    }
    try {
      await apiFetch(`/saml/logs/${tenantId}`, { method: "DELETE" });
      setStatus("Cleared");
      setLogs([]);
    } catch (e: any) {
      setStatus(e.message || "Clear failed");
    }
  };

  return (
    <div style={{ padding: "2rem", minHeight: "100vh", background: colors.background, color: colors.text }}>
      <h1>SAML Logs</h1>
      <p style={{ color: colors.muted }}>
        Tenant admins can view their own logs. MSP admins can specify a tenant ID to view/clear.
      </p>
      <div style={{ display: "flex", gap: "0.5rem", alignItems: "center", margin: "1rem 0" }}>
        <input
          placeholder="Tenant ID (MSP only)"
          value={tenantId}
          onChange={(e) => setTenantId(e.target.value)}
          style={input(colors)}
        />
        <input
          type="number"
          value={limit}
          onChange={(e) => setLimit(Number(e.target.value) || 50)}
          style={{ ...input(colors), width: 90 }}
        />
        <button style={btn(colors)} onClick={load}>
          Refresh
        </button>
        <button style={btn(colors)} onClick={clearLogs}>
          Clear (MSP)
        </button>
      </div>
      {status && <p style={{ color: colors.muted }}>{status}</p>}
      <div style={{ marginTop: "1rem", background: colors.surface, borderRadius: 12, padding: "1rem" }}>
        {logs.length === 0 && <p style={{ color: colors.muted }}>No entries.</p>}
        {logs.map((l, idx) => (
          <div key={idx} style={{ padding: "0.5rem 0", borderBottom: "1px solid " + colors.muted }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 600 }}>
              <span>{l.level}</span>
              <span style={{ color: colors.muted }}>{new Date(l.created_at).toLocaleString()}</span>
            </div>
            <div>{l.message}</div>
            {l.details && Object.keys(l.details).length > 0 && (
              <pre style={{ background: "#111", color: "#eee", padding: "0.5rem", borderRadius: 8, overflowX: "auto" }}>
                {JSON.stringify(l.details, null, 2)}
              </pre>
            )}
          </div>
        ))}
      </div>
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
  padding: "0.6rem 1rem",
  borderRadius: 8,
  border: "none",
  background: colors.primary,
  color: colors.text,
  cursor: "pointer",
  fontWeight: 600,
});
