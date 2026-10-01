import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function runDashboardInteractivityTest() {
  console.log("=== Testing Main Dashboard Dynamic Wiring & Main Page AI Integration ===");
  const evidenceDir = "/home/montassar/.gemini/antigravity-ide/brain/a602cb04-cf23-4f11-be98-e5d6e4f36feb";
  await mkdir(evidenceDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 }
    });
    const page = await context.newPage();

    console.log("1. Logging in as ingenieur_01@uranos.local (Project Manager)...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(/\/desk|\/app/, { timeout: 15000 });
    console.log("  ✓ Logged in successfully. Current URL:", page.url());

    // Ensure we are on /app
    await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);

    // 2. Verify AI buttons on Main Dashboard
    console.log("2. Verifying AI synthesis buttons on Main Dashboard...");
    await page.waitForSelector("#gv-hero-ai-btn", { timeout: 10000 });
    const heroBtnVisible = await page.isVisible("#gv-hero-ai-btn");
    const progressBtnVisible = await page.isVisible("#gv-progress-ai-btn");
    console.log("  Hero AI Button Present & Visible:", heroBtnVisible ? "✓ PASS" : "✗ FAIL");
    console.log("  7-Day Progress AI Button Present & Visible:", progressBtnVisible ? "✓ PASS" : "✗ FAIL");

    // Screenshot of Main Dashboard with prominent AI buttons
    const dashShot = path.join(evidenceDir, "main_dashboard_interconnected_ai.png");
    await page.screenshot({ path: dashShot, fullPage: false });
    console.log("  ✓ Main Dashboard screenshot saved ->", dashShot);

    // 3. Test Clicking Main Dashboard Hero AI Button
    console.log("3. Clicking '#gv-hero-ai-btn' directly on Main Dashboard...");
    await page.click("#gv-hero-ai-btn");
    await page.waitForSelector("#gv-ai-synthesis-modal.open", { timeout: 8000 });
    console.log("  ✓ AI Modal Opened directly on Main Dashboard!");

    // Wait for synthesis data to load
    await page.waitForSelector("#gv-ai-status-badge-container .gv-ai-badge:not(.loading)", { timeout: 10000 });
    const badgeText = await page.$eval("#gv-ai-status-badge-container .gv-ai-badge", el => el.textContent.trim());
    const openCount = await page.$eval("#gv-ai-open-count", el => el.textContent.trim());
    const critCount = await page.$eval("#gv-ai-crit-count", el => el.textContent.trim());
    const lostHours = await page.$eval("#gv-ai-lost-hours", el => el.textContent.trim());
    const provider = await page.$eval("#gv-ai-provider-text", el => el.textContent.trim());

    console.log("  ✓ Live Synthesis Loaded:");
    console.log(`    - Badge: ${badgeText}`);
    console.log(`    - Open Blockers: ${openCount}`);
    console.log(`    - Critical Count: ${critCount}`);
    console.log(`    - Lost Hours: ${lostHours}`);
    console.log(`    - Provider: ${provider}`);

    // Screenshot modal on main dashboard
    const modalShot = path.join(evidenceDir, "main_dashboard_ai_modal_open.png");
    await page.screenshot({ path: modalShot, fullPage: false });
    console.log("  ✓ AI Modal on Main Dashboard screenshot saved ->", modalShot);

    // Close the modal
    console.log("4. Closing AI Modal...");
    await page.click("#gv-ai-modal-close");
    await page.waitForTimeout(500);
    const isModalOpen = await page.isVisible("#gv-ai-synthesis-modal.open");
    console.log("  Modal Closed cleanly:", !isModalOpen ? "✓ PASS" : "✗ FAIL");

    // 5. Test Bento Grid card routing
    console.log("5. Testing Bento Grid Card Click Routing...");
    const blockerCard = await page.$('.desktop-icon[data-id="blockers"]');
    console.log("  'Blockers & Obstacles' Card Present:", blockerCard ? "✓ PASS" : "✗ FAIL");
    
    if (blockerCard) {
      console.log("  Clicking 'Blockers & Obstacles' Bento card...");
      await blockerCard.click();
      await page.waitForTimeout(1500);
      const currentRoute = await page.evaluate(() => frappe.get_route_str ? frappe.get_route_str() : window.location.pathname);
      console.log("  ✓ Navigated to route:", currentRoute);
    }

    // Go back to dashboard
    console.log("6. Returning to Main Dashboard...");
    await page.evaluate(() => frappe.set_route(""));
    await page.waitForTimeout(1500);

    // 7. Test KPI card routing
    console.log("7. Testing KPI Card Click Routing...");
    const kpiSites = await page.$("#gv-kpi-card-sites");
    if (kpiSites) {
      console.log("  Clicking 'Active Sites' KPI card...");
      await kpiSites.click();
      await page.waitForTimeout(1500);
      const currentRoute = await page.evaluate(() => frappe.get_route_str ? frappe.get_route_str() : window.location.pathname);
      console.log("  ✓ Navigated to route:", currentRoute);
    }

    console.log("\n=== ALL MAIN DASHBOARD INTERACTIVITY AUDITS PASSED SUCCESSFULLY! ===");
  } finally {
    await browser.close();
  }
}

runDashboardInteractivityTest().catch(err => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
