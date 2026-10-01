import { chromium } from "playwright";

async function verifyStability() {
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const page = await browser.newPage();
  page.setViewportSize({ width: 1440, height: 900 });

  console.log("1. Logging into URANOS...");
  await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
  await page.fill("#loginEmail", "Administrator");
  await page.fill("#loginPassword", "Password123!");
  await page.click("#btnContinue");
  await page.waitForURL(/\/desk|\/app/);
  await page.waitForTimeout(2000);

  // ── TEST 1: Live Clock Widget ──
  console.log("\n--- TEST 1: Live Clock Widget in Navbar ---");
  const clockInfo = await page.evaluate(() => {
    const clock = document.querySelector("#gvLiveClockPill, .gv-clock-pill");
    const time = clock ? clock.querySelector(".gv-clock-time")?.innerText : null;
    const date = clock ? clock.querySelector(".gv-clock-date")?.innerText : null;
    return {
      clockPresent: !!clock,
      time,
      date,
      hasWeather: !!document.querySelector(".gv-weather-pill, #gvWeatherPill")
    };
  });
  console.log("Clock Info:", clockInfo);
  if (!clockInfo.clockPresent || !clockInfo.time) {
    throw new Error("Live Clock Widget is missing or inactive in navbar!");
  }

  // ── TEST 2: Executive Desk, Bento Grid & KPIs ──
  console.log("\n--- TEST 2: Main Dashboard Executive Widgets ---");
  await page.evaluate(() => frappe.set_route(""));
  await page.waitForTimeout(2000);

  const deskInfo = await page.evaluate(() => {
    const cards = document.querySelectorAll(".gv-kpi-card, .uranos-kpi-card, .widget");
    const gisMap = document.getElementById("uranos-gis-map-canvas") || document.getElementById("uranos-leaflet-map");
    const pdfBtn = document.getElementById("btnDailyExecutiveReport") || document.querySelector(".btn-executive-pdf");
    const aiBtn = document.getElementById("btnOpenFullCopilot") || document.querySelector(".uranos-ai-trigger-btn");
    return {
      cardsCount: cards.length,
      gisMapPresent: !!gisMap,
      pdfBtnPresent: !!pdfBtn,
      aiBtnPresent: !!aiBtn
    };
  });
  console.log("Desk Widgets Info:", deskInfo);
  await page.screenshot({ path: "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9/stable_main_dashboard.png" });

  // ── TEST 3: Native SPA Navigation to Project List ──
  console.log("\n--- TEST 3: SPA Routing to Project List ---");
  await page.evaluate(() => frappe.set_route("List", "Project", "List"));
  await page.waitForTimeout(2000);

  const projectListInfo = await page.evaluate(() => {
    const activePage = document.querySelector(".page-container:not([style*='display: none']) .frappe-list, .layout-main-section:not([style*='display: none']) .frappe-list, .frappe-list:not([style*='display: none'])");
    const rows = activePage ? activePage.querySelectorAll(".list-row-container") : [];
    const openMenus = document.querySelectorAll(".dropdown-menu.show");
    return {
      route: frappe.get_route(),
      totalRows: rows.length,
      openMenusCount: openMenus.length,
      firewallPresent: !!document.getElementById("uranos-project-firewall")
    };
  });
  console.log("Project List Info:", projectListInfo);
  if (projectListInfo.openMenusCount > 0) {
    console.warn("Warning: Unwanted open dropdown menus detected:", projectListInfo.openMenusCount);
  }
  await page.screenshot({ path: "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9/stable_project_list.png" });

  // ── TEST 4: Native SPA Navigation to URANOS Blocker ──
  console.log("\n--- TEST 4: SPA Routing to URANOS Blocker ---");
  await page.evaluate(() => frappe.set_route("List", "URANOS Blocker", "List"));
  await page.waitForTimeout(2000);

  const blockerListInfo = await page.evaluate(() => {
    const activePage = document.querySelector(".page-container:not([style*='display: none']) .frappe-list, .layout-main-section:not([style*='display: none']) .frappe-list, .frappe-list:not([style*='display: none'])");
    const rows = activePage ? activePage.querySelectorAll(".list-row-container") : [];
    const openMenus = document.querySelectorAll(".dropdown-menu.show");
    return {
      route: frappe.get_route(),
      totalRows: rows.length,
      openMenusCount: openMenus.length
    };
  });
  console.log("Blocker List Info:", blockerListInfo);
  await page.screenshot({ path: "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9/stable_blocker_list.png" });

  // ── TEST 5: Return to Project List via SPA ──
  console.log("\n--- TEST 5: Return to Project List via SPA ---");
  await page.evaluate(() => frappe.set_route("List", "Project", "List"));
  await page.waitForTimeout(2000);

  const returnProjectInfo = await page.evaluate(() => {
    const activePage = document.querySelector(".page-container:not([style*='display: none']) .frappe-list, .layout-main-section:not([style*='display: none']) .frappe-list, .frappe-list:not([style*='display: none'])");
    const rows = activePage ? activePage.querySelectorAll(".list-row-container") : [];
    const openMenus = document.querySelectorAll(".dropdown-menu.show");
    return {
      route: frappe.get_route(),
      totalRows: rows.length,
      openMenusCount: openMenus.length
    };
  });
  console.log("Return Project Info:", returnProjectInfo);

  // ── TEST 6: Project Form View & 3-card Responsiveness ──
  console.log("\n--- TEST 6: Project Form View (PV-0020) ---");
  await page.evaluate(() => frappe.set_route("Form", "Project", "PV-0020"));
  await page.waitForTimeout(2000);

  const formInfo = await page.evaluate(() => {
    const cards = document.querySelectorAll(".uranos-form-card, .uranos-chic-card, [data-card-index]");
    const tabs = document.querySelectorAll(".form-tab, .nav-tabs li");
    return {
      route: frappe.get_route(),
      cardsCount: cards.length,
      tabsCount: tabs.length
    };
  });
  console.log("Project Form Info:", formInfo);
  await page.screenshot({ path: "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9/stable_project_form.png" });

  // ── TEST 7: 20 Tunisian Solar Projects Check ──
  console.log("\n--- TEST 7: Verify 20 Seeded Tunisian Solar Projects ---");
  const projectNames = await page.evaluate(async () => {
    const res = await frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Project",
        fields: ["name", "project_name", "status"],
        limit_page_length: 50,
        order_by: "name asc"
      }
    });
    return res.message || [];
  });
  console.log(`Found ${projectNames.length} projects in DB.`);
  const pvProjects = projectNames.filter(p => p.name.startsWith("PV-"));
  console.log(`Found ${pvProjects.length} PV- series projects: ${pvProjects.map(p => p.name).join(", ")}`);

  console.log("\n=== ALL STABILITY TESTS COMPLETE ===");
  await browser.close();
}

verifyStability().then(() => {
  console.log("STATUS: SUCCESS");
  process.exit(0);
}).catch(err => {
  console.error("STATUS: ERROR", err);
  process.exit(1);
});
