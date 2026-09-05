// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";
import { GET } from "./route";

afterEach(() => vi.unstubAllEnvs());

describe("system status proxy", () => {
  it("maps valid health responses without exposing service configuration", async () => {
    vi.stubEnv("API_BASE_URL", "http://internal.example:8000/");
    const mock = vi.fn().mockResolvedValueOnce({ ok: true, json: async () => ({ status: "ok" }) }).mockResolvedValueOnce({ ok: true, json: async () => ({ status: "ready", database: "private" }) });
    vi.stubGlobal("fetch", mock);
    const result = await GET();
    expect(await result.json()).toEqual({ live: "available", ready: "available" });
    expect(mock.mock.calls[0][0]).toBe("http://internal.example:8000/health/live");
    expect(result.headers.get("cache-control")).toContain("no-store");
  });

  it.each([
    ["invalid response", { ok: true, json: async () => ({ status: "unexpected" }) }],
    ["non-object response", { ok: true, json: async () => null }],
    ["unhealthy response", { ok: false }],
  ])("maps %s to unavailable", async (_label, upstream) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(upstream));
    expect(await (await GET()).json()).toEqual({ live: "unavailable", ready: "unavailable" });
  });

  it("handles unreachable services without leaking errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("postgresql://secret")));
    expect(await (await GET()).json()).toEqual({ live: "unavailable", ready: "unavailable" });
  });
});
