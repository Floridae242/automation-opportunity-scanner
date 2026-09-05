import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { parseProject, parseProjectList } from "./contract";
import { formatMetricValue, parseMetricsInput } from "./client-api";
import { IntakeForm } from "./intake-form";
import { ProjectCreateForm } from "./workspace-forms";

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
});
