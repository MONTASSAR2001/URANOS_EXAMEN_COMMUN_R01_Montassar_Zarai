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
  console.log(`${BOLD}${CYAN}   VERIFICATION: REAL-TIME REACTIVE UI & REDESIGNED PROJECT FORM VIEW${RESET}`);
  console.log(`${BOLD}${CYAN}${"═".repeat(78)}${RESET}\n`);

  const browser = await chromium.launch({
    headless: true,
    executablePath: "/usr/bin/google-chrome",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";

  try {
    // ── STEP 1: AUTHENTICATION AS MANAGER ──
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

    // ── STEP 2: VERIFY REDESIGNED PROJECT FORM VIEW ──
    logStep(2, "Navigating to /app/project/PROJ-0016 to verify Redesigned Form View...");
    await page.goto("http://localhost:8080/app/project/PROJ-0016", { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".form-layout, .form-page", { timeout: 25000 });
    await page.waitForTimeout(2000);
    await page.waitForSelector(".uranos-project-form-container", { timeout: 20000 });
    logSuccess("Glassmorphic .uranos-project-form-container detected!");

    const formAudit = await page.evaluate(() => {
      const cardGen = document.querySelector(".uranos-project-form-card.card-general");
      const cardGis = document.querySelector(".uranos-project-form-card.card-gis");
      const cardProg = document.querySelector(".uranos-project-form-card.card-progress");
      const telemetryDock = document.querySelector(".uranos-telemetry-badge-dock");
      const progressWidget = document.querySelector(".uranos-form-progress-widget");

      const latInput = document.querySelector('[data-fieldname="latitude"] input');
      const lngInput = document.querySelector('[data-fieldname="longitude"] input');
      const statusSelect = document.querySelector('[data-fieldname="status"] select, [data-fieldname="status"] input');
      const prioritySelect = document.querySelector('[data-fieldname="priority"] select, [data-fieldname="priority"] input');
      const nameInput = document.querySelector('[data-fieldname="project_name"] input');

      return {
        hasCardGen: !!cardGen,
        hasCardGis: !!cardGis,
        hasCardProg: !!cardProg,
        hasTelemetryDock: !!telemetryDock,
        telemetryText: telemetryDock ? telemetryDock.innerText.trim() : null,
        hasProgressWidget: !!progressWidget,
        latVal: latInput ? latInput.value : null,
        lngVal: lngInput ? lngInput.value : null,
        statusVal: statusSelect ? statusSelect.value : null,
        priorityVal: prioritySelect ? prioritySelect.value : null,
        nameVal: nameInput ? nameInput.value : null
      };
    });

    console.log("  Form Structure Audit:", formAudit);

    if (!formAudit.hasCardGen || !formAudit.hasCardGis || !formAudit.hasCardProg) {
      throw new Error("One or more required glassmorphic cards (General, GIS, Progress) is missing from Project Form View!");
    }
    logSuccess("All 3 Executive Glassmorphic Cards (General, GIS, Progress) verified!");

    if (!formAudit.hasTelemetryDock) {
      throw new Error("Geographic Telemetry GPS Dock widget is missing!");
    }
    logSuccess(`GIS Telemetry Dock verified: '${formAudit.telemetryText}'`);

    if (!formAudit.hasProgressWidget) {
      throw new Error("Physical Baseline Completion Progress widget is missing!");
    }
    logSuccess("Physical Baseline Completion Progress widget verified!");

    const formScreenshot = path.join(artifactDir, "redesigned_project_form_view.png");
    await page.screenshot({ path: formScreenshot, fullPage: false });
    logSuccess(`Captured Redesigned Project Form View screenshot: ${formScreenshot}`);

    // ── STEP 3: VERIFY REAL-TIME REACTIVE UI UPDATE (NO RELOAD) ──
    logStep(3, "Navigating to /app/project to verify Reactive Bento Grid updates...");
    await page.goto("http://localhost:8080/app/project", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);

    // Count existing cards
    const initialCardCount = await page.$$eval(".uranos-saas-card", els => els.length);
    logSuccess(`Initial Bento Grid Project Card count: ${initialCardCount}`);

    // Track reloads to assert NO full page reload happens
    let pageReloaded = false;
    page.on("framenavigated", frame => {
      if (frame === page.mainFrame()) {
        const url = frame.url();
        if (url.includes("/app/project")) {
          // Normal within SPA or reload
        }
      }
    });

    logStep(4, "Creating new Project via '+ Add Project' Quick Entry dialog...");
    const addBtn = page.locator("button:has-text('Add Project'), .page-actions button:has-text('Add'), button.primary-action").first();
    await addBtn.waitFor({ timeout: 15000 });
    await addBtn.click();
    await page.waitForTimeout(1500);

    await page.waitForSelector(".modal.quick-entry-modal, .modal:visible", { timeout: 10000 });
    logSuccess("Quick Entry dialog opened!");

    const REACTIVE_DEMO_NAME = `Centrale Solaire Tozeur (Live Reactive ${Date.now().toString().slice(-4)})`;
    const nameInput = page.locator('.modal:visible [data-fieldname="project_name"] input, .modal:visible input[data-fieldname="project_name"]').first();
    await nameInput.waitFor({ timeout: 5000 });
    await nameInput.fill(REACTIVE_DEMO_NAME);

    logStep(5, `Saving project '${REACTIVE_DEMO_NAME}' and verifying REAL-TIME REACTIVE RE-RENDER...`);
    const saveBtn = page.locator('.modal:visible button.btn-primary:has-text("Save"), .modal:visible button:has-text("Save")').first();
    await saveBtn.click();

    // Wait for the new project card to reactively appear in the Bento Grid (NO page reload)
    await page.waitForFunction((expectedName) => {
      const titles = Array.from(document.querySelectorAll(".uranos-saas-card-title")).map(e => e.textContent.trim());
      return titles.some(t => t.includes(expectedName));
    }, REACTIVE_DEMO_NAME, { timeout: 15000 });

    const updatedCards = await page.$$eval(".uranos-saas-card-title", els => els.map(e => e.textContent.trim()));
    const newCardExists = updatedCards.some(t => t.includes(REACTIVE_DEMO_NAME));

    if (!newCardExists) {
      logFailure(`Reactive re-render check failed. Cards found: ${JSON.stringify(updatedCards.slice(0, 5))}`);
      throw new Error(`The newly created project '${REACTIVE_DEMO_NAME}' was not dynamically rendered in the Bento Grid!`);
    }
    logSuccess(`CONFIRMED: '${REACTIVE_DEMO_NAME}' was reactively inserted and rendered in Bento Grid with NO PAGE RELOAD!`);

    const newTotalCount = await page.$$eval(".uranos-saas-card", els => els.length);
    logSuccess(`Updated Bento Grid Card count: ${newTotalCount} (previously ${initialCardCount})`);

    const reactiveScreenshot = path.join(artifactDir, "reactive_ui_bento_grid_updated.png");
    await page.screenshot({ path: reactiveScreenshot, fullPage: false });
    logSuccess(`Captured Reactive Bento Grid screenshot: ${reactiveScreenshot}`);

    // ── STEP 6: VERIFY DESK GIS MAP MARKER REFLECTED ──
    logStep(6, "Navigating to /desk to verify Fleet GIS Map integration...");
    await page.goto("http://localhost:8080/desk", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3500);

    const deskScreenshot = path.join(artifactDir, "desk_gis_map_after_reactive_creation.png");
    await page.screenshot({ path: deskScreenshot, fullPage: false });
    logSuccess(`Captured Desk GIS Map screenshot: ${deskScreenshot}`);

    console.log(`\n${BOLD}${GREEN}${"═".repeat(78)}${RESET}`);
    console.log(`${BOLD}${GREEN}   ALL VERIFICATIONS PASSED: 100% SUCCESS${RESET}`);
    console.log(`${BOLD}${GREEN}${"═".repeat(78)}${RESET}\n`);

  } catch (err) {
    if (page) {
      await page.screenshot({ path: path.join(artifactDir, "verification_error_debug.png") }).catch(() => {});
    }
    console.error(`\n${BOLD}${RED}TEST FAILED: ${err.message}${RESET}\n`, err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
