import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { getInitialMode, palette, resolveMode, ThemeMode } from "../../styles/theme";

type UserRow = {
  id: string;
  email: string;
  is_msp_admin: boolean;
  auth_preference: string;
  allow_local_fallback: boolean;
};

export default function UsersAdmin() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const [rows, setRows] = useState<UserRow[]>([]);
  const [status, setStatus] = useState<string | null>(null);

  const load = async () => {
    setStatus("Loading…");
    try {
      const data = await apiFetch("/users");
      setRows(data);
      setStatus(null);
    } catch (e: any) {
      setStatus(e.message);
    }
  };

  const save = async (row: UserRow) => {
    try {
      await apiFetch(`/users/${row.id}/auth`, {
        method: "PATCH",
        body: JSON.stringify({
          auth_preference: row.auth_preference,
          allow_local_fallback: row.allow_local_fallback,
        }),
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
      <h1>Users</h1>
      <p style={{ color: colors.muted }}>Set auth preference and break-glass local fallback.</p>
      {status && <p style={{ color: colors.muted }}>{status}</p>}
      <div style={{ marginTop: "1rem", display: "grid", gap: "0.75rem" }}>
        {rows.map((r) => (
          <div
            key={r.id}
            style={{
              padding: "0.75rem",
              borderRadius: 10,
              background: colors.surface,
              display: "grid",
              gap: "0.4rem",
            }}
          >
            <div style={{ fontWeight: 600 }}>{r.email}</div>
            <div style={{ color: colors.muted }}>MSP admin: {r.is_msp_admin ? "yes" : "no"}</div>
            <select
              value={r.auth_preference}
              onChange={(e) =>
                setRows((prev) =>
                  prev.map((row) =>
                    row.id === r.id ? { ...row, auth_preference: e.target.value } : row,
                  ),
                )
              }
              style={input(colors)}
            >
              <option value="external">External (IdP)</option>
              <option value="local">Local only</option>
              <option value="either">Either (prefer external)</option>
            </select>
            <label style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
              <input
                type="checkbox"
                checked={r.allow_local_fallback}
                onChange={(e) =>
                  setRows((prev) =>
                    prev.map((row) =>
                      row.id === r.id ? { ...row, allow_local_fallback: e.target.checked } : row,
                    ),
                  ),
                }
              />
              Allow local fallback
            </label>
            <button style={btn(colors)} onClick={() => save(r)}>
              Save
            </button>
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
