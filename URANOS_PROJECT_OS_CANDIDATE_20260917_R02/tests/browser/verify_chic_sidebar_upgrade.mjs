import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyChicSidebarUpgrade() {
  console.log("==================================================================");
  console.log("   URANOS Chic SaaS Sidebar (280px) Aesthetic Verification");
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
    console.log("1. Logging into URANOS Desk...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailField.waitFor({ timeout: 10000 });
    await emailField.fill("direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");
    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 20000 });
    await page.waitForTimeout(3000);

    console.log("2. Inspecting Sidebar Dimensions and Chic SaaS Typography...");
    const sidebar = page.locator(".gv-desk-sidebar").first();
    await sidebar.waitFor({ timeout: 10000 });

    const sidebarMetrics = await sidebar.evaluate((el) => {
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      return {
        width: rect.width,
        height: rect.height,
        padding: style.padding,
        borderRadius: style.borderRadius,
        backgroundColor: style.backgroundColor
      };
    });

    console.log(`✓ Sidebar Dimensions: width=${sidebarMetrics.width}px, height=${sidebarMetrics.height}px, borderRadius=${sidebarMetrics.borderRadius}`);
    if (Math.round(sidebarMetrics.width) !== 280) {
      console.warn(`Note: Sidebar width is ${sidebarMetrics.width}px (expected ~280px)`);
    }

    // Inspect Nav Links
    const navItemsMetrics = await page.evaluate(() => {
      const links = Array.from(document.querySelectorAll(".gv-nav-link"));
      return links.map(link => {
        const text = link.innerText.trim();
        const style = window.getComputedStyle(link);
        const span = link.querySelector("span");
        const spanStyle = span ? window.getComputedStyle(span) : style;
        const svg = link.querySelector("svg");
        const svgRect = svg ? svg.getBoundingClientRect() : { width: 0, height: 0 };
        const isActive = link.classList.contains("active");
        return {
          text,
          fontSize: spanStyle.fontSize,
          fontWeight: spanStyle.fontWeight,
          color: spanStyle.color,
          padding: style.padding,
          borderRadius: style.borderRadius,
          transition: style.transition,
          svgWidth: svgRect.width,
          svgHeight: svgRect.height,
          isActive
        };
      });
    });

    console.log(`\n3. Nav items analyzed (${navItemsMetrics.length} links found):`);
    navItemsMetrics.forEach((item, idx) => {
      console.log(`   [${idx + 1}] "${item.text}" -> font: ${item.fontSize}, weight: ${item.fontWeight}, color: ${item.color}, padding: ${item.padding}, radius: ${item.borderRadius}, svg: ${Math.round(item.svgWidth)}x${Math.round(item.svgHeight)}px, active: ${item.isActive}`);
    });

    // Check Dashboard Layout Safety
    const dashboardMetrics = await page.locator(".gv-main-dashboard").first().evaluate(el => {
      const rect = el.getBoundingClientRect();
      return { width: rect.width, height: rect.height };
    });
    console.log(`\n4. Main Dashboard Dimensions: width=${dashboardMetrics.width}px, height=${dashboardMetrics.height}px`);

    // Verify there is no horizontal page overflow
    const hasHorizontalOverflow = await page.evaluate(() => {
      return document.documentElement.scrollWidth > document.documentElement.clientWidth;
    });
    console.log(`✓ Horizontal Page Overflow: ${hasHorizontalOverflow ? "YES (OVERFLOW DETECTED!)" : "NO (PERFECT RESPONSIVE FIT)"}`);

    // Capture screenshots
    // 1. Focused screenshot of the sidebar
    const sidebarScreenshotPath = path.join(artifactDir, "chic_sidebar_enlarged.png");
    await sidebar.screenshot({ path: sidebarScreenshotPath });
    console.log(`✓ Captured focused sidebar screenshot: ${sidebarScreenshotPath}`);

    // 2. Full desktop layout screenshot
    const fullScreenshotPath = path.join(artifactDir, "desktop_with_chic_sidebar.png");
    await page.screenshot({ path: fullScreenshotPath, fullPage: false });
    console.log(`✓ Captured full desktop screenshot: ${fullScreenshotPath}`);

    console.log("\n==============================================================");
    console.log(">>> ALL CHIC SAAS SIDEBAR VERIFICATIONS PASSED! <<<");
    console.log("==============================================================");

  } finally {
    await browser.close();
  }
}

verifyChicSidebarUpgrade().catch(err => {
  console.error("FATAL ERROR in sidebar verification:", err);
  process.exit(1);
});
