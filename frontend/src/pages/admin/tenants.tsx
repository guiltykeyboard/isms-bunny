import useSWR from "swr";
import { useState } from "react";
import { apiFetch } from "../../lib/api";
import { palette, resolveMode, getInitialMode, ThemeMode } from "../../styles/theme";
import { TableCard } from "../../components/TableCard";

export default function TenantsPage() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data, mutate } = useSWR("/tenants", apiFetch);

  const [form, setForm] = useState({ name: "", fqdn: "", type: "customer" });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiFetch("/tenants", {
      method: "POST",
      body: JSON.stringify(form),
    });
    setForm({ name: "", fqdn: "", type: "customer" });
    mutate();
  };

  return (
    <div style={{ padding: "2rem", background: colors.background, minHeight: "100vh", color: colors.text }}>
      <h1>Tenants</h1>
      <form onSubmit={submit} style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <input style={inp(colors)} placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
        <input style={inp(colors)} placeholder="FQDN" value={form.fqdn} onChange={(e) => setForm({ ...form, fqdn: e.target.value })} />
        <select style={inp(colors)} value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
          <option value="customer">Customer</option>
          <option value="internal_msp">Internal MSP</option>
        </select>
        <button style={btn(colors)} type="submit">Add</button>
      </form>

      <TableCard
        title="Existing"
        colors={colors}
        columns={["Name", "FQDN", "Type", "Id"]}
        rows={(data || []).map((t: any) => [t.name, t.fqdn, t.type, t.id])}
      />
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
  padding: "0.6rem 1rem",
  borderRadius: 8,
  border: "none",
  background: colors.primary,
  color: colors.text,
  cursor: "pointer",
});
