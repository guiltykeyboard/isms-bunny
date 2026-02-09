import useSWR from "swr";
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  palette,
  resolveMode,
  getInitialMode,
  ThemeMode,
} from "../../styles/theme";
import { TableCard } from "../../components/TableCard";

type AlertPref = {
  alert_type: string;
  channel: string;
  recipients: string[];
  last_sent_at?: string | null;
};

export default function AlertsPage() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data: tenant } = useSWR<any>("/tenants/current", apiFetch);
  const [prefs, setPrefs] = useState<AlertPref[]>([]);
  const [alertTypes, setAlertTypes] = useState<{ id: string; description: string }[]>([]);
  const [saving, setSaving] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      if (!tenant?.id) return;
      setLoading(true);
      const res = await apiFetch(`/tenants/${tenant.id}/alerts`);
      const types = await apiFetch("/tenants/alert-types");
      setPrefs(res || []);
      setAlertTypes(types || []);
      setLoading(false);
    };
    load();
  }, [tenant]);

  const rows = (prefs || []).map((p) => [
    p.alert_type,
    p.channel,
    (p.recipients || []).join(", "),
    p.last_sent_at || "—",
  ]);

  const missing = alertTypes.filter(
    (t) => !(prefs || []).some((p) => p.alert_type === t.id),
  );

  const merged = alertTypes.map((t) => {
    const match = (prefs || []).find((p) => p.alert_type === t.id);
    return (
      match || {
        alert_type: t.id,
        channel: "webhook",
        recipients: [],
        last_sent_at: null,
      }
    );
  });

  const savePref = async (alertType: string, channel: string, recipients: string) => {
    if (!tenant?.id) return;
    setSaving(alertType);
    try {
      await apiFetch(`/tenants/${tenant.id}/alerts/${alertType}`, {
        method: "PUT",
        body: JSON.stringify({
          channel,
          recipients: recipients
            .split(",")
            .map((r) => r.trim())
            .filter(Boolean),
        }),
      });
      const updated = merged.map((m) =>
        m.alert_type === alertType
          ? {
              ...m,
              channel,
              recipients: recipients
                .split(",")
                .map((r) => r.trim())
                .filter(Boolean),
            }
          : m,
      );
      setPrefs(updated);
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
      <h1>Alert Preferences</h1>
      <p style={{ color: colors.muted }}>
        Per-tenant alert channels and recipients. Use task reminders to configure
        task_due; other alert types will appear here as they are added.
      </p>
      <TableCard
        title={loading ? "Loading…" : "Alerts"}
        colors={colors}
        columns={["Alert", "Channel", "Recipients", "Last sent"]}
        rows={rows}
      />
      <div style={{ marginTop: "1rem", display: "grid", gap: "0.75rem" }}>
        {merged.map((p) => (
          <div
            key={p.alert_type}
            style={{
              background: colors.surface,
              padding: "0.75rem",
              borderRadius: 10,
              display: "grid",
              gap: "0.35rem",
            }}
          >
            <strong>{p.alert_type}</strong>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <select
                defaultValue={p.channel}
                style={inp(colors)}
                id={`channel-${p.alert_type}`}
              >
                <option value="webhook">webhook</option>
                <option value="email">email</option>
                <option value="both">both</option>
                <option value="none">none</option>
              </select>
              <input
                style={inp(colors)}
                id={`recipients-${p.alert_type}`}
                defaultValue={(p.recipients || []).join(", ")}
                placeholder="Recipients (comma separated)"
              />
              <button
                style={btn(colors)}
                disabled={saving === p.alert_type}
                onClick={() =>
                  savePref(
                    p.alert_type,
                    (
                      document.getElementById(
                        `channel-${p.alert_type}`,
                      ) as HTMLSelectElement
                    ).value,
                    (
                      document.getElementById(
                        `recipients-${p.alert_type}`,
                      ) as HTMLInputElement
                    ).value,
                  )
                }
              >
                {saving === p.alert_type ? "Saving…" : "Save"}
              </button>
            </div>
            <div style={{ color: colors.muted, fontSize: "0.9em" }}>
              Last sent: {p.last_sent_at || "—"}
            </div>
          </div>
        ))}
      </div>
      {missing.length > 0 && (
        <div
          style={{
            marginTop: "1rem",
            background: colors.surface,
            padding: "0.75rem",
            borderRadius: 10,
            color: colors.muted,
          }}
        >
          <strong>Not configured yet:</strong>{" "}
          {missing.map((m) => m.description || m.id).join(", ")}
        </div>
      )}
      {!rows.length && !loading && (
        <div style={{ marginTop: "1rem", color: colors.muted }}>
          No alert preferences found.
        </div>
      )}
    </div>
  );
}

const inp = (colors: any) => ({
  padding: "0.6rem",
  borderRadius: 8,
  border: `1px solid ${colors.surface}`,
  background: colors.surface,
  color: colors.text,
});

const btn = (colors: any) => ({
  padding: "0.5rem 0.9rem",
  borderRadius: 8,
  border: "none",
  background: colors.primary,
  color: colors.text,
  cursor: "pointer",
});
