import useSWR from "swr";
import { useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  palette,
  resolveMode,
  getInitialMode,
  ThemeMode,
} from "../../styles/theme";

type SoARow = { id: string; ref: string; title: string };
type Evidence = {
  id: string;
  name: string;
  url?: string;
  s3_key?: string;
  added_at: string;
};

export default function EvidencePage() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data: controls } = useSWR<SoARow[]>("/controls/soa", apiFetch);
  const [selected, setSelected] = useState<string>("");
  const { data: items, mutate } = useSWR<Evidence[]>(
    () => (selected ? `/controls/${selected}/evidence` : null),
    apiFetch,
  );
  const [form, setForm] = useState({ name: "", url: "", s3_key: "" });
  const [status, setStatus] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected) {
      setStatus("Select a control first");
      return;
    }
    setStatus("Saving…");
    try {
      await apiFetch(`/controls/${selected}/evidence`, {
        method: "POST",
        body: JSON.stringify(form),
      });
      setForm({ name: "", url: "", s3_key: "" });
      mutate();
      setStatus("Saved");
    } catch (err: any) {
      setStatus(err.message || "Save failed");
    }
  };

  return (
    <div
      style={{
        padding: "2rem",
        background: colors.background,
        minHeight: "100vh",
        color: colors.text,
      }}
    >
      <h1>Evidence</h1>
      <p style={{ color: colors.muted }}>
        Attach evidence references to controls (URLs or stored keys).
      </p>
      <select
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
        style={input(colors)}
      >
        <option value="">Select control…</option>
        {(controls || []).map((c) => (
          <option key={c.id} value={c.id}>
            {c.ref} — {c.title}
          </option>
        ))}
      </select>

      {selected && (
        <>
          <form
            onSubmit={submit}
            style={{
              display: "grid",
              gap: "0.5rem",
              maxWidth: 480,
              marginTop: "0.75rem",
            }}
          >
            <input
              placeholder="Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              style={input(colors)}
            />
            <input
              placeholder="URL (optional)"
              value={form.url}
              onChange={(e) => setForm({ ...form, url: e.target.value })}
              style={input(colors)}
            />
            <input
              placeholder="S3 key (optional)"
              value={form.s3_key}
              onChange={(e) => setForm({ ...form, s3_key: e.target.value })}
              style={input(colors)}
            />
            <button style={btn(colors)} type="submit">
              Add evidence
            </button>
          </form>
          {status && <p style={{ color: colors.muted }}>{status}</p>}
          <div style={{ marginTop: "1rem", display: "grid", gap: "0.5rem" }}>
            {(items || []).map((ev) => (
              <div
                key={ev.id}
                style={{
                  background: colors.surface,
                  padding: "0.6rem",
                  borderRadius: 8,
                }}
              >
                <div style={{ fontWeight: 600 }}>{ev.name}</div>
                <div style={{ color: colors.muted }}>
                  {ev.url || ev.s3_key || "No link provided"}
                </div>
                <div style={{ color: colors.muted, fontSize: "0.85em" }}>
                  {new Date(ev.added_at).toLocaleString()}
                </div>
              </div>
            ))}
            {!items?.length && (
              <div style={{ color: colors.muted }}>No evidence yet.</div>
            )}
          </div>
        </>
      )}
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
