import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyCleanSearchNavigation() {
  console.log("================================================================================");
  console.log("   URANOS OS — Post-Search Navigation UI Glitch & Clean Top Bar Verification");
  console.log("================================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/4c9276b4-96e1-471d-ad96-037a119e20ff";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const BASE_URL = "http://localhost:8080";

  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 960 },
      ignoreHTTPSErrors: true
    });
    const page = await context.newPage();

    // -------------------------------------------------------------------------
    // 1. LOGIN
    // -------------------------------------------------------------------------
    console.log("1. Logging in as direction_01@uranos.local...");
    await page.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail, #login_email, input[name='usr']", "direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name=\"pwd\"]", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");
    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 25000 });
    await page.waitForTimeout(2500);

    if (page.url().includes("/desk")) {
      await page.goto(`${BASE_URL}/app`, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(2500);
    }
    console.log("✓ Logged into URANOS OS Desk successfully");

    // -------------------------------------------------------------------------
    // 2. SEARCH NAVIGATION TO PROJECT LIST
    // -------------------------------------------------------------------------
    console.log("\n2. Initiating Global Search for 'Project'...");
    const searchBar = page.locator("#navbar-search").first();
    await searchBar.waitFor({ state: "visible", timeout: 10000 });
    await searchBar.focus();
    await page.keyboard.type("Project", { delay: 50 });
    await page.waitForTimeout(1000);

    const projectListItem = page.locator(".awesomplete ul li:has-text('Project List')").first();
    await projectListItem.waitFor({ state: "visible", timeout: 8000 });
    console.log("✓ Search dropdown is open with 'Project List' visible");

    console.log("3. Clicking on 'Project List' search result...");
    await projectListItem.click();

    // Wait for route change to settle
    await page.waitForTimeout(2000);
    console.log("   Current URL after search click:", page.url());

    // -------------------------------------------------------------------------
    // 3. AUDIT DOM STATE AFTER NAVIGATION
    // -------------------------------------------------------------------------
    console.log("\n4. Auditing DOM for post-navigation glitches...");
    const auditResults = await page.evaluate(() => {
      // A. Check search input and Awesomplete dropdown
      const searchInput = document.getElementById("navbar-search");
      const searchUl = document.querySelector(".gv-navbar-search .awesomplete > ul");
      const searchUlVisible = searchUl && window.getComputedStyle(searchUl).display !== "none" && !searchUl.hasAttribute("hidden") && searchUl.children.length > 0;

      // B. Check modal backdrops or overlays
      const modalBackdrops = Array.from(document.querySelectorAll(".modal-backdrop, .freeze-ui, .overlay")).filter(el => {
        const cs = window.getComputedStyle(el);
        return cs.display !== "none" && cs.visibility !== "hidden" && cs.opacity !== "0";
      });

      // C. Check body modal-open class
      const hasModalOpenClass = document.body.classList.contains("modal-open");

      // D. Check for unhidden / rogue dropdown menus
      const visibleDropdowns = Array.from(document.querySelectorAll(".dropdown-menu")).filter(el => {
        const cs = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && cs.display !== "none" && cs.visibility !== "hidden" && !el.classList.contains("show");
      }).map(el => ({
        classes: el.className,
        parent: el.parentElement ? el.parentElement.className : "",
        text: (el.innerText || "").substring(0, 40).replace(/\n+/g, " ")
      }));

      // E. Check page header height and duplication
      const pageHeads = Array.from(document.querySelectorAll(".page-container:not(#page-desktop):not([style*='display: none']) .page-head, .page-head")).filter(h => {
        const rect = h.getBoundingClientRect();
        return rect.height > 0 && window.getComputedStyle(h).display !== "none";
      });

      const activePageHead = pageHeads[0];
      const pageHeadRect = activePageHead ? activePageHead.getBoundingClientRect() : null;

      const backButtons = Array.from(document.querySelectorAll(".page-container:not([style*='display: none']) .gv-return-dashboard-btn, #gv-back-to-dashboard"));
      const diagPills = Array.from(document.querySelectorAll(".page-container:not([style*='display: none']) .gv-realtime-diagnostic-pill"));

      // F. Check activeElement (is search input still focused?)
      const isSearchFocused = document.activeElement === searchInput;

      return {
        searchInputValue: searchInput ? searchInput.value : null,
        isSearchFocused,
        searchUlVisible: !!searchUlVisible,
        modalBackdropsCount: modalBackdrops.length,
        hasModalOpenClass,
        unhiddenDropdownsCount: visibleDropdowns.length,
        unhiddenDropdowns: visibleDropdowns,
        backButtonsCount: backButtons.length,
        diagPillsCount: diagPills.length,
        pageHeadHeight: pageHeadRect ? Math.round(pageHeadRect.height) : 0,
        pageHeadTop: pageHeadRect ? Math.round(pageHeadRect.top) : 0
      };
    });

    console.log("   Audit Results:", JSON.stringify(auditResults, null, 2));

    // Assertions
    if (auditResults.searchInputValue && auditResults.searchInputValue !== "") {
      throw new Error(`FAILED: Search input was not cleared! Value: "${auditResults.searchInputValue}"`);
    }
    console.log("✓ Search input value is cleared");

    if (auditResults.isSearchFocused) {
      throw new Error("FAILED: Search input is still focused after navigation!");
    }
    console.log("✓ Search input is blurred");

    if (auditResults.searchUlVisible) {
      throw new Error("FAILED: Awesomplete dropdown is still visible after navigation!");
    }
    console.log("✓ Search dropdown is closed and hidden");

    if (auditResults.modalBackdropsCount > 0) {
      throw new Error(`FAILED: Found ${auditResults.modalBackdropsCount} lingering modal backdrops!`);
    }
    console.log("✓ No lingering modal backdrops");

    if (auditResults.hasModalOpenClass) {
      throw new Error("FAILED: Body still retains 'modal-open' class!");
    }
    console.log("✓ Body has no 'modal-open' class");

    if (auditResults.unhiddenDropdownsCount > 0) {
      throw new Error(`FAILED: Found ${auditResults.unhiddenDropdownsCount} unhidden dropdown-menus showing: ${JSON.stringify(auditResults.unhiddenDropdowns)}`);
    }
    console.log("✓ All dropdown menus are properly closed and hidden");

    if (auditResults.backButtonsCount > 1) {
      throw new Error(`FAILED: Found duplicate return buttons (${auditResults.backButtonsCount})!`);
    }
    console.log("✓ Return button is unique and clean (no duplication)");

    if (auditResults.pageHeadHeight > 100) {
      throw new Error(`FAILED: Page head height is too large (${auditResults.pageHeadHeight}px) - unhidden elements are still expanding the header!`);
    }
    console.log(`✓ Page header is clean and compact: height=${auditResults.pageHeadHeight}px`);

    // Capture screenshot of the pristine post-search navigation view
    const screenshotPath = path.join(artifactDir, "search_navigation_clean_verified.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`✓ Post-search navigation screenshot saved: ${screenshotPath}`);

    // -------------------------------------------------------------------------
    // 4. TEST SECOND ROUTE VIA RETURN AND SEARCH AGAIN
    // -------------------------------------------------------------------------
    console.log("\n5. Testing Return to Dashboard and secondary search navigation...");
    const backBtn = page.locator("#gv-back-to-dashboard, .gv-return-dashboard-btn").first();
    await backBtn.click();
    await page.waitForTimeout(2000);

    console.log("   Returned to dashboard URL:", page.url());

    // Search for "User"
    const searchBar2 = page.locator("#navbar-search").first();
    await searchBar2.waitFor({ state: "visible", timeout: 10000 });
    await searchBar2.focus();
    await page.keyboard.type("User", { delay: 50 });
    await page.waitForTimeout(1000);

    const userListItem = page.locator(".awesomplete ul li:has-text('User List')").first();
    await userListItem.waitFor({ state: "visible", timeout: 8000 });
    await userListItem.click();
    await page.waitForTimeout(2000);

    console.log("   Navigated to User List URL:", page.url());

    const secondPageAudit = await page.evaluate(() => {
      const searchUl = document.querySelector(".gv-navbar-search .awesomplete > ul");
      const searchUlVisible = searchUl && window.getComputedStyle(searchUl).display !== "none" && !searchUl.hasAttribute("hidden") && searchUl.children.length > 0;
      const unhiddenDropdowns = Array.from(document.querySelectorAll(".dropdown-menu")).filter(el => {
        const cs = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0 && cs.display !== "none" && cs.visibility !== "hidden" && !el.classList.contains("show");
      });
      const activeHead = document.querySelector(".page-container:not(#page-desktop):not([style*='display: none']) .page-head");
      const headRect = activeHead ? activeHead.getBoundingClientRect() : null;

      return {
        searchUlVisible: !!searchUlVisible,
        unhiddenDropdownsCount: unhiddenDropdowns.length,
        headHeight: headRect ? Math.round(headRect.height) : 0
      };
    });

    console.log("   User List Audit Results:", JSON.stringify(secondPageAudit, null, 2));

    if (secondPageAudit.searchUlVisible) {
      throw new Error("FAILED: Search dropdown visible on User List page!");
    }
    if (secondPageAudit.unhiddenDropdownsCount > 0) {
      throw new Error(`FAILED: Found ${secondPageAudit.unhiddenDropdownsCount} unhidden dropdowns on User List page!`);
    }
    if (secondPageAudit.headHeight > 100) {
      throw new Error(`FAILED: User List page head height is too large (${secondPageAudit.headHeight}px)!`);
    }

    const userListScreenshotPath = path.join(artifactDir, "search_user_list_clean_verified.png");
    await page.screenshot({ path: userListScreenshotPath, fullPage: false });
    console.log(`✓ Second search navigation screenshot saved: ${userListScreenshotPath}`);

    console.log("\n================================================================================");
    console.log("   ALL POST-SEARCH UI CHECKS PASSED WITH ZERO ARTIFACTS!");
    console.log("================================================================================");

  } finally {
    await browser.close();
  }
}

verifyCleanSearchNavigation().catch(err => {
  console.error("Verification failed:", err);
  process.exit(1);
});
