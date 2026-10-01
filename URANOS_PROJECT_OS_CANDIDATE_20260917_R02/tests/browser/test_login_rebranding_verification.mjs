import { chromium } from "playwright";
import fs from "fs";
import path from "path";

async function verifyLoginRebranding() {
  console.log("==================================================================");
  console.log("   URANOS Group Rebranding QA & Playwright Automated Audit");
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

  console.log("1. Navigating to http://localhost:8080/login...");
  await page.goto("http://localhost:8080/login", { waitUntil: "networkidle" });

  // 1. Title verification
  const title = await page.title();
  console.log(`✓ Page Title: "${title}"`);
  if (!title.includes("URANOS Group") || title.includes("GreenVolt")) {
    throw new Error(`Title assertion failed: ${title}`);
  }

  // 2. Logo verification
  const logoSelector = 'img[src*="uranos-logo.jpeg"]';
  await page.waitForSelector(logoSelector, { timeout: 5000 });
  const logoInfo = await page.$eval(logoSelector, img => ({
    src: img.src,
    alt: img.alt,
    naturalWidth: img.naturalWidth,
    naturalHeight: img.naturalHeight,
    displayedWidth: img.clientWidth,
    displayedHeight: img.clientHeight,
    isComplete: img.complete
  }));
  console.log("✓ Logo Image Verified:", logoInfo);
  if (!logoInfo.isComplete || logoInfo.naturalWidth === 0) {
    throw new Error("Logo image failed to load or has 0 natural dimensions!");
  }

  // 3. Brand Text verification
  const brandTitleText = await page.$eval(".brand-title", el => el.textContent.trim());
  console.log(`✓ Header Brand Title: "${brandTitleText}"`);
  if (brandTitleText !== "URANOS Group") {
    throw new Error(`Expected ".brand-title" to be "URANOS Group", got "${brandTitleText}"`);
  }

  // 4. Hero section branding
  const heroBadgeText = await page.$eval(".hero-badge-text", el => el.textContent.trim());
  console.log(`✓ Hero Badge Text: "${heroBadgeText}"`);
  if (!heroBadgeText.includes("URANOS Group")) {
    throw new Error(`Expected hero badge to contain "URANOS Group", got "${heroBadgeText}"`);
  }

  const heroDescText = await page.$eval(".hero-description", el => el.textContent.trim());
  console.log(`✓ Hero Description: "${heroDescText}"`);
  if (!heroDescText.includes("URANOS Group")) {
    throw new Error(`Expected hero description to contain "URANOS Group"`);
  }

  // 5. Welcome Card Subtitle
  const cardSubtitle = await page.$eval(".card-subtitle", el => el.textContent.trim());
  console.log(`✓ Card Subtitle: "${cardSubtitle}"`);
  if (!cardSubtitle.includes("URANOS Group") || cardSubtitle.includes("GreenVolt")) {
    throw new Error(`Card subtitle assertion failed: "${cardSubtitle}"`);
  }

  // 6. Zero GreenVolt occurrences across entire page body
  const bodyText = await page.$eval("body", el => el.innerText);
  const greenVoltCount = (bodyText.match(/GreenVolt/gi) || []).length;
  console.log(`✓ "GreenVolt" occurrences in page text: ${greenVoltCount}`);
  if (greenVoltCount > 0) {
    throw new Error(`Found ${greenVoltCount} residual occurrences of "GreenVolt" on page!`);
  }

  // 7. Capture High-Resolution Screenshot
  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";
  const screenshotPath = path.join(artifactDir, "rebranded_login_verified.png");
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`✓ High-resolution screenshot captured to: ${screenshotPath}`);

  // 8. Capture Mobile Viewport Screenshot for UX completeness
  await page.setViewportSize({ width: 390, height: 844 });
  const mobileScreenshotPath = path.join(artifactDir, "rebranded_login_mobile_verified.png");
  await page.screenshot({ path: mobileScreenshotPath, fullPage: true });
  console.log(`✓ Mobile responsive screenshot captured to: ${mobileScreenshotPath}`);

  // 9. Functional verification: Authenticate as Administrator
  await page.setViewportSize({ width: 1440, height: 900 });
  console.log("7. Testing Authentication Flow with Rebranded Form...");
  await page.fill("#loginEmail", "Administrator");
  await page.fill("#loginPassword", "Password123!");
  await page.click("#btnContinue");

  await page.waitForURL(/\/app|\/desk/, { timeout: 15000 });
  console.log("✓ Login successful! Redirected to authenticated Desk:", page.url());

  await browser.close();
  console.log("==================================================================");
  console.log("   ALL REBRANDING CHECKS & VERIFICATIONS PASSED 100%!");
  console.log("==================================================================");
}

verifyLoginRebranding().catch(err => {
  console.error("FATAL ERROR in Playwright Verification:", err);
  process.exit(1);
});
