import { describe, expect, it, vi } from "vitest";
import { authErrorBody, proxyAuthEndpoint } from "./proxy";

const upstream = (
  status: number,
  body: string,
  headers: Record<string, string> = {},
) =>
  new Response(body, {
    status,
    headers: { "content-type": "application/json", ...headers },
  });

describe("auth proxy", () => {
  it("forwards cookies, body, and rotated session to the browser", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation((url: string, init: RequestInit) => {
        expect(url).toBe("http://127.0.0.1:8000/auth/login");
        expect(init.method).toBe("POST");
        expect((init.headers as Record<string, string>).cookie).toBe(
          "theme=dark; aos_session=old",
        );
        expect(init.body).toContain("ada@corp.test");
        return Promise.resolve(
          upstream(200, '{"ok":true}', {
            "set-cookie": "aos_session=new; HttpOnly; Path=/; SameSite=lax",
          }),
        );
      });
    vi.stubGlobal("fetch", fetchMock);
    const request = new Request("http://localhost:3000/api/auth/login", {
      method: "POST",
      headers: { cookie: "theme=dark; aos_session=old" },
      body: JSON.stringify({
        email: "ada@corp.test",
        password: "strong-pass-123",
      }),
    });
    const response = await proxyAuthEndpoint(request, "POST", "login");
    expect(response.status).toBe(200);
    expect(response.headers.get("set-cookie")).toContain("aos_session=new");
    expect(response.headers.get("cache-control")).toBe("no-store");
  });

  it("passes rejection envelopes through untouched and never leaks upstream detail", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          upstream(
            401,
            '{"error":{"code":"AUTH_INVALID","message":"Email or password is incorrect.","request_id":"r1","details":{}}}',
          ),
        ),
    );
    const response = await proxyAuthEndpoint(
      new Request("http://localhost:3000/api/auth/login", {
        method: "POST",
        body: "{}",
      }),
      "POST",
      "login",
    );
    expect(response.status).toBe(401);
    const payload = await response.json();
    expect(payload.error.code).toBe("AUTH_INVALID");
  });

  it("fails closed to a safe 503 when the identity service is unreachable", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockRejectedValue(new Error("psycopg://user:secret@host internal")),
    );
    const response = await proxyAuthEndpoint(
      new Request("http://localhost:3000/api/auth/me"),
      "GET",
      "me",
    );
    expect(response.status).toBe(503);
    expect(await response.text()).not.toContain("secret");
  });

  it("maps statuses to safe fallback messages", async () => {
    const body = authErrorBody(429);
    expect(body.status).toBe(429);
    expect((await body.json()).error.code).toBe("AUTH_RATE_LIMITED");
  });
});
