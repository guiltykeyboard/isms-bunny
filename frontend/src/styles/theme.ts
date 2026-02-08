export const palette = {
  dark: {
    background: "#0F1116",
    surface: "#1A1D24",
    primary: "#4B2C82",
    accent: "#6F3CCF",
    text: "#F4F5FB",
    muted: "#C5C8D4",
  },
  light: {
    background: "#F7F8FB",
    surface: "#E6E8EF",
    primary: "#4B2C82",
    accent: "#6F3CCF",
    text: "#0F1116",
    muted: "#4B5565",
  },
} as const;

export type ThemeMode = "light" | "dark" | "system";

export const getInitialMode = (): ThemeMode => {
  if (typeof window === "undefined") return "system";
  const stored = window.localStorage.getItem("theme");
  if (stored === "light" || stored === "dark" || stored === "system") return stored;
  return "system";
};

export const resolveMode = (mode: ThemeMode): "light" | "dark" => {
  if (mode === "system") {
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }
  return mode;
};
