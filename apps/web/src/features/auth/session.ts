import { cookies } from "next/headers";
import { parseAuthSession, type AuthSession } from "./contract";

const API_BASE = () =>
  (process.env.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

export async function readServerSession(): Promise<AuthSession | null> {
  const store = await cookies();
  if (!store.has("aos_session")) return null;
  try {
    const response = await fetch(`${API_BASE()}/auth/me`, {
      headers: { cookie: store.toString() },
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) return null;
    return parseAuthSession(await response.json());
  } catch {
    return null;
  }
}
