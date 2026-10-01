import { chromium } from "playwright";
import path from "path";

async function verifyDistinctInnerViews() {
  console.log("==================================================================");
  console.log("   URANOS Group Distinct SaaS Inner Views Verification");
  console.log("==================================================================");

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 950 }
  });
  const page = await context.newPage();

  console.log("1. Authenticating as Administrator...");
  await page.goto("http://localhost:8080/login", { waitUntil: "networkidle" });
  await page.fill("#loginEmail", "Administrator");
  await page.fill("#loginPassword", "Password123!");
  await page.click("#btnContinue");
  await page.waitForURL(/\/app|\/desk/, { timeout: 15000 });
  console.log("✓ Logged in successfully!");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";

  // -------------------------------------------------------------------------
  // TEST VIEW 1: Work Packages — Engineering Milestone & Physical Progress
  // -------------------------------------------------------------------------
  console.log("2. Navigating to Work Packages (/app/uranos-work-package)...");
  await page.goto("http://localhost:8080/app/uranos-work-package", { waitUntil: "networkidle" });
  await page.waitForSelector(".uranos-chic-saas-view[data-module='work-packages']", { timeout: 10000 });
  await page.waitForTimeout(1500);

  const wpAudit = await page.evaluate(() => {
    const root = document.querySelector(".uranos-chic-saas-view[data-module='work-packages']");
    const title = root?.querySelector(".uranos-saas-title-group h2")?.innerText;
    const cards = Array.from(root?.querySelectorAll(".uranos-wp-milestone-card") || []).map(card => ({
      code: card.querySelector(".uranos-wp-code")?.innerText,
      title: card.querySelector(".uranos-wp-card-title")?.innerText,
      discipline: card.querySelector(".uranos-wp-discipline")?.innerText,
      scope: card.querySelector(".s-planned")?.innerText,
      weightPct: card.querySelector(".m-pct")?.innerText,
      hasProgressBar: !!card.querySelector(".uranos-wp-progress-bar"),
      hasReadinessGates: card.querySelectorAll(".uranos-wp-gate").length
    }));
    const kpis = Array.from(root?.querySelectorAll(".uranos-saas-kpi-tile") || []).map(tile => ({
      label: tile.querySelector(".kpi-label")?.innerText,
      val: tile.querySelector(".kpi-value")?.innerText
    }));

    return {
      moduleFound: !!root,
      title,
      kpis,
      cardsCount: cards.length,
      cards
    };
  });

  console.log("✓ Work Packages Audit Result:", JSON.stringify(wpAudit, null, 2));

  if (!wpAudit.moduleFound) throw new Error("Work Packages SaaS view not found!");
  if (wpAudit.cardsCount < 3) throw new Error(`Expected at least 3 real work packages, got ${wpAudit.cardsCount}`);
  if (!wpAudit.cards.some(c => c.code === "WP-CIV-01" || c.code === "WP-MEC-03")) {
    throw new Error("Expected real work package codes from MariaDB not found!");
  }

  const wpScreenshot = path.join(artifactDir, "verified_work_packages_milestone_tracker.png");
  await page.screenshot({ path: wpScreenshot, fullPage: true });
  console.log(`✓ Work Packages full-page screenshot saved to: ${wpScreenshot}`);

  // -------------------------------------------------------------------------
  // TEST VIEW 2: Daily Site Reports — Chronological Field Journal & Logbook
  // -------------------------------------------------------------------------
  console.log("3. Navigating to Daily Site Reports (/app/uranos-daily-site-report)...");
  await page.goto("http://localhost:8080/app/uranos-daily-site-report", { waitUntil: "networkidle" });
  await page.waitForSelector(".uranos-chic-saas-view[data-module='daily-reports']", { timeout: 10000 });
  await page.waitForTimeout(1500);

  const reportAudit = await page.evaluate(() => {
    const root = document.querySelector(".uranos-chic-saas-view[data-module='daily-reports']");
    const title = root?.querySelector(".uranos-saas-title-group h2")?.innerText;
    const cards = Array.from(root?.querySelectorAll(".uranos-report-journal-card") || []).map(card => ({
      reportId: card.querySelector(".uranos-report-code")?.innerText,
      projectTag: card.querySelector(".uranos-report-project-tag")?.innerText,
      dateMonth: card.querySelector(".cal-month")?.innerText,
      dateDay: card.querySelector(".cal-day")?.innerText,
      dateYear: card.querySelector(".cal-year")?.innerText,
      status: card.querySelector(".uranos-saas-badge")?.innerText,
      hasExcerpt: !!card.querySelector(".uranos-report-excerpt"),
      conditionsCount: card.querySelectorAll(".condition-pill").length,
      hasActionBtn: !!card.querySelector(".uranos-report-btn")
    }));
    const kpis = Array.from(root?.querySelectorAll(".uranos-saas-kpi-tile") || []).map(tile => ({
      label: tile.querySelector(".kpi-label")?.innerText,
      val: tile.querySelector(".kpi-value")?.innerText
    }));

    return {
      moduleFound: !!root,
      title,
      kpis,
      reportsCount: cards.length,
      cards
    };
  });

  console.log("✓ Daily Reports Audit Result:", JSON.stringify(reportAudit, null, 2));

  if (!reportAudit.moduleFound) throw new Error("Daily Site Reports SaaS view not found!");
  if (reportAudit.reportsCount < 2) throw new Error(`Expected at least 2 real reports, got ${reportAudit.reportsCount}`);
  if (!reportAudit.cards.some(c => c.reportId?.includes("ev35q1bgic") || c.reportId?.includes("ev4okkj1kf"))) {
    throw new Error("Expected real daily report IDs from MariaDB not found!");
  }

  const reportScreenshot = path.join(artifactDir, "verified_daily_site_reports_journal_feed.png");
  await page.screenshot({ path: reportScreenshot, fullPage: true });
  console.log(`✓ Daily Reports full-page screenshot saved to: ${reportScreenshot}`);

  await browser.close();
  console.log("==================================================================");
  console.log("   ALL DISTINCT INNER VIEWS VERIFIED SUCCESSFULLY 100%!");
  console.log("==================================================================");
}

verifyDistinctInnerViews().catch(err => {
  console.error("FATAL ERROR in Views Verification:", err);
  process.exit(1);
});
