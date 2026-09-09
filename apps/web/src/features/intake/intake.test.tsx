import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  parseProcess,
  parseProject,
  parseProjectList,
  parseVersion,
  parseVersionDetail,
} from "./contract";
import {
  callScannerApi,
  formatMetricValue,
  parseMetricsInput,
  uploadScannerFile,
} from "./client-api";
import { IntakeForm } from "./intake-form";
import { DocumentUpload } from "./document-upload";
import {
  ProcessCreateForm,
  ProjectActions,
  ProjectCreateForm,
} from "./workspace-forms";

vi.mock("next/navigation", () => ({
  usePathname: () => "/projects",
  useRouter: () => ({ replace: vi.fn(), refresh: vi.fn(), push: vi.fn() }),
}));

const project = {
  id: "6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f",
  name: "Claims",
  department: null,
  status: "active",
  process_count: 0,
  created_at: "2026-09-05T00:00:00Z",
  updated_at: "2026-09-05T00:00:00Z",
};

const version = {
  id: "7f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f",
  version_no: 1,
  review_status: "draft",
  source_summary: "A short workflow summary.",
  metrics: {},
  created_at: "2026-09-05T00:00:00Z",
};

describe("intake contract", () => {
  it("validates project payloads and rejects unknown shapes", () => {
    expect(parseProject(project)?.name).toBe("Claims");
    expect(parseProject({ ...project, status: "deleted" })).toBeNull();
    expect(parseProject({ ...project, processes: [{ id: "x" }] })).toBeNull();
    expect(parseProjectList([project])?.length).toBe(1);
    expect(parseProjectList("not-a-list")).toBeNull();
  });

  it("formats unknown metrics as Not provided, never zero", () => {
    expect(formatMetricValue(undefined)).toBe("Not provided");
    expect(formatMetricValue(null)).toBe("Not provided");
    expect(formatMetricValue({ value: 40, period: "week" })).toBe(
      "40 per week",
    );
    expect(formatMetricValue(["Outlook", "SAP"])).toBe("Outlook, SAP");
  });

  it("omits blank metrics instead of fabricating values", () => {
    const form = new FormData();
    form.set("frequency_value", "40");
    form.set("frequency_period", "week");
    form.set("systems", "Outlook, , SAP");
    form.set("error_rate", "");
    expect(parseMetricsInput(form)).toEqual({
      frequency: { value: 40, period: "week" },
      systems: ["Outlook", "SAP"],
    });
  });

  it("accepts complete valid metrics and drops invalid values", () => {
    const form = new FormData();
    form.set("frequency_value", "48");
    form.set("frequency_period", "month");
    form.set("duration_minutes", "12.5");
    form.set("error_rate", "0.25");
    form.set("rework_rate", "0.1");
    form.set("sla", `  ${"urgent ".repeat(40)} `);
    form.set("systems", "CRM, ERP");
    form.set("approvals_required", "2.9");
    form.set("sensitivity", "restricted");
    form.set("loaded_hourly_cost", "650");
    form.set("monthly_operating_cost", "1000");
    form.set("implementation_cost", "24000");
    form.set("currency", " thb ");
    const metrics = parseMetricsInput(form);
    expect(metrics).toMatchObject({
      frequency: { value: 48, period: "month" },
      duration_minutes: 12.5,
      error_rate: 0.25,
      rework_rate: 0.1,
      systems: ["CRM", "ERP"],
      approvals_required: 2,
      sensitivity: "restricted",
      loaded_hourly_cost: 650,
      monthly_operating_cost: 1000,
      implementation_cost: 24000,
      currency: "THB",
    });
    expect(metrics.sla).toHaveLength(200);

    const invalid = new FormData();
    invalid.set("frequency_value", "-2");
    invalid.set("frequency_period", "week");
    invalid.set("duration_minutes", "0");
    invalid.set("error_rate", "1.1");
    invalid.set("rework_rate", "not-a-number");
    invalid.set("approvals_required", "-1");
    invalid.set("sensitivity", "secret");
    invalid.set("currency", "thai");
    invalid.set("loaded_hourly_cost", "-1");
    expect(parseMetricsInput(invalid)).toEqual({});
  });

  it("validates nested process versions and version detail identifiers", () => {
    const process = {
      id: "8f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f",
      project_id: project.id,
      name: "Check claim",
      status: "active",
      versions: [version],
      latest_version: version,
    };
    expect(parseVersion(version)?.review_status).toBe("draft");
    expect(parseProcess(process)?.versions).toHaveLength(1);
    expect(parseVersion({ ...version, review_status: "approved" })).toBeNull();
    expect(parseProcess({ ...process, versions: [{ id: "bad" }] })).toBeNull();

    const detail = {
      id: version.id,
      process_id: process.id,
      version_no: 1,
      review_status: "reviewed",
      source_summary: version.source_summary,
      steps: [
        {
          step_id: "9f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f",
          step_key: "S1",
          sequence_no: 1,
          name: "Verify evidence",
          actor: "Agent",
          system: "CRM",
          manual: true,
          duration_minutes: 10,
          evidence_refs: ["E1"],
        },
      ],
      evidence: [],
      systems: [{ name: "CRM", integration_status: "evidence_of_api" }],
    };
    expect(parseVersionDetail(detail)?.steps[0]?.step_key).toBe("S1");
    expect(
      parseVersionDetail({
        ...detail,
        systems: [{ name: "CRM", integration_status: "invented" }],
      }),
    ).toBeNull();
    expect(
      parseVersionDetail({
        ...detail,
        steps: [{ ...detail.steps[0], step_key: "step-1" }],
      }),
    ).toBeNull();
  });

  it("uses safe API outcomes for GET, malformed failures, and network errors", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({ ok: true })
      .mockResolvedValueOnce({ ok: false, json: async () => ({}) })
      .mockRejectedValueOnce(new Error("offline"));
    vi.stubGlobal("fetch", fetchMock);
    await expect(callScannerApi("GET", "projects")).resolves.toEqual({
      ok: true,
    });
    await expect(
      callScannerApi("POST", "projects", { name: "Claims" }),
    ).resolves.toEqual({
      ok: false,
      message: "Something went wrong. Please try again.",
    });
    await expect(callScannerApi("PATCH", "projects/x")).resolves.toEqual({
      ok: false,
      message: "We could not reach the workspace service. Try again.",
    });
    expect(fetchMock.mock.calls[0][1]).toMatchObject({ method: "GET" });
    expect(fetchMock.mock.calls[0][1].headers).toBeUndefined();
    expect(fetchMock.mock.calls[1][1].headers).toEqual({
      "content-type": "application/json",
    });
  });

  it("uploads a selected file as multipart data without setting a JSON content type", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      uploadScannerFile(
        "processes/example/documents",
        new File(["evidence"], "notes.txt", { type: "text/plain" }),
      ),
    ).resolves.toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/scanner/processes/example/documents",
      expect.objectContaining({ method: "POST", body: expect.any(FormData) }),
    );
  });
});

