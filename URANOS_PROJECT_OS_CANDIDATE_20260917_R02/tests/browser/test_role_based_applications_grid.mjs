// tests/browser/test_role_based_applications_grid.mjs
import { chromium } from "playwright";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";

async function loginAndInspectUser(browser, email, password, roleLabel) {
  console.log(`\n===============================================================`);
  console.log(`Testing Role: ${roleLabel} (${email})`);
  console.log(`===============================================================`);

  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 }
  });
  const page = await context.newPage();

  await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#loginEmail", { timeout: 10000 });
  await page.fill("#loginEmail", email);
  await page.fill("#loginPassword", password);
  await page.click("#btnContinue");

  await page.waitForURL(/\/desk|\/app/, { timeout: 15000 });
  console.log(`  ✓ Logged in as ${email}. URL: ${page.url()}`);

  await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await page.waitForSelector(".gv-applications-card", { timeout: 15000 });
  await page.waitForSelector(".gv-applications-card .desktop-icon", { timeout: 15000 });

  // Scroll applications card into view
  const appCard = page.locator(".gv-applications-card");
  await appCard.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1000);

  const visibleCards = await page.$$eval(".gv-applications-card .desktop-icon", elements => {
    return elements.map(el => ({
      id: el.getAttribute("data-id"),
      title: el.querySelector(".icon-title") ? el.querySelector(".icon-title").innerText.trim() : "",
      category: el.getAttribute("data-category"),
      href: el.getAttribute("href")
    }));
  });

  const visibleIds = visibleCards.map(c => c.id);
  console.log(`  ✓ Total Visible Cards: ${visibleCards.length}`);
  visibleCards.forEach(c => {
    console.log(`    - [${c.id}] "${c.title}" (${c.category}) -> ${c.href}`);
  });

  return { visibleCards, visibleIds, appCard, page, context };
}

async function verifyRoleBasedApplicationsGrid() {
  console.log("=== Testing Dynamic Role-Based Visibility on Applications Grid ===");
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  try {
    // ── 1. TEST PERSONA: ingenieur_01@uranos.local (Engineering Director & PM) ──
    const ing = await loginAndInspectUser(
      browser,
      "ingenieur_01@uranos.local",
      "Password123!",
      "Engineering Director / Project Manager"
    );

    // Verify Hors V1 cards are strictly absent
    const horsV1Ids = ["purchase", "sales", "hr", "payroll", "accounting", "settings"];
    horsV1Ids.forEach(id => {
      if (ing.visibleIds.includes(id)) {
        throw new Error(`Security Violation: Hors V1 card '${id}' leaked to ingenieur_01!`);
      }
    });
    console.log("  ✓ Hors V1 modules successfully hidden from Engineering Director (0 leaked)");

    // Capture element screenshot of Applications Bento Grid
    const ingShotPath = path.join(artifactDir, "applications_grid_ingenieur.png");
    await ing.appCard.screenshot({ path: ingShotPath });
    console.log("  ✓ Applications Grid screenshot saved to:", ingShotPath);

    // Test Category filter button
    await ing.page.click(".gv-applications-card .gv-filter-btn[data-filter='energy']");
    await ing.page.waitForTimeout(400);
    const energyCount = await ing.page.$$eval(".gv-applications-card .desktop-icon:visible", els => els.length);
    console.log(`  ✓ 'Energy' filter clicked. Visible cards: ${energyCount}`);
    await ing.context.close();

    // ── 2. TEST PERSONA: chantier_01@uranos.local (Site Controller & Team Lead) ──
    const ch = await loginAndInspectUser(
      browser,
      "chantier_01@uranos.local",
      "Password123!",
      "Site Controller / Team Lead"
    );

    // Verify Hors V1 cards are strictly absent
    horsV1Ids.forEach(id => {
      if (ch.visibleIds.includes(id)) {
        throw new Error(`Security Violation: Hors V1 card '${id}' leaked to chantier_01!`);
      }
    });
    console.log("  ✓ Hors V1 modules successfully hidden from Site Controller (0 leaked)");

    // Maintenance card should also be hidden for Site Controller (restricted to Electrical Mgr / Eng Dir / PM)
    if (ch.visibleIds.includes("maintenance")) {
      throw new Error("Security Violation: 'maintenance' card should be restricted from Site Controller!");
    }
    console.log("  ✓ 'maintenance' card correctly hidden from Site Controller");

    const chShotPath = path.join(artifactDir, "applications_grid_chantier.png");
    await ch.appCard.screenshot({ path: chShotPath });
    console.log("  ✓ Applications Grid screenshot saved to:", chShotPath);
    await ch.context.close();

    // ── 3. TEST PERSONA: direction_01@uranos.local (URANOS Executive) ──
    const dir = await loginAndInspectUser(
      browser,
      "direction_01@uranos.local",
      "Password123!",
      "URANOS Executive"
    );

    // Verify Hors V1 cards (HR, Payroll, Purchase, Sales, Accounting, Settings) are strictly absent
    horsV1Ids.forEach(id => {
      if (dir.visibleIds.includes(id)) {
        throw new Error(`Security Violation: Hors V1 card '${id}' leaked to direction_01!`);
      }
    });
    console.log("  ✓ Hors V1 modules successfully hidden from URANOS Executive (0 leaked)");

    const dirShotPath = path.join(artifactDir, "applications_grid_executive.png");
    await dir.appCard.screenshot({ path: dirShotPath });
    console.log("  ✓ Applications Grid screenshot saved to:", dirShotPath);
    await dir.context.close();

    // ── 4. TEST PERSONA: Administrator (System Superuser) ──
    const admin = await loginAndInspectUser(
      browser,
      "Administrator",
      "Password123!",
      "Administrator (Superuser)"
    );

    // Administrator MUST see all 17 application cards
    const expectedAll17 = [
      "projects", "sites", "energy-analytics", "blockers", "work-packages",
      "reports", "quality-inspections", "operations", "maintenance", "stock",
      "purchase", "sales", "hr", "payroll", "accounting", "settings", "help-support"
    ];
    let all17Present = true;
    expectedAll17.forEach(id => {
      if (!admin.visibleIds.includes(id)) {
        console.error(`  ❌ Missing expected card '${id}' for Administrator`);
        all17Present = false;
      }
    });
    if (!all17Present || admin.visibleCards.length < 17) {
      throw new Error(`Administrator should have access to all 17 cards, got ${admin.visibleCards.length}`);
    }
    console.log(`  ✓ Administrator sees all ${admin.visibleCards.length} application cards!`);

    const adminShotPath = path.join(artifactDir, "applications_grid_admin.png");
    await admin.appCard.screenshot({ path: adminShotPath });
    console.log("  ✓ Applications Grid screenshot saved to:", adminShotPath);

    // Full dashboard overview
    const fullShotPath = path.join(artifactDir, "role_based_applications_grid_verified.png");
    await admin.page.screenshot({ path: fullShotPath, fullPage: true });
    console.log("  ✓ Full dashboard overview saved to:", fullShotPath);
    await admin.context.close();

    console.log("\n===============================================================");
    console.log("=== ALL MULTI-ROLE CONTRAST & VISIBILITY TESTS PASSED 100% ===");
    console.log("===============================================================");
  } catch (err) {
    console.error("Verification failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyRoleBasedApplicationsGrid();


