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

  const save = async () => {
    setStatus("Saving…");
    try {
      await apiFetch("/trust/content", {
        method: "PUT",
        body: JSON.stringify(content),
      });
      setStatus("Saved");
    } catch (e: any) {
      setStatus(e.message || "Save failed");
    }
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div style={{ padding: "2rem", background: colors.background, color: colors.text, minHeight: "100vh" }}>
      <h1>Trust Page Editor</h1>
      <p style={{ color: colors.muted }}>Edit public overview markdown.</p>
      <textarea
        value={content.overview_md || ""}
        onChange={(e) => setContent({ ...content, overview_md: e.target.value })}
        style={{ width: "100%", height: "300px", padding: "1rem", background: colors.surface, color: colors.text, borderRadius: 12, border: `1px solid ${colors.surface}` }}
      />
      <div style={{ marginTop: "1rem" }}>
        <button style={btn(colors)} onClick={save}>
          Save
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
