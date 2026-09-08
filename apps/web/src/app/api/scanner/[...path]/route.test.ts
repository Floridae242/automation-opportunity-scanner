// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";
import { GET } from "./route";

afterEach(() => vi.unstubAllGlobals());

describe("scanner proxy", () => {
  it("preserves binary report downloads", async () => {
    const pdf = new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x00, 0xff, 0x0a]);
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(pdf, {
          headers: {
            "content-disposition": 'attachment; filename="report.pdf"',
            "content-type": "application/pdf",
          },
        }),
      ),
    );

    const response = await GET(
      new Request("http://localhost/api/scanner/reports/6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f/pdf"),
      { params: Promise.resolve({ path: ["reports", "6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f", "pdf"] }) },
    );

    expect(new Uint8Array(await response.arrayBuffer())).toEqual(pdf);
    expect(response.headers.get("content-type")).toBe("application/pdf");
  });
});
