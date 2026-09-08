import { describe, expect, it } from "vitest";
import { scopedScannerPath } from "./scanner-path";

const ID = "6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f";

describe("scanner proxy path whitelist", () => {
  it.each([
    [["projects"], "projects"],
    [["portfolio"], "portfolio"],
    [["portfolio", "opportunities"], "portfolio/opportunities"],
    [["scoring-configurations"], "scoring-configurations"],
    [["integration-catalog"], "integration-catalog"],
    [["audit-events"], "audit-events"],
    [["projects", ID], `projects/${ID}`],
    [["projects", ID, "processes"], `projects/${ID}/processes`],
    [["processes", ID], `processes/${ID}`],
    [["processes", ID, "intake"], `processes/${ID}/intake`],
    [["processes", ID, "analyses"], `processes/${ID}/analyses`],
    [["analyses", ID], `analyses/${ID}`],
    [["analyses", ID, "report"], `analyses/${ID}/report`],
    [["process-versions", ID], `process-versions/${ID}`],
    [["process-versions", ID, "review"], `process-versions/${ID}/review`],
    [["process-versions", ID, "comments"], `process-versions/${ID}/comments`],
    [["process-versions", ID, "compare"], `process-versions/${ID}/compare`],
    [["analyses", ID, "opportunities"], `analyses/${ID}/opportunities`],
    [["opportunities", ID], `opportunities/${ID}`],
    [["reports", ID, "pdf"], `reports/${ID}/pdf`],
    [["reports", ID, "docx"], `reports/${ID}/docx`],
    [["reports", ID, "slides"], `reports/${ID}/slides`],
  ])("allows %s", (segments, expected) => {
    expect(scopedScannerPath(segments)).toBe(expected);
  });

  it.each([
    ["auth escape", ["auth", "me"]],
    ["session escape", ["sessions", ID]],
    ["traversal", ["projects", "..", "sessions"]],
    ["foreign id segment", ["projects", "not-a-uuid", "processes"]],
    ["unknown action", ["processes", ID, "delete"]],
    ["too deep", ["projects", ID, "processes", "x"]],
    ["empty", [] as string[]],
  ])("rejects %s", (_label, segments) => {
    expect(scopedScannerPath(segments)).toBeNull();
  });
});
