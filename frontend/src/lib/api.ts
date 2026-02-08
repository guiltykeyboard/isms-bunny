const base =
  process.env.NEXT_PUBLIC_API_BASE || (typeof window === "undefined" ? "" : "");

export async function apiFetch(path: string, options: RequestInit = {}) {
  const res = await fetch(`${base}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    credentials: "include",
    ...options,
  });
  const text = await res.text();
  let body: any = null;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = text;
  }
  if (!res.ok) {
    throw new Error(body?.detail || body?.error || res.statusText);
  }
  return body;
}
