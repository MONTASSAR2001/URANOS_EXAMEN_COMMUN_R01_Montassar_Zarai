import { chromium } from "playwright";

async function verifySpaRouting() {
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const page = await browser.newPage();
  page.setViewportSize({ width: 1440, height: 900 });

  page.on("console", msg => {
    const text = msg.text();
    if (text.includes("URANOS") || text.includes("error") || text.includes("refresh")) {
      console.log(`[BROWSER CONSOLE] ${msg.type()}: ${text}`);
    }
  });

  console.log("Navigating to login...");
  await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
  await page.fill("#loginEmail", "Administrator");
  await page.fill("#loginPassword", "Password123!");
  await page.click("#btnContinue");
  await page.waitForURL(/\/desk|\/app/);
  await page.waitForTimeout(2000);

  const testResults = [];

  // Helper to test active list view
  const inspectActiveList = async (stepDescription) => {
    return await page.evaluate((desc) => {
      const route = frappe.get_route();
      const doctype = route ? route[1] : null;
      const cur = window.cur_list;

      const activePage = document.querySelector(".page-container:not([style*='display: none']) .frappe-list, .layout-main-section:not([style*='display: none']) .frappe-list, .frappe-list:not([style*='display: none'])");
      const rows = activePage ? activePage.querySelectorAll(".list-row-container") : [];
      const visibleRows = Array.from(rows).filter(r => window.getComputedStyle(r).display !== "none" && window.getComputedStyle(r).visibility !== "hidden");

      const noResultEl = activePage ? activePage.querySelector(".no-result") : null;
      const noResultVisible = noResultEl ? (window.getComputedStyle(noResultEl).display !== "none" && window.getComputedStyle(noResultEl).visibility !== "hidden") : false;
      const noResultText = noResultEl ? noResultEl.innerText.trim().replace(/\s+/g, " ") : null;

      const resultEl = activePage ? activePage.querySelector(".result") : null;
      const resultVisible = resultEl ? (window.getComputedStyle(resultEl).display !== "none" && window.getComputedStyle(resultEl).visibility !== "hidden") : false;

      const firewall = document.getElementById("uranos-project-firewall");

      return {
        step: desc,
        route,
        curListDoctype: cur ? cur.doctype : null,
        curListDataCount: (cur && cur.data) ? cur.data.length : 0,
        activeListFound: !!activePage,
        totalRows: rows.length,
        visibleRows: visibleRows.length,
        resultVisible,
        noResultVisible,
        noResultText: noResultVisible ? noResultText : null,
        firewallPresent: !!firewall
      };
    }, stepDescription);
  };

  // ── STEP 1: Navigate to Project List via Client Router ──
  console.log("\n=== STEP 1: Client routing to /app/project ===");
  await page.evaluate(() => frappe.set_route("List", "Project", "List"));
  await page.waitForTimeout(2000);
  const step1 = await inspectActiveList("Step 1: First visit to /app/project");
  console.log(JSON.stringify(step1, null, 2));
  testResults.push(step1);
  await page.screenshot({ path: "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9/step1_project_list.png" });

  // ── STEP 2: Navigate to URANOS Blocker List via Client Router ──
  console.log("\n=== STEP 2: Client routing to /app/uranos-blocker ===");
  await page.evaluate(() => frappe.set_route("List", "URANOS Blocker", "List"));
  await page.waitForTimeout(2000);
  const step2 = await inspectActiveList("Step 2: Client-side routing to /app/uranos-blocker");
  console.log(JSON.stringify(step2, null, 2));
  testResults.push(step2);
  await page.screenshot({ path: "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9/step2_blocker_list.png" });

  // ── STEP 3: Navigate to User List via Client Router ──
  console.log("\n=== STEP 3: Client routing to /app/user ===");
  await page.evaluate(() => frappe.set_route("List", "User", "List"));
  await page.waitForTimeout(2000);
  const step3 = await inspectActiveList("Step 3: Client-side routing to /app/user");
  console.log(JSON.stringify(step3, null, 2));
  testResults.push(step3);

  // ── STEP 4: Navigate BACK to Project List via Client Router (WITHOUT F5) ──
  console.log("\n=== STEP 4: Client routing BACK to /app/project (without reload) ===");
  await page.evaluate(() => frappe.set_route("List", "Project", "List"));
  await page.waitForTimeout(2000);
  const step4 = await inspectActiveList("Step 4: Client-side routing BACK to /app/project");
  console.log(JSON.stringify(step4, null, 2));
  testResults.push(step4);
  await page.screenshot({ path: "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9/step4_project_list_back.png" });

  // ── STEP 5: Navigate to Workspace /app then back to Project List ──
  console.log("\n=== STEP 5: Workspace to Project List via Client Router ===");
  await page.evaluate(() => frappe.set_route(""));
  await page.waitForTimeout(1500);
  await page.evaluate(() => frappe.set_route("List", "Project", "List"));
  await page.waitForTimeout(2000);
  const step5 = await inspectActiveList("Step 5: Workspace -> Project List routing");
  console.log(JSON.stringify(step5, null, 2));
  testResults.push(step5);

  // ── VALIDATION CHECKS ──
  console.log("\n=== RUNNING ASSERTIONS ===");
  let passed = true;

  for (const r of testResults) {
    if (r.firewallPresent) {
      console.error(`FAIL: Destructive firewall still present in ${r.step}`);
      passed = false;
    }
    if (r.noResultVisible) {
      console.error(`FAIL: "No result" message visible in ${r.step}: ${r.noResultText}`);
      passed = false;
    }
    if (r.curListDataCount === 0) {
      console.error(`FAIL: cur_list data is empty in ${r.step}`);
      passed = false;
    }
    if (r.visibleRows === 0) {
      console.error(`FAIL: No visible rows rendered in ${r.step}`);
      passed = false;
    }
    if (!r.resultVisible) {
      console.error(`FAIL: Result container is not visible in ${r.step}`);
      passed = false;
    }
  }

  if (passed) {
    console.log("SUCCESS: All client-side routing assertions passed! Data renders instantly on SPA transitions without manual reload.");
  } else {
    console.error("FAILED: Some assertions did not pass.");
  }

  await browser.close();
  process.exit(passed ? 0 : 1);
}

verifySpaRouting().catch(err => {
  console.error("Test threw unhandled error:", err);
  process.exit(1);
});
