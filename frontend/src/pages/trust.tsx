import { useState } from "react";
import useSWR from "swr";
import { apiFetch } from "../lib/api";
import {
  palette,
  ThemeMode,
  getInitialMode,
  resolveMode,
} from "../styles/theme";
import { TrustCard } from "../components/TrustCard";

export default function TrustPage() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data: content, mutate } = useSWR("/trust/content", apiFetch);

  const [req, setReq] = useState({
    name: "",
    email: "",
    company: "",
    justification: "",
  });
  const [reqStatus, setReqStatus] = useState<string | null>(null);
  const [emailLookup, setEmailLookup] = useState("");
  const [statusResult, setStatusResult] = useState<any>(null);
  const [gated, setGated] = useState<any>(null);
  const [gatedStatus, setGatedStatus] = useState<string | null>(null);

  const submitRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setReqStatus("Submitting…");
    try {
      await apiFetch("/trust/request-access", {
        method: "POST",
        body: JSON.stringify(req),
      });
      setReqStatus("Request sent. Check status below.");
      setReq({ name: "", email: "", company: "", justification: "" });
    } catch (err: any) {
      setReqStatus(err.message || "Submit failed");
    }
  };

  const checkStatus = async () => {
    if (!emailLookup) return;
    setReqStatus("Checking…");
    try {
      const res = await apiFetch(
        `/trust/request-status?email=${encodeURIComponent(emailLookup)}`,
      );
      setStatusResult(res[0] || null);
      setReqStatus(null);
    } catch (err: any) {
      setReqStatus(err.message || "Lookup failed");
      setStatusResult(null);
    }
  };

  const loadGated = async () => {
    setGatedStatus(
      "Loading gated content… (requires approved request and login)",
    );
    try {
      const res = await apiFetch("/trust/gated");
      setGated(res);
      setGatedStatus(null);
    } catch (err: any) {
      setGated(null);
      setGatedStatus(err.message || "Failed to load gated content");
    }
  };

  return (
    <div
      style={{
        background: colors.background,
        color: colors.text,
        minHeight: "100vh",
        padding: "2rem",
      }}
    >
      <h1>Trust Center</h1>
      <p style={{ color: colors.muted }}>Public view for this tenant.</p>

      <div style={{ display: "grid", gap: "1rem" }}>
        <TrustCard title="Overview">
          <div style={{ whiteSpace: "pre-wrap" }}>
            {content?.overview_md || "No overview published yet."}
          </div>
        </TrustCard>

        <TrustCard title="Subprocessors">
          <pre style={{ margin: 0 }}>
            {JSON.stringify(content?.subprocessors || [], null, 2)}
          </pre>
        </TrustCard>

        <TrustCard title="Request access to gated documents">
          <form
            onSubmit={submitRequest}
            style={{ display: "grid", gap: "0.5rem" }}
          >
            <input
              style={input(colors)}
              placeholder="Full name"
              value={req.name}
              onChange={(e) => setReq({ ...req, name: e.target.value })}
            />
            <input
              style={input(colors)}
              placeholder="Work email"
              value={req.email}
              onChange={(e) => setReq({ ...req, email: e.target.value })}
            />
            <input
              style={input(colors)}
              placeholder="Company"
              value={req.company}
              onChange={(e) => setReq({ ...req, company: e.target.value })}
            />
            <textarea
              style={{ ...input(colors), minHeight: "80px" }}
              placeholder="Justification"
              value={req.justification}
              onChange={(e) =>
                setReq({ ...req, justification: e.target.value })
              }
            />
            <button style={btn(colors)} type="submit">
              Request access
            </button>
          </form>
          {reqStatus && (
            <p style={{ color: colors.muted, marginTop: "0.5rem" }}>
              {reqStatus}
            </p>
          )}
        </TrustCard>

        <TrustCard title="Check request status">
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <input
              style={input(colors)}
              placeholder="Your email"
              value={emailLookup}
              onChange={(e) => setEmailLookup(e.target.value)}
            />
            <button style={btn(colors)} onClick={checkStatus}>
              Check
            </button>
          </div>
          {statusResult && (
            <p style={{ color: colors.muted, marginTop: "0.4rem" }}>
              Latest: {statusResult.status} (updated{" "}
              {statusResult.updated_at || statusResult.created_at})
            </p>
          )}
        </TrustCard>

        <TrustCard title="Gated content (requires approval + login)">
          <button style={btn(colors)} onClick={loadGated}>
            Load gated content
          </button>
          {gatedStatus && (
            <p style={{ color: colors.muted, marginTop: "0.4rem" }}>
              {gatedStatus}
            </p>
          )}
          {gated && (
            <div
              style={{ marginTop: "0.6rem", display: "grid", gap: "0.5rem" }}
            >
              <div>
                <strong>Policies</strong>
                <pre style={{ margin: 0 }}>
                  {JSON.stringify(gated.gated_policies || [], null, 2)}
                </pre>
              </div>
              <div>
                <strong>Attestations</strong>
                <pre style={{ margin: 0 }}>
                  {JSON.stringify(gated.gated_attestations || [], null, 2)}
                </pre>
              </div>
              <div>
                <strong>Evidence</strong>
                {(gated.evidence || []).length === 0 && (
                  <div style={{ color: colors.muted }}>No evidence listed.</div>
                )}
                {(gated.evidence || []).map((e: any) => (
                  <div key={e.id} style={{ marginTop: "0.3rem" }}>
                    {e.filename} —{" "}
                    <a href={e.download_url} style={{ color: colors.primary }}>
                      download
                    </a>
                  </div>
                ))}
              </div>
            </div>
          )}
        </TrustCard>
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
  width: "100%",
});

const btn = (colors: any) => ({
  padding: "0.7rem 1.1rem",
  borderRadius: 10,
  border: "none",
  background: colors.primary,
  color: colors.text,
  cursor: "pointer",
  fontWeight: 700,
});
