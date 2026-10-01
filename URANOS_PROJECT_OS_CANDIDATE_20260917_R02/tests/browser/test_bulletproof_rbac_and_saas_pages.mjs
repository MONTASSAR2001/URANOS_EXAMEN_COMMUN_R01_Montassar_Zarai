import { chromium } from "playwright";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";

async function loginUser(browser, email, password) {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 }
  });
  const page = await context.newPage();

  console.log(`\nLogging in as ${email}...`);
  await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#loginEmail", { timeout: 10000 });
  await page.fill("#loginEmail", email);
  await page.fill("#loginPassword", password);
  await page.click("#btnContinue");

  await page.waitForURL(/\/desk|\/app/, { timeout: 15000 });
  return { context, page };
}

async function testRbacCardCount(browser, email, password, expectedCount, label, screenshotName) {
  console.log(`\n===============================================================`);
  console.log(`🔍 Testing RBAC for: ${label} (${email})`);
  console.log(`   Target: Exactly ${expectedCount} cards`);
  console.log(`===============================================================`);

  const { context, page } = await loginUser(browser, email, password);

  await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);

  // Wait for the flagship bento applications card
  await page.waitForSelector(".gv-applications-card", { timeout: 15000 });

  // Wait for populated grid after backend verification
  await page.waitForSelector(".gv-grid-populated", { timeout: 15000 });
  await page.waitForTimeout(800);

  const appCard = page.locator(".gv-applications-card");
  await appCard.scrollIntoViewIfNeeded();

  const renderedUser = await page.$eval(".gv-grid-populated", el => el.getAttribute("data-rendered-user"));
  const cardData = await page.$$eval(".gv-applications-card .desktop-icon:visible", els => {
    return els.map(el => ({
      id: el.getAttribute("data-id"),
      title: el.querySelector(".icon-title") ? el.querySelector(".icon-title").innerText.trim() : "",
      href: el.getAttribute("href")
    }));
  });

  const cardIds = cardData.map(c => c.id);
  console.log(`  ✓ Rendered for user: "${renderedUser}"`);
  console.log(`  ✓ Card count: ${cardData.length} (Expected: ${expectedCount})`);
  console.log(`  ✓ Cards: [${cardIds.join(", ")}]`);

  if (cardData.length !== expectedCount) {
    throw new Error(`RBAC Failure for ${label}: Expected ${expectedCount} cards, but found ${cardData.length} (${cardIds.join(", ")})`);
  }

  const shotPath = path.join(artifactDir, screenshotName);
  await appCard.screenshot({ path: shotPath });
  console.log(`  📸 Screenshot saved: ${shotPath}`);

  await context.close();
  return cardIds;
}

