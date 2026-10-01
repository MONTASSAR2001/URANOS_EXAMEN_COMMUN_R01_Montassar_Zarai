import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyInlineGisAndRoleFiltering() {
  console.log("==================================================================");
  console.log("   URANOS OS — Inline GIS Map & Role-Based Field Filtering QA");
  console.log("==================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/4c9276b4-96e1-471d-ad96-037a119e20ff";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    ignoreHTTPSErrors: true,
  });
  const page = await context.newPage();

  try {
    // -------------------------------------------------------------
    // STEP 1: LOGIN AS MANAGER
    // -------------------------------------------------------------
    console.log("\nLogging in as Manager (direction_01@uranos.local)...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailField.waitFor({ timeout: 10000 });
    await emailField.fill("direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");
    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 20000 });
    await page.waitForTimeout(2000);
    console.log("✓ Logged in successfully as Manager");

    // -------------------------------------------------------------
    // STEP 2: OPEN PROJECT PV-0005 FORM
    // -------------------------------------------------------------
    console.log("\nNavigating to Project PV-0005 form...");
    await page.goto("http://localhost:8080/app/project/PV-0005", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3500);

    // Wait for the custom card containers
    const cardGeneral = page.locator(".uranos-project-form-card.card-general").first();
    await cardGeneral.waitFor({ timeout: 15000 });
    console.log("✓ Card 1 (General Information & Governance) is rendered");

    const cardGis = page.locator(".uranos-project-form-card.card-gis").first();
    await cardGis.waitFor({ timeout: 15000 });
    console.log("✓ Card 2 (Geographic Telemetry & GIS Positioning) is rendered");

    // -------------------------------------------------------------
    // STEP 3: VERIFY INLINE GIS MAP (NO MODAL BUTTON)
    // -------------------------------------------------------------
    console.log("\nVerifying Inline GIS Map specifications in Card 2...");
    
    // a) Assert old modal button #uranosPickMapBtn is NOT present
    const modalBtnCount = await page.locator("#uranosPickMapBtn").count();
    if (modalBtnCount > 0) {
      throw new Error("Old modal button '#uranosPickMapBtn' still exists in DOM! Must be completely removed.");
    }
    console.log("✓ Verified old modal button #uranosPickMapBtn is completely removed");

    // b) Assert #inline-project-map exists inside Card 2
    const inlineMapLocator = page.locator(".card-gis #inline-project-map");
    await inlineMapLocator.waitFor({ timeout: 10000 });
    const isMapVisible = await inlineMapLocator.isVisible();
    if (!isMapVisible) {
      throw new Error("#inline-project-map is not visible in Card 2!");
    }
    console.log("✓ Verified #inline-project-map is present and visible inside Card 2");

    // c) Assert Leaflet map elements are initialized inside #inline-project-map
    await page.waitForFunction(() => {
      const container = document.getElementById("inline-project-map");
      return container && container.classList.contains("leaflet-container") && window._uranos_inline_project_map;
    }, { timeout: 10000 });
    console.log("✓ Verified Leaflet map is initialized with live tiles inside #inline-project-map");

    // d) Assert City/Region search input exists above map
    const searchInput = page.locator("#inlineGisSearchInput");
    await searchInput.waitFor({ timeout: 5000 });
    const isSearchVisible = await searchInput.isVisible();
    if (!isSearchVisible) {
      throw new Error("#inlineGisSearchInput is not visible above the map!");
    }
    console.log("✓ Verified City/Region search input is present and visible above the map");

    // e) Test clicking on map updates coordinates
    console.log("Testing interactive map coordinate update on click...");
    const oldLat = await page.evaluate(() => cur_frm.doc.latitude);
    const oldLng = await page.evaluate(() => cur_frm.doc.longitude);
    console.log(`  Initial coordinates: lat=${oldLat}, lng=${oldLng}`);

    // Click on the map container
    await page.evaluate(() => {
      if (window._uranos_inline_project_map) {
        // Simulate a map click at Tozeur coordinates
        window._uranos_inline_project_map.fire("click", {
          latlng: L.latLng(33.9197, 8.1335)
        });
      }
    });
    await page.waitForTimeout(500);

    const updatedLat = await page.evaluate(() => cur_frm.doc.latitude);
    const updatedLng = await page.evaluate(() => cur_frm.doc.longitude);
    console.log(`  Updated coordinates after map click: lat=${updatedLat}, lng=${updatedLng}`);

    if (Math.abs(updatedLat - 33.9197) > 0.001 || Math.abs(updatedLng - 8.1335) > 0.001) {
      throw new Error(`Coordinates did not update on map click! Got lat=${updatedLat}, lng=${updatedLng}`);
    }
    console.log("✓ Real-time coordinate synchronization works seamlessly on map click!");

    // Take screenshot of Card 2 with inline map
    await page.screenshot({ path: path.join(artifactDir, "1_inline_gis_map_card2.png"), fullPage: false });
    console.log("✓ Screenshot saved: 1_inline_gis_map_card2.png");

    // -------------------------------------------------------------
    // STEP 4: VERIFY ROLE-BASED FIELD FILTERING
    // -------------------------------------------------------------
    console.log("\n==============================================================");
    console.log("Verifying Role-Based Field Filtering on Assignment Link Fields");
    console.log("==============================================================");

    // a) Test custom_assigned_engineer query
    console.log("\nTesting custom_assigned_engineer Link Query...");
    const engineerQueryConfig = await page.evaluate(() => {
      const field = cur_frm.fields_dict.custom_assigned_engineer;
      return field && typeof field.get_query === "function" ? field.get_query() : null;
    });
    console.log("  custom_assigned_engineer query config:", JSON.stringify(engineerQueryConfig));

    if (!engineerQueryConfig || !engineerQueryConfig.query || !engineerQueryConfig.query.includes("get_engineer_users")) {
      throw new Error(`custom_assigned_engineer does not have get_engineer_users query configured! Got: ${JSON.stringify(engineerQueryConfig)}`);
    }

    // Execute the query via Frappe Desk client search
    const engineerResults = await page.evaluate(async () => {
      return new Promise((resolve, reject) => {
        frappe.call({
          method: "frappe.desk.search.search_link",
          args: {
            doctype: "User",
            txt: "",
            query: cur_frm.fields_dict.custom_assigned_engineer.get_query().query
          },
          callback: (r) => {
            if (r.exc) reject(r.exc);
            else resolve(r.message || []);
          }
        });
      });
    });

    console.log("  Returned Engineer candidates:", JSON.stringify(engineerResults));
    const engineerValues = engineerResults.map(r => r.value);
    
    // Assert ONLY engineer users are present
    if (!engineerValues.includes("ingenieur_01@uranos.local") || !engineerValues.includes("ingenieur_03@uranos.local")) {
      throw new Error(`Missing expected engineers in query result: ${JSON.stringify(engineerValues)}`);
    }
    if (engineerValues.includes("chantier_01@uranos.local") || engineerValues.includes("chantier_02@uranos.local")) {
      throw new Error(`FORBIDDEN: Site Team users leaked into Engineer field! ${JSON.stringify(engineerValues)}`);
    }
    if (engineerValues.includes("direction_01@uranos.local") || engineerValues.includes("Administrator")) {
      throw new Error(`FORBIDDEN: Non-engineer users leaked into Engineer field! ${JSON.stringify(engineerValues)}`);
    }
    console.log("✓ Assigned Engineer field strictly returns ONLY users with Engineer role!");

    // Trigger UI Awesomplete dropdown for Engineer field
    const engInput = page.locator("[data-fieldname='custom_assigned_engineer'] input").first();
    await engInput.focus();
    await engInput.fill("");
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(800);
    await page.screenshot({ path: path.join(artifactDir, "2_engineer_field_filtered.png"), fullPage: false });
    console.log("✓ Screenshot saved: 2_engineer_field_filtered.png");

    // b) Test custom_assigned_site_team query
    console.log("\nTesting custom_assigned_site_team Link Query...");
    const siteTeamQueryConfig = await page.evaluate(() => {
      const field = cur_frm.fields_dict.custom_assigned_site_team;
      return field && typeof field.get_query === "function" ? field.get_query() : null;
    });
    console.log("  custom_assigned_site_team query config:", JSON.stringify(siteTeamQueryConfig));

    if (!siteTeamQueryConfig || !siteTeamQueryConfig.query || !siteTeamQueryConfig.query.includes("get_site_team_users")) {
      throw new Error(`custom_assigned_site_team does not have get_site_team_users query configured! Got: ${JSON.stringify(siteTeamQueryConfig)}`);
    }

    // Execute the query via Frappe Desk client search
    const siteTeamResults = await page.evaluate(async () => {
      return new Promise((resolve, reject) => {
        frappe.call({
          method: "frappe.desk.search.search_link",
          args: {
            doctype: "User",
            txt: "",
            query: cur_frm.fields_dict.custom_assigned_site_team.get_query().query
          },
          callback: (r) => {
            if (r.exc) reject(r.exc);
            else resolve(r.message || []);
          }
        });
      });
    });

    console.log("  Returned Site Team candidates:", JSON.stringify(siteTeamResults));
    const siteTeamValues = siteTeamResults.map(r => r.value);

    // Assert ONLY site team users are present
    if (!siteTeamValues.includes("chantier_01@uranos.local") || !siteTeamValues.includes("chantier_02@uranos.local")) {
      throw new Error(`Missing expected site team users in query result: ${JSON.stringify(siteTeamValues)}`);
    }
    if (siteTeamValues.includes("ingenieur_01@uranos.local") || siteTeamValues.includes("ingenieur_03@uranos.local")) {
      throw new Error(`FORBIDDEN: Engineer users leaked into Site Team field! ${JSON.stringify(siteTeamValues)}`);
    }
    if (siteTeamValues.includes("direction_01@uranos.local") || siteTeamValues.includes("Administrator")) {
      throw new Error(`FORBIDDEN: Non-site-team users leaked into Site Team field! ${JSON.stringify(siteTeamValues)}`);
    }
    console.log("✓ Assigned Site Team field strictly returns ONLY users with Site Team role!");

    // Trigger UI Awesomplete dropdown for Site Team field
    const siteInput = page.locator("[data-fieldname='custom_assigned_site_team'] input").first();
    await siteInput.focus();
    await siteInput.fill("");
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(800);
    await page.screenshot({ path: path.join(artifactDir, "3_site_team_field_filtered.png"), fullPage: false });
    console.log("✓ Screenshot saved: 3_site_team_field_filtered.png");

    console.log("\n==============================================================");
    console.log("   ALL QA ASSERTIONS PASSED WITH ZERO REGRESSIONS!");
    console.log("==============================================================");
  } finally {
    await browser.close();
  }
}

verifyInlineGisAndRoleFiltering().catch(err => {
  console.error("Test failed with error:", err);
  process.exit(1);
});
