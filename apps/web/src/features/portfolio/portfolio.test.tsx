import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import {
  parseAnalysisOverview,
  parseOpportunityDetail,
  parseOpportunityList,
} from "./contract";
import { OpportunityAnalyzer } from "./opportunity-analyzer";

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
