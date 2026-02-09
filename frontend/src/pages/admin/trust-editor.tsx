import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import { getInitialMode, palette, resolveMode, ThemeMode } from "../../styles/theme";

export default function TrustEditor() {
  const [mode] = useState<ThemeMode>(() =>
    typeof window === "undefined" ? "dark" : getInitialMode(),
  );
  const colors = palette[resolveMode(mode)];
  const [content, setContent] = useState<any>({ overview_md: "" });
  const [status, setStatus] = useState<string | null>(null);

  const load = async () => {
    setStatus("Loading trust content…");
    try {
      const data = await apiFetch("/trust/content");
      setContent(data);
      setStatus(null);
    } catch (e: any) {
      setStatus(e.message || "Failed to load");
    }
  };

  const regenerate = async () => {
    setStatus("Generating from ISMS public docs…");
    try {
      const res = await apiFetch("/trust/generate", { method: "POST" });
      setContent((prev: any) => ({ ...prev, overview_md: res.overview_md }));
      setStatus("Generated from documents");
    } catch (e: any) {
      setStatus(e.message || "Generate failed");
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div style={{ padding: "2rem", background: colors.background, color: colors.text, minHeight: "100vh" }}>
      <h1>Trust Page</h1>
      <p style={{ color: colors.muted }}>
        Overview is generated from public ISMS documents (iso27001/public/*.md). Use regenerate to refresh.
      </p>
      <pre style={{ whiteSpace: "pre-wrap", padding: "1rem", background: colors.surface, color: colors.text, borderRadius: 12, border: `1px solid ${colors.surface}` }}>
        {content.overview_md || "No content yet."}
      </pre>
      <div style={{ marginTop: "1rem" }}>
        <button style={btn(colors)} onClick={regenerate}>
          Regenerate from docs
        </button>
      </div>
      {status && <p style={{ color: colors.muted, marginTop: "0.75rem" }}>{status}</p>}
    </div>
  );
}

const btn = (colors: any) => ({
  padding: "0.7rem 1.1rem",
  borderRadius: 10,
  border: "none",
  background: colors.primary,
  color: colors.text,
  cursor: "pointer",
  fontWeight: 600,
});
