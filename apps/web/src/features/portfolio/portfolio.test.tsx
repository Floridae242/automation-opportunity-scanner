import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import {
  parseAnalysisOverview,
  parseAxes,
  parseOpportunityDetail,
  parseOpportunityList,
  parseOpportunityRow,
} from "./contract";
import { OpportunityAnalyzer } from "./opportunity-analyzer";
import { ExportReportButton } from "./export-report";

const nav = vi.hoisted(() => ({
  replace: vi.fn(),
  refresh: vi.fn(),
  push: vi.fn(),
}));
vi.mock("next/navigation", () => ({
  usePathname: () => "/processes/x",
  useRouter: () => nav,
}));

const ROW = {
  id: "6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f",
  title: "Automate repetitive manual steps",
  status: "candidate",
  result_state: "final",
  confidence: 93,
  priority_band: "investigate now",
  total_score: 82.4,
  scoring_version: "aos-score-v1",
  axes: { version: "aos-portfolio-axes-v1", impact: 80, effort: 30 },
  governance_review: true,
};

const DETAIL = {
  ...ROW,
  analysis_run_id: "1b2c3d4e-5f60-41a2-93b4-c5d6e7f80911",
  scope: { step_keys: ["S1"], pain_categories: ["repetitive_manual_work"] },
  score: {
    total: 82.4,
    scoring_version: "aos-score-v1",
    dimensions: { business_value: 80, time_saving: null },
    dimension_evidence: { business_value: ["weekly hours"] },
    coverage: 85.7,
    confidence_version: "aos-confidence-v1",
  },
};

describe("portfolio contract", () => {
  it("parses rows and refuses invented states", () => {
    expect(parseOpportunityList([ROW])?.[0]?.priority_band).toBe(
      "investigate now",
    );
    expect(
      parseOpportunityList([{ ...ROW, result_state: "approved" }]),
    ).toBeNull();
    expect(parseOpportunityList([{ ...ROW, confidence: "secret" }])).toBeNull();
  });

  it("preserves known scores while making unknown optional fields explicit", () => {
    expect(parseAxes(undefined)).toEqual({ impact: null, effort: null });
    expect(parseAxes({ version: 1, impact: Infinity, effort: 20 })).toEqual({
      version: undefined,
      impact: null,
      effort: 20,
    });
    expect(
      parseOpportunityRow({
        ...ROW,
        status: undefined,
        priority_band: 1,
        total_score: "82",
        scoring_version: false,
        governance_review: false,
      }),
    ).toMatchObject({
      status: "candidate",
      priority_band: null,
      total_score: null,
      scoring_version: null,
      governance_review: false,
    });
  });

  it("parses analysis overview and opportunity detail", () => {
    const overview = {
      analysis_id: ROW.id,
      status: "completed",
      task: "opportunity_analysis",
      pain_points: [
        {
          category: "repetitive_manual_work",
          description: "Manual steps repeat.",
          severity: "high",
          confidence: "medium",
          evidence_refs: ["S1"],
        },
      ],
      error_code: null,
    };
    expect(parseAnalysisOverview(overview)?.pain_points[0].category).toBe(
      "repetitive_manual_work",
    );
    expect(
      parseAnalysisOverview({ ...overview, pain_points: "not-list" }),
    ).toBeNull();
    expect(
      parseOpportunityDetail(DETAIL)?.score.dimensions.time_saving,
    ).toBeNull();
    expect(parseOpportunityDetail({ ...DETAIL, score: null })).toBeNull();
  });

  it("parses defensible recommendation and ROI evidence, dropping malformed advice", () => {
    const detail = {
      ...DETAIL,
      scope: "not-a-record",
      recommendation: {
        patterns: ["workflow automation"],
        rationale: "Evidence shows repeated manual data entry.",
        prerequisites: ["Confirm API access"],
        risks: ["Exception handling"],
        human_control: "Review exceptions before release.",
        rejected_alternatives: [
          { pattern: "RPA", why: "No stable UI evidence" },
        ],
        confidence: "medium",
      },
      roi: {
        available: true,
        scenarios: [
          {
            automation_rate: 0.7,
            exception_rate: 0.1,
            net_hours_saved_month: 24,
            stated_by: "Assumption",
          },
        ],
      },
    };
    const parsed = parseOpportunityDetail(detail);
    expect(parsed?.scope).toEqual({});
    expect(parsed?.recommendation?.patterns).toEqual(["workflow automation"]);
    expect(parsed?.roi?.available).toBe(true);
    expect(
      parseOpportunityDetail({
        ...detail,
        recommendation: {
          ...detail.recommendation,
          rejected_alternatives: [null],
        },
        roi: { available: true, scenarios: [null] },
      }),
    ).toMatchObject({ recommendation: null, roi: null });
    expect(
      parseOpportunityDetail({
        ...detail,
        score: { ...DETAIL.score, dimensions: { business_value: "80" } },
      }),
    ).toBeNull();
  });
});

describe("report envelope", () => {
  it("freezes snapshot with a usable report id and rejects tampered payloads", async () => {
    const { parseReportEnvelope } = await import("./contract");
    const good = {
      report_id: "2b1f6a7c-9d3e-4f5a-8b6c-7d8e9f0a1b2c",
      status: "ready",
      snapshot: {
        schema_version: "aos-report-v1",
        pain_points: [],
        opportunities: [],
      },
    };
    expect(parseReportEnvelope(good)?.report_id).toBe(good.report_id);
    expect(parseReportEnvelope({ ...good, report_id: "../evil" })).toBeNull();
    expect(
      parseReportEnvelope({
        ...good,
        snapshot: { ...good.snapshot, pain_points: null },
      }),
    ).toBeNull();
  });
});

describe("opportunity analyzer", () => {
  it("starts the reviewed-version analysis and routes to the overview", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ analysis_id: ROW.id }),
      }),
    );
    render(<OpportunityAnalyzer processId="proc-1" />);
    await userEvent.click(
      screen.getByRole("button", { name: "Analyze opportunities" }),
    );
    await vi.waitFor(() =>
      expect(nav.push).toHaveBeenCalledWith(`/analyses/${ROW.id}`),
    );
  });

  it("surfaces a safe message when analysis is rejected", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({
          error: {
            message:
              "Mark the process version reviewed before scoring opportunities.",
          },
        }),
      }),
    );
    render(<OpportunityAnalyzer processId="proc-1" />);
    await userEvent.click(
      screen.getByRole("button", { name: "Analyze opportunities" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "reviewed before scoring",
    );
  });
});

describe("report export", () => {
  it("freezes the analysis and opens its immutable report", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ status: "ready" }),
      }),
    );
    render(<ExportReportButton analysisId={ROW.id} />);
    await userEvent.click(
      screen.getByRole("button", { name: "Export executive report" }),
    );
    await vi.waitFor(() =>
      expect(nav.push).toHaveBeenCalledWith(`/analyses/${ROW.id}/report`),
    );
  });

  it("keeps the analysis page and shows a safe failure message", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network")));
    render(<ExportReportButton analysisId={ROW.id} />);
    await userEvent.click(
      screen.getByRole("button", { name: "Export executive report" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("Export failed");
  });
});
