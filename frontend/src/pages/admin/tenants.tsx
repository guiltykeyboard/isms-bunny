import useSWR from "swr";
import { useMemo, useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  palette,
  resolveMode,
  getInitialMode,
  ThemeMode,
} from "../../styles/theme";
import { TableCard } from "../../components/TableCard";

export default function TenantsPage() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data, mutate } = useSWR("/tenants", apiFetch);
  const [parentOptions, setParentOptions] = useState<any[]>([]);
  const [form, setForm] = useState({
    name: "",
    fqdn: "",
    type: "customer",
    parent_tenant_id: "",
  });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiFetch("/tenants", {
      method: "POST",
      body: JSON.stringify(form),
    });
    setForm({ name: "", fqdn: "", type: "customer", parent_tenant_id: "" });
    mutate();
  };

  // Populate parent options (excluding the new tenant itself)
  useEffect(() => {
    if (data) setParentOptions(data);
  }, [data]);

  return (
    <div
      style={{
        padding: "2rem",
        background: colors.background,
        minHeight: "100vh",
        color: colors.text,
      }}
    >
      <h1>Tenants</h1>
      <form
        onSubmit={submit}
        style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}
      >
        <input
          style={inp(colors)}
          placeholder="Name"
          value={form.name}
          onChange={(e) => setForm({ ...form, name: e.target.value })}
        />
        <input
          style={inp(colors)}
          placeholder="FQDN"
          value={form.fqdn}
          onChange={(e) => setForm({ ...form, fqdn: e.target.value })}
        />
        <select
          style={inp(colors)}
          value={form.type}
          onChange={(e) => setForm({ ...form, type: e.target.value })}
        >
          <option value="customer">Customer</option>
          <option value="internal_msp">Internal MSP</option>
        </select>
        <select
          style={inp(colors)}
          value={form.parent_tenant_id}
          onChange={(e) =>
            setForm({ ...form, parent_tenant_id: e.target.value })
          }
        >
          <option value="">(no parent)</option>
          {(parentOptions || []).map((t: any) => (
            <option key={t.id} value={t.id}>
              {t.name} ({t.type})
            </option>
          ))}
        </select>
        <button style={btn(colors)} type="submit">
          Add
        </button>
      </form>

      <TableCard
        title="Existing (hierarchy)"
        colors={colors}
        columns={["Path", "Type", "Id"]}
        rows={(data || []).map((t: any) => {
          const parent = (data || []).find(
            (p: any) => p.id === t.parent_tenant_id,
          );
          const path = parent ? `${parent.name} → ${t.name}` : t.name;
          return [path, t.type, t.id];
        })}
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