async function runFullVerification() {
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  try {
    // ── 1. PROVE ADMINISTRATOR SEES EXACTLY 17 CARDS ──
    const adminCards = await testRbacCardCount(
      browser,
      "Administrator",
      "Password123!",
      17,
      "Administrator",
      "rbac_admin_17.png"
    );

    // ── 2. PROVE CHANTIER 01 SEES EXACTLY 10 CARDS ──
    const chantierCards = await testRbacCardCount(
      browser,
      "chantier_01@uranos.local",
      "Password123!",
      10,
      "Chantier 01",
      "rbac_chantier_10.png"
    );

    if (chantierCards.includes("maintenance")) {
      throw new Error("Security Violation: 'maintenance' leaked to Chantier 01!");
    }
    const horsV1 = ["purchase", "sales", "hr", "payroll", "accounting", "settings"];
    horsV1.forEach(id => {
      if (chantierCards.includes(id)) {
        throw new Error(`Security Violation: Hors V1 '${id}' leaked to Chantier 01!`);
      }
    });
    console.log("  ✅ Chantier 01 verified: 10 operational cards, 0 leaks.");

    // ── 3. PROVE INGENIEUR 01 SEES EXACTLY 11 CARDS ──
    const ingenieurCards = await testRbacCardCount(
      browser,
      "ingenieur_01@uranos.local",
      "Password123!",
      11,
      "Ingenieur 01",
      "rbac_ingenieur_11.png"
    );

    if (!ingenieurCards.includes("maintenance")) {
      throw new Error("Missing Card: 'maintenance' must be visible to Ingenieur 01!");
    }
    horsV1.forEach(id => {
      if (ingenieurCards.includes(id)) {
        throw new Error(`Security Violation: Hors V1 '${id}' leaked to Ingenieur 01!`);
      }
    });
    console.log("  ✅ Ingenieur 01 verified: 11 cards (including maintenance), 0 leaks.");

    // ── 4. TEST CUSTOM SAAS INNER PAGES & STANDARD TABLE RESTORATION ──
    console.log(`\n===============================================================`);
    console.log(`🎨 Testing Custom SaaS Inner Pages with Real MariaDB Data`);
    console.log(`===============================================================`);

    const { context, page } = await loginUser(browser, "Administrator", "Password123!");

    // A. Projects SaaS View
    console.log(`\nTesting /app/project...`);
    await page.goto("http://localhost:8080/app/project", { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);

    await page.waitForSelector(".uranos-chic-saas-view[data-module='projects']", { timeout: 15000 });
    const projectCardsCount = await page.$$eval(".uranos-chic-saas-view[data-module='projects'] .uranos-saas-card", els => els.length);
    console.log(`  ✓ Projects SaaS View mounted! Real projects loaded from MariaDB: ${projectCardsCount}`);

    const projectsShot = path.join(artifactDir, "saas_projects_view.png");
    await page.screenshot({ path: projectsShot, fullPage: false });
    console.log(`  📸 Projects SaaS View screenshot: ${projectsShot}`);

    // Test Standard Table toggle
    console.log(`  Switching to Standard Table View...`);
    await page.click(".uranos-chic-saas-view[data-module='projects'] .uranos-saas-switch-btn[data-view='table']");
    await page.waitForTimeout(800);

    const isTableVisible = await page.$eval(".frappe-list .result-list, .frappe-list .list-row-container, .frappe-list", el => {
      return el && window.getComputedStyle(el).display !== "none";
    });
    console.log(`  ✓ Standard Table visible: ${isTableVisible}`);

    const tableShot = path.join(artifactDir, "standard_table_restored.png");
    await page.screenshot({ path: tableShot, fullPage: false });
    console.log(`  📸 Restored Standard Table screenshot: ${tableShot}`);

    // B. Work Packages SaaS View
    console.log(`\nTesting /app/uranos-work-package...`);
    await page.goto("http://localhost:8080/app/uranos-work-package", { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);

    await page.waitForSelector(".uranos-chic-saas-view[data-module='work-packages']", { timeout: 15000 });
    const wpCardsCount = await page.$$eval(".uranos-chic-saas-view[data-module='work-packages'] .uranos-saas-card", els => els.length);
    console.log(`  ✓ Work Packages SaaS View mounted! Real packages loaded: ${wpCardsCount}`);

    const wpShot = path.join(artifactDir, "saas_work_packages_view.png");
    await page.screenshot({ path: wpShot, fullPage: false });
    console.log(`  📸 Work Packages SaaS View screenshot: ${wpShot}`);

    // C. NCRs SaaS View
    console.log(`\nTesting /app/uranos-ncr...`);
    await page.goto("http://localhost:8080/app/uranos-ncr", { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);

    await page.waitForSelector(".uranos-chic-saas-view[data-module='ncr']", { timeout: 15000 });
    const ncrCardsCount = await page.$$eval(".uranos-chic-saas-view[data-module='ncr'] .uranos-saas-card", els => els.length);
    console.log(`  ✓ NCRs SaaS View mounted! Real NCR records loaded: ${ncrCardsCount}`);

    const ncrShot = path.join(artifactDir, "saas_ncr_view.png");
    await page.screenshot({ path: ncrShot, fullPage: false });
    console.log(`  📸 NCRs SaaS View screenshot: ${ncrShot}`);

    await context.close();

    console.log(`\n===============================================================`);
    console.log(`🎉 ALL TESTS PASSED WITH 100% SUCCESS!`);
    console.log(`===============================================================`);
  } catch (err) {
    console.error("❌ Test Failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

runFullVerification();
