import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { parseVersionDetail } from "./contract";
import { ExtractionPanel } from "./extraction-panel";
import { StepReviewEditor } from "./step-review";

vi.mock("next/navigation", () => ({
  usePathname: () => "/processes/x",
  useRouter: () => ({ replace: vi.fn(), refresh: vi.fn(), push: vi.fn() }),
}));

const VERSION_ID = "6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f";
const PROCESS_ID = "1b2c3d4e-5f60-41a2-93b4-c5d6e7f80911";
const STEP_ID = "9c8b7a65-4321-4fed-cba9-876543210fed";

const detail = {
  id: VERSION_ID,
  process_id: PROCESS_ID,
  version_no: 2,
  review_status: "draft",
  source_summary: "AI extraction draft (analysis x)",
  steps: [
    {
      step_id: STEP_ID,
      step_key: "S1",
      sequence_no: 1,
      name: "Receive invoices",
      actor: null,
      system: null,
      manual: null,
      duration_minutes: null,
      evidence_refs: ["intake"],
    },
  ],
  evidence: [
    {
      source_ref: "intake",
      excerpt: "Finance receives supplier invoices.",
      confidence: "medium",
    },
  ],
};

describe("version detail contract", () => {
  it("accepts server payloads and rejects forged step keys", () => {
    expect(parseVersionDetail(detail)?.steps[0].step_key).toBe("S1");
    expect(
      parseVersionDetail({
        ...detail,
        steps: [{ ...detail.steps[0], step_key: "DROP TABLE" }],
      }),
    ).toBeNull();
    expect(
      parseVersionDetail({ ...detail, review_status: "approved" }),
    ).toBeNull();
  });
});

describe("extraction panel", () => {
  it("starts an analysis and reports the running state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 202,
        json: async () => ({ analysis_id: "a1", status: "queued" }),
      }),
    );
    render(<ExtractionPanel processId={PROCESS_ID} />);
    await userEvent.click(
      screen.getByRole("button", { name: "Run extraction" }),
    );
    expect(await screen.findByText(/Analysis is queued/i)).toBeVisible();
  });

  it("shows the safe failure copy and offers a retry", async () => {
    vi.useRealTimers();
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 202,
        json: async () => ({ analysis_id: "a2", status: "queued" }),
      })
      .mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          analysis_id: "a2",
          status: "failed",
          error_code: "AI_SCHEMA_INVALID",
          draft_version_id: null,
        }),
      });
    vi.stubGlobal("fetch", fetchMock);
    render(<ExtractionPanel processId={PROCESS_ID} />);
    await userEvent.click(
      screen.getByRole("button", { name: "Run extraction" }),
    );
    expect(
      await screen.findByText(/rejected by validation/i, {}, { timeout: 4000 }),
    ).toBeVisible();
    expect(
      screen.getByRole("button", { name: "Retry extraction" }),
    ).toBeEnabled();
  });
});

describe("step review editor", () => {
  beforeEach(() => vi.resetAllMocks());

  it("sends analyst corrections for edited fields only", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", fetchMock);
    render(<StepReviewEditor version={detail as never} />);
    await userEvent.clear(screen.getByLabelText("Step S1 name"));
    await userEvent.type(
      screen.getByLabelText("Step S1 name"),
      "Collect invoices from email",
    );
    await userEvent.type(
      screen.getByPlaceholderText("Actor — not provided"),
      "Finance team",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Save corrections" }),
    );
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`/api/scanner/process-versions/${VERSION_ID}`);
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(init.body).steps[0]).toMatchObject({
      step_key: "S1",
      name: "Collect invoices from email",
      actor: "Finance team",
    });
    expect(JSON.parse(init.body).steps[0]).not.toHaveProperty(
      "duration_minutes",
    );
  });

  it("marks a reviewed version read-only", () => {
    render(
      <StepReviewEditor
        version={{ ...detail, review_status: "reviewed" } as never}
      />,
    );
    expect(screen.getByText("reviewed — immutable")).toBeVisible();
    expect(screen.getByLabelText("Step S1 name")).toBeDisabled();
    expect(
      screen.queryByRole("button", { name: "Mark reviewed" }),
    ).not.toBeInTheDocument();
  });

  it("confirms review through the review endpoint", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", fetchMock);
    render(<StepReviewEditor version={detail as never} />);
    await userEvent.click(
      screen.getByRole("button", { name: "Mark reviewed" }),
    );
    await vi.waitFor(() =>
      expect(fetchMock).toHaveBeenCalledWith(
        `/api/scanner/process-versions/${VERSION_ID}/review`,
        expect.objectContaining({ method: "POST" }),
      ),
    );
  });
});
