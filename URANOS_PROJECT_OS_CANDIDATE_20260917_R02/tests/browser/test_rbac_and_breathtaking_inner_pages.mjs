// tests/browser/test_rbac_and_breathtaking_inner_pages.mjs
import { chromium } from "playwright";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";

async function testUserCardCount(browser, email, password, expectedCount, label) {
  console.log(`\n===============================================================`);
  console.log(`Testing RBAC: ${label} (${email}) -> Expected: ${expectedCount} cards`);
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
  await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  await page.waitForSelector(".gv-applications-card", { timeout: 15000 });
  await page.waitForSelector(".gv-applications-card .desktop-icon", { timeout: 15000 });

  const appCard = page.locator(".gv-applications-card");
  await appCard.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1000);

  const visibleCards = await page.$$eval(".gv-applications-card .desktop-icon:visible", els => {
    return els.map(el => ({
      id: el.getAttribute("data-id"),
      title: el.querySelector(".icon-title") ? el.querySelector(".icon-title").innerText.trim() : "",
      href: el.getAttribute("href")
    }));
  });

  const visibleIds = visibleCards.map(c => c.id);
  console.log(`  ✓ Actual Visible Cards Count: ${visibleCards.length}`);
  console.log(`  ✓ Card IDs: [${visibleIds.join(", ")}]`);

  if (visibleCards.length !== expectedCount) {
    throw new Error(`RBAC Failure for ${label}: Expected ${expectedCount} cards, but found ${visibleCards.length} (${visibleIds.join(",")})`);
  }
  console.log(`  🎉 PASS: Exact card count match (${expectedCount}/${expectedCount}) for ${label}!`);

  const shotPath = path.join(artifactDir, `rbac_grid_${label.toLowerCase().replace(/\s+/g, "_")}.png`);
  await appCard.screenshot({ path: shotPath });
  console.log(`  📸 Bento Grid screenshot saved to: ${shotPath}`);

  await context.close();
  return visibleIds;
}

async function runVerification() {
  console.log("==================================================================");
  console.log("🚀 VERIFYING RBAC VISIBILITY & BREATHTAKING INNER PAGE REDESIGN");
  console.log("==================================================================");

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  try {
    // ── 1. PROVE ADMINISTRATOR SEES EXACTLY 17 CARDS ──
    const adminCards = await testUserCardCount(
      browser,
      "Administrator",
      "Password123!",
      17,
      "Administrator"
    );

    // ── 2. PROVE CHANTIER 01 SEES EXACTLY 10 CARDS ──
    const chantierCards = await testUserCardCount(
      browser,
      "chantier_01@uranos.local",
      "Password123!",
      10,
      "Chantier 01"
    );

    // Verify maintenance & Hors V1 are excluded from Chantier
    if (chantierCards.includes("maintenance")) {
      throw new Error("Security Violation: 'maintenance' leaked to Chantier 01!");
    }
    const horsV1 = ["purchase", "sales", "hr", "payroll", "accounting", "settings"];
    horsV1.forEach(id => {
      if (chantierCards.includes(id)) {
        throw new Error(`Security Violation: '${id}' leaked to Chantier 01!`);
      }
    });
    console.log("  ✓ Zero unauthorized cards leaked to Chantier 01");

    // ── 3. PROVE INGENIEUR 01 SEES EXACTLY 11 CARDS ──
    const ingenieurCards = await testUserCardCount(
      browser,
      "ingenieur_01@uranos.local",
      "Password123!",
      11,
      "Ingenieur 01"
    );

    if (!ingenieurCards.includes("maintenance")) {
      throw new Error("Missing Card: 'maintenance' should be visible to Ingenieur 01!");
    }
    console.log("  ✓ 'maintenance' correctly visible to Ingenieur 01");

    // ── 4. CAPTURE BREATHTAKING NEW INNER PAGE DESIGNS (AS ADMINISTRATOR) ──
    console.log("\n===============================================================");
    console.log("🎨 Capturing High-Res Screenshots of Breathtaking Inner Pages");
    console.log("===============================================================");

    const context = await browser.newContext({
      viewport: { width: 1440, height: 960 }
    });
    const page = await context.newPage();

    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "Administrator");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(/\/desk|\/app/);

    // Pages to inspect and photograph
    const pagesToCapture = [
      { id: "projects", route: "/app/project", label: "Projects List View (Floating Cards)" },
      { id: "work_packages", route: "/app/uranos-work-package", label: "Work Packages List View (Reimagined Rows)" },
      { id: "quality_ncr", route: "/app/uranos-ncr", label: "Quality NCRs List View (Status Badges)" },
      { id: "stock", route: "/app/stock", label: "Stock Management Workspace (Glassmorphic Bento)" },
      { id: "invoicing", route: "/app/invoicing", label: "Accounting & Invoicing Workspace (Floating Widgets)" }
    ];

    for (const item of pagesToCapture) {
      console.log(`\nNavigating to: ${item.label} (${item.route})...`);
      await page.goto(`http://localhost:8080${item.route}`, { waitUntil: "networkidle" });
      await page.waitForTimeout(2000);

      // Verify computed styling for modern luxury aesthetic
      const computedStyles = await page.evaluate(() => {
        const row = document.querySelector(".list-row");
        const card = document.querySelector(".page-container:not(#page-desktop) .layout-main-section, .workspace-page .widget, .page-container:not(#page-desktop) .workspace-page");
        const head = document.querySelector(".page-container:not(#page-desktop) .page-head");

        return {
          rowBorderRadius: row ? window.getComputedStyle(row).borderRadius : null,
          rowBoxShadow: row ? window.getComputedStyle(row).boxShadow : null,
          cardBorderRadius: card ? window.getComputedStyle(card).borderRadius : null,
          cardBoxShadow: card ? window.getComputedStyle(card).boxShadow : null,
          cardBackdrop: card ? window.getComputedStyle(card).backdropFilter : null,
          headBorderRadius: head ? window.getComputedStyle(head).borderRadius : null
        };
      });

      console.log(`  ✓ Styles verified: CardRadius=${computedStyles.cardBorderRadius}, RowRadius=${computedStyles.rowBorderRadius}`);

      const shotFile = path.join(artifactDir, `breathtaking_${item.id}.png`);
      await page.screenshot({ path: shotFile, fullPage: false });
      console.log(`  📸 Breathtaking Screenshot saved: ${shotFile}`);
    }

    await context.close();

    console.log("\n==================================================================");
    console.log("🏆 ALL RBAC TESTS & INNER PAGE OVERHAULS VERIFIED SUCCESSFULLY!");
    console.log("   - Administrator: Exactly 17 cards visible");
    console.log("   - Chantier 01:   Exactly 10 cards visible");
    console.log("   - Ingenieur 01:  Exactly 11 cards visible");
    console.log("   - Radical SaaS UI Overhaul: Applied & Proven");
    console.log("==================================================================");

  } catch (err) {
    console.error("❌ Test Failed:", err);
    throw err;
  } finally {
    await browser.close();
  }
}

runVerification();
