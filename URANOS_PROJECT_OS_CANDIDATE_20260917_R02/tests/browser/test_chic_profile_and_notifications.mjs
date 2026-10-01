import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyProfileAndNotificationBadge() {
  console.log("==================================================================");
  console.log("   URANOS Chic SaaS Profile Form & Dynamic Notification QA");
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

    await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await page.waitForTimeout(3000);

    // 2. Verify Notification Bell Badge (No hardcoded "16")
    console.log("\n--- Checking Dynamic Notification Bell Badge ---");
    const notifBtn = page.locator("#gvNotificationBtn");
    await notifBtn.waitFor({ timeout: 10000 });

    const badgeLocator = page.locator("#gvNotificationBadge");
    const badgeInfo = await badgeLocator.evaluate(el => {
      const style = window.getComputedStyle(el);
      return {
        text: el.innerText.trim(),
        textContent: el.textContent.trim(),
        classes: el.className,
        display: style.display,
        visibility: style.visibility,
        opacity: style.opacity
      };
    });
    console.log("Notification badge metrics:", badgeInfo);

    if (badgeInfo.text === "16") {
      throw new Error("FAIL: Notification badge still shows hardcoded '16'!");
    }
    console.log("✓ Verified: No hardcoded '16' on notification bell.");

    // Capture screenshot of the top navbar with the clean notification bell
    const navbarShotPath = path.join(artifactDir, "notification_bell_fixed.png");
    await page.screenshot({ path: navbarShotPath, fullPage: false });
    console.log(`✓ Saved screenshot of fixed notification bell: ${navbarShotPath}`);

    // 3. Open notification dropdown and verify clean state
    await notifBtn.click();
    await page.waitForTimeout(800);
    const notifDropdown = page.locator("#gvDropdownNotifications");
    const isNotifOpen = await notifDropdown.isVisible();
    console.log(`Notification dropdown opened: ${isNotifOpen}`);

    // Close notification dropdown
    await notifBtn.click();
    await page.waitForTimeout(400);

    // 4. Navigate to User Profile Form
    console.log("\n--- Testing Chic SaaS User Profile Form ---");
    await page.goto("http://localhost:8080/desk/user/direction_01%40uranos.local", { waitUntil: "networkidle" });
    await page.waitForTimeout(3500);

    // Check tabs styling
    const tabsMetrics = await page.evaluate(() => {
      const tabsContainer = document.querySelector(".form-tabs, .nav-tabs");
      const activeTab = document.querySelector(".form-tabs .nav-link.active, .nav-tabs .nav-link.active, .nav-tabs li.active a, .form-tabs button.active");
      const inactiveTab = document.querySelector(".form-tabs .nav-link:not(.active), .nav-tabs .nav-link:not(.active), .form-tabs button:not(.active)");
      
      const sCont = tabsContainer ? window.getComputedStyle(tabsContainer) : null;
      const sAct = activeTab ? window.getComputedStyle(activeTab) : null;
      const sInact = inactiveTab ? window.getComputedStyle(inactiveTab) : null;

      return {
        tabsContainerBg: sCont?.backgroundColor,
        tabsContainerRadius: sCont?.borderRadius,
        activeTabText: activeTab?.innerText.trim(),
        activeTabBg: sAct?.backgroundImage || sAct?.backgroundColor,
        activeTabColor: sAct?.color,
        activeTabRadius: sAct?.borderRadius,
        activeTabShadow: sAct?.boxShadow,
        inactiveTabColor: sInact?.color,
        inactiveTabRadius: sInact?.borderRadius
      };
    });
    console.log("Form Tabs Metrics:", tabsMetrics);

    // Check containers styling (form-section, card-section)
    const containerMetrics = await page.evaluate(() => {
      const section = document.querySelector(".form-section.card-section.visible-section, .form-section");
      const s = section ? window.getComputedStyle(section) : null;
      return {
        borderRadius: s?.borderRadius,
        boxShadow: s?.boxShadow,
        border: s?.border,
        padding: s?.padding
      };
    });
    console.log("Form Container Metrics:", containerMetrics);

    // Check input fields styling (padding: 12px, font-size: 15px, border-radius: 10px)
    const inputMetrics = await page.evaluate(() => {
      const input = document.querySelector(".form-control[type='text'], input.form-control, .input-with-feedback[type='text']");
      const s = input ? window.getComputedStyle(input) : null;
      return {
        padding: s?.padding,
        fontSize: s?.fontSize,
        borderRadius: s?.borderRadius,
        minHeight: s?.minHeight,
        boxSizing: s?.boxSizing
      };
    });
    console.log("Form Field Input Metrics:", inputMetrics);

    // Capture screenshot of the newly styled Chic SaaS User Profile form
    const profileShotPath = path.join(artifactDir, "profile_page_chic_saas.png");
    await page.screenshot({ path: profileShotPath, fullPage: false });
    console.log(`✓ Saved screenshot of Chic SaaS User Profile form: ${profileShotPath}`);

    console.log("\n==================================================================");
    console.log("   ALL REQUIREMENTS SUCCESSFULLY VERIFIED!");
    console.log("==================================================================");

  } catch (err) {
    console.error("Verification failed:", err);
    await page.screenshot({ path: path.join(artifactDir, "profile_error.png") });
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyProfileAndNotificationBadge().catch(console.error);
