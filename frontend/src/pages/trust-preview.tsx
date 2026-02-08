import useSWR from "swr";
import { apiFetch } from "../lib/api";
import { palette, ThemeMode, getInitialMode, resolveMode } from "../styles/theme";
import { TrustCard } from "../components/TrustCard";

export default function TrustPreview() {
  const [mode] = useState<ThemeMode>(getInitialMode());
  const resolved = resolveMode(mode);
  const colors = palette[resolved];

  const { data } = useSWR("/trust/content", apiFetch);

  return (
    <div
      style={{
        background: colors.background,
        color: colors.text,
        minHeight: "100vh",
        padding: "2rem",
        fontFamily: "Inter, system-ui, -apple-system, sans-serif",
      }}
    >
      <h1>Trust Page (Preview)</h1>
      <p style={{ color: colors.muted }}>Rendered for current tenant host.</p>

      <div style={{ display: "grid", gap: "1rem" }}>
        <TrustCard title="Overview">
          <div
            style={{
              background: colors.surface,
              padding: "0.75rem",
              borderRadius: "10px",
              whiteSpace: "pre-wrap",
            }}
          >
            {data?.overview_md || "No overview published yet."}
          </div>
        </TrustCard>
        <TrustCard title="Policies / Attestations">
          <pre style={{ margin: 0 }}>{JSON.stringify(data?.policies || [], null, 2)}</pre>
        </TrustCard>
        <TrustCard title="Subprocessors">
          <pre style={{ margin: 0 }}>{JSON.stringify(data?.subprocessors || [], null, 2)}</pre>
        </TrustCard>
      </div>
    </div>
  );
}
