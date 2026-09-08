import { describe, expect, it } from "vitest";
import { scannerUpstreamUrl } from "./scanner-url";

describe("scanner upstream URL", () => {
  it("preserves allowed client query parameters for the API", () => {
    const upstream = scannerUpstreamUrl(
      "http://localhost:8100/",
      "portfolio/opportunities",
      "http://localhost:3000/api/scanner/portfolio/opportunities?category=repetitive_manual_work&page=2",
    );

    expect(upstream.toString()).toBe(
      "http://localhost:8100/portfolio/opportunities?category=repetitive_manual_work&page=2",
    );
  });
});
