import { chromium } from "playwright";
import path from "path";

async function verifyUnifiedSaaSTable() {
  console.log("==================================================================");
  console.log("   URANOS Group Unified SaaS Table (Stripe/Linear) Audit");
  console.log("==================================================================");

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  const page = await context.newPage();

  page.on("console", msg => {
    if (msg.type() === "error") {
      console.log(`[BROWSER ERROR] ${msg.text()}`);
    }
  });

  console.log("1. Authenticating as Administrator...");
  await page.goto("http://localhost:8080/login", { waitUntil: "networkidle" });
  await page.fill("#loginEmail", "Administrator");
  await page.fill("#loginPassword", "Password123!");
  await page.click("#btnContinue");
  await page.waitForURL(/\/app|\/desk/, { timeout: 15000 });
  console.log("✓ Logged in successfully!");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";

  // -------------------------------------------------------------------------
  // Audit 1: /app/project (Unified SaaS Table)
  // -------------------------------------------------------------------------
  console.log("2. Navigating to /app/project (List View)...");
  await page.goto("http://localhost:8080/app/project", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  const tableAudit = await page.evaluate(() => {
    const filterBar = document.querySelector(".frappe-list .page-form");
    const tableCard = document.querySelector(".frappe-list .result");
    const headRow = document.querySelector(".frappe-list .list-row-head");
    const firstRowContainer = document.querySelector(".frappe-list .list-row-container");
    const firstRow = document.querySelector(".frappe-list .list-row");
    const subjectEl = firstRow ? firstRow.querySelector(".list-subject, .list-subject a") : null;
    const headerMeta = headRow ? headRow.querySelector(".list-header-meta, .list-row-col, span") : null;

    const filterStyle = filterBar ? window.getComputedStyle(filterBar) : null;
    const cardStyle = tableCard ? window.getComputedStyle(tableCard) : null;
    const headStyle = headRow ? window.getComputedStyle(headRow) : null;
    const rowContainerStyle = firstRowContainer ? window.getComputedStyle(firstRowContainer) : null;
    const rowStyle = firstRow ? window.getComputedStyle(firstRow) : null;
    const subjectStyle = subjectEl ? window.getComputedStyle(subjectEl) : null;
    const headMetaStyle = headerMeta ? window.getComputedStyle(headerMeta) : null;

    return {
      filterBg: filterStyle ? filterStyle.backgroundColor : null,
      filterBorderRadius: filterStyle ? filterStyle.borderRadius : null,
      cardBg: cardStyle ? cardStyle.backgroundColor : null,
      cardBorder: cardStyle ? cardStyle.border : null,
      cardBorderRadius: cardStyle ? cardStyle.borderRadius : null,
      cardBoxShadow: cardStyle ? cardStyle.boxShadow : null,
      headBg: headStyle ? headStyle.backgroundColor : null,
      headBorderBottom: headStyle ? headStyle.borderBottom : null,
      headColor: headMetaStyle ? headMetaStyle.color : null,
      headTextTransform: headMetaStyle ? headMetaStyle.textTransform : null,
      rowMargin: rowStyle ? rowStyle.margin : null,
      rowPadding: rowStyle ? rowStyle.padding : null,
      rowBoxShadow: rowStyle ? rowStyle.boxShadow : null,
      rowContainerBorderBottom: rowContainerStyle ? rowContainerStyle.borderBottom : null,
      subjectColor: subjectStyle ? subjectStyle.color : null,
      subjectFontSize: subjectStyle ? subjectStyle.fontSize : null,
      totalRows: document.querySelectorAll(".frappe-list .list-row").length
    };
  });

  console.log("✓ Unified SaaS Table Audit Result:", JSON.stringify(tableAudit, null, 2));

  // Assertions for Unified Table Card
  if (!tableAudit.cardBg || !tableAudit.cardBg.includes("255, 255, 255")) {
    throw new Error(`Expected unified table card background to be white, got ${tableAudit.cardBg}`);
  }
  if (!tableAudit.cardBorderRadius || !tableAudit.cardBorderRadius.includes("12px")) {
    throw new Error(`Expected card border radius to be 12px, got ${tableAudit.cardBorderRadius}`);
  }
  if (tableAudit.rowBoxShadow && tableAudit.rowBoxShadow !== "none") {
    throw new Error(`Expected individual row box-shadow to be "none" (unified card), got ${tableAudit.rowBoxShadow}`);
  }

  const projectScreenshotPath = path.join(artifactDir, "refined_projects_unified_table.png");
  await page.screenshot({ path: projectScreenshotPath, fullPage: true });
  console.log(`✓ High-resolution screenshot captured to: ${projectScreenshotPath}`);

  // -------------------------------------------------------------------------
  // Audit 2: /app/projects (Workspace Page)
  // -------------------------------------------------------------------------
  console.log("3. Navigating to /app/projects (Workspace)...");
  await page.goto("http://localhost:8080/app/projects", { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);

  const workspaceScreenshotPath = path.join(artifactDir, "refined_projects_workspace_view.png");
  await page.screenshot({ path: workspaceScreenshotPath, fullPage: true });
  console.log(`✓ High-resolution screenshot captured to: ${workspaceScreenshotPath}`);

  await browser.close();
  console.log("==================================================================");
  console.log("   ALL UNIFIED SAAS TABLE AUDITS & VERIFICATIONS PASSED 100%!");
  console.log("==================================================================");
}

verifyUnifiedSaaSTable().catch(err => {
  console.error("FATAL ERROR in Playwright Verification:", err);
  process.exit(1);
});
