import { expect, test } from "@playwright/test";

// Recruiter main flow (§B.8.1): pick archetype → generate → watch the live
// graph → per-platform result → ingest own data → run the learning cycle.
// Screenshots feed EXAMPLES.md (PS-G3).

const SHOT = (name: string) => `../docs/screenshots/${name}`;

test("recruiter flow: archetype → generate → graph → result → ingest → learning", async ({
  page,
}) => {
  await page.goto("/");
  await expect(page.getByTestId("archetype-card-ai_engineer")).toBeVisible({
    timeout: 30_000,
  });
  await page.screenshot({ path: SHOT("01-home-archetypes.png"), fullPage: true });

  await page.getByTestId("archetype-card-ai_engineer").click();
  await expect(page.getByTestId("topic-input")).toBeVisible({ timeout: 30_000 });

  await page.getByTestId("topic-input").fill("Why typed Python saves LLM systems");
  await page.getByTestId("generate-button").click();

  await expect(page.getByTestId("generated-post-preview")).toBeVisible({
    timeout: 90_000,
  });
  await expect(page.getByTestId("agent-node-finalizer")).toHaveAttribute(
    "data-status",
    "done",
  );
  await page.screenshot({ path: SHOT("02-live-graph-result.png"), fullPage: true });

  for (const platform of ["telegram", "x", "linkedin", "medium", "threads"]) {
    await expect(page.getByTestId(`tab-${platform}`)).toBeVisible();
  }
  await page.getByTestId("tab-linkedin").click();
  await expect(page.getByTestId("platform-panel")).toBeVisible();

  await page
    .getByTestId("ingest-text")
    .fill("Manually added post from the e2e smoke: typed Python everywhere.");
  await page.getByTestId("ingest-views").fill("1200");
  await page.getByTestId("ingest-likes").fill("90");
  await page.getByTestId("ingest-submit").click();
  await expect(page.getByTestId("ingest-success")).toBeVisible({ timeout: 20_000 });
  await page.screenshot({ path: SHOT("03-data-ingest.png"), fullPage: true });

  await page.getByTestId("learning-run").click();
  await expect(page.getByTestId("learning-results")).toBeVisible({ timeout: 60_000 });
  // RU is the default interface language after the redesign.
  await expect(page.getByTestId("learning-results")).toContainText(
    "добавлено в этой сессии",
  );
  await page.screenshot({ path: SHOT("04-learning-cycle.png"), fullPage: true });
});
