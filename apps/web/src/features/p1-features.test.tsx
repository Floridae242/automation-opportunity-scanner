import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { CommentsPanel } from "./intake/comments-panel";
import { VersionCompare } from "./intake/version-compare";
import { ScoringSettings } from "./portfolio/scoring-settings";

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
});
