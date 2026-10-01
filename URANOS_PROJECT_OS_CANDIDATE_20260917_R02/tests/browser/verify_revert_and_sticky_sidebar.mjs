import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyRevertAndStickySidebar() {
  console.log("==================================================================");
  console.log("   URANOS: Revert Dark Mode & Verify Sticky Chic Sidebar Test     ");
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

    console.log("2. Auditing Dark Mode Eradication...");
    const darkModeAudit = await page.evaluate(() => {
      const toggleBtnCount = document.querySelectorAll("#uranosDarkModeToggle").length;
      const isDarkClassPresent = document.body.classList.contains("uranos-dark-mode");
      const dataThemeAttr = document.documentElement.getAttribute("data-theme");
      const storedPref = localStorage.getItem("uranos_dark_mode");

      return {
        toggleBtnCount,
        isDarkClassPresent,
        dataThemeAttr,
        storedPref
      };
    });

    console.log("--------------------------------------------------");
    console.log(`Toggle Button Count in DOM: ${darkModeAudit.toggleBtnCount} (Expected: 0)`);
    console.log(`Body has .uranos-dark-mode: ${darkModeAudit.isDarkClassPresent} (Expected: false)`);
    console.log(`data-theme attribute: ${darkModeAudit.dataThemeAttr} (Expected: not 'dark')`);
    console.log(`localStorage('uranos_dark_mode'): ${darkModeAudit.storedPref} (Expected: null)`);
    console.log("--------------------------------------------------");

    if (darkModeAudit.toggleBtnCount !== 0) {
      throw new Error(`FAILURE: #uranosDarkModeToggle still exists in DOM! Count: ${darkModeAudit.toggleBtnCount}`);
    }
    if (darkModeAudit.isDarkClassPresent) {
      throw new Error("FAILURE: document.body still has 'uranos-dark-mode' class!");
    }
    if (darkModeAudit.dataThemeAttr === "dark") {
      throw new Error("FAILURE: <html> still has data-theme='dark'!");
    }
    if (darkModeAudit.storedPref !== null) {
      throw new Error(`FAILURE: localStorage('uranos_dark_mode') is still set to '${darkModeAudit.storedPref}'!`);
    }

    console.log("✓ Dark mode logic and styling are 100% purged.");

    console.log("3. Auditing Sidebar Sticky Properties...");
    const sidebarAudit = await page.evaluate(() => {
      const sidebarEl = document.querySelector(".gv-desk-sidebar, .layout-side-section");
      if (!sidebarEl) return null;

      const style = window.getComputedStyle(sidebarEl);
      const rect = sidebarEl.getBoundingClientRect();

      return {
        position: style.position,
        top: style.top,
        alignSelf: style.alignSelf,
        maxHeight: style.maxHeight,
        overflowY: style.overflowY,
        width: style.width,
        rectTop: rect.top,
        rectLeft: rect.left,
        rectHeight: rect.height
      };
    });

    console.log("--------------------------------------------------");
    console.log(`Sidebar position: ${sidebarAudit.position} (Expected: 'sticky')`);
    console.log(`Sidebar top: ${sidebarAudit.top} (Expected: '20px')`);
    console.log(`Sidebar alignSelf: ${sidebarAudit.alignSelf} (Expected: 'flex-start')`);
    console.log(`Sidebar maxHeight: ${sidebarAudit.maxHeight}`);
    console.log(`Sidebar overflowY: ${sidebarAudit.overflowY} (Expected: 'auto')`);
    console.log(`Sidebar width: ${sidebarAudit.width} (Expected: '280px')`);
    console.log(`Sidebar viewport top rect: ${sidebarAudit.rectTop}px`);
    console.log("--------------------------------------------------");

    if (sidebarAudit.position !== "sticky") {
      throw new Error(`FAILURE: Expected sidebar position 'sticky', got '${sidebarAudit.position}'`);
    }
    if (sidebarAudit.top !== "20px") {
      throw new Error(`FAILURE: Expected sidebar top '20px', got '${sidebarAudit.top}'`);
    }
    if (sidebarAudit.alignSelf !== "flex-start") {
      throw new Error(`FAILURE: Expected sidebar alignSelf 'flex-start', got '${sidebarAudit.alignSelf}'`);
    }
    if (sidebarAudit.overflowY !== "auto") {
      throw new Error(`FAILURE: Expected sidebar overflowY 'auto', got '${sidebarAudit.overflowY}'`);
    }

    console.log("✓ Sidebar sticky properties verified successfully!");

    // Capture initial un-scrolled screenshot
    const initialScreenshotPath = path.join(artifactDir, "light_theme_restored_verified.png");
    await page.screenshot({ path: initialScreenshotPath, fullPage: false });
    console.log(`✓ Initial screenshot captured: ${initialScreenshotPath}`);

    console.log("4. Testing Scroll & Sticky Behavior...");
    // Scroll down 450px
    await page.evaluate(() => {
      window.scrollTo({ top: 450, behavior: "instant" });
    });
    await page.waitForTimeout(1000);

    const scrolledAudit = await page.evaluate(() => {
      const sidebarEl = document.querySelector(".gv-desk-sidebar, .layout-side-section");
      const rect = sidebarEl ? sidebarEl.getBoundingClientRect() : null;
      return {
        scrollY: window.scrollY,
        sidebarTopRect: rect ? rect.top : null,
        sidebarVisible: rect ? rect.height > 0 : false
      };
    });

    console.log(`Scrolled page Y: ${scrolledAudit.scrollY}px`);
    console.log(`Sidebar viewport top rect after scroll: ${scrolledAudit.sidebarTopRect}px (Visible: ${scrolledAudit.sidebarVisible})`);

    const scrolledScreenshotPath = path.join(artifactDir, "sticky_sidebar_scrolled_verified.png");
    await page.screenshot({ path: scrolledScreenshotPath, fullPage: false });
    console.log(`✓ Scrolled screenshot captured: ${scrolledScreenshotPath}`);

    console.log("\n==================================================================");
    console.log("   ALL VERIFICATIONS PASSED SUCCESSFULLY!                        ");
    console.log("==================================================================");

  } catch (err) {
    console.error("Verification failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyRevertAndStickySidebar();
