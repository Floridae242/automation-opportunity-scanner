import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import StatusPage from "@/app/status/page";

const response = (live: string, ready: string) => ({
  ok: true,
  json: async () => ({ live, ready }),
});

describe("workspace status", () => {
  it("checks current services and reports healthy infrastructure honestly", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(response("available", "available"));
    vi.stubGlobal("fetch", fetchMock);
    render(<StatusPage />);
    expect(
      screen.getByRole("button", { name: "Checking services…" }),
    ).toBeDisabled();
    expect(await screen.findByText("Services are available")).toBeVisible();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/system-status",
      expect.objectContaining({ cache: "no-store" }),
    );
    expect(
      screen.getByText(/does not prove that every external AI provider/i),
    ).toBeVisible();
  });

  it("offers a retry after an unavailable service and recovers", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(response("available", "unavailable"))
        .mockResolvedValueOnce(response("available", "available")),
    );
    render(<StatusPage />);
    expect(
      await screen.findByText("Some services need attention"),
    ).toBeVisible();
    await userEvent.click(screen.getByRole("button", { name: "Check again" }));
    expect(await screen.findByText("Services are available")).toBeVisible();
  });

  it.each([
    [
      "network failure",
      () => Promise.reject(new Error("private server detail")),
    ],
    ["http failure", () => Promise.resolve({ ok: false })],
    [
      "malformed response",
      () =>
        Promise.resolve({ ok: true, json: async () => ({ live: "secret" }) }),
    ],
  ])("shows safe recovery for %s", async (_label, implementation) => {
    vi.stubGlobal("fetch", vi.fn().mockImplementation(implementation));
    render(<StatusPage />);
    expect(await screen.findByText("Unable to check services")).toBeVisible();
    expect(screen.queryByText(/private server detail/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Check again" })).toBeEnabled();
  });

  it("stops updates when leaving the page", async () => {
    const fetchMock = vi.fn(
      (_url, options) =>
        new Promise((_resolve, reject) => {
          options.signal.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          );
        }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const { unmount } = render(<StatusPage />);
    unmount();
    await waitFor(() =>
      expect(fetchMock.mock.calls[0][1].signal.aborted).toBe(true),
    );
  });
});
