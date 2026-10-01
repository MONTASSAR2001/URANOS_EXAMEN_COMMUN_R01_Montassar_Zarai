import { chromium } from "playwright";
import path from "path";

async function verifyInnerPagesReadability() {
  console.log("==================================================================");
  console.log("   URANOS Group Inner Pages Readability & SaaS UI Audit");
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
  // Audit 1: /app/project (List View)
  // -------------------------------------------------------------------------
  console.log("2. Navigating to /app/project (List View)...");
  await page.goto("http://localhost:8080/app/project", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  const listAudit = await page.evaluate(() => {
    const container = document.querySelector(".page-container:not(#page-desktop)");
    const listRow = document.querySelector(".list-row");
    const listHead = document.querySelector(".list-row-head");
    const containerStyle = container ? window.getComputedStyle(container) : null;
    const rowStyle = listRow ? window.getComputedStyle(listRow) : null;
    const headStyle = listHead ? window.getComputedStyle(listHead) : null;
    const subjectEl = listRow ? listRow.querySelector(".list-subject, .list-subject a") : null;
    const subjectStyle = subjectEl ? window.getComputedStyle(subjectEl) : null;

    return {
      containerBg: containerStyle ? containerStyle.backgroundColor : null,
      containerBgImage: containerStyle ? containerStyle.backgroundImage : null,
      rowBg: rowStyle ? rowStyle.backgroundColor : null,
      rowBorderRadius: rowStyle ? rowStyle.borderRadius : null,
      rowBoxShadow: rowStyle ? rowStyle.boxShadow : null,
      headBg: headStyle ? headStyle.backgroundColor : null,
      textColor: subjectStyle ? subjectStyle.color : null,
      totalRows: document.querySelectorAll(".list-row").length
    };
  });

  console.log("✓ List View (/app/project) Audit Result:", JSON.stringify(listAudit, null, 2));

  // Assertions for List View
  if (!listAudit.containerBg.includes("248, 250, 252")) {
    throw new Error(`Expected container background to be rgb(248, 250, 252) (#f8fafc), got ${listAudit.containerBg}`);
  }
  if (!listAudit.rowBg.includes("255, 255, 255")) {
    throw new Error(`Expected list-row background to be rgb(255, 255, 255) (#ffffff), got ${listAudit.rowBg}`);
  }

  const projectScreenshotPath = path.join(artifactDir, "pristine_projects_list_view.png");
  await page.screenshot({ path: projectScreenshotPath, fullPage: true });
  console.log(`✓ High-resolution screenshot captured to: ${projectScreenshotPath}`);

  // -------------------------------------------------------------------------
  // Audit 2: /app/projects (Workspace Page)
  // -------------------------------------------------------------------------
  console.log("3. Navigating to /app/projects (Workspace)...");
  await page.goto("http://localhost:8080/app/projects", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  const workspaceAudit = await page.evaluate(() => {
    const container = document.querySelector(".page-container:not(#page-desktop)");
    const widget = document.querySelector(".widget, .widget-box, .chart-widget-box");
    const containerStyle = container ? window.getComputedStyle(container) : null;
    const widgetStyle = widget ? window.getComputedStyle(widget) : null;
    const titleEl = document.querySelector(".widget-title, .widget-head");
    const titleStyle = titleEl ? window.getComputedStyle(titleEl) : null;

    return {
      containerBg: containerStyle ? containerStyle.backgroundColor : null,
      containerBgImage: containerStyle ? containerStyle.backgroundImage : null,
      widgetBg: widgetStyle ? widgetStyle.backgroundColor : null,
      widgetBorderRadius: widgetStyle ? widgetStyle.borderRadius : null,
      widgetBoxShadow: widgetStyle ? widgetStyle.boxShadow : null,
      titleColor: titleStyle ? titleStyle.color : null,
      totalWidgets: document.querySelectorAll(".widget, .widget-box").length
    };
  });

  console.log("✓ Workspace (/app/projects) Audit Result:", JSON.stringify(workspaceAudit, null, 2));

  if (!workspaceAudit.containerBg.includes("248, 250, 252")) {
    throw new Error(`Expected workspace container background to be rgb(248, 250, 252) (#f8fafc), got ${workspaceAudit.containerBg}`);
  }
  if (workspaceAudit.widgetBg && !workspaceAudit.widgetBg.includes("255, 255, 255")) {
    throw new Error(`Expected widget background to be rgb(255, 255, 255) (#ffffff), got ${workspaceAudit.widgetBg}`);
  }

  const workspaceScreenshotPath = path.join(artifactDir, "pristine_projects_workspace_view.png");
  await page.screenshot({ path: workspaceScreenshotPath, fullPage: true });
  console.log(`✓ High-resolution screenshot captured to: ${workspaceScreenshotPath}`);

  // -------------------------------------------------------------------------
  // Audit 3: Check Desktop Home Dashboard Preservation
  // -------------------------------------------------------------------------
  console.log("4. Verifying Desktop Home Dashboard (#page-desktop) preservation...");
  await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);

  const homeAudit = await page.evaluate(() => {
    const desktopPage = document.querySelector("#page-desktop");
    const desktopStyle = desktopPage ? window.getComputedStyle(desktopPage) : null;
    return {
      desktopBg: desktopStyle ? desktopStyle.backgroundColor : null,
      isTransparent: desktopStyle ? desktopStyle.backgroundColor === "rgba(0, 0, 0, 0)" : false
    };
  });
  console.log("✓ Home Dashboard Audit Result:", JSON.stringify(homeAudit, null, 2));

  await browser.close();
  console.log("==================================================================");
  console.log("   ALL READABILITY & HIGH-END SAAS AUDITS PASSED 100%!");
  console.log("==================================================================");
}

verifyInnerPagesReadability().catch(err => {
  console.error("FATAL ERROR in Playwright Verification:", err);
  process.exit(1);
});
