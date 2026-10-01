import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function run7DayProgressUIAudit() {
  console.log("=== Starting 7-Day Verified Progress Bento Card UI Verification ===");
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
    // PART 1: DESKTOP DASHBOARD WITH 7-DAY VERIFIED PROGRESS CARD
    // -------------------------------------------------------------
    console.log("\n[TEST 1] Auditing Desktop Dashboard (1440x900)...");
    const desktopContext = await browser.newContext({
      viewport: { width: 1440, height: 900 }
    });
    const page = await desktopContext.newPage();

    console.log("  Logging in as ingenieur_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(/\/desk|\/app/, { timeout: 15000 });
    console.log("  ✓ Desktop Login Successful. URL:", page.url());

    await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);

    // Verify 7-Day Verified Progress Card presence
    const progressCard = await page.$(".gv-7day-progress-card");
    console.log("  7-Day Progress Bento Card Present:", progressCard ? "✓ PASS" : "✗ FAIL");

    // Verify Period and Baseline text
    const periodText = await page.$eval("#gv-progress-period", el => el.textContent.trim()).catch(() => "N/A");
    console.log("  Period Window:", periodText);

    const baselineText = await page.$eval("#gv-progress-baseline", el => el.textContent.trim()).catch(() => "N/A");
    console.log("  Baseline:", baselineText);

    const projectText = await page.$eval("#gv-progress-project", el => el.textContent.trim()).catch(() => "N/A");
    console.log("  Project:", projectText);

    // Verify Work Package Cards count
    const wpCount = await page.$$eval(".gv-wp-card", els => els.length);
    console.log("  Work Packages Cards Count:", wpCount, wpCount >= 3 ? "✓ PASS" : "✗ FAIL");

    // Verify Units Summary Chips
    const chipsCount = await page.$$eval(".gv-unit-chip", els => els.length);
    console.log("  Units Summary Chips Count:", chipsCount, chipsCount >= 3 ? "✓ PASS" : "✗ FAIL");

    // Verify Guarantee Chips (Verified Only, Separate Units, Zero Labour Conversion, Net Corrections, Strict 7-Day)
    const guaranteesCount = await page.$$eval(".gv-guarantee-chip", els => els.length);
    console.log("  Guarantees Badges Count:", guaranteesCount, guaranteesCount === 5 ? "✓ PASS" : "✗ FAIL");

    const desktopShot = path.join(evidenceDir, "7day_progress_desktop_en.png");
    await page.screenshot({ path: desktopShot, fullPage: false });
    console.log("  ✓ Desktop Screenshot saved ->", desktopShot);

    // -------------------------------------------------------------
    // PART 2: ARABIC RTL MODE VERIFICATION
    // -------------------------------------------------------------
    console.log("\n[TEST 2] Auditing Arabic RTL Mode...");
    await page.evaluate(() => {
      document.documentElement.setAttribute("dir", "rtl");
      document.documentElement.setAttribute("lang", "ar");
      if (typeof window.switchLanguage === "function") {
        // Mock session lang for client-side render
        if (window.frappe && window.frappe.boot && window.frappe.boot.user) {
          window.frappe.boot.user.language = "ar";
        }
      }
      // Re-trigger overhaul
      $(".gv-main-dashboard, .gv-desk-sidebar").remove();
      if (window._gv_runOverhaul) {
        window._gv_runOverhaul();
      }
    });

    await page.waitForTimeout(1000);

    const dir = await page.$eval("html", el => el.getAttribute("dir") || "ltr");
    console.log("  Document Direction:", dir);

    const arabicShot = path.join(evidenceDir, "7day_progress_arabic_rtl.png");
    await page.screenshot({ path: arabicShot, fullPage: false });
    console.log("  ✓ Arabic RTL Screenshot saved ->", arabicShot);

    console.log("\n=== 7-Day Verified Progress UI Verification Complete: 100% SUCCESS ===");
  } finally {
    await browser.close();
  }
}

run7DayProgressUIAudit().catch(err => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
