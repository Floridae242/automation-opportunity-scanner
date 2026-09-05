import { expect, test } from "@playwright/test";

test("workspace preview leads to guide and live service status", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("main")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.getByRole("link", { name: "Assessment guide", exact: true }).first().click();
  await expect(page).toHaveURL(/\/guide$/);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  await page.getByRole("link", { name: "Workspace status", exact: true }).first().click();
  await expect(page).toHaveURL(/\/status$/);
  await expect(page.getByText("Ready", { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: /check again|refresh|retry/i }).click();
  await expect(page.getByText("Ready", { exact: true }).first()).toBeVisible();
});

test("layout fits narrow screens without losing content", async ({ page }) => {
  await page.goto("/");
  const overflows = await page.evaluate(() =>
    document.documentElement.scrollWidth > window.innerWidth,
  );
  expect(overflows).toBe(false);
  await page.keyboard.press("Tab");
  await expect(page.getByRole("link", { name: "Skip to content" })).toBeFocused();
});
