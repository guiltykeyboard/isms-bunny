import { useState } from "react";
import useSWR from "swr";
import { apiFetch } from "../lib/api";
import { palette, ThemeMode, getInitialMode, resolveMode } from "../styles/theme";
import { TrustCard } from "../components/TrustCard";

export default function TrustPage() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const { data: content, mutate } = useSWR("/trust/content", apiFetch);

  const [req, setReq] = useState({ name: "", email: "", company: "", justification: "" });
  const [reqStatus, setReqStatus] = useState<string | null>(null);
  const [emailLookup, setEmailLookup] = useState("");
  const [statusResult, setStatusResult] = useState<any>(null);

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
      const res = await apiFetch(`/trust/request-status?email=${encodeURIComponent(emailLookup)}`);
      setStatusResult(res[0] || null);
      setReqStatus(null);
    } catch (err: any) {
      setReqStatus(err.message || "Lookup failed");
      setStatusResult(null);
    }
  };

  return (
    <div style={{ background: colors.background, color: colors.text, minHeight: "100vh", padding: "2rem" }}>
      <h1>Trust Center</h1>
      <p style={{ color: colors.muted }}>Public view for this tenant.</p>

      <div style={{ display: "grid", gap: "1rem" }}>
        <TrustCard title="Overview">
          <div style={{ whiteSpace: "pre-wrap" }}>{content?.overview_md || "No overview published yet."}</div>
        </TrustCard>

        <TrustCard title="Subprocessors">
          <pre style={{ margin: 0 }}>{JSON.stringify(content?.subprocessors || [], null, 2)}</pre>
        </TrustCard>

        <TrustCard title="Request access to gated documents">
          <form onSubmit={submitRequest} style={{ display: "grid", gap: "0.5rem" }}>
            <input style={input(colors)} placeholder="Full name" value={req.name} onChange={(e) => setReq({ ...req, name: e.target.value })} />
            <input style={input(colors)} placeholder="Work email" value={req.email} onChange={(e) => setReq({ ...req, email: e.target.value })} />
            <input style={input(colors)} placeholder="Company" value={req.company} onChange={(e) => setReq({ ...req, company: e.target.value })} />
            <textarea
              style={{ ...input(colors), minHeight: "80px" }}
              placeholder="Justification"
              value={req.justification}
              onChange={(e) => setReq({ ...req, justification: e.target.value })}
            />
            <button style={btn(colors)} type="submit">Request access</button>
          </form>
          {reqStatus && <p style={{ color: colors.muted, marginTop: "0.5rem" }}>{reqStatus}</p>}
        </TrustCard>

        <TrustCard title="Check request status">
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
            <input
              style={input(colors)}
              placeholder="Your email"
              value={emailLookup}
              onChange={(e) => setEmailLookup(e.target.value)}
            />
            <button style={btn(colors)} onClick={checkStatus}>Check</button>
          </div>
          {statusResult && (
            <p style={{ color: colors.muted, marginTop: "0.4rem" }}>
              Latest: {statusResult.status} (updated {statusResult.updated_at || statusResult.created_at})
            </p>
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
