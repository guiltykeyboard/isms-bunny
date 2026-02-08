import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { getInitialMode, palette, resolveMode, ThemeMode } from "../../styles/theme";

type StorageConfig = {
  use_msp_storage?: boolean;
  bucket?: string;
  region?: string;
  endpoint?: string;
  access_key?: string;
  secret_key?: string;
};

export default function StorageAdmin() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const [tenant, setTenant] = useState<any>(null);
  const [cfg, setCfg] = useState<StorageConfig>({});
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    apiFetch("/tenants/current")
      .then((t) => {
        setTenant(t);
        setCfg(t.storage_config || {});
      })
      .catch((e: any) => setStatus(e.message));
  }, []);

  const save = async () => {
    if (!tenant) return;
    setStatus("Saving…");
    try {
      await apiFetch(`/tenants/${tenant.id}/storage`, {
        method: "PATCH",
        body: JSON.stringify({ storage_config: cfg }),
      });
      setStatus("Saved.");
    } catch (e: any) {
      setStatus(e.message || "Save failed");
    }
  };

  return (
    <div style={{ padding: "2rem", background: colors.background, color: colors.text, minHeight: "100vh" }}>
      <h1>Storage settings</h1>
      <p style={{ color: colors.muted }}>
        Choose MSP-shared storage (with per-tenant prefixes) or provide tenant-specific S3 credentials.
      </p>
      <div style={{ marginTop: "1rem", display: "grid", gap: "0.75rem", maxWidth: 520 }}>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <input
            type="checkbox"
            checked={Boolean(cfg.use_msp_storage)}
            onChange={(e) => setCfg({ ...cfg, use_msp_storage: e.target.checked })}
          />
          Use MSP shared storage (recommended)
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <input
            type="checkbox"
            checked={cfg.allow_local_login ?? true}
            onChange={(e) => setCfg({ ...cfg, allow_local_login: e.target.checked })}
          />
          Allow local login (break-glass)
        </label>
        {!cfg.use_msp_storage && (
          <>
            <input
              placeholder="Bucket"
              value={cfg.bucket || ""}
              onChange={(e) => setCfg({ ...cfg, bucket: e.target.value })}
              style={input(colors)}
            />
            <input
              placeholder="Region"
              value={cfg.region || ""}
              onChange={(e) => setCfg({ ...cfg, region: e.target.value })}
              style={input(colors)}
            />
            <input
              placeholder="Endpoint (optional)"
              value={cfg.endpoint || ""}
              onChange={(e) => setCfg({ ...cfg, endpoint: e.target.value })}
              style={input(colors)}
            />
            <input
              placeholder="Access key"
              value={cfg.access_key || ""}
              onChange={(e) => setCfg({ ...cfg, access_key: e.target.value })}
              style={input(colors)}
            />
            <input
              placeholder="Secret key"
              type="password"
              value={cfg.secret_key || ""}
              onChange={(e) => setCfg({ ...cfg, secret_key: e.target.value })}
              style={input(colors)}
            />
          </>
        )}
        <button style={btn(colors)} onClick={save}>
          Save
        </button>
        {status && <p style={{ color: colors.muted }}>{status}</p>}
      </div>
    </div>
  );
}

const input = (colors: any) => ({
  padding: "0.7rem",
  borderRadius: 10,
  border: `1px solid ${colors.surface}`,
  background: colors.surface,
  color: colors.text,
});

const btn = (colors: any) => ({
  padding: "0.7rem 1.1rem",
  borderRadius: 10,
  border: "none",
  background: colors.primary,
  color: colors.text,
  cursor: "pointer",
  fontWeight: 600,
});
