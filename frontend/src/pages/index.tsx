import { useEffect, useState } from "react";
import { palette, ThemeMode } from "../styles/theme";
import { TrustCard } from "../components/TrustCard";
import Link from "next/link";

export default function Home({
  themeMode,
  setThemeMode,
  resolvedTheme,
}: {
  themeMode: ThemeMode;
  setThemeMode: (m: ThemeMode) => void;
  resolvedTheme: "light" | "dark";
}) {
  const colors = palette[resolvedTheme];
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/ping")
      .then((r) => r.json())
      .then((d) => setToken(d.status))
      .catch(() => setToken(null));
  }, []);

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
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: 0 }}>ISMS-Bunny</h1>
          <p style={{ color: colors.muted, marginTop: "0.25rem" }}>
            MSP-friendly ISMS & Trust Center (alpha scaffold)
          </p>
        </div>
        <select
          value={themeMode}
          onChange={(e) => setThemeMode(e.target.value as ThemeMode)}
          style={{ padding: "0.5rem", background: colors.surface, color: colors.text }}
        >
          <option value="system">System</option>
          <option value="dark">Dark</option>
          <option value="light">Light</option>
        </select>
      </header>

      <main style={{ marginTop: "2rem", display: "grid", gap: "1rem" }}>
        <TrustCard title="Trust Page">
          <p style={{ color: colors.muted }}>
            Custom domains via SNI (Caddy) will render tenant-specific trust content with signed
            URLs for gated docs.
          </p>
          <Link
            href="/trust-preview"
            style={{
              display: "inline-block",
              marginTop: "0.5rem",
              background: colors.primary,
              color: colors.text,
              padding: "0.6rem 1.2rem",
              borderRadius: "10px",
              textDecoration: "none",
            }}
          >
            Preview (coming soon)
          </Link>
        </TrustCard>
        <TrustCard title="Status">
          <p>API ping: {token ?? "…"}</p>
          <p>Resolved theme: {resolvedTheme}</p>
          <p style={{ color: colors.muted, marginTop: "0.5rem" }}>
            Need to run setup? Head to <Link href="/setup">/setup</Link>.
          </p>
        </TrustCard>
      </main>
    </div>
  );
}
