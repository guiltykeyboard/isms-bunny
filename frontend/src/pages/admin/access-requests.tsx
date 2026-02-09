import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { getInitialMode, palette, resolveMode, ThemeMode } from "../../styles/theme";

type RequestRow = {
  id: string;
  name: string;
  email: string;
  company: string;
  justification: string;
  status: string;
  created_at: string;
};

export default function AccessRequests() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const [rows, setRows] = useState<RequestRow[]>([]);
  const [status, setStatus] = useState<string | null>(null);

  const load = async () => {
    setStatus("Loading requests…");
    try {
      const data = await apiFetch("/trust/requests");
      setRows(data);
      setStatus(null);
    } catch (e: any) {
      setStatus(e.message || "Failed to load");
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div style={{ padding: "2rem", minHeight: "100vh", background: colors.background, color: colors.text }}>
      <h1>Trust Access Requests</h1>
      <p style={{ color: colors.muted }}>View public users requesting gated documents.</p>
      {status && <p style={{ color: colors.muted }}>{status}</p>}
      <div style={{ marginTop: "1rem", display: "grid", gap: "0.75rem" }}>
        {rows.map((r) => (
          <div key={r.id} style={{ background: colors.surface, padding: "0.75rem", borderRadius: 10 }}>
            <div style={{ fontWeight: 600 }}>{r.name} ({r.company})</div>
            <div style={{ color: colors.muted }}>{r.email}</div>
            <div style={{ marginTop: "0.3rem" }}>{r.justification}</div>
            <div style={{ color: colors.muted, marginTop: "0.3rem" }}>
              Status: {r.status} • {new Date(r.created_at).toLocaleString()}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
