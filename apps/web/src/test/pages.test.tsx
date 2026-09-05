import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Overview from "@/app/page";
import Guide from "@/app/guide/page";
import { AppShell } from "@/components/app-shell";

vi.mock("next/navigation", () => ({ usePathname: () => "/guide" }));

describe("foundation workspace", () => {
  it("provides working destinations and identifies the active page", () => {
    render(
      <AppShell>
        <p>Page content</p>
      </AppShell>,
    );
    expect(
      screen.getByRole("link", { name: "Assessment guide" }),
    ).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Overview" })).toHaveAttribute(
      "href",
      "/",
    );
    expect(
      screen.getByRole("link", { name: "Workspace status" }),
    ).toHaveAttribute("href", "/status");
    expect(screen.getByRole("main")).toHaveTextContent("Page content");
  });

  it("shows a truthful preview with a clearly illustrative workflow", () => {
    render(<Overview />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Make the process clear.",
    );
    expect(
      screen.getByRole("heading", { name: "How assessment works" }),
    ).toBeVisible();
    expect(screen.getByText("No assessments yet")).toBeVisible();
    expect(
      screen.getByRole("link", { name: /Read the assessment guide/ }),
    ).toHaveAttribute("href", "/guide");
    expect(
      screen.queryByRole("button", { name: /new assessment/i }),
    ).not.toBeInTheDocument();
  });

  it("explains evidence, review, and unknown values before assessment", () => {
    render(<Guide />);
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Start with the work.",
    );
    expect(
      screen.getByText(/unknown values stay “Not provided”/i),
    ).toBeVisible();
    expect(
      screen.getByRole("heading", { name: "Review before you prioritize" }),
    ).toBeVisible();
    expect(
      screen.getByRole("link", { name: /View workspace status/ }),
    ).toHaveAttribute("href", "/status");
  });
});
