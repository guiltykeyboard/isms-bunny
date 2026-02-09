import useSWR from "swr";
import { useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  palette,
  resolveMode,
  getInitialMode,
  ThemeMode,
} from "../../styles/theme";

type SoARow = {
  id: string;
  standard: string;
  ref: string;
  title: string;
  description: string;
  status?: string;
  rationale?: string;
};

const statuses = [
  "not_started",
  "in_progress",
  "implemented",
  "not_applicable",
];

export default function ControlsAdmin() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data, mutate } = useSWR<SoARow[]>("/controls/soa", apiFetch);
  const [saving, setSaving] = useState<string | null>(null);

  const updateState = async (row: SoARow, status: string) => {
    setSaving(row.id);
    try {
      await apiFetch(`/controls/${row.id}/state`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      mutate();
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(null);
    }
  };

  return (
    <div
      style={{
        padding: "2rem",
        minHeight: "100vh",
        background: colors.background,
        color: colors.text,
      }}
    >
      <h1>Controls / SoA</h1>
      <p style={{ color: colors.muted }}>
        Mark implementation status per control.
      </p>
      <a
        href="/reports/soa.csv"
        style={{ color: colors.primary, fontWeight: 600 }}
      >
        Download SoA CSV
      </a>
      <div style={{ display: "grid", gap: "0.75rem", marginTop: "1rem" }}>
        {(data || []).map((row) => (
          <div
            key={row.id}
            style={{
              background: colors.surface,
              padding: "0.75rem",
              borderRadius: 10,
            }}
          >
            <div style={{ fontWeight: 700 }}>
              {row.standard} {row.ref} — {row.title}
            </div>
            <div style={{ color: colors.muted }}>{row.description}</div>
            <div
              style={{
                marginTop: "0.5rem",
                display: "flex",
                gap: "0.5rem",
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <select
                value={row.status || "not_started"}
                onChange={(e) => updateState(row, e.target.value)}
                style={select(colors)}
                disabled={saving === row.id}
              >
                {statuses.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
              <span style={{ color: colors.muted, fontSize: "0.9em" }}>
                Current: {row.status || "not set"}
              </span>
            </div>
          </div>
        ))}
        {!data && <div style={{ color: colors.muted }}>Loading…</div>}
      </div>
    </div>
  );
}

const select = (colors: any) => ({
  padding: "0.6rem",
  borderRadius: 8,
  border: `1px solid ${colors.surface}`,
  background: colors.surface,
  color: colors.text,
});
