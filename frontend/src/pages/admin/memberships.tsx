import useSWR from "swr";
import { useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  palette,
  resolveMode,
  getInitialMode,
  ThemeMode,
} from "../../styles/theme";
import { TableCard } from "../../components/TableCard";

export default function MembershipsPage() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data, mutate } = useSWR("/memberships", apiFetch);
  const [form, setForm] = useState({
    user_id: "",
    tenant_id: "",
    roles: ["tenant_ciso"] as string[],
  });
  const roleOptions = [
    "msp_admin",
    "sub_msp_admin",
    "tenant_ciso",
    "manager",
    "auditor",
    "viewer",
  ];

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    await apiFetch("/memberships", {
      method: "POST",
      body: JSON.stringify(form),
    });
    mutate();
  };

  const toggleRole = (role: string) => {
    setForm((prev) => {
      const has = prev.roles.includes(role);
      return {
        ...prev,
        roles: has
          ? prev.roles.filter((r) => r !== role)
          : [...prev.roles, role],
      };
    });
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
      <h1>Memberships</h1>
      <form
        onSubmit={submit}
        style={{
          display: "flex",
          gap: "0.5rem",
          marginBottom: "1rem",
          flexWrap: "wrap",
        }}
      >
        <input
          style={inp(colors)}
          placeholder="User ID"
          value={form.user_id}
          onChange={(e) => setForm({ ...form, user_id: e.target.value })}
        />
        <input
          style={inp(colors)}
          placeholder="Tenant ID"
          value={form.tenant_id}
          onChange={(e) => setForm({ ...form, tenant_id: e.target.value })}
        />
        <div
          style={{
            display: "flex",
            gap: "0.5rem",
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          {roleOptions.map((r) => {
            const checked = form.roles.includes(r);
            return (
              <label
                key={r}
                style={{
                  color: colors.text,
                  display: "flex",
                  gap: "0.25rem",
                  alignItems: "center",
                }}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => toggleRole(r)}
                />
                {r}
              </label>
            );
          })}
        </div>
        <button style={btn(colors)} type="submit">
          Upsert
        </button>
      </form>

      <TableCard
        title="Existing"
        colors={colors}
        columns={["User", "Tenant", "Roles", "Tenant Name", "Tenant FQDN"]}
        rows={(data || []).map((m: any) => [
          m.user_id,
          m.tenant_id,
          m.roles.join(", "),
          m.tenant_name,
          m.tenant_fqdn,
        ])}
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
