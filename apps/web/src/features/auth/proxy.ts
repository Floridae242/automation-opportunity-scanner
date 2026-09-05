const API_BASE = () =>
  (process.env.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

const SAFE_FAILURES: Record<number, { code: string; message: string }> = {
  401: { code: "AUTH_INVALID", message: "Authentication failed." },
  403: { code: "AUTH_FORBIDDEN", message: "You cannot perform this action." },
  404: { code: "NOT_FOUND", message: "The requested resource was not found." },
  409: {
    code: "CONFLICT",
    message: "This request conflicts with current data.",
  },
  422: {
    code: "VALIDATION_ERROR",
    message: "Please check the entered values.",
  },
  429: {
    code: "AUTH_RATE_LIMITED",
    message: "Too many attempts. Try again shortly.",
  },
};

export function authErrorBody(
  status: number,
  message = "Request failed. Try again.",
) {
  const known = SAFE_FAILURES[status];
  return Response.json(
    {
      error: {
        code: known?.code ?? "SERVICE_UNAVAILABLE",
        message: known?.message ?? message,
        request_id: "",
        details: {},
      },
    },
    { status, headers: { "Cache-Control": "no-store" } },
  );
}

export async function proxyAuthEndpoint(
  request: Request,
  method: "GET" | "POST",
  suffix: string,
): Promise<Response> {
  const cookie = request.headers.get("cookie");
  const headers: Record<string, string> = { "Cache-Control": "no-store" };
  if (cookie) headers.cookie = cookie;
  let body: string | undefined;
  if (method === "POST") {
    const raw = await request.text();
    if (raw) {
      body = raw;
      headers["content-type"] = "application/json";
    }
  }
  let upstream: Response;
  try {
    upstream = await fetch(`${API_BASE()}/auth/${suffix}`, {
      method,
      headers,
      body,
      cache: "no-store",
      redirect: "error",
      signal: AbortSignal.timeout(5000),
    });
  } catch {
    return authErrorBody(503, "Identity service is unavailable. Try again.");
  }
  const text = await upstream.text();
  const responseHeaders = new Headers({ "Cache-Control": "no-store" });
  const contentType = upstream.headers.get("content-type");
  if (contentType) responseHeaders.set("content-type", contentType);
  for (const setCookie of upstream.headers.getSetCookie()) {
    responseHeaders.append("set-cookie", setCookie);
  }
  return new Response(upstream.status === 204 ? null : text, {
    status: upstream.status,
    headers: responseHeaders,
  });
}
