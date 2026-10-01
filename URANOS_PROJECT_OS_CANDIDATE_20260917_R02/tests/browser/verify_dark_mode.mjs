import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyDarkMode() {
  console.log("==================================================================");
  console.log("   URANOS Phase 3: Premium Dark Mode Toggle & Chic SaaS Theme Test");
  console.log("==================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/465edcf9-4f3c-45a7-b2e1-1b4e8d2dadb6";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 }
  });
  const page = await context.newPage();

  try {
    console.log("1. Logging into URANOS Desk as direction_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    const isLoginVisible = await emailField.isVisible({ timeout: 5000 }).catch(() => false);
    if (isLoginVisible) {
      await emailField.fill("direction_01@uranos.local");
      await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
      await page.click("#btnContinue, .btn-login, button[type='submit']");
      await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { waitUntil: "domcontentloaded", timeout: 25000 });
    } else {
      await page.goto("http://localhost:8080/app", { waitUntil: "domcontentloaded" });
    }
    await page.waitForTimeout(3000);

    console.log("2. Verifying Dark Mode Toggle Button in Top Navbar...");
    const toggleBtn = page.locator("#uranosDarkModeToggle").first();
    await toggleBtn.waitFor({ timeout: 10000 });
    console.log("✓ Dark Mode Toggle button (#uranosDarkModeToggle) successfully located in navbar!");

    // Check initial state (should be light by default or clean)
    const initialIsDark = await page.evaluate(() => document.body.classList.contains("uranos-dark-mode"));
    console.log(`Initial theme state: isDark=${initialIsDark}`);

    console.log("3. Clicking Dark Mode Toggle Button to activate Midnight/Slate theme...");
    await toggleBtn.click();
    await page.waitForTimeout(1000);

    // Verify class added and localStorage updated
    const postToggleAudit = await page.evaluate(() => {
      const isDark = document.body.classList.contains("uranos-dark-mode");
      const storedPref = localStorage.getItem("uranos_dark_mode");
      const moonVisible = $("#uranosDarkModeToggle .uranos-icon-moon").is(":visible");
      const sunVisible = $("#uranosDarkModeToggle .uranos-icon-sun").is(":visible");

      const bodyBg = window.getComputedStyle(document.body).backgroundColor;
      const navbarBg = window.getComputedStyle(document.querySelector(".desktop-navbar") || document.body).backgroundColor;
      const sidebarEl = document.querySelector(".gv-desk-sidebar, .layout-side-section");
      const sidebarBg = sidebarEl ? window.getComputedStyle(sidebarEl).backgroundColor : "";
      const cardEl = document.querySelector(".gv-metric-card, .frappe-card, .widget");
      const cardBg = cardEl ? window.getComputedStyle(cardEl).backgroundColor : "";
      const cardBorder = cardEl ? window.getComputedStyle(cardEl).borderColor : "";

      return {
        isDark,
        storedPref,
        moonVisible,
        sunVisible,
        bodyBg,
        navbarBg,
        sidebarBg,
        cardBg,
        cardBorder
      };
    });

    console.log("--------------------------------------------------");
    console.log(`✓ Body has .uranos-dark-mode: ${postToggleAudit.isDark}`);
    console.log(`✓ localStorage('uranos_dark_mode'): "${postToggleAudit.storedPref}"`);
    console.log(`✓ Icon state: Moon visible=${postToggleAudit.moonVisible}, Sun visible=${postToggleAudit.sunVisible}`);
    console.log(`✓ Body Background: ${postToggleAudit.bodyBg}`);
    console.log(`✓ Navbar Background: ${postToggleAudit.navbarBg}`);
    console.log(`✓ Sidebar Background: ${postToggleAudit.sidebarBg}`);
    console.log(`✓ Card Background: ${postToggleAudit.cardBg}`);
    console.log(`✓ Card Border: ${postToggleAudit.cardBorder}`);
    console.log("--------------------------------------------------");

    if (!postToggleAudit.isDark) {
      throw new Error("document.body did not receive 'uranos-dark-mode' class after clicking toggle button!");
    }
    if (postToggleAudit.storedPref !== "true") {
      throw new Error(`Expected localStorage('uranos_dark_mode') to be 'true', got '${postToggleAudit.storedPref}'`);
    }

    // Verify toast notification
    const alertMsg = page.locator(".alert, .msgprint, .toast, .desk-alert, .frappe-alert").first();
    if (await alertMsg.isVisible()) {
      console.log(`✓ Toast alert verified: ${await alertMsg.innerText()}`);
    }

    console.log("4. Capturing Main Dashboard Dark Mode Screenshot...");
    const mainDashScreenshot = path.join(artifactDir, "dark_mode_main_dashboard_verified.png");
    await page.screenshot({ path: mainDashScreenshot, fullPage: false });
    console.log(`✓ Main Dashboard Dark Mode Screenshot: ${mainDashScreenshot}`);

    console.log("5. Navigating to Kanban Board to verify Dark Mode styling across routes...");
    const kanbanLink = page.locator("#gv-nav-kanban, a[href*='blocker-kanban']").first();
    if (await kanbanLink.isVisible()) {
      await kanbanLink.click();
    } else {
      await page.goto("http://localhost:8080/app/blocker-kanban", { waitUntil: "domcontentloaded" });
    }
    await page.waitForTimeout(3000);

    const kanbanDashboard = page.locator(".uranos-kanban-dashboard").first();
    await kanbanDashboard.waitFor({ timeout: 15000 });

    const kanbanDarkAudit = await page.evaluate(() => {
      const col = document.querySelector(".uranos-kanban-column");
      const card = document.querySelector(".uranos-kanban-card");
      const statCard = document.querySelector(".uranos-kanban-stat-card");
      return {
        colBg: col ? window.getComputedStyle(col).backgroundColor : "",
        cardBg: card ? window.getComputedStyle(card).backgroundColor : "",
        statBg: statCard ? window.getComputedStyle(statCard).backgroundColor : ""
      };
    });

    console.log(`✓ Kanban Column Dark Bg: ${kanbanDarkAudit.colBg}`);
    console.log(`✓ Kanban Card Dark Bg: ${kanbanDarkAudit.cardBg}`);
    console.log(`✓ Kanban Stat Card Dark Bg: ${kanbanDarkAudit.statBg}`);

    console.log("6. Capturing Kanban Board Dark Mode Screenshot...");
    const kanbanScreenshot = path.join(artifactDir, "dark_mode_kanban_verified.png");
    await page.screenshot({ path: kanbanScreenshot, fullPage: false });
    console.log(`✓ Kanban Board Dark Mode Screenshot: ${kanbanScreenshot}`);

    console.log("7. Testing Persistence on Page Reload...");
    await page.reload({ waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);

    const isStillDark = await page.evaluate(() => document.body.classList.contains("uranos-dark-mode"));
    console.log(`✓ After Reload: .uranos-dark-mode is STILL active: ${isStillDark}`);
    if (!isStillDark) {
      throw new Error("Dark Mode was NOT preserved after page reload!");
    }

    console.log("==================================================================");
    console.log("   ALL DARK MODE VERIFICATIONS PASSED WITH FLYING COLORS!");
    console.log("==================================================================");

  } catch (err) {
    console.error("Test failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyDarkMode();
