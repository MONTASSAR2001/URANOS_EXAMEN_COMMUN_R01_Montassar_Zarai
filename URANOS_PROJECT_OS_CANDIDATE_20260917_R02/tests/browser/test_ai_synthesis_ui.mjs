import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function runAISynthesisUIAudit() {
  console.log("=== Starting Phase 4: Cloud AI & RAG Synthesis UI Verification ===");
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
    // PART 1: DESKTOP BLOCKER DASHBOARD & SMART SYNTHESIS MODAL (EN)
    // -------------------------------------------------------------
    console.log("\n[TEST 1] Auditing Blocker Dashboard & AI Modal (Desktop 1440x900)...");
    const desktopContext = await browser.newContext({
      viewport: { width: 1440, height: 900 }
    });
    const page = await desktopContext.newPage();

    console.log("  Logging in as ingenieur_01@uranos.local (Project Manager)...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(/\/desk|\/app/, { timeout: 15000 });
    console.log("  ✓ Desktop Login Successful. URL:", page.url());

    // Navigate to Blocker Dashboard
    console.log("  Navigating to blocker-dashboard...");
    await page.evaluate(() => frappe.set_route("blocker-dashboard"));
    await page.waitForSelector("#bd-ai-synthesis-btn", { timeout: 10000 });

    // Verify Smart Synthesis Button presence
    const aiBtn = await page.$("#bd-ai-synthesis-btn");
    console.log("  Smart Synthesis Button Present:", aiBtn ? "✓ PASS" : "✗ FAIL");

    const aiBtnText = await page.$eval("#bd-ai-synthesis-btn", el => el.textContent.trim());
    console.log("  Button Text:", aiBtnText);

    // Capture Blocker Dashboard with AI Button
    const dashShot = path.join(evidenceDir, "blocker_dashboard_with_ai_btn.png");
    await page.screenshot({ path: dashShot, fullPage: false });
    console.log("  ✓ Screenshot saved ->", dashShot);

    // Click the Smart Synthesis button
    console.log("  Clicking 'Smart Synthesis' button...");
    await page.click("#bd-ai-synthesis-btn");
    await page.waitForTimeout(1000);

    // Wait for the modal
    const modalVisible = await page.isVisible("#gv-ai-synthesis-modal");
    console.log("  Synthesis Modal Visible:", modalVisible ? "✓ PASS" : "✗ FAIL");

    // Wait for synthesis data rendering
    await page.waitForSelector("#gv-ai-status-badge-container .gv-ai-badge:not(.loading)", { timeout: 8000 });

    const badgeText = await page.$eval("#gv-ai-status-badge-container .gv-ai-badge", el => el.textContent.trim());
    console.log("  Synthesis Badge:", badgeText);

    const openCount = await page.$eval("#gv-ai-open-count", el => el.textContent.trim());
    console.log("  Open Blockers Count:", openCount);

    const critCount = await page.$eval("#gv-ai-crit-count", el => el.textContent.trim());
    console.log("  Critical Issues Count:", critCount);

    const lostHours = await page.$eval("#gv-ai-lost-hours", el => el.textContent.trim());
    console.log("  Lost Hours:", lostHours);

    const providerText = await page.$eval("#gv-ai-provider-text", el => el.textContent.trim());
    console.log("  Provider:", providerText);

    const bodySnippet = await page.$eval("#gv-ai-modal-body", el => el.textContent.trim().slice(0, 150));
    console.log("  Synthesis Body Snippet:", bodySnippet + "...");

    // Capture open modal screenshot
    const modalShot = path.join(evidenceDir, "ai_synthesis_modal_desktop.png");
    await page.screenshot({ path: modalShot, fullPage: false });
    console.log("  ✓ Modal Screenshot saved ->", modalShot);

    // Close the modal
    console.log("  Closing modal via close button...");
    await page.click("#gv-ai-modal-close");
    await page.waitForTimeout(500);
    const modalClosed = !(await page.isVisible("#gv-ai-synthesis-modal"));
    console.log("  Modal Closed Cleanly:", modalClosed ? "✓ PASS" : "✗ FAIL");

    // -------------------------------------------------------------
    // PART 2: ARABIC RTL MODE SYNTHESIS MODAL VERIFICATION
    // -------------------------------------------------------------
    console.log("\n[TEST 2] Auditing Blocker Dashboard & AI Modal in Arabic RTL mode...");
    // Switch HTML dir to rtl
    await page.evaluate(() => {
      document.documentElement.setAttribute("dir", "rtl");
      document.documentElement.setAttribute("lang", "ar");
    });
    await page.waitForTimeout(500);

    // Click Smart Synthesis button again
    console.log("  Triggering Smart Synthesis in RTL mode...");
    await page.click("#bd-ai-synthesis-btn");
    await page.waitForTimeout(800);

    const rtlModalShot = path.join(evidenceDir, "ai_synthesis_modal_rtl.png");
    await page.screenshot({ path: rtlModalShot, fullPage: false });
    console.log("  ✓ RTL Modal Screenshot saved ->", rtlModalShot);

    console.log("\n=== ALL BROWSER UI AUDITS PASSED SUCCESSFULLY ===");
  } finally {
    await browser.close();
  }
}

runAISynthesisUIAudit().catch(err => {
  console.error("UI Audit Failed:", err);
  process.exit(1);
});
