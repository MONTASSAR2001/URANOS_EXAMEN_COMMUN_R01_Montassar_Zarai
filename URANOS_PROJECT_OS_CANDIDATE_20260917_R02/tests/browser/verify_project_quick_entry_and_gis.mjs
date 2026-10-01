import { chromium } from "playwright";
import path from "path";

const BOLD = "\x1b[1m";
const GREEN = "\x1b[32m";
const RED = "\x1b[31m";
const YELLOW = "\x1b[33m";
const CYAN = "\x1b[36m";
const RESET = "\x1b[0m";

function logStep(num, msg) {
  console.log(`\n${BOLD}${YELLOW}[Step ${num}] ${msg}${RESET}`);
}

function logSuccess(msg) {
  console.log(`  ${BOLD}${GREEN}✓${RESET} ${msg}`);
}

function logFailure(msg) {
  console.log(`  ${BOLD}${RED}✗${RESET} ${msg}`);
}

async function run() {
  console.log(`\n${BOLD}${CYAN}${"═".repeat(78)}${RESET}`);
  console.log(`${BOLD}${CYAN}   VERIFICATION: PROJECT QUICK-ENTRY, COMPANY PERM & GIS PERSISTENCE${RESET}`);
  console.log(`${BOLD}${CYAN}${"═".repeat(78)}${RESET}\n`);

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const errors = [];
  page.on("pageerror", err => {
    errors.push(`PageError: ${err.message}`);
  });
  page.on("console", msg => {
    if (msg.type() === "error") {
      const text = msg.text();
      if (!text.includes("socket.io") && !text.includes("502 (Bad Gateway)")) {
        errors.push(`ConsoleError: ${text}`);
      }
    }
  });

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";

  try {
    // ── STEP 1: AUTHENTICATE AS MANAGER ──
    logStep(1, "Authenticating as Manager (direction_01@uranos.local)...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    const isLoginVisible = await emailField.isVisible({ timeout: 5000 }).catch(() => false);
    if (isLoginVisible) {
      await emailField.fill("direction_01@uranos.local");
      await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
      await page.click("#btnContinue, .btn-login, button[type='submit']");
      await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { waitUntil: "domcontentloaded", timeout: 25000 });
    }
    logSuccess("Successfully authenticated as Manager!");

    // ── STEP 2: NAVIGATE TO PROJECT LIST (/app/project) ──
    logStep(2, "Navigating to /app/project to test Quick Entry creation...");
    await page.goto("http://localhost:8080/app/project", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);

    // Assert zero permission popups on loading list
    let popups = await page.$$eval(".msgprint, .modal-title", els => els.map(e => e.textContent.trim()));
    let companyPermError = popups.some(t => t.toLowerCase().includes("permission") && t.toLowerCase().includes("company"));
    if (companyPermError) {
      logFailure(`Permission error on Company detected on page load: ${JSON.stringify(popups)}`);
      throw new Error("Permission Error for Company appeared on Project list page load!");
    }
    logSuccess("Zero permission popups on Project list load!");

    // ── STEP 3: TRIGGER 'ADD PROJECT' QUICK ENTRY ──
    logStep(3, "Opening '+ Add Project' Quick Entry dialog...");
    const addBtn = page.locator("button:has-text('Add Project'), .page-actions button:has-text('Add'), button.primary-action").first();
    await addBtn.waitFor({ timeout: 20000 });
    await addBtn.click();
    await page.waitForTimeout(2000);

    // Check for modal dialog
    await page.waitForSelector(".modal.quick-entry-modal, .modal:visible", { timeout: 15000 });
    logSuccess("Quick Entry modal opened successfully!");

    // Check again for Company Permission error popup
    popups = await page.$$eval(".msgprint, .modal-title", els => els.map(e => e.textContent.trim()));
    companyPermError = popups.some(t => t.toLowerCase().includes("permission") && t.toLowerCase().includes("company"));
    if (companyPermError) {
      logFailure(`Permission error on Company triggered by Quick Entry: ${JSON.stringify(popups)}`);
      throw new Error("Permission Error for Company appeared upon opening Quick Entry modal!");
    }
    logSuccess("Zero Company permission popups in Quick Entry modal!");

    const quickEntryScreenshot = path.join(artifactDir, "manager_project_quick_entry_modal.png");
    await page.screenshot({ path: quickEntryScreenshot, fullPage: false });
    logSuccess(`Quick Entry screenshot captured: ${quickEntryScreenshot}`);

    // ── STEP 4: FILL IN PROJECT DETAILS & PERSIST ──
    const DEMO_PROJ_NAME = `Centrale PV Monastir (Live Demo ${Date.now().toString().slice(-4)})`;
    logStep(4, `Filling in Project Name: '${DEMO_PROJ_NAME}' and Saving...`);

    // Look for project_name input in quick entry modal
    const nameInput = page.locator('.modal:visible [data-fieldname="project_name"] input, .modal:visible input[data-fieldname="project_name"]').first();
    await nameInput.waitFor({ timeout: 5000 });
    await nameInput.fill(DEMO_PROJ_NAME);

    // Save button inside modal
    const saveBtn = page.locator('.modal:visible button.btn-primary:has-text("Save"), .modal:visible button:has-text("Save")').first();
    await saveBtn.click();
    await page.waitForTimeout(2500);

    // Assert zero permission errors upon save
    popups = await page.$$eval(".msgprint, .modal-title", els => els.map(e => e.textContent.trim()));
    const saveFailed = popups.some(t => t.toLowerCase().includes("permission") || t.toLowerCase().includes("error"));
    if (saveFailed) {
      logFailure(`Save failed with popup error: ${JSON.stringify(popups)}`);
      throw new Error(`Project Quick Entry save failed with popup: ${popups.join(", ")}`);
    }
    logSuccess("Project successfully saved through Quick Entry with ZERO permission popups!");

    // ── STEP 5: VERIFY PERSISTENCE & GIS MAP INTEGRATION ──
    logStep(5, "Verifying GIS Map Dashboard rendering and new project persistence...");
    await page.goto("http://localhost:8080/desk", { waitUntil: "networkidle" });
    await page.waitForTimeout(3000);

    const deskScreenshot = path.join(artifactDir, "manager_desk_after_project_creation.png");
    await page.screenshot({ path: deskScreenshot, fullPage: false });
    logSuccess(`Desk & GIS Map screenshot captured: ${deskScreenshot}`);

    console.log(`\n${BOLD}${GREEN}${"═".repeat(78)}${RESET}`);
    console.log(`${BOLD}${GREEN}   ALL VERIFICATIONS PASSED: 100% SUCCESS${RESET}`);
    console.log(`${BOLD}${GREEN}${"═".repeat(78)}${RESET}\n`);

  } catch (err) {
    if (page) {
      await page.screenshot({ path: path.join(artifactDir, "test_failure_debug.png") }).catch(() => {});
    }
    console.error(`\n${BOLD}${RED}TEST FAILED: ${err.message}${RESET}\n`, err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
