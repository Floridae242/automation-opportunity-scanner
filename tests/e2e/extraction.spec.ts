import { randomUUID } from "node:crypto";
import { expect, test } from "@playwright/test";

async function onboard(page) {
  await page.goto("/login");
  await page.getByRole("tab", { name: "Create account" }).click();
  await page.getByLabel("Email").fill(`m3.e2e.${randomUUID()}@scanner.test`);
  await page.getByLabel("Password").fill("e2e-strong-pass-123");
  await page.getByLabel("Your name").fill("M3 Analyst");
  await page.getByLabel("Organization name").fill("Extraction Labs");
  await page.getByRole("button", { name: "Create organization" }).click();
  await expect(page).toHaveURL(/\/$/);
  await page.goto("/projects");
  await page.getByLabel("Project name").fill("Order operations");
  await page.getByRole("button", { name: "Create project" }).click();
  await page.getByRole("link", { name: "Order operations" }).click();
  await page.getByLabel("Process name").fill("Handle order changes");
  await page.getByRole("button", { name: "Add process" }).click();
  await page.getByRole("link", { name: "Handle order changes" }).click();
  await page
    .getByLabel("Workflow description")
    .fill(
      "Support receives a change request. Agents validate the order in ERP and confirm by email.",
    );
  await page.getByRole("button", { name: "Save intake draft" }).click();
  await expect(
    page.getByText("Intake saved as a new draft version."),
  ).toBeVisible();
}

test("intake flows into AI draft extraction, correction, and human review", async ({
  page,
}) => {
  await onboard(page);

  await page.getByRole("button", { name: "Run extraction" }).click();
  await expect(page.getByRole("button", { name: "Analyzing…" })).toBeVisible();

  // Review editor appears once the draft with steps lands (poll up to 10s).
  const stepOne = page.getByLabel("Step S1 name");
  await expect(stepOne).toBeVisible({ timeout: 10_000 });
  await expect(page.getByText("draft — editable")).toBeVisible();
  await expect(page.getByText(/evidence: intake/).first()).toBeVisible();

  await stepOne.fill("Receive change request from support queue");
  await page
    .getByPlaceholder("Actor — not provided")
    .first()
    .fill("Support agent");
  await page.getByRole("button", { name: "Save corrections" }).click();
  await expect(stepOne).toHaveValue(
    "Receive change request from support queue",
    { timeout: 10_000 },
  );

  await page.getByRole("button", { name: "Mark reviewed" }).click();
  await expect(page.getByText("reviewed").first()).toBeVisible({
    timeout: 10_000,
  });
});

test("source summary is preserved as intake history after extraction", async ({
  page,
}) => {
  await onboard(page);
  await page.getByRole("button", { name: "Run extraction" }).click();
  await expect(page.getByLabel("Step S1 name")).toBeVisible({
    timeout: 10_000,
  });
  await expect(
    page.getByText(/Source: “Support receives a change request/),
  ).toBeVisible();
});
