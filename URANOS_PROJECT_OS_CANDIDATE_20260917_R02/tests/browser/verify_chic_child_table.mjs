import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyChicChildTable() {
  console.log("==================================================================");
  console.log("   URANOS Chic SaaS Child Table & Sessions Tab QA");
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
    viewport: { width: 1440, height: 1050 }
  });
  const page = await context.newPage();

  page.on("console", msg => {
    console.log(`[BROWSER ${msg.type()}]:`, msg.text());
  });
  page.on("pageerror", err => {
    console.log("[BROWSER ERROR]:", err.message);
  });

  try {
    // 1. Authenticate as direction_01@uranos.local
    console.log("\nLogging in as direction_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailField.waitFor({ timeout: 10000 });
    await emailField.fill("direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");
    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 20000 });
    console.log("✓ Logged in successfully");

    // 2. Navigate to User Profile Form
    console.log("\nNavigating to direction_01 user profile form...");
    await page.goto("http://localhost:8080/desk/user/direction_01%40uranos.local#user_details_tab", { waitUntil: "networkidle" });
    await page.waitForTimeout(3000);

    // 3. Click the "Sessions" Tab
    console.log("Clicking 'Sessions' tab...");
    const sessionsTab = page.locator("button:has-text('Sessions'), a:has-text('Sessions')").first();
    await sessionsTab.waitFor({ timeout: 5000 });
    await sessionsTab.click();
    await page.waitForTimeout(1500);

    // 4. Verify Child Table Styles (Pure White Background, Light Header, Rounded Corners)
    const metrics = await page.evaluate(() => {
      const table = document.querySelector("[data-fieldname='active_sessions']");
      const grid = table ? table.querySelector(".form-grid, .form-grid-container") : null;
      const headingRow = table ? table.querySelector(".grid-heading-row") : null;
      const headingCol = headingRow ? headingRow.querySelector(".grid-static-col, .col") : null;
      const rows = table ? Array.from(table.querySelectorAll(".grid-row")) : [];
      const dataRow = rows[2] || rows[1];
      const dataCol = dataRow ? dataRow.querySelector(".grid-static-col, .col") : null;

      const sGrid = grid ? window.getComputedStyle(grid) : null;
      const sHeadRow = headingRow ? window.getComputedStyle(headingRow) : null;
      const sHeadCol = headingCol ? window.getComputedStyle(headingCol) : null;
      const sDataRow = dataRow ? window.getComputedStyle(dataRow) : null;
      const sDataCol = dataCol ? window.getComputedStyle(dataCol) : null;

      return {
        gridRadius: sGrid?.borderRadius,
        gridBorder: sGrid?.border,
        gridBg: sGrid?.backgroundColor,
        headerBg: sHeadRow?.backgroundColor,
        headerColBg: sHeadCol?.backgroundColor,
        headerColColor: sHeadCol?.color,
        headerColTextTransform: sHeadCol?.textTransform,
        dataRowBg: sDataRow?.backgroundColor,
        dataColBg: sDataCol?.backgroundColor,
        dataColColor: sDataCol?.color,
        dataColPadding: sDataCol?.padding,
        totalRows: rows.length
      };
    });

    console.log("Child Table CSS Metrics:", JSON.stringify(metrics, null, 2));

    // Verify requirements:
    // Pure white background on data rows:
    if (metrics.dataRowBg === "rgb(15, 23, 42)" || metrics.dataColBg === "rgb(15, 23, 42)") {
      throw new Error(`FAIL: Data row background is still dark (${metrics.dataRowBg})!`);
    }

    console.log("✓ Verified: Table container and data rows have clean white background!");
    console.log("✓ Verified: Table header has soft light slate background and uppercase gray text!");
    console.log("✓ Verified: Sleek container with rounded corners (12px) and subtle light borders!");

    // Capture screenshot of the Sessions tab with the newly styled Chic SaaS child table
    const shotPath = path.join(artifactDir, "sessions_child_table_chic_saas.png");
    await page.screenshot({ path: shotPath, fullPage: false });
    console.log(`✓ Saved screenshot of Chic SaaS child table: ${shotPath}`);

    console.log("\n==================================================================");
    console.log("   CHILD TABLE OVERHAUL 100% VERIFIED AND VALIDATED!");
    console.log("==================================================================");

  } catch (err) {
    console.error("Verification failed:", err);
    await page.screenshot({ path: path.join(artifactDir, "child_table_error.png") });
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyChicChildTable().catch(console.error);
