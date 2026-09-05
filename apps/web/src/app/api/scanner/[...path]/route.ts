import { authErrorBody } from "@/features/auth/proxy";
import { scopedScannerPath } from "@/features/intake/scanner-path";

export const dynamic = "force-dynamic";

async function forward(
  request: Request,
  method: "GET" | "POST" | "PATCH",
  path: string,
) {
  const headers: Record<string, string> = { "Cache-Control": "no-store" };
  const cookie = request.headers.get("cookie");
  if (cookie) headers.cookie = cookie;
  let body: string | undefined;
  if (method !== "GET") {
    const raw = await request.text();
    if (raw) {
      body = raw;
      headers["content-type"] = "application/json";
    }
  }
  const base = (process.env.API_BASE_URL || "http://127.0.0.1:8000").replace(
    /\/+$/,
    "",
  );
  let upstream: Response;
  try {
    upstream = await fetch(`${base}/${path}`, {
      method,
      headers,
      body,
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(8000),
    });
  } catch {
    return authErrorBody(
      503,
      "The workspace service is unavailable. Try again.",
    );
  }
  const text = await upstream.text();
  const responseHeaders = new Headers({ "Cache-Control": "no-store" });
  const contentType = upstream.headers.get("content-type");
  if (contentType) responseHeaders.set("content-type", contentType);
  return new Response(text, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export async function GET(
  original: Request,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  const scoped = scopedScannerPath(path);
  if (scoped === null)
    return authErrorBody(404, "The requested resource was not found.");
  return forward(original, "GET", scoped);
}

export async function POST(
  original: Request,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  const scoped = scopedScannerPath(path);
  if (scoped === null)
    return authErrorBody(404, "The requested resource was not found.");
  return forward(original, "POST", scoped);
}

export async function PATCH(
  original: Request,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  const scoped = scopedScannerPath(path);
  if (scoped === null)
    return authErrorBody(404, "The requested resource was not found.");
  return forward(original, "PATCH", scoped);
}
