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
  risk_id?: string;
  assignee?: string;
};

export default function TasksPage() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data, mutate } = useSWR<Task[]>("/tasks", apiFetch);
  const { data: controls } = useSWR<any[]>("/controls/soa", apiFetch);
  const { data: risks } = useSWR<any[]>("/risks", apiFetch);
  const [form, setForm] = useState<Partial<Task>>({
    title: "",
    status: "open",
  });
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>("all");

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
          list="control-options"
          value={form.control_id || ""}
          onChange={(e) => setForm({ ...form, control_id: e.target.value })}
        />
        <datalist id="control-options">
          {(controls || []).map((c) => (
            <option key={c.id} value={c.id}>{`${c.ref} ${c.title}`}</option>
          ))}
        </datalist>
        <input
          style={input(colors)}
          placeholder="Risk ID (optional)"
          list="risk-options"
          value={form.risk_id || ""}
          onChange={(e) => setForm({ ...form, risk_id: e.target.value })}
        />
        <datalist id="risk-options">
          {(risks || []).map((r) => (
            <option key={r.id} value={r.id}>
              {r.title}
            </option>
          ))}
        </datalist>
        <input
          style={input(colors)}
          placeholder="Risk ID (optional)"
          value={form.risk_id || ""}
          onChange={(e) => setForm({ ...form, risk_id: e.target.value })}
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

      <div
        style={{
          marginTop: "1rem",
          display: "flex",
          gap: "0.5rem",
          alignItems: "center",
        }}
      >
        <span style={{ color: colors.muted }}>Filter:</span>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={input(colors)}
        >
          <option value="all">all</option>
          <option value="open">open</option>
          <option value="in_progress">in_progress</option>
          <option value="done">done</option>
        </select>
      </div>

      <div style={{ marginTop: "1rem", display: "grid", gap: "0.5rem" }}>
        {(data || [])
          .filter((t) => (filter === "all" ? true : t.status === filter))
          .map((t) => {
            const overdue =
              t.due_date &&
              !["done"].includes(t.status) &&
              new Date(t.due_date).getTime() < new Date().setHours(0, 0, 0, 0);
            return (
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
                  Status{" "}
                  <select
                    value={t.status}
                    onChange={async (e) => {
                      await apiFetch(`/tasks/${t.id}`, {
                        method: "PATCH",
                        body: JSON.stringify({ status: e.target.value }),
                      });
                      mutate();
                    }}
                    style={input(colors)}
                  >
                    <option value="open">open</option>
                    <option value="in_progress">in_progress</option>
                    <option value="done">done</option>
                  </select>{" "}
                  {t.due_date ? `• due ${t.due_date}` : ""}
                  {overdue && (
                    <span style={{ color: "tomato", marginLeft: 6 }}>
                      OVERDUE
                    </span>
                  )}
                </div>
                {t.control_id && (
                  <div style={{ color: colors.muted }}>
                    Control: {t.control_id}
                  </div>
                )}
                {t.risk_id && (
                  <div style={{ color: colors.muted }}>Risk: {t.risk_id}</div>
                )}
                {t.assignee && (
                  <div style={{ color: colors.muted }}>
                    Assignee: {t.assignee}
                  </div>
                )}
              </div>
            );
          })}
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
