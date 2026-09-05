import type {
  Availability,
  SystemStatus,
} from "@/features/system-status/contract";

export const dynamic = "force-dynamic";

async function checkService(
  base: string,
  path: string,
  expectedStatus: string,
): Promise<Availability> {
  try {
    const response = await fetch(`${base}${path}`, {
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(3000),
    });
    if (!response.ok) return "unavailable";
    const payload: unknown = await response.json();
    return typeof payload === "object" &&
      payload !== null &&
      "status" in payload &&
      payload.status === expectedStatus
      ? "available"
      : "unavailable";
  } catch {
    // Health transport failures are represented as unavailable; never return infrastructure details.
    return "unavailable";
  }
}

export async function GET() {
  const base = (process.env.API_BASE_URL || "http://127.0.0.1:8000").replace(
    /\/+$/,
    "",
  );
  const [live, ready] = await Promise.all([
    checkService(base, "/health/live", "ok"),
    checkService(base, "/health/ready", "ready"),
  ]);
  const status: SystemStatus = { live, ready };
  return Response.json(status, { headers: { "Cache-Control": "no-store" } });
}
