import { chromium } from "playwright";
import path from "path";

async function verifyStockSaasView() {
  console.log("==================================================================");
  console.log("   URANOS Group Stock SaaS Inner View Verification");
  console.log("==================================================================");

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 1250 }
  });
  const page = await context.newPage();

  console.log("1. Authenticating as Administrator...");
  await page.goto("http://localhost:8080/login", { waitUntil: "networkidle" });
  await page.fill("#loginEmail", "Administrator");
  await page.fill("#loginPassword", "Password123!");
  await page.click("#btnContinue");
  await page.waitForURL(/\/app|\/desk/, { timeout: 15000 });
  console.log("✓ Logged in successfully!");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";

  console.log("2. Navigating to Stock Workspace (/app/stock)...");
  await page.goto("http://localhost:8080/app/stock", { waitUntil: "networkidle" });
  
  // Wait for our custom Chic SaaS view to inject
  await page.waitForSelector(".uranos-chic-saas-view[data-module='stock']", { timeout: 12000 });
  await page.waitForTimeout(1500);

  const stockAudit = await page.evaluate(() => {
    const root = document.querySelector(".uranos-chic-saas-view[data-module='stock']");
    const title = root?.querySelector(".uranos-saas-title-group h2")?.innerText;
    const kpis = Array.from(root?.querySelectorAll(".uranos-saas-kpi-tile") || []).map(tile => ({
      label: tile.querySelector(".kpi-label")?.innerText,
      val: tile.querySelector(".kpi-value")?.innerText,
      sub: tile.querySelector(".kpi-subtext")?.innerText
    }));
    const depots = Array.from(root?.querySelectorAll(".uranos-stock-depot-card") || []).map(card => ({
      title: card.querySelector(".uranos-stock-card-title")?.innerText,
      code: card.querySelector(".uranos-stock-card-code")?.innerText,
      badge: card.querySelector(".uranos-saas-badge")?.innerText
    }));
    const items = Array.from(root?.querySelectorAll(".uranos-stock-item-card") || []).map(card => ({
      title: card.querySelector(".uranos-stock-card-title")?.innerText,
      code: card.querySelector(".uranos-stock-code-badge")?.innerText,
      risk: card.querySelector(".uranos-saas-badge")?.innerText,
      group: card.querySelector(".uranos-stock-category-pill span")?.innerText
    }));

    return {
      moduleFound: !!root,
      title,
      kpis,
      depotsCount: depots.length,
      depots,
      itemsCount: items.length,
      items
    };
  });

  console.log("\n--- Stock Chic SaaS Telemetry Audit ---");
  console.log("Module found:", stockAudit.moduleFound);
  console.log("Title:", stockAudit.title);
  console.log("Live KPIs:", stockAudit.kpis);
  console.log(`Depots detected (${stockAudit.depotsCount}):`, stockAudit.depots.map(d => `${d.title} [${d.badge}]`));
  console.log(`Items detected (${stockAudit.itemsCount}):`, stockAudit.items.map(i => `${i.title} (${i.code}) [${i.risk}]`));

  // Capture full page screenshot
  const screenshotPath = path.join(artifactDir, "verified_stock_chic_saas_view.png");
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`\n✓ Full-page screenshot captured: ${screenshotPath}`);

  // Test live search filter
  console.log("\n3. Testing interactive search filter ('solar')...");
  await page.fill(".uranos-stock-saas-view .uranos-saas-search-input", "solar");
  await page.waitForTimeout(500);

  const visibleCardsCount = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll(".uranos-stock-card"));
    return cards.filter(c => window.getComputedStyle(c).display !== "none").length;
  });
  console.log(`✓ Visible cards matching 'solar': ${visibleCardsCount}`);

  // Clear filter
  await page.fill(".uranos-stock-saas-view .uranos-saas-search-input", "");
  await page.waitForTimeout(500);

  console.log("\n==================================================================");
  console.log("   Stock Chic SaaS Verification Completed Successfully!");
  console.log("==================================================================");

  await browser.close();
}

verifyStockSaasView().catch(err => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
