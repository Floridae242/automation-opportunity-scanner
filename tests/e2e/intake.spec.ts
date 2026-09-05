import { randomUUID } from "node:crypto";
import { expect, test } from "@playwright/test";

test("analyst captures a project, process, and intake draft end to end", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByRole("tab", { name: "Create account" }).click();
  await page.getByLabel("Email").fill(`m2.e2e.${randomUUID()}@scanner.test`);
  await page.getByLabel("Password").fill("e2e-strong-pass-123");
  await page.getByLabel("Your name").fill("M2 Analyst");
  await page.getByLabel("Organization name").fill("Intake Labs");
  await page.getByRole("button", { name: "Create organization" }).click();
  await expect(page).toHaveURL(/\/$/);

  await page
    .getByRole("link", { name: "Projects", exact: true })
    .first()
    .click();
  await expect(page).toHaveURL(/\/projects$/);
  await expect(
    page.getByRole("heading", { name: "No projects yet" }),
  ).toBeVisible();

  await page.getByLabel("Project name").fill("Billing operations");
  await page.getByRole("button", { name: "Create project" }).click();
  await expect(
    page.getByRole("link", { name: "Billing operations" }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Billing operations" }).click();

  await expect(
    page.getByRole("heading", { name: "No processes yet" }),
  ).toBeVisible();
  await page.getByLabel("Process name").fill("Post supplier invoices");
  await page.getByRole("button", { name: "Add process" }).click();
  await expect(page.getByText("intake needed")).toBeVisible();
  await page.getByRole("link", { name: "Post supplier invoices" }).click();

  await page
    .getByLabel("Workflow description")
    .fill(
      "Finance receives supplier invoices by email, keys them into SAP, then routes them for approval.",
    );
  await page.getByLabel("Frequency value").fill("60");
  await page.getByLabel("Frequency period").selectOption("week");
  await page.getByRole("button", { name: "Save intake draft" }).click();
  await expect(
    page.getByText("Intake saved as a new draft version."),
  ).toBeVisible();

  await expect(page.getByText("v1", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Finance receives supplier invoices by email"),
  ).toBeVisible();
  await expect(page.getByText("60 per week")).toBeVisible();
  await expect(page.getByText("Not provided").first()).toBeVisible();

  await page.reload();
  await expect(page.getByText("draft", { exact: true }).first()).toBeVisible();
});
