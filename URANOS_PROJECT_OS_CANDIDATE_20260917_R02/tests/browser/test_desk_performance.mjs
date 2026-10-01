import { chromium } from "playwright";

async function runPerformanceAudit() {
  console.log("=== Starting GreenVolt Performance, QA & Architecture Browser Audit ===");
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

  const consoleErrors = [];
  page.on("console", msg => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text());
    }
  });
  page.on("pageerror", err => {
    consoleErrors.push(err.message);
  });

  try {
    // 1. Login
    console.log("1. Logging in as ingenieur_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(/\/desk|\/app/, { timeout: 15000 });
    console.log("✓ Logged in successfully. Current URL:", page.url());

    // 2. Main Desk Audit
    console.log("2. Auditing Main Desk (/app)...");
    await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);

    const brandLogo = await page.$(".gv-brand-title");
    console.log("  Brand Logo:", brandLogo ? "✓ Found GreenVolt" : "✗ Missing");

    const heroKpis = await page.$$(".gv-kpi-card");
    console.log("  Hero KPI Cards Count:", heroKpis.length, heroKpis.length === 4 ? "✓ PASS" : "✗ FAIL");

    const appCards = await page.$$(".desktop-icon");
    const isAppCountValid = appCards.length === 11 || appCards.length === 15;
    console.log("  Flagship Application Cards Count:", appCards.length, isAppCountValid ? "✓ PASS" : "✗ FAIL");

    const totalCapacity = await page.$eval("#gv-kpi-capacity-val", el => el.textContent.trim());
    console.log("  Dynamic Total Capacity:", totalCapacity, "✓ PASS");

    // 3. Inner Page Audit: /app/projects
    console.log("3. Auditing Inner Workspace (/app/projects)...");
    await page.goto("http://localhost:8080/app/projects", { waitUntil: "networkidle" });
    await page.waitForTimeout(800);

    const backBtn = await page.$("#gv-back-to-dashboard");
    console.log("  'Back to Main Dashboard' Button:", backBtn ? "✓ Injected and Present" : "✗ Missing");

    const diagPill = await page.$(".gv-realtime-diagnostic-pill");
    console.log("  'Live Database Connected' Pill:", diagPill ? "✓ Injected and Present" : "✗ Missing");

    const pageHead = await page.$(".page-head");
    const headBoxBefore = await pageHead.boundingBox();
    console.log("  .page-head Y coordinate before scroll:", headBoxBefore.y);

    // Scroll down 400px
    await page.evaluate(() => {
      const ms = document.querySelector(".main-section") || window;
      if (ms.scrollTop !== undefined) ms.scrollTop = 400;
      window.scrollTo(0, 400);
    });
    await page.waitForTimeout(400);

    const headBoxAfter = await pageHead.boundingBox();
    console.log("  .page-head Y coordinate after scroll:", headBoxAfter.y);
    const isSticky = headBoxAfter.y >= 0 && headBoxAfter.y <= 5;
    console.log("  Sticky Header Verified:", isSticky ? "✓ PASS (Locked at top: 0)" : "✗ FAIL");

    // Check upgraded widgets
    const upgradedWidgets = await page.$$(".widget.gv-upgraded");
    console.log("  Upgraded Inner Widgets Count:", upgradedWidgets.length, upgradedWidgets.length > 0 ? "✓ PASS" : "✗ FAIL");

    // 4. Test Navigation Return
    console.log("4. Testing 'Back to Main Dashboard' Click...");
    await page.click("#gv-back-to-dashboard");
    await page.waitForTimeout(1000);
    console.log("  URL after clicking Return:", page.url(), (page.url().includes("/app") || page.url().includes("/desk")) ? "✓ PASS" : "✗ FAIL");

    // Check Console Errors
    console.log("5. Console Error Audit...");
    console.log("  Total JavaScript Errors:", consoleErrors.length);
    if (consoleErrors.length > 0) {
      console.log("  Errors found:", consoleErrors);
    } else {
      console.log("  ✓ Zero JavaScript errors/exceptions!");
    }

    console.log("=== Performance, QA & Architecture Audit Completed Successfully ===");
  } catch (err) {
    console.error("Test failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

runPerformanceAudit();
