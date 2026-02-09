import type { AppProps } from "next/app";
import { useEffect, useState } from "react";
import { Analytics } from "@vercel/analytics/react";
import { SpeedInsights } from "@vercel/speed-insights/next";
import "../styles/globals.css";
import { ThemeMode, getInitialMode, resolveMode } from "../styles/theme";

export default function App({ Component, pageProps }: AppProps) {
  const [mode, setMode] = useState<ThemeMode>("system");
  const [resolved, setResolved] = useState<"light" | "dark">("dark");

  useEffect(() => {
    const initial = getInitialMode();
    setMode(initial);
    setResolved(resolveMode(initial));
  }, []);

  useEffect(() => {
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const listener = () => setResolved(resolveMode(mode));
    mql.addEventListener("change", listener);
    return () => mql.removeEventListener("change", listener);
  }, [mode]);

  useEffect(() => {
    window.localStorage.setItem("theme", mode);
    setResolved(resolveMode(mode));
    document.documentElement.dataset.theme = resolved;
  }, [mode, resolved]);

  return (
    <>
      <Component
        {...pageProps}
        themeMode={mode}
        setThemeMode={setMode}
        resolvedTheme={resolved}
      />
      <Analytics />
      <SpeedInsights />
    </>
  );
}
