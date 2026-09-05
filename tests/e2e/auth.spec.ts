import { randomUUID } from "node:crypto";
import { expect, test } from "@playwright/test";

test("analyst can create an organization, see their identity, and sign out", async ({
  page,
}) => {
  const email = `m1.e2e.${randomUUID()}@scanner.test`;
  await page.goto("/login");
  await page.getByRole("tab", { name: "Create account" }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill("e2e-strong-pass-123");
  await page.getByLabel("Your name").fill("E2E Analyst");
  await page.getByLabel("Organization name").fill("Evidence Labs");
  await page.getByRole("button", { name: "Create organization" }).click();

  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByText("E2E Analyst")).toBeVisible();
  await expect(page.getByText("Evidence Labs · owner")).toBeVisible();

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(
    page.getByRole("heading", { name: /evidence stays yours/i }),
  ).toBeVisible();
});

test("wrong credentials show a safe error and keep the analyst on the page", async ({
  page,
}) => {
  await page.goto("/login");
  await page.getByLabel("Email").fill("nobody@scanner.test");
  await page.getByLabel("Password").fill("definitely-wrong-pass");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByText("Email or password is incorrect.")).toBeVisible();
  await expect(page).toHaveURL(/\/login$/);
});
