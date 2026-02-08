import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { palette, resolveMode, getInitialMode, ThemeMode } from "../../styles/theme";

interface Provider {
  id?: string;
  name: string;
  type: "oidc" | "saml";
  enabled: boolean;
  tenant_id?: string | null;
  config: Record<string, any>;
}

const emptyProvider = (type: "oidc" | "saml"): Provider => ({
  name: "",
  type,
  enabled: true,
  tenant_id: null,
  config: {},
});

export default function ProvidersPage() {
  const [mode, setMode] = useState<ThemeMode>(getInitialMode());
  const colors = palette[resolveMode(mode)];
  const [oidc, setOidc] = useState<Provider[]>([]);
  const [saml, setSaml] = useState<Provider[]>([]);
  const [status, setStatus] = useState<string | null>(null);

  const load = async () => {
    const [o, s] = await Promise.all([
      apiFetch("/providers/oidc"),
      apiFetch("/providers/saml"),
    ]);
    setOidc(o);
    setSaml(s);
  };

  useEffect(() => {
    load().catch((e) => setStatus(e.message));
  }, []);

  const save = async () => {
    setStatus("Saving…");
    await apiFetch("/providers/oidc", { method: "PUT", body: JSON.stringify(oidc) });
    await apiFetch("/providers/saml", { method: "PUT", body: JSON.stringify(saml) });
    setStatus("Saved.");
  };

  const updateItem = (
    list: Provider[],
    setList: (items: Provider[]) => void,
    idx: number,
    patch: Partial<Provider>,
  ) => {
    const next = [...list];
    next[idx] = { ...next[idx], ...patch } as Provider;
    setList(next);
  };

  const addProvider = (type: "oidc" | "saml") => {
    const fn = type === "oidc" ? setOidc : setSaml;
    const list = type === "oidc" ? oidc : saml;
    fn([...list, emptyProvider(type)]);
  };

  const removeProvider = (type: "oidc" | "saml", idx: number) => {
    const fn = type === "oidc" ? setOidc : setSaml;
    const list = type === "oidc" ? oidc : saml;
    fn(list.filter((_, i) => i !== idx));
  };

  const card = (items: Provider[], setItems: any, title: string) => (
    <div style={{ border: `1px solid ${colors.surface}`, borderRadius: 12, padding: "1rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>{title}</h3>
        <button onClick={() => addProvider(title.toLowerCase().includes("oidc") ? "oidc" : "saml")}>+ Add</button>
      </div>
      {items.map((p, idx) => (
        <div
          key={idx}
          style={{
            border: `1px solid ${colors.surface}`,
            padding: "0.75rem",
            marginTop: "0.5rem",
            borderRadius: 8,
            display: "grid",
            gap: "0.5rem",
          }}
        >
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <input
              placeholder="Name (e.g., Okta)"
              value={p.name}
              onChange={(e) => updateItem(items, setItems, idx, { name: e.target.value })}
              style={input(colors)}
            />
            <label style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}>
              <input
                type="checkbox"
                checked={p.enabled}
                onChange={(e) => updateItem(items, setItems, idx, { enabled: e.target.checked })}
              />
              Enabled
            </label>
          </div>
          <textarea
            placeholder="Config JSON"
            value={JSON.stringify(p.config, null, 2)}
            onChange={(e) => updateItem(items, setItems, idx, { config: safeParse(e.target.value, p.config) })}
            rows={6}
            style={textarea(colors)}
          />
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <input
              placeholder="Tenant ID (optional)"
              value={p.tenant_id || ""}
              onChange={(e) => updateItem(items, setItems, idx, { tenant_id: e.target.value || null })}
              style={input(colors)}
            />
            <button onClick={() => removeProvider(title.toLowerCase().includes("oidc") ? "oidc" : "saml", idx)}>
              Remove
            </button>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div style={{ padding: "1.5rem", color: colors.text, background: colors.background, minHeight: "100vh" }}>
      <h1>Identity Providers</h1>
      <p style={{ color: colors.muted, maxWidth: 720 }}>
        Configure OIDC (Okta/Azure/Google/BYO) and SAML 2.0 providers. Leave tenant blank to make it available
        to all tenants; set a tenant id to scope access.
      </p>
      <div style={{ display: "grid", gap: "1rem", maxWidth: 960 }}>
        {card(oidc, setOidc, "OIDC Providers")}
        {card(saml, setSaml, "SAML Providers")}
      </div>
      <button onClick={save} style={{ marginTop: "1rem", padding: "0.8rem 1.2rem" }}>
        Save providers
      </button>
      {status && <p style={{ marginTop: "0.5rem", color: colors.muted }}>{status}</p>}
    </div>
  );
}

function safeParse(text: string, fallback: any) {
  try {
    return JSON.parse(text);
  } catch (e) {
    return fallback;
  }
}

const input = (colors: any) => ({
  flex: 1,
  padding: "0.6rem",
  borderRadius: 8,
  border: `1px solid ${colors.surface}`,
  background: colors.surface,
  color: colors.text,
});

const textarea = (colors: any) => ({
  width: "100%",
  padding: "0.6rem",
  borderRadius: 8,
  border: `1px solid ${colors.surface}`,
  background: colors.surface,
  color: colors.text,
  fontFamily: "monospace",
});
