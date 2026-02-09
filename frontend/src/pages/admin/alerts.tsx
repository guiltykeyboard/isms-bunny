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
