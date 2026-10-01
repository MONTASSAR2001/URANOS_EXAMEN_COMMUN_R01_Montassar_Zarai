import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyAwesomeBarDropdown() {
  console.log("================================================================================");
  console.log("   URANOS OS — AwesomeBar & Global Search Dropdown Verification Test");
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

    // 1. Login as Manager
    console.log("1. Logging in as direction_01@uranos.local...");
    await page.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailInput = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailInput.waitFor({ timeout: 15000 });
    await emailInput.fill("direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");

    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 25000 });
    await page.waitForTimeout(2500);

    if (page.url().includes("/desk")) {
      await page.goto(`${BASE_URL}/app`, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(2500);
    }
    console.log("✓ Logged in successfully into URANOS OS Desk");

    // 2. Locate #navbar-search
    console.log("2. Locating #navbar-search...");
    const searchBar = page.locator("#navbar-search").first();
    await searchBar.waitFor({ timeout: 10000 });
    const isSearchVisible = await searchBar.isVisible();
    if (!isSearchVisible) {
      throw new Error("Search input #navbar-search is not visible!");
    }
    console.log("✓ #navbar-search is rendered and visible in top navbar");

    // 3. Focus and type "Project"
    console.log("3. Focusing and typing 'Project' into #navbar-search...");
    await searchBar.focus();
    await searchBar.fill("");
    await page.keyboard.type("Project", { delay: 60 });

    // 4. Wait 1 second
    console.log("4. Waiting 1 second for Awesomplete dropdown to populate...");
    await page.waitForTimeout(1000);

    // 5. Assert .awesomplete ul li elements exist and are visible
    const dropdownUl = page.locator(".awesomplete ul, .gv-navbar-search .awesomplete > ul").first();
    await dropdownUl.waitFor({ state: "visible", timeout: 8000 });

    const lis = page.locator(".awesomplete ul li, .gv-navbar-search .awesomplete > ul > li");
    const count = await lis.count();
    console.log(`✓ Awesomplete dropdown items count: ${count}`);

    if (count === 0) {
      throw new Error("FAILED: .awesomplete ul li elements count is 0!");
    }

    // Verify first item is visible
    const firstLi = lis.first();
    const isFirstLiVisible = await firstLi.isVisible();
    if (!isFirstLiVisible) {
      throw new Error("FAILED: First .awesomplete ul li is not visible!");
    }
    console.log("✓ First .awesomplete ul li is visible");

    // Extract item texts
    const itemsData = await page.evaluate(() => {
      const elements = Array.from(document.querySelectorAll(".awesomplete ul li"));
      return elements.map(el => ({
        text: (el.innerText || el.textContent).trim(),
        visible: window.getComputedStyle(el).display !== "none" && window.getComputedStyle(el).visibility !== "hidden"
      }));
    });

    console.log("✓ Dropdown results sample:");
    itemsData.slice(0, 8).forEach((item, idx) => {
      console.log(`   [${idx + 1}] ${item.text.replace(/\n+/g, " | ")} (visible: ${item.visible})`);
    });

    // 6. Check computed styles of dropdown
    const computedStyles = await page.evaluate(() => {
      const ul = document.querySelector(".gv-navbar-search .awesomplete > ul") || document.querySelector(".awesomplete ul");
      if (!ul) return null;
      const cs = window.getComputedStyle(ul);
      const bbox = ul.getBoundingClientRect();
      return {
        display: cs.display,
        zIndex: cs.zIndex,
        position: cs.position,
        opacity: cs.opacity,
        overflowY: cs.overflowY,
        width: bbox.width,
        height: bbox.height,
        top: bbox.top,
        left: bbox.left
      };
    });
    console.log("✓ Computed styles of .awesomplete > ul:", JSON.stringify(computedStyles, null, 2));

    if (computedStyles.display !== "block" || computedStyles.opacity !== "1" || computedStyles.position !== "absolute") {
      throw new Error(`Dropdown CSS override failed: display=${computedStyles.display}, opacity=${computedStyles.opacity}, position=${computedStyles.position}`);
    }

    // 7. Capture screenshot for verification
    const screenshotPath = path.join(artifactDir, "awesomebar_dropdown_visible.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`✓ Verification screenshot saved to ${screenshotPath}`);

    console.log("\n================================================================================");
    console.log("   ALL AWESOMEBAR DROPDOWN CHECKS PASSED SUCCESSFULLY!");
    console.log("================================================================================");
  } finally {
    await browser.close();
  }
}

verifyAwesomeBarDropdown().catch(err => {
  console.error("Verification failed:", err);
  process.exit(1);
});
