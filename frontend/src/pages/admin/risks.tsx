import useSWR from "swr";
import { useState } from "react";
import { apiFetch } from "../../lib/api";
import {
  palette,
  resolveMode,
  getInitialMode,
  ThemeMode,
} from "../../styles/theme";

type Asset = {
  id: string;
  name: string;
  category?: string;
  criticality?: string;
  owner_user_id?: string;
  notes?: string;
};

type Risk = {
  id: string;
  title: string;
  threat?: string;
  vulnerability?: string;
  impact?: number;
  likelihood?: number;
  status: string;
  treatment?: string;
  asset_id?: string;
};

export default function RisksPage() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data: assets, mutate: reloadAssets } = useSWR<Asset[]>(
    "/risks/assets",
    apiFetch,
  );
  const { data: risks, mutate: reloadRisks } = useSWR<Risk[]>(
    "/risks",
    apiFetch,
  );

  const [assetForm, setAssetForm] = useState<Partial<Asset>>({ name: "" });
  const [riskForm, setRiskForm] = useState<Partial<Risk>>({
    title: "",
    status: "open",
  });
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const addAsset = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMsg("Saving asset…");
    try {
      await apiFetch("/risks/assets", {
        method: "POST",
        body: JSON.stringify(assetForm),
      });
      setAssetForm({ name: "" });
      reloadAssets();
      setStatusMsg("Asset saved");
    } catch (err: any) {
      setStatusMsg(err.message || "Failed to save asset");
    }
  };

  const addRisk = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMsg("Saving risk…");
    try {
      await apiFetch("/risks", {
        method: "POST",
        body: JSON.stringify(riskForm),
      });
      setRiskForm({ title: "", status: "open" });
      reloadRisks();
      setStatusMsg("Risk saved");
    } catch (err: any) {
      setStatusMsg(err.message || "Failed to save risk");
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
      <h1>Risk register</h1>
      {statusMsg && <p style={{ color: colors.muted }}>{statusMsg}</p>}
      <a
        href="/reports/risks.csv"
        style={{ color: colors.primary, fontWeight: 600 }}
      >
        Download Risks CSV
      </a>

      <section style={{ marginTop: "1rem" }}>
        <h3>Assets</h3>
        <form
          onSubmit={addAsset}
          style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}
        >
          <input
            placeholder="Name"
            value={assetForm.name || ""}
            onChange={(e) =>
              setAssetForm({ ...assetForm, name: e.target.value })
            }
            style={input(colors)}
          />
          <input
            placeholder="Category"
            value={assetForm.category || ""}
            onChange={(e) =>
              setAssetForm({ ...assetForm, category: e.target.value })
            }
            style={input(colors)}
          />
          <input
            placeholder="Criticality"
            value={assetForm.criticality || ""}
            onChange={(e) =>
              setAssetForm({ ...assetForm, criticality: e.target.value })
            }
            style={input(colors)}
          />
          <input
            placeholder="Notes"
            value={assetForm.notes || ""}
            onChange={(e) =>
              setAssetForm({ ...assetForm, notes: e.target.value })
            }
            style={input(colors)}
          />
          <button style={btn(colors)} type="submit">
            Add asset
          </button>
        </form>
        <div style={{ marginTop: "0.75rem", display: "grid", gap: "0.35rem" }}>
          {(assets || []).map((a) => (
            <div
              key={a.id}
              style={{
                background: colors.surface,
                padding: "0.6rem",
                borderRadius: 8,
              }}
            >
              <strong>{a.name}</strong>{" "}
              <span style={{ color: colors.muted }}>{a.category}</span>
              {a.criticality && (
                <span style={{ color: colors.muted, marginLeft: 8 }}>
                  criticality: {a.criticality}
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      <section style={{ marginTop: "1.5rem" }}>
        <h3>Risks</h3>
        <form
          onSubmit={addRisk}
          style={{ display: "grid", gap: "0.5rem", maxWidth: 720 }}
        >
          <input
            placeholder="Title"
            value={riskForm.title || ""}
            onChange={(e) =>
              setRiskForm({ ...riskForm, title: e.target.value })
            }
            style={input(colors)}
          />
          <textarea
            placeholder="Threat"
            value={riskForm.threat || ""}
            onChange={(e) =>
              setRiskForm({ ...riskForm, threat: e.target.value })
            }
            style={{ ...input(colors), minHeight: 60 }}
          />
          <textarea
            placeholder="Vulnerability"
            value={riskForm.vulnerability || ""}
            onChange={(e) =>
              setRiskForm({ ...riskForm, vulnerability: e.target.value })
            }
            style={{ ...input(colors), minHeight: 60 }}
          />
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <input
              placeholder="Impact (1-5)"
              type="number"
              min={1}
              max={5}
              value={riskForm.impact || ""}
              onChange={(e) =>
                setRiskForm({ ...riskForm, impact: Number(e.target.value) })
              }
              style={input(colors)}
            />
            <input
              placeholder="Likelihood (1-5)"
              type="number"
              min={1}
              max={5}
              value={riskForm.likelihood || ""}
              onChange={(e) =>
                setRiskForm({ ...riskForm, likelihood: Number(e.target.value) })
              }
              style={input(colors)}
            />
            <select
              value={riskForm.status || "open"}
              onChange={(e) =>
                setRiskForm({ ...riskForm, status: e.target.value })
              }
              style={input(colors)}
            >
              <option value="open">open</option>
              <option value="treated">treated</option>
              <option value="accepted">accepted</option>
            </select>
            <select
              value={riskForm.asset_id || ""}
              onChange={(e) =>
                setRiskForm({ ...riskForm, asset_id: e.target.value })
              }
              style={input(colors)}
            >
              <option value="">(no asset)</option>
              {(assets || []).map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name}
                </option>
              ))}
            </select>
          </div>
          <textarea
            placeholder="Treatment plan"
            value={riskForm.treatment || ""}
            onChange={(e) =>
              setRiskForm({ ...riskForm, treatment: e.target.value })
            }
            style={{ ...input(colors), minHeight: 60 }}
          />
          <button style={btn(colors)} type="submit">
            Add risk
          </button>
        </form>

        <div style={{ marginTop: "1rem", display: "grid", gap: "0.75rem" }}>
          {(risks || []).map((r) => (
            <div
              key={r.id}
              style={{
                background: colors.surface,
                padding: "0.8rem",
                borderRadius: 10,
              }}
            >
              <div style={{ fontWeight: 700 }}>{r.title}</div>
              <div style={{ color: colors.muted }}>
                Threat: {r.threat || "—"}
              </div>
              <div style={{ color: colors.muted }}>
                Vuln: {r.vulnerability || "—"}
              </div>
              <div style={{ color: colors.muted }}>
                Impact {r.impact || "-"} / Likelihood {r.likelihood || "-"} /
                Status {r.status}
              </div>
              {r.asset_id && (
                <div style={{ color: colors.muted }}>
                  Asset:{" "}
                  {(assets || []).find((a) => a.id === r.asset_id)?.name ||
                    r.asset_id}
                </div>
              )}
              {r.treatment && (
                <div style={{ marginTop: "0.35rem" }}>{r.treatment}</div>
              )}
            </div>
          ))}
        </div>
      </section>
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