describe("intake form", () => {
  beforeEach(() => vi.resetAllMocks());

  it("saves a draft through the scanner proxy and reports success", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({}) });
    vi.stubGlobal("fetch", fetchMock);
    render(<IntakeForm processId="6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f" />);
    await userEvent.type(
      screen.getByLabelText("Workflow description"),
      "Agents copy claim data between three systems.",
    );
    await userEvent.type(screen.getByLabelText("Duration (minutes)"), "25");
    await userEvent.click(
      screen.getByRole("button", { name: "Save intake draft" }),
    );
    expect(await screen.findByRole("status")).toHaveTextContent(
      "new draft version",
    );
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(
      "/api/scanner/processes/6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f/intake",
    );
    expect(JSON.parse(String(init.body))).toEqual({
      description: "Agents copy claim data between three systems.",
      metrics: { duration_minutes: 25 },
    });
  });

  it("shows the API message when saving fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({
          error: { message: "Please check the entered values." },
        }),
      }),
    );
    render(<IntakeForm processId="6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f" />);
    await userEvent.type(
      screen.getByLabelText("Workflow description"),
      "anything",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Save intake draft" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Please check the entered values.",
    );
  });

  it("uploads a chosen document and reports that it remains untrusted evidence", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true }));
    render(<DocumentUpload processId="6f1d0b3e-1a2b-4c5d-8e9f-0a1b2c3d4e5f" />);
    const form = screen.getByRole("form", { name: "Upload process document" });
    const input = screen.getByLabelText("Text or PDF, up to 1 MB");
    Object.defineProperty(input, "files", {
      configurable: true,
      value: [
        new File(["invoice evidence"], "invoice.txt", { type: "text/plain" }),
      ],
    });
    fireEvent.submit(form);
    expect(await screen.findByRole("status")).toHaveTextContent(
      "Document stored as untrusted evidence",
    );
  });
});

describe("project creation", () => {
  it("posts to the projects endpoint with trimmed optionality", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => project });
    vi.stubGlobal("fetch", fetchMock);
    render(<ProjectCreateForm />);
    await userEvent.type(
      screen.getByLabelText("Project name"),
      "Claims intake",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Create project" }),
    );
    await vi.waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(fetchMock.mock.calls[0][0]).toBe("/api/scanner/projects");
    expect(JSON.parse(String(fetchMock.mock.calls[0][1].body))).toEqual({
      name: "Claims intake",
      department: null,
    });
  });

  it("renames and archives a project through the typed proxy", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => project });
    vi.stubGlobal("fetch", fetchMock);
    render(
      <ProjectActions projectId={project.id} name="Claims" status="active" />,
    );
    const name = screen.getByLabelText("Rename project");
    await userEvent.clear(name);
    await userEvent.type(name, "Claims review");
    await userEvent.click(screen.getByRole("button", { name: "Rename" }));
    await userEvent.click(
      screen.getByRole("button", { name: "Archive project" }),
    );
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      `/api/scanner/projects/${project.id}`,
      `/api/scanner/projects/${project.id}`,
    ]);
    expect(JSON.parse(String(fetchMock.mock.calls[0][1].body))).toEqual({
      name: "Claims review",
    });
    expect(JSON.parse(String(fetchMock.mock.calls[1][1].body))).toEqual({
      status: "archived",
    });
  });

  it("shows safe errors when project and process creation are rejected", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        json: async () => ({ error: { message: "Name is already in use." } }),
      }),
    );
    const { rerender } = render(<ProjectCreateForm />);
    await userEvent.type(screen.getByLabelText("Project name"), "Claims");
    await userEvent.click(
      screen.getByRole("button", { name: "Create project" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "already in use",
    );
    rerender(<ProcessCreateForm projectId={project.id} />);
    await userEvent.type(screen.getByLabelText("Process name"), "Check claim");
    await userEvent.click(screen.getByRole("button", { name: "Add process" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "already in use",
    );
  });
});
