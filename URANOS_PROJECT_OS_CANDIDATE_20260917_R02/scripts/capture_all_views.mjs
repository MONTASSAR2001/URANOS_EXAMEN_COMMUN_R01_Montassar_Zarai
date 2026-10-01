import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function main() {
  const screenshotsDir = path.resolve("./screenshots");
  await mkdir(screenshotsDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 2
  });
  const page = await context.newPage();

  console.log("1. Authenticating as direction_01@uranos.local...");
  await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1000);

  const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
  await emailField.waitFor({ timeout: 10000 });
  await emailField.fill("direction_01@uranos.local");
  await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
  await page.click("#btnContinue, .btn-login, button[type='submit']");
  await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { waitUntil: "domcontentloaded", timeout: 25000 });
  await page.waitForTimeout(4000);
  console.log("✓ Logged in successfully");

  // 1. Main Bento Grid Desk
  console.log("2. Capturing Main Glassmorphic Bento Grid Desk...");
  await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
  await page.waitForSelector("#navbar-search, #gv-main-dashboard, .layout-main", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(3000);
  await page.screenshot({ path: path.join(screenshotsDir, "01_main_desk_bento.png"), fullPage: false });
  console.log("✓ Captured 01_main_desk_bento.png");

  // 2. Blocker Executive Dashboard with Leaflet GIS Fleet Map
  console.log("3. Capturing Blocker Executive Dashboard with GIS Fleet Map...");
  await page.goto("http://localhost:8080/app/blocker-dashboard", { waitUntil: "networkidle" });
  await page.waitForSelector("#uranosGisMapCard, #uranos-leaflet-map, .uranos-dashboard", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(4000);
  await page.screenshot({ path: path.join(screenshotsDir, "02_blocker_dashboard_gis.png"), fullPage: false });
  console.log("✓ Captured 02_blocker_dashboard_gis.png");

  // 3. 4-Column Blocker Kanban Board
  console.log("4. Capturing Blocker Kanban Board...");
  await page.goto("http://localhost:8080/app/blocker-kanban", { waitUntil: "networkidle" });
  await page.waitForSelector(".uranos-kanban-dashboard, #kanban-col-open, .kanban-board", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(3500);
  await page.screenshot({ path: path.join(screenshotsDir, "03_blocker_kanban.png"), fullPage: false });
  console.log("✓ Captured 03_blocker_kanban.png");

  // 4. Dual-Engine AI Copilot Page
  console.log("5. Capturing Dual-Engine AI Copilot Page...");
  await page.goto("http://localhost:8080/app/uranos-ai-copilot/PV-0004", { waitUntil: "networkidle" });
  await page.waitForSelector("#uac-project-select, .uac-dashboard, .uac-chat-container", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(4000);
  await page.screenshot({ path: path.join(screenshotsDir, "04_uranos_ai_copilot.png"), fullPage: false });
  console.log("✓ Captured 04_uranos_ai_copilot.png");

  // 5. Security & Access Audit Matrix
  console.log("6. Capturing Security & Access Audit Matrix...");
  await page.goto("http://localhost:8080/app/access-audit", { waitUntil: "networkidle" });
  await page.waitForSelector(".uranos-audit-dashboard, .uranos-chic-saas-view", { timeout: 15000 }).catch(() => {});
  await page.waitForTimeout(4000);
  await page.screenshot({ path: path.join(screenshotsDir, "05_access_audit_matrix.png"), fullPage: false });
  console.log("✓ Captured 05_access_audit_matrix.png");

  await context.close();

  // Mobile Viewport (390x844)
  console.log("7. Capturing Mobile Responsive Views (390x844)...");
  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    isMobile: true,
    hasTouch: true
  });
  const mobilePage = await mobileContext.newPage();

  // Login on mobile
  await mobilePage.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
  await mobilePage.waitForTimeout(1000);
  const mEmail = mobilePage.locator("#loginEmail, #login_email, input[name='usr']").first();
  await mEmail.fill("direction_01@uranos.local");
  await mobilePage.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
  await mobilePage.click("#btnContinue, .btn-login, button[type='submit']");
  await mobilePage.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { waitUntil: "domcontentloaded", timeout: 25000 });
  await mobilePage.waitForTimeout(4000);

  // Mobile Desk
  await mobilePage.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
  await mobilePage.waitForSelector("#navbar-search, #gv-main-dashboard, .layout-main", { timeout: 15000 }).catch(() => {});
  await mobilePage.waitForTimeout(3000);
  await mobilePage.screenshot({ path: path.join(screenshotsDir, "06_mobile_desk.png"), fullPage: false });
  console.log("✓ Captured 06_mobile_desk.png");

  // Mobile Blocker Kanban
  await mobilePage.goto("http://localhost:8080/app/blocker-kanban", { waitUntil: "networkidle" });
  await mobilePage.waitForSelector(".uranos-kanban-dashboard, #kanban-col-open", { timeout: 15000 }).catch(() => {});
  await mobilePage.waitForTimeout(3000);
  await mobilePage.screenshot({ path: path.join(screenshotsDir, "07_mobile_blocker.png"), fullPage: false });
  console.log("✓ Captured 07_mobile_blocker.png");

  await mobileContext.close();
  await browser.close();
  console.log("All screenshots captured successfully!");
}

main().catch(err => {
  console.error("Error capturing screenshots:", err);
  process.exit(1);
});
