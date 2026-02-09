import useSWR from "swr";
import { useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  palette,
  resolveMode,
  getInitialMode,
  ThemeMode,
} from "../../styles/theme";

type AuditRow = { email: string; action: string; created_at: string };

export default function TrustAudit() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data, error, mutate } = useSWR<AuditRow[]>("/trust/audit", apiFetch, {
    refreshInterval: 15000,
  });

  return (
    <div
      style={{
        padding: "2rem",
        minHeight: "100vh",
        background: colors.background,
        color: colors.text,
      }}
    >
      <h1>Trust Audit</h1>
      <p style={{ color: colors.muted }}>
        Recent gated-content access events. Auto-refreshes every 15s. MSP admins
        only.
      </p>
      <button style={btn(colors)} onClick={() => mutate()}>
        Refresh
      </button>
      {error && (
        <p style={{ color: colors.muted, marginTop: "0.5rem" }}>
          {String(error)}
        </p>
      )}
      <div style={{ marginTop: "1rem", display: "grid", gap: "0.5rem" }}>
        {(data || []).map((row, i) => (
          <div
            key={`${row.email}-${row.created_at}-${i}`}
            style={{
              background: colors.surface,
              padding: "0.75rem",
              borderRadius: 10,
            }}
          >
            <div style={{ fontWeight: 600 }}>{row.email}</div>
            <div style={{ color: colors.muted }}>{row.action}</div>
            <div style={{ color: colors.muted }}>
              {new Date(row.created_at).toLocaleString()}
            </div>
          </div>
        ))}
        {!data?.length && !error && (
          <div style={{ color: colors.muted }}>No audit entries yet.</div>
        )}
      </div>
    </div>
  );
}

const btn = (colors: any) => ({
  padding: "0.6rem 1rem",
  borderRadius: 8,
  border: "none",
  background: colors.primary,
  color: colors.text,
  cursor: "pointer",
  fontWeight: 600,
  marginTop: "0.5rem",
});
