import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyRevertDarkMode() {
  console.log("==================================================================");
  console.log("   URANOS Revert Dark Mode: Verification of Chic SaaS Light Theme ");
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
    console.log("1. Logging into URANOS Desk as direction_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    const isLoginVisible = await emailField.isVisible({ timeout: 5000 }).catch(() => false);
    if (isLoginVisible) {
      await emailField.fill("direction_01@uranos.local");
      await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
      await page.click("#btnContinue, .btn-login, button[type='submit']");
      await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { waitUntil: "domcontentloaded", timeout: 25000 });
    } else {
      await page.goto("http://localhost:8080/app", { waitUntil: "domcontentloaded" });
    }
    await page.waitForTimeout(3000);

    console.log("2. Auditing DOM and Theme State...");
    const auditResult = await page.evaluate(() => {
      const toggleBtnCount = document.querySelectorAll("#uranosDarkModeToggle").length;
      const isDarkClassPresent = document.body.classList.contains("uranos-dark-mode");
      const dataThemeAttr = document.documentElement.getAttribute("data-theme");
      const storedPref = localStorage.getItem("uranos_dark_mode");

      const bodyBg = window.getComputedStyle(document.body).backgroundColor;
      const navbarBg = window.getComputedStyle(document.querySelector(".desktop-navbar") || document.body).backgroundColor;
      const cardEl = document.querySelector(".gv-metric-card, .frappe-card, .uranos-gis-map-card, .widget");
      const cardBg = cardEl ? window.getComputedStyle(cardEl).backgroundColor : "";
      const textColor = window.getComputedStyle(document.body).color;

      return {
        toggleBtnCount,
        isDarkClassPresent,
        dataThemeAttr,
        storedPref,
        bodyBg,
        navbarBg,
        cardBg,
        textColor
      };
    });

    console.log("--------------------------------------------------");
    console.log(`Toggle Button Count in DOM: ${auditResult.toggleBtnCount} (Expected: 0)`);
    console.log(`Body has .uranos-dark-mode: ${auditResult.isDarkClassPresent} (Expected: false)`);
    console.log(`data-theme attribute: ${auditResult.dataThemeAttr} (Expected: null or not 'dark')`);
    console.log(`localStorage('uranos_dark_mode'): ${auditResult.storedPref} (Expected: null)`);
    console.log(`Body Background Color: ${auditResult.bodyBg}`);
    console.log(`Navbar Background Color: ${auditResult.navbarBg}`);
    console.log(`Card Background Color: ${auditResult.cardBg}`);
    console.log(`Body Text Color: ${auditResult.textColor}`);
    console.log("--------------------------------------------------");

    if (auditResult.toggleBtnCount !== 0) {
      throw new Error(`FAILURE: #uranosDarkModeToggle is still in DOM! Count: ${auditResult.toggleBtnCount}`);
    }
    if (auditResult.isDarkClassPresent) {
      throw new Error("FAILURE: document.body still has 'uranos-dark-mode' class!");
    }
    if (auditResult.dataThemeAttr === "dark") {
      throw new Error("FAILURE: <html> still has data-theme='dark'!");
    }
    if (auditResult.storedPref !== null) {
      throw new Error(`FAILURE: localStorage('uranos_dark_mode') is still set to '${auditResult.storedPref}'!`);
    }

    console.log("✓ All Dark Mode logic and classes are completely absent!");
    console.log("✓ Light Theme verified active!");

    // Capture screenshot of main dashboard
    const screenshotPath = path.join(artifactDir, "light_theme_restored_verified.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`✓ Screenshot captured: ${screenshotPath}`);

    console.log("\n==================================================================");
    console.log("   REVERT DARK MODE VERIFICATION PASSED SUCCESSFULLY!          ");
    console.log("==================================================================");

  } catch (err) {
    console.error("Verification failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyRevertDarkMode();
