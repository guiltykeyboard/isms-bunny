import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  getInitialMode,
  palette,
  resolveMode,
  ThemeMode,
} from "../../styles/theme";

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
  const [filters, setFilters] = useState({ status: "all" });

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

  const updateRow = (id: string, updates: Partial<RequestRow>) => {
    setRows((prev) =>
      prev.map((row) => (row.id === id ? { ...row, ...updates } : row)),
    );
  };

  useEffect(() => {
    load();
  }, []);

  const filtered = rows.filter((r) =>
    filters.status === "all" ? true : r.status === filters.status,
  );

  return (
    <div
      style={{
        padding: "2rem",
        minHeight: "100vh",
        background: colors.background,
        color: colors.text,
      }}
    >
      <h1>Trust Access Requests</h1>
      <p style={{ color: colors.muted }}>
        View public users requesting gated documents.
      </p>
      {status && <p style={{ color: colors.muted }}>{status}</p>}
      <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.5rem" }}>
        <label style={{ color: colors.muted }}>Filter</label>
        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          style={input(colors)}
        >
          <option value="all">all</option>
          <option value="new">new</option>
          <option value="approved">approved</option>
          <option value="denied">denied</option>
        </select>
      </div>
      <div style={{ marginTop: "1rem", display: "grid", gap: "0.75rem" }}>
        {filtered.map((r) => (
          <div
            key={r.id}
            style={{
              background: colors.surface,
              padding: "0.75rem",
              borderRadius: 10,
            }}
          >
            <div style={{ fontWeight: 600 }}>
              {r.name} ({r.company})
            </div>
            <div style={{ color: colors.muted }}>{r.email}</div>
            <div style={{ marginTop: "0.3rem" }}>{r.justification}</div>
            <div style={{ color: colors.muted, marginTop: "0.3rem" }}>
              Status: {r.status} • {new Date(r.created_at).toLocaleString()}
            </div>
            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                marginTop: "0.5rem",
                flexWrap: "wrap",
              }}
            >
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
              <button
                style={btn(colors)}
                onClick={() => {
                  updateRow(r.id, { status: "approved" });
                  save({ ...r, status: "approved" });
                }}
              >
                Approve
              </button>
              <button
                style={btn(colors)}
                onClick={() => {
                  updateRow(r.id, { status: "denied" });
                  save({ ...r, status: "denied" });
                }}
              >
                Deny
              </button>
            </div>
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
