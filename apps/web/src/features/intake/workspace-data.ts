import { cookies } from "next/headers";

const API_BASE = () =>
  (process.env.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

export async function fetchWorkspaceJson<T>(
  path: string,
  parse: (value: unknown) => T | null,
  fallback: T,
): Promise<T> {
  const store = await cookies();
  if (!store.has("aos_session")) return fallback;
  try {
    const response = await fetch(`${API_BASE()}/${path.replace(/^\/+/, "")}`, {
      headers: { cookie: store.toString() },
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(5000),
    });
    if (!response.ok) return fallback;
    const parsed = parse(await response.json());
    return parsed === null ? fallback : parsed;
  } catch {
    return fallback;
  }
}
