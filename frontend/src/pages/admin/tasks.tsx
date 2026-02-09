import useSWR from "swr";
import { useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  palette,
  resolveMode,
  getInitialMode,
  ThemeMode,
} from "../../styles/theme";

type Task = {
  id: string;
  title: string;
  status: string;
  due_date?: string;
  control_id?: string;
  assignee?: string;
};

export default function TasksPage() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data, mutate } = useSWR<Task[]>("/tasks", apiFetch);
  const [form, setForm] = useState<Partial<Task>>({
    title: "",
    status: "open",
  });
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMsg("Saving…");
    try {
      await apiFetch("/tasks", { method: "POST", body: JSON.stringify(form) });
      setForm({ title: "", status: "open" });
      mutate();
      setStatusMsg("Saved");
    } catch (err: any) {
      setStatusMsg(err.message || "Save failed");
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
      <h1>Tasks</h1>
      {statusMsg && <p style={{ color: colors.muted }}>{statusMsg}</p>}
      <form
        onSubmit={submit}
        style={{ display: "grid", gap: "0.5rem", maxWidth: 480 }}
      >
        <input
          style={input(colors)}
          placeholder="Title"
          value={form.title || ""}
          onChange={(e) => setForm({ ...form, title: e.target.value })}
        />
        <input
          style={input(colors)}
          placeholder="Control ID (optional)"
          value={form.control_id || ""}
          onChange={(e) => setForm({ ...form, control_id: e.target.value })}
        />
        <input
          style={input(colors)}
          placeholder="Assignee user id"
          value={form.assignee || ""}
          onChange={(e) => setForm({ ...form, assignee: e.target.value })}
        />
        <input
          style={input(colors)}
          placeholder="Due date (YYYY-MM-DD)"
          value={form.due_date || ""}
          onChange={(e) => setForm({ ...form, due_date: e.target.value })}
        />
        <select
          style={input(colors)}
          value={form.status || "open"}
          onChange={(e) => setForm({ ...form, status: e.target.value })}
        >
          <option value="open">open</option>
          <option value="in_progress">in_progress</option>
          <option value="done">done</option>
        </select>
        <button style={btn(colors)} type="submit">
          Add task
        </button>
      </form>

      <div style={{ marginTop: "1rem", display: "grid", gap: "0.5rem" }}>
        {(data || []).map((t) => (
          <div
            key={t.id}
            style={{
              background: colors.surface,
              padding: "0.7rem",
              borderRadius: 10,
            }}
          >
            <div style={{ fontWeight: 700 }}>{t.title}</div>
            <div style={{ color: colors.muted }}>
              Status {t.status} {t.due_date ? `• due ${t.due_date}` : ""}
            </div>
            {t.control_id && (
              <div style={{ color: colors.muted }}>Control: {t.control_id}</div>
            )}
            {t.assignee && (
              <div style={{ color: colors.muted }}>Assignee: {t.assignee}</div>
            )}
          </div>
        ))}
        {!data?.length && (
          <div style={{ color: colors.muted }}>No tasks yet.</div>
        )}
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
