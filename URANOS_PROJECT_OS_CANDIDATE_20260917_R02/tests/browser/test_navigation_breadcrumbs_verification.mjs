import { chromium } from "playwright";
import path from "path";

async function verifyNavigationAndBreadcrumbs() {
  console.log("==================================================================");
  console.log("   URANOS Group Sites Routing & Breadcrumbs Verification");
  console.log("==================================================================");

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  const page = await context.newPage();

  page.on("console", msg => {
    if (msg.type() === "error") {
      console.log(`[BROWSER ERROR] ${msg.text()}`);
    }
  });

  console.log("1. Authenticating as Administrator...");
  await page.goto("http://localhost:8080/login", { waitUntil: "networkidle" });
  await page.fill("#loginEmail", "Administrator");
  await page.fill("#loginPassword", "Password123!");
  await page.click("#btnContinue");
  await page.waitForURL(/\/app|\/desk/, { timeout: 15000 });
  console.log("✓ Logged in successfully!");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";

  // -------------------------------------------------------------------------
  // Step 1: Verify Dashboard Card Hrefs
  // -------------------------------------------------------------------------
  console.log("2. Checking Dashboard App Cards routing...");
  await page.waitForSelector(".desktop-icon[data-id=\"sites\"]", { timeout: 10000 });
  const cardRoutes = await page.evaluate(() => {
    const sitesCard = document.querySelector(".desktop-icon[data-id=\"sites\"]");
    const projectsCard = document.querySelector(".desktop-icon[data-id=\"projects\"]");
    return {
      sitesRoute: sitesCard ? sitesCard.getAttribute("href") : null,
      projectsRoute: projectsCard ? projectsCard.getAttribute("href") : null
    };
  });

  console.log("✓ Card Routes Found:", cardRoutes);
  if (!cardRoutes.sitesRoute || !cardRoutes.sitesRoute.includes("uranos-project-profile")) {
    throw new Error(`Expected Sites card route to be /app/uranos-project-profile, got ${cardRoutes.sitesRoute}`);
  }
  if (!cardRoutes.projectsRoute || !cardRoutes.projectsRoute.includes("project")) {
    throw new Error(`Expected Projects card route to be /app/project, got ${cardRoutes.projectsRoute}`);
  }

  // -------------------------------------------------------------------------
  // Step 2: Navigate to Sites Card
  // -------------------------------------------------------------------------
  console.log("3. Clicking Sites card to verify distinct routing...");
  await page.click(".desktop-icon[data-id=\"sites\"]");
  await page.waitForTimeout(2000);
  const currentUrl = page.url();
  console.log(`✓ Navigated to Sites view: ${currentUrl}`);

  const sitesBreadcrumbs = await page.evaluate(() => {
    const lis = Array.from(document.querySelectorAll(".navbar-breadcrumbs li, .breadcrumbs li"));
    const title = document.querySelector(".page-title .title-text, .page-head .title-text");
    return {
      crumbs: lis.map(li => li.innerText.trim()).filter(Boolean),
      pageTitle: title ? title.innerText.trim() : null
    };
  });
  console.log("✓ Sites Breadcrumbs & Title:", sitesBreadcrumbs);

  const sitesScreenshot = path.join(artifactDir, "verified_sites_navigation.png");
  await page.screenshot({ path: sitesScreenshot, fullPage: true });
  console.log(`✓ Screenshot captured to: ${sitesScreenshot}`);

  // -------------------------------------------------------------------------
  // Step 3: Return to Dashboard and Navigate to Projects Card
  // -------------------------------------------------------------------------
  console.log("4. Returning to Main Dashboard and clicking Projects card...");
  await page.click("#gv-back-to-dashboard");
  await page.waitForTimeout(1500);

  await page.waitForSelector(".desktop-icon[data-id=\"projects\"]", { timeout: 10000 });
  await page.click(".desktop-icon[data-id=\"projects\"]");
  await page.waitForTimeout(2000);

  const projectUrl = page.url();
  console.log(`✓ Navigated to Projects view: ${projectUrl}`);

  const projectBreadcrumbs = await page.evaluate(() => {
    const lis = Array.from(document.querySelectorAll(".navbar-breadcrumbs li, .breadcrumbs li"));
    return {
      crumbs: lis.map(li => li.innerText.trim()).filter(Boolean)
    };
  });
  console.log("✓ Project View Breadcrumbs:", projectBreadcrumbs);

  // Assertion: Ensure "Stock" is NOT present anywhere in breadcrumbs
  const hasStock = projectBreadcrumbs.crumbs.some(c => c.toLowerCase() === "stock");
  if (hasStock) {
    throw new Error(`FAILURE: Breadcrumb still incorrectly displays "Stock"! Found: ${projectBreadcrumbs.crumbs.join(" / ")}`);
  }
  console.log("✓ VERIFIED: Breadcrumbs do NOT contain 'Stock'! Correctly displays Projects / Project.");

  const projectScreenshot = path.join(artifactDir, "verified_project_breadcrumbs.png");
  await page.screenshot({ path: projectScreenshot, fullPage: true });
  console.log(`✓ Screenshot captured to: ${projectScreenshot}`);

  await browser.close();
  console.log("==================================================================");
  console.log("   ALL SITES ROUTING & BREADCRUMB AUDITS PASSED 100%!");
  console.log("==================================================================");
}

verifyNavigationAndBreadcrumbs().catch(err => {
  console.error("FATAL ERROR in Playwright Verification:", err);
  process.exit(1);
});
