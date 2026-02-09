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
  note?: string;
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

  const save = async (row: RequestRow) => {
    setStatus("Saving…");
    try {
      await apiFetch(`/trust/requests/${row.id}`, {
        method: "PATCH",
        body: JSON.stringify({ status: row.status, note: row.note }),
      });
      setStatus("Saved");
    } catch (e: any) {
      setStatus(e.message || "Save failed");
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
            <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
              <select
                value={r.status}
                onChange={(e) => updateRow(r.id, { status: e.target.value })}
                style={input(colors)}
              >
                <option value="new">new</option>
                <option value="approved">approved</option>
                <option value="denied">denied</option>
              </select>
              <input
                placeholder="note (optional)"
                value={r.note || ""}
                onChange={(e) => updateRow(r.id, { note: e.target.value })}
                style={input(colors)}
              />
              <button style={btn(colors)} onClick={() => save(r)}>
                Save
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function updateRow(id: string, updates: Partial<RequestRow>) {
  setRows((prev) => prev.map((row) => (row.id === id ? { ...row, ...updates } : row)));
}
