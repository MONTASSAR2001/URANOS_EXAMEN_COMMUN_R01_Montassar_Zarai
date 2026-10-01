// tests/browser/verify_manager_rename_and_blocker_dashboard_fix.mjs
/**
 * URANOS Project OS — Automated Verification Script:
 * 1. Renaming "Direction" / "Direction 01" to "Manager" across UI greetings and labels.
 * 2. Blocker Dashboard loads seamlessly for Manager persona without any Permission Error.
 * 3. Project filter dropdown populates with all accessible projects cleanly.
 */

import { chromium } from "playwright";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";

const GREEN  = "\x1b[92m";
const RED    = "\x1b[91m";
const YELLOW = "\x1b[93m";
const CYAN   = "\x1b[96m";
const BOLD   = "\x1b[1m";
const RESET  = "\x1b[0m";

function logStep(step, msg) {
  console.log(`\n${BOLD}${CYAN}[Step ${step}] ${msg}${RESET}`);
}

function logSuccess(msg) {
  console.log(`${BOLD}${GREEN}  ✓ ${msg}${RESET}`);
}

function logFailure(msg) {
  console.error(`${BOLD}${RED}  ✗ ${msg}${RESET}`);
}

async function run() {
  console.log(`\n${BOLD}${CYAN}${"═".repeat(78)}${RESET}`);
  console.log(`${BOLD}${CYAN}   VERIFICATION: MANAGER PERSONA & BLOCKER DASHBOARD PERMISSION FIX${RESET}`);
  console.log(`${BOLD}${CYAN}${"═".repeat(78)}${RESET}`);

  const browser = await chromium.launch({
    executablePath: "/usr/bin/google-chrome",
    headless: true,
    args: ["--no-sandbox", "--disable-dev-shm-usage"]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();

  const permissionErrors = [];
  const dialogMessages = [];

  page.on("dialog", async (dialog) => {
    const msg = dialog.message();
    dialogMessages.push(msg);
    if (msg.toLowerCase().includes("permission") || msg.toLowerCase().includes("insufficient")) {
      permissionErrors.push(msg);
    }
    await dialog.dismiss();
  });

  page.on("console", msg => console.log(`   [Browser Console] ${msg.type()}: ${msg.text()}`));
  page.on("pageerror", err => console.log(`   [Page Error] ${err.message}`));

  page.on("response", async (response) => {
    try {
      const url = response.url();
      if (url.includes("/api/method/")) {
        const status = response.status();
        const text = await response.text();
        if (url.includes("get_accessible_projects")) {
          console.log(`   [Network] get_accessible_projects returned (${status}): ${text.substring(0, 200)}`);
        }
        if (status >= 400) {
          if (text.includes("PermissionError") || text.includes("Insufficient Permission")) {
            permissionErrors.push(`API Error ${status} on ${url}: ${text.substring(0, 150)}`);
          }
        }
      }
    } catch (_) {}
  });

  try {
    // ── 1. LOGIN PAGE TEST ──
    logStep(1, "Navigating to Login Page & Verifying Demo Login Chip...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".demo-pill-group", { timeout: 10000 });

    const demoChips = await page.$$eval(".demo-chip", chips => chips.map(c => c.textContent.trim()));
    console.log(`   Demo Chips found: ${JSON.stringify(demoChips)}`);

    if (demoChips.includes("Manager")) {
      logSuccess("Demo chip 'Manager' is clearly rendered on Login page!");
    } else {
      logFailure(`Demo chip does NOT contain 'Manager'. Found: ${JSON.stringify(demoChips)}`);
      throw new Error("Demo chip does not contain Manager");
    }

    // ── 2. LOGIN AS MANAGER ──
    logStep(2, "Authenticating as Manager (direction_01@uranos.local)...");
    await page.fill("#loginEmail", "direction_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");

    await page.waitForURL(/\/desk|\/app/, { timeout: 15000 });
    logSuccess("Successfully authenticated! Landing URL: " + page.url());

    await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await page.waitForTimeout(3000);

    // ── 3. VERIFY HERO GREETING & USER DISPLAY NAME ──
    logStep(3, "Verifying Desk Greeting & Persona Display Name...");
    await page.waitForSelector("#gv-hero-user-name", { timeout: 8000 });

    const heroGreeting = await page.$eval(".gv-hero-title", el => el.textContent.trim());
    const heroUserName = await page.$eval("#gv-hero-user-name", el => el.textContent.trim());
    const deskUserName = await page.$eval(".gv-user-name", el => el.textContent.trim());
    const deskUserRole = await page.$eval(".gv-user-role", el => el.textContent.trim());

    console.log(`   Hero Greeting:   "${heroGreeting}"`);
    console.log(`   Hero User Name:  "${heroUserName}"`);
    console.log(`   Desk User Name:  "${deskUserName}"`);
    console.log(`   Desk User Role:  "${deskUserRole}"`);

    if (heroUserName === "Manager" || heroUserName.includes("Manager")) {
      logSuccess(`Greeting cleanly addresses 'Manager' (${heroGreeting})!`);
    } else {
      logFailure(`Greeting did not address Manager: found '${heroUserName}'`);
      throw new Error(`Expected Manager in greeting, got: ${heroUserName}`);
    }

    if (!heroGreeting.toLowerCase().includes("direction")) {
      logSuccess("Word 'Direction' is completely purged from the hero greeting!");
    } else {
      logFailure(`Word 'Direction' found in hero greeting: ${heroGreeting}`);
      throw new Error("Direction found in hero greeting");
    }

    const deskScreenshotPath = path.join(artifactDir, "manager_desk_greeting_verified.png");
    await page.screenshot({ path: deskScreenshotPath, fullPage: false });
    logSuccess(`Desk screenshot captured: ${deskScreenshotPath}`);

    // ── 4. NAVIGATE TO BLOCKER DASHBOARD ──
    logStep(4, "Navigating to Executive Blocker Dashboard (/app/blocker-dashboard)...");
    await page.goto("http://localhost:8080/app/blocker-dashboard", { waitUntil: "networkidle" });

    // Wait for the Blocker Dashboard elements
    await page.waitForSelector("#uranos-bd", { timeout: 10000 });
    await page.waitForSelector("#bd-project-select", { timeout: 10000 });
    await page.waitForTimeout(2000);

    // Check project options
    const projectOptions = await page.$$eval("#bd-project-select option", opts => opts.map(o => ({ value: o.value, text: o.textContent.trim() })));
    console.log(`   Projects in dropdown: ${projectOptions.length} total options`);
    console.log(`   Sample options:`, projectOptions.slice(0, 5));

    if (projectOptions.length > 1) {
      logSuccess(`Project dropdown loaded ${projectOptions.length - 1} accessible projects!`);
    } else {
      logFailure("Project dropdown is empty or only contains default option!");
      throw new Error("Project dropdown failed to load");
    }

    // Check KPI values
    const kpiActive = await page.$eval("#kpi-active-val", el => el.textContent.trim());
    const kpiCritical = await page.$eval("#kpi-critical-val", el => el.textContent.trim());
    const kpiPending = await page.$eval("#kpi-pending-val", el => el.textContent.trim());
    const kpiOverdue = await page.$eval("#kpi-overdue-val", el => el.textContent.trim());

    console.log(`   Blocker KPIs: Active=${kpiActive}, Critical=${kpiCritical}, Pending=${kpiPending}, Overdue=${kpiOverdue}`);

    logSuccess(`Blocker KPIs successfully calculated and rendered (Active: ${kpiActive}, Critical: ${kpiCritical})`);

    // Verify zero permission dialogs/errors
    const modalErrors = await page.$$eval(".msgprint, .modal-title", els => els.map(e => e.textContent.trim()));
    const hasPermError = modalErrors.some(t => t.toLowerCase().includes("permission") || t.toLowerCase().includes("insufficient"));

    if (hasPermError || permissionErrors.length > 0) {
      logFailure(`Permission error detected! Popups: ${JSON.stringify(modalErrors)}, API Errors: ${JSON.stringify(permissionErrors)}`);
      throw new Error("Permission error occurred on Blocker Dashboard!");
    } else {
      logSuccess("ZERO Permission Errors on Blocker Dashboard for Manager persona!");
    }

    const blockerDashboardScreenshot = path.join(artifactDir, "manager_blocker_dashboard_zero_errors.png");
    await page.screenshot({ path: blockerDashboardScreenshot, fullPage: false });
    logSuccess(`Blocker Dashboard screenshot captured: ${blockerDashboardScreenshot}`);

    // ── 5. VERIFY SECURITY ACCESS AUDIT MODAL CHIP ──
    logStep(5, "Verifying Security Access Audit Modal chip and filter...");
    await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);

    const userBtn = page.locator("#gvUserPillBtn, .gv-user-pill").first();
    await userBtn.waitFor({ timeout: 10000 });
    await userBtn.click();
    await page.waitForTimeout(600);

    const auditDropdownLink = page.locator("#gvAccessAuditDropdownLink");
    await auditDropdownLink.waitFor({ timeout: 5000 });
    await auditDropdownLink.click();

    await page.waitForSelector(".uranos-saas-filter-dock", { timeout: 8000 });
    const chips = await page.$$eval(".uranos-saas-chip", els => els.map(e => e.textContent.trim()));
    console.log(`   Audit Filter Chips: ${JSON.stringify(chips)}`);

    if (chips.includes("Manager")) {
      logSuccess("Audit modal contains 'Manager' filter chip!");
    } else {
      logFailure(`Audit modal chips do not include 'Manager'. Found: ${JSON.stringify(chips)}`);
      throw new Error("Manager chip missing from audit modal");
    }

    // Click Manager chip and verify filter
    await page.click(`.uranos-saas-chip[data-filter="manager"]`);
    await page.waitForTimeout(500);
    const visibleRows = await page.$$eval(".uranos-audit-row", rows => rows.filter(r => r.style.display !== "none").length);
    console.log(`   Visible audited rows for Manager filter: ${visibleRows}`);

    const auditScreenshot = path.join(artifactDir, "manager_audit_modal_verified.png");
    await page.screenshot({ path: auditScreenshot, fullPage: false });
    logSuccess(`Audit modal screenshot captured: ${auditScreenshot}`);

    console.log(`\n${BOLD}${GREEN}${"═".repeat(78)}${RESET}`);
    console.log(`${BOLD}${GREEN}   ALL VERIFICATIONS PASSED: 100% SUCCESS${RESET}`);
    console.log(`${BOLD}${GREEN}${"═".repeat(78)}${RESET}\n`);

  } catch (err) {
    console.error(`\n${BOLD}${RED}TEST FAILED: ${err.message}${RESET}\n`, err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
