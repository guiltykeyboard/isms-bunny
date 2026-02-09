import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  getInitialMode,
  palette,
  resolveMode,
  ThemeMode,
} from "../../styles/theme";

type StorageConfig = {
  use_msp_storage?: boolean;
  allow_local_login?: boolean;
  bucket?: string;
  region?: string;
  endpoint?: string;
  access_key?: string;
  secret_key?: string;
  prefix?: string;
};

export default function StorageAdmin() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const [tenant, setTenant] = useState<any>(null);
  const [cfg, setCfg] = useState<StorageConfig>({});
  const [target, setTarget] = useState<StorageConfig>({});
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

  const migrate = async (direction: "to_msp" | "to_byo") => {
    if (!tenant) return;
    setStatus("Migrating… this may take time.");
    try {
      await apiFetch(`/tenants/${tenant.id}/storage/migrate`, {
        method: "POST",
        body: JSON.stringify({ direction, target }),
      });
      setStatus("Migration complete.");
    } catch (e: any) {
      setStatus(e.message || "Migration failed");
    }
  };

  return (
    <div
      style={{
        padding: "2rem",
        background: colors.background,
        color: colors.text,
        minHeight: "100vh",
      }}
    >
      <h1>Storage settings</h1>
      <p style={{ color: colors.muted }}>
        Choose MSP-shared storage (with per-tenant prefixes) or provide
        tenant-specific S3 credentials. MSP storage uses prefixes:
        tenants/&lt;tenant-id&gt; (or msp/&lt;id&gt; for internal MSP).
      </p>
      <div
        style={{
          marginTop: "1rem",
          display: "grid",
          gap: "0.75rem",
          maxWidth: 520,
        }}
      >
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <input
            type="checkbox"
            checked={Boolean(cfg.use_msp_storage)}
            onChange={(e) =>
              setCfg({ ...cfg, use_msp_storage: e.target.checked })
            }
          />
          Use MSP shared storage (recommended)
        </label>
        <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
          <input
            type="checkbox"
            checked={cfg.allow_local_login ?? true}
            onChange={(e) =>
              setCfg({ ...cfg, allow_local_login: e.target.checked })
            }
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
        <div
          style={{
            marginTop: "1rem",
            padding: "1rem",
            borderRadius: 12,
            background: colors.surface,
            color: colors.text,
          }}
        >
          <h3>Migration</h3>
          <p style={{ color: colors.muted, marginTop: 0 }}>
            Copy objects between MSP shared storage and a BYO bucket. Use
            cautiously; long-running operations may take time.
          </p>
          <div style={{ display: "grid", gap: "0.5rem" }}>
            <input
              placeholder="Target bucket (for to_byo)"
              value={target.bucket || ""}
              onChange={(e) => setTarget({ ...target, bucket: e.target.value })}
              style={input(colors)}
            />
            <input
              placeholder="Target region"
              value={target.region || ""}
              onChange={(e) => setTarget({ ...target, region: e.target.value })}
              style={input(colors)}
            />
            <input
              placeholder="Target endpoint (optional)"
              value={target.endpoint || ""}
              onChange={(e) =>
                setTarget({ ...target, endpoint: e.target.value })
              }
              style={input(colors)}
            />
            <input
              placeholder="Target access key"
              value={target.access_key || ""}
              onChange={(e) =>
                setTarget({ ...target, access_key: e.target.value })
              }
              style={input(colors)}
            />
            <input
              placeholder="Target secret key"
              type="password"
              value={target.secret_key || ""}
              onChange={(e) =>
                setTarget({ ...target, secret_key: e.target.value })
              }
              style={input(colors)}
            />
          </div>
          <div
            style={{
              display: "flex",
              gap: "0.75rem",
              marginTop: "0.75rem",
              flexWrap: "wrap",
            }}
          >
            <button style={btn(colors)} onClick={() => migrate("to_byo")}>
              Migrate to BYO bucket
            </button>
            <button style={btn(colors)} onClick={() => migrate("to_msp")}>
              Migrate to MSP shared
            </button>
          </div>
        </div>
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
