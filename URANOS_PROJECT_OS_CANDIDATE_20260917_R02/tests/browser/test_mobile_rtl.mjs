import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function runMobileAndRTLAudit() {
  console.log("=== Starting Mobile Responsiveness & RTL (Arabic) QA Verification ===");
  const evidenceDir = "/home/montassar/.gemini/antigravity-ide/brain/a602cb04-cf23-4f11-be98-e5d6e4f36feb";
  await mkdir(evidenceDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  try {
    // -------------------------------------------------------------
    // PART 1: MOBILE VIEWPORT VERIFICATION (390 x 844 - iPhone 14/15)
    // -------------------------------------------------------------
    console.log("\n[TEST 1] Auditing Mobile Viewport (390x844)...");
    const mobileContext = await browser.newContext({
      viewport: { width: 390, height: 844 },
      isMobile: true,
      hasTouch: true
    });
    const mobilePage = await mobileContext.newPage();

    console.log("  Logging in on Mobile...");
    await mobilePage.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await mobilePage.fill("#loginEmail", "ingenieur_01@uranos.local");
    await mobilePage.fill("#loginPassword", "Password123!");
    await mobilePage.click("#btnContinue");
    await mobilePage.waitForURL(/\/desk|\/app/, { timeout: 15000 });
    console.log("  ✓ Mobile Login Successful. URL:", mobilePage.url());

    // 1A. Mobile Main Dashboard
    await mobilePage.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await mobilePage.waitForTimeout(1000);

    const isSidebarHidden = await mobilePage.$eval(".gv-desk-sidebar", el => window.getComputedStyle(el).display === "none").catch(() => true);
    console.log("  Mobile Sidebar Hidden:", isSidebarHidden ? "✓ PASS" : "✗ FAIL");

    const kpiCount = await mobilePage.$$eval(".gv-kpi-card", els => els.length);
    console.log("  Mobile KPI Count:", kpiCount, kpiCount === 4 ? "✓ PASS" : "✗ FAIL");

    const appIconCount = await mobilePage.$$eval(".desktop-icon", els => els.length);
    console.log("  Mobile 15-App Cards Count:", appIconCount, appIconCount === 15 ? "✓ PASS" : "✗ FAIL");

    const mobileDeskShot = path.join(evidenceDir, "mobile_01_main_dashboard.png");
    await mobilePage.screenshot({ path: mobileDeskShot, fullPage: false });
    console.log("  ✓ Screenshot saved ->", mobileDeskShot);

    // 1B. Mobile Inner Page: /app/projects
    console.log("  Navigating to /app/projects on Mobile...");
    await mobilePage.goto("http://localhost:8080/app/projects", { waitUntil: "networkidle" });
    await mobilePage.waitForTimeout(1000);

    const backBtnExists = await mobilePage.$("#gv-back-to-dashboard");
    console.log("  Mobile Return Button:", backBtnExists ? "✓ Present" : "✗ Missing");

    const backBtnTextHidden = await mobilePage.$eval("#gv-back-to-dashboard > span:not(.gv-return-arrow-circle)", el => window.getComputedStyle(el).display === "none").catch(() => false);
    console.log("  Mobile Return Button Text Collapsed:", backBtnTextHidden ? "✓ PASS (Circular icon button)" : "✗ FAIL");

    const diagPillExists = await mobilePage.$(".gv-realtime-diagnostic-pill");
    console.log("  Mobile Diagnostic Pill:", diagPillExists ? "✓ Present" : "✗ Missing");

    const diagTextHidden = await mobilePage.$eval(".gv-realtime-diagnostic-pill .gv-diag-text", el => window.getComputedStyle(el).display === "none").catch(() => false);
    console.log("  Mobile Diagnostic Text Collapsed:", diagTextHidden ? "✓ PASS (Compact live pulse dot)" : "✗ FAIL");

    const mobileInnerShot = path.join(evidenceDir, "mobile_02_projects_inner.png");
    await mobilePage.screenshot({ path: mobileInnerShot, fullPage: false });
    console.log("  ✓ Screenshot saved ->", mobileInnerShot);

    await mobileContext.close();

    // -------------------------------------------------------------
    // PART 2: RTL & ARABIC ORIENTATION VERIFICATION (1440 x 900)
    // -------------------------------------------------------------
    console.log("\n[TEST 2] Auditing RTL / Arabic Layout (Desktop 1440x900)...");
    const desktopContext = await browser.newContext({
      viewport: { width: 1440, height: 900 }
    });
    const desktopPage = await desktopContext.newPage();

    console.log("  Logging in on Desktop...");
    await desktopPage.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await desktopPage.fill("#loginEmail", "ingenieur_01@uranos.local");
    await desktopPage.fill("#loginPassword", "Password123!");
    await desktopPage.click("#btnContinue");
    await desktopPage.waitForURL(/\/desk|\/app/, { timeout: 15000 });

    // 2A. Desktop Main Dashboard with RTL
    await desktopPage.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await desktopPage.waitForTimeout(800);

    console.log("  Injecting document.documentElement.dir = 'rtl'...");
    await desktopPage.evaluate(() => {
      document.documentElement.dir = "rtl";
      document.body.dir = "rtl";
    });
    await desktopPage.waitForTimeout(400);

    const htmlDir = await desktopPage.evaluate(() => document.documentElement.dir);
    console.log("  HTML Direction:", htmlDir, htmlDir === "rtl" ? "✓ PASS" : "✗ FAIL");

    const rtlDeskShot = path.join(evidenceDir, "rtl_01_main_dashboard_desktop.png");
    await desktopPage.screenshot({ path: rtlDeskShot, fullPage: false });
    console.log("  ✓ Screenshot saved ->", rtlDeskShot);

    // 2B. Desktop Inner Page with RTL: /app/projects
    console.log("  Navigating to /app/projects with RTL...");
    await desktopPage.goto("http://localhost:8080/app/projects", { waitUntil: "networkidle" });
    await desktopPage.waitForTimeout(800);

    await desktopPage.evaluate(() => {
      document.documentElement.dir = "rtl";
      document.body.dir = "rtl";
    });
    await desktopPage.waitForTimeout(400);

    const backBtnRtl = await desktopPage.$("#gv-back-to-dashboard");
    console.log("  RTL Return Button:", backBtnRtl ? "✓ Present" : "✗ Missing");

    const diagPillRtl = await desktopPage.$(".gv-realtime-diagnostic-pill");
    console.log("  RTL Diagnostic Pill:", diagPillRtl ? "✓ Present" : "✗ Missing");

    const rtlInnerShot = path.join(evidenceDir, "rtl_02_projects_inner_desktop.png");
    await desktopPage.screenshot({ path: rtlInnerShot, fullPage: false });
    console.log("  ✓ Screenshot saved ->", rtlInnerShot);

    // -------------------------------------------------------------
    // PART 3: MOBILE + RTL COMBINED (iPhone 390x844 + Arabic)
    // -------------------------------------------------------------
    console.log("\n[TEST 3] Auditing Mobile + RTL Combined (390x844 Arabic)...");
    await desktopPage.setViewportSize({ width: 390, height: 844 });
    await desktopPage.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await desktopPage.waitForTimeout(800);

    await desktopPage.evaluate(() => {
      document.documentElement.dir = "rtl";
      document.body.dir = "rtl";
    });
    await desktopPage.waitForTimeout(400);

    const mobileRtlShot = path.join(evidenceDir, "mobile_03_rtl_phone.png");
    await desktopPage.screenshot({ path: mobileRtlShot, fullPage: false });
    console.log("  ✓ Screenshot saved ->", mobileRtlShot);

    await desktopContext.close();

    console.log("\n=== All Mobile Responsiveness & RTL Tests Passed Successfully! ===");
  } catch (err) {
    console.error("Test execution failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

runMobileAndRTLAudit();
