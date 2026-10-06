import { expect, test } from "@playwright/test";

test.describe("Vault Lovelace Dashboard Cards Browser Tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/test/browser/fixture.html");
    await page.waitForFunction(
      () => (window as unknown as { fixtureReady?: boolean }).fixtureReady === true
    );
  });

  test("defines all custom card elements without template corruption", async ({ page }) => {
    const defined = await page.evaluate(() => {
      const tags = [
        "vault-health-card",
        "vault-protected-card",
        "vault-next-run-card",
        "vault-last-backup-card",
        "vault-progress-card",
        "vault-jobs-card",
        "vault-activity-card",
        "vault-storage-card",
        "vault-rules-card",
        "vault-anomalies-card",
        "vault-dashboard-card",
      ];
      return tags.every((t) => Boolean(customElements.get(t)));
    });
    expect(defined).toBe(true);

    // Verify NO raw Lit placeholder markers or leaked attribute syntax exist in DOM
    const rawLitMarkers = await page.evaluate(() => {
      const allText = document.body.innerText;
      return allText.includes("lit$") || allText.includes("@click=") || allText.includes(".style=");
    });
    expect(rawLitMarkers).toBe(false);
  });

  test("renders Health Score Card with score ring and status", async ({ page }) => {
    const card = page.locator("#health-card");
    await expect(card).toBeVisible();
    await expect(card.getByText("Health Score")).toBeVisible();
    await expect(card.getByText("100")).toBeVisible();
    await expect(card.getByText("All backups healthy")).toBeVisible();
  });

  test("renders Protected Items Card with coverage and progress bar", async ({ page }) => {
    const card = page.locator("#protected-card");
    await expect(card).toBeVisible();
    await expect(card.locator(".header-tag")).toHaveText("Protected");
    await expect(card.locator(".kpi-value")).toContainText("2");
    await expect(card.locator(".kpi-unit")).toContainText("/3");
  });

  test("renders Next Run Card with scheduled job info", async ({ page }) => {
    const card = page.locator("#next-run-card");
    await expect(card).toBeVisible();
    await expect(card.locator(".header-tag")).toHaveText("Next Run");
    await expect(card.getByText("Scheduled")).toBeVisible();
    await expect(card.getByText("Daily Containers Backup")).toBeVisible();
  });

  test("renders Last Backup Card with success badge and size/duration", async ({ page }) => {
    const card = page.locator("#last-backup-card");
    await expect(card).toBeVisible();
    await expect(card.locator(".header-tag")).toHaveText("Last Backup");
    await expect(card.getByText("Success")).toBeVisible();
  });

  test("renders Backup In Progress Card in idle state", async ({ page }) => {
    const card = page.locator("#progress-card");
    await expect(card).toBeVisible();
    await expect(card.locator(".header-tag")).toHaveText("Backup In Progress");
    await expect(card.getByText("No backup running")).toBeVisible();
  });

  test("renders Backup Jobs Card with action buttons", async ({ page }) => {
    const card = page.locator("#jobs-card");
    await expect(card).toBeVisible();
    await expect(card.locator(".header-tag")).toHaveText("Backup Jobs");
    await expect(card.getByText("Daily Containers Backup")).toBeVisible();
    await expect(card.getByText("Home Assistant Backup")).toBeVisible();

    const runNowButtons = card.getByText("Run Now");
    await expect(runNowButtons.first()).toBeVisible();

    await runNowButtons.first().click();
    const lastCall = await page.evaluate(
      () =>
        (
          window as unknown as {
            lastServiceCall?: { domain: string; service: string; data: Record<string, unknown> };
          }
        ).lastServiceCall
    );
    expect(lastCall).toEqual({
      domain: "button",
      service: "press",
      data: { entity_id: "button.vault_backup_daily_containers_backup_run_now" },
    });

    const restoreButtons = card.getByText("Restore");
    await expect(restoreButtons.first()).toBeVisible();
  });

  test("renders Recent Activity Card with item check chips", async ({ page }) => {
    const card = page.locator("#activity-card");
    await expect(card).toBeVisible();
    await expect(card.locator(".header-tag")).toHaveText("Recent Activity");
    await expect(card.getByText("completed").first()).toBeVisible();
  });

  test("renders Storage Card with capacity usage and health", async ({ page }) => {
    const card = page.locator("#storage-card");
    await expect(card).toBeVisible();
    await expect(card.locator(".header-tag")).toHaveText("Storage Destinations");
    await expect(card.getByText("Backups")).toBeVisible();
    await expect(card.getByText("Healthy")).toBeVisible();
  });

  test("renders 3-2-1 Rule Compliance Card", async ({ page }) => {
    const card = page.locator("#rules-card");
    await expect(card).toBeVisible();
    await expect(card.locator(".header-tag")).toHaveText("3-2-1 Backup Rule");
    await expect(card.getByText("3 Copies")).toBeVisible();
    await expect(card.getByText("2 Media")).toBeVisible();
    await expect(card.getByText("1 Offsite")).toBeVisible();
  });

  test("renders Anomalies Card with clear status", async ({ page }) => {
    const card = page.locator("#anomalies-card");
    await expect(card).toBeVisible();
    await expect(card.locator(".header-tag")).toHaveText("Anomalies & Attention");
    await expect(card.getByText("No open anomalies")).toBeVisible();
  });

  test("renders Unified Dashboard Card with embedded sub-cards", async ({ page }) => {
    const card = page.locator("#dashboard-card");
    await expect(card).toBeVisible();
    await expect(card.locator(".header-title").first()).toBeVisible();
    await expect(card.getByText("Online")).toBeVisible();

    await expect(card.locator("vault-health-card")).toBeVisible();
    await expect(card.locator("vault-protected-card")).toBeVisible();
    await expect(card.locator("vault-next-run-card")).toBeVisible();
    await expect(card.locator("vault-last-backup-card")).toBeVisible();
    await expect(card.locator("vault-jobs-card")).toBeVisible();
    await expect(card.locator("vault-storage-card")).toBeVisible();
  });
});
