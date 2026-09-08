import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { CommentsPanel } from "./intake/comments-panel";
import { VersionCompare } from "./intake/version-compare";
import { MemberAdministration } from "./auth/member-administration";
import { ScoringSettings } from "./portfolio/scoring-settings";
import { BenefitTracker } from "./portfolio/benefit-tracker";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

const callScannerApi = vi.hoisted(() => vi.fn());
vi.mock("./intake/client-api", () => ({ callScannerApi }));

const ID_A = "6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f";
const ID_B = "7f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f";
const weights = {
  business_value: 0.2,
  time_saving: 0.2,
  repetitiveness: 0.15,
  feasibility: 0.15,
  error_reduction: 0.1,
  integration_ease: 0.1,
  risk_safety: 0.1,
};

describe("P1 collaboration and configuration features", () => {
  it("loads comments and posts a valid new comment", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        json: async () => [
          {
            id: "comment",
            body: "Looks good",
            author: { display_name: "Ada" },
          },
        ],
      }),
    );
    callScannerApi.mockResolvedValue({ ok: true });
    const user = userEvent.setup();
    render(<CommentsPanel versionId={ID_A} />);
    expect(await screen.findByText("Looks good")).toBeInTheDocument();
    await user.type(
      screen.getByLabelText("Add comment"),
      "Please verify the approval.",
    );
    await user.click(screen.getByRole("button", { name: "Post comment" }));
    await waitFor(() =>
      expect(callScannerApi).toHaveBeenCalledWith(
        "POST",
        `process-versions/${ID_A}/comments`,
        { body: "Please verify the approval." },
      ),
    );
    expect(screen.getByRole("status")).toHaveTextContent("Comment added");
  });

  it("handles an empty discussion and requires a non-blank comment", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ json: async () => [] }));
    const user = userEvent.setup();
    render(<CommentsPanel versionId={ID_A} />);
    expect(
      await screen.findByText("No comments on this version yet."),
    ).toBeInTheDocument();
    await user.type(screen.getByLabelText("Add comment"), "   ");
    await user.click(screen.getByRole("button", { name: "Post comment" }));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Write a comment before posting.",
    );
  });

  it("compares two versions and shows the changed summary", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({
          base: { version_no: 1 },
          target: { version_no: 2 },
          changes: { source_summary_changed: true },
        }),
      }),
    );
    const user = userEvent.setup();
    render(
      <VersionCompare
        versions={[
          {
            id: ID_B,
            version_no: 2,
            review_status: "reviewed",
            source_summary: "new",
            metrics: {},
            created_at: "",
          },
          {
            id: ID_A,
            version_no: 1,
            review_status: "reviewed",
            source_summary: "old",
            metrics: {},
            created_at: "",
          },
        ]}
      />,
    );
    await user.click(screen.getByRole("button", { name: "Compare" }));
    expect(
      await screen.findByText("v1 → v2: summary changed"),
    ).toBeInTheDocument();
  });

  it("saves editable weights as percentages and makes viewers read-only", async () => {
    callScannerApi.mockResolvedValue({ ok: true });
    const user = userEvent.setup();
    const { rerender } = render(
      <ScoringSettings
        configuration={{ id: ID_A, version_no: 2, weights }}
        editable
      />,
    );
    await user.clear(screen.getByLabelText("Business value"));
    await user.type(screen.getByLabelText("Business value"), "40");
    await user.click(
      screen.getByRole("button", { name: "Save as new version" }),
    );
    await waitFor(() =>
      expect(callScannerApi).toHaveBeenCalledWith(
        "POST",
        "scoring-configurations",
        { weights: expect.objectContaining({ business_value: 0.4 }) },
      ),
    );
    expect(refresh).toHaveBeenCalled();
    rerender(
      <ScoringSettings
        configuration={{ id: ID_A, version_no: 2, weights }}
        editable={false}
      />,
    );
    expect(
      screen.getByText(
        "Only owners and administrators can change scoring weights.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Business value")).toBeDisabled();
  });

  it("shows the unavailable configuration state", () => {
    render(<ScoringSettings configuration={null} editable={false} />);
    expect(
      screen.getByText("Scoring settings are unavailable for this workspace."),
    ).toBeInTheDocument();
  });

  it("records actual benefits separately from estimates", async () => {
    callScannerApi.mockResolvedValue({ ok: true });
    const user = userEvent.setup();
    render(<BenefitTracker benefits={[]} editable opportunityId={ID_A} />);
    expect(screen.getByText("No actual benefits recorded yet.")).toBeVisible();
    fireEvent.change(screen.getByLabelText("Month"), {
      target: { value: "2026-09" },
    });
    await user.type(screen.getByLabelText("Actual hours saved"), "12.5");
    await user.type(screen.getByLabelText("Evidence or notes"), "Timesheet");
    await user.click(
      screen.getByRole("button", { name: "Record actual benefit" }),
    );
    await waitFor(() =>
      expect(callScannerApi).toHaveBeenCalledWith(
        "POST",
        `opportunities/${ID_A}/benefits`,
        {
          period: "2026-09",
          hours_saved: 12.5,
          monetary_benefit: null,
          notes: "Timesheet",
        },
      ),
    );
    expect(refresh).toHaveBeenCalled();
  });

  it("adds an account to the organization and changes its role", async () => {
    callScannerApi.mockResolvedValue({ ok: true });
    const user = userEvent.setup();
    render(
      <MemberAdministration
        members={[
          {
            id: ID_B,
            user_id: ID_A,
            email: "member@corp.test",
            display_name: "Member",
            role: "viewer",
          },
        ]}
      />,
    );
    await user.type(screen.getByLabelText("Account email"), "new@corp.test");
    await user.selectOptions(screen.getByLabelText("Initial role"), "analyst");
    await user.click(screen.getByRole("button", { name: "Add member" }));
    await waitFor(() =>
      expect(callScannerApi).toHaveBeenCalledWith(
        "POST",
        "organization-members",
        {
          email: "new@corp.test",
          role: "analyst",
        },
      ),
    );
    await user.selectOptions(
      screen.getByLabelText("Role for Member"),
      "reviewer",
    );
    await waitFor(() =>
      expect(callScannerApi).toHaveBeenCalledWith(
        "PATCH",
        `organization-members/${ID_B}`,
        { role: "reviewer" },
      ),
    );
  });
});
