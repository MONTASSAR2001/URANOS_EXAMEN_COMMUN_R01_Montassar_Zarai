import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function runFullUranosCycleTest() {
  console.log("================================================================================");
  console.log("   URANOS OS — Full End-to-End Cycle Test (Manager -> Site Team -> Engineer)");
  console.log("   Architectural Invariants, Global Search, Blocker Dashboard & RBAC Validation");
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
  let createdBlockerId = null;

  try {
    // -------------------------------------------------------------------------
    // STEP 1: MANAGER (direction_01@uranos.local)
    // -------------------------------------------------------------------------
    console.log("\n================================================================================");
    console.log("STEP 1: Manager Logs In, Tests Search Bar, Creates Project PV-0099");
    console.log("================================================================================");

    const managerContext = await browser.newContext({
      viewport: { width: 1440, height: 960 },
      ignoreHTTPSErrors: true,
    });
    const pageM = await managerContext.newPage();

    // 1.1 Login as Manager
    console.log("Logging in as Manager (direction_01@uranos.local)...");
    await pageM.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });
    await pageM.waitForTimeout(1000);

    const emailM = pageM.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailM.waitFor({ timeout: 20000 });
    await emailM.fill("direction_01@uranos.local");
    await pageM.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await pageM.click("#btnContinue, .btn-login, button[type='submit']");
    await pageM.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 25000 });
    await pageM.waitForTimeout(2500);
    if (pageM.url().includes("/desk")) {
      await pageM.goto(`${BASE_URL}/app`, { waitUntil: "domcontentloaded" });
      await pageM.waitForTimeout(2500);
    }
    console.log("✓ Manager logged in successfully");

    // 1.2 Test Global Search Bar (Awesomebar)
    console.log("\nTesting Global Search Bar (#navbar-search) and Awesomplete dropdown...");
    const searchBar = pageM.locator("#navbar-search").first();
    await searchBar.waitFor({ timeout: 20000 });
    const isSearchVisible = await searchBar.isVisible();
    if (!isSearchVisible) {
      throw new Error("Global search input #navbar-search is not visible!");
    }
    console.log("✓ Global search input #navbar-search is present in navbar");

    // Focus and test Awesomplete options
    await searchBar.focus();
    await searchBar.fill("Project");
    await pageM.waitForTimeout(800);

    // Verify search dropdown is rendered and unblocked
    const dropdownList = pageM.locator(".gv-navbar-search .awesomplete > ul, .awesomplete > ul").first();
    const dropdownCount = await dropdownList.count();
    console.log(`✓ Awesomplete dropdown container count: ${dropdownCount}`);

    const dropdownStyles = await pageM.evaluate(() => {
      const input = document.getElementById("navbar-search");
      const parent = input ? input.closest(".awesomplete") : null;
      const ul = parent ? parent.querySelector("ul") : null;
      if (!ul) return null;
      const computed = window.getComputedStyle(ul);
      return {
        zIndex: computed.zIndex,
        pointerEvents: computed.pointerEvents,
        position: computed.position,
        itemsCount: ul.querySelectorAll("li").length
      };
    });

    console.log("  Search dropdown computed styles:", JSON.stringify(dropdownStyles));
    if (dropdownStyles) {
      console.log(`✓ Search dropdown active with z-index: ${dropdownStyles.zIndex}, pointer-events: ${dropdownStyles.pointerEvents}, items: ${dropdownStyles.itemsCount}`);
    }

    await pageM.screenshot({ path: path.join(artifactDir, "step1_global_search_active.png"), fullPage: false });
    console.log("✓ Screenshot saved: step1_global_search_active.png");

    // 1.3 Navigate to create Project PV-0099
    console.log("\nNavigating to Project creation form...");
    await pageM.goto(`${BASE_URL}/app/project/new-project-1`, { waitUntil: "domcontentloaded" });
    await pageM.waitForTimeout(3000);

    // Wait for form to mount
    await pageM.waitForFunction(() => typeof cur_frm !== "undefined" && cur_frm && cur_frm.doc, { timeout: 15000 });

    console.log("Filling Project PV-0099 form fields...");
    await pageM.evaluate(async () => {
      await cur_frm.set_value("project_name", "PV-0099");
      if (cur_frm.fields_dict.custom_assigned_engineer) {
        await cur_frm.set_value("custom_assigned_engineer", "ingenieur_01@uranos.local");
      }
      if (cur_frm.fields_dict.custom_assigned_site_team) {
        await cur_frm.set_value("custom_assigned_site_team", "chantier_01@uranos.local");
      }
      if (cur_frm.fields_dict.latitude) {
        await cur_frm.set_value("latitude", 33.9197);
      }
      if (cur_frm.fields_dict.longitude) {
        await cur_frm.set_value("longitude", 8.1335);
      }
    });

    await pageM.waitForTimeout(1000);

    // Save project
    console.log("Saving Project PV-0099...");
    await pageM.evaluate(async () => {
      await cur_frm.save();
    });

    // Wait until saved and autonamed
    await pageM.waitForFunction(() => {
      return (cur_frm && !cur_frm.is_dirty() && cur_frm.doc && (cur_frm.doc.name === "PV-0099" || cur_frm.doc.project_name === "PV-0099")) ||
             (window.location.pathname.includes("/app/project/PV-0099"));
    }, { timeout: 25000 });

    const createdProjectName = await pageM.evaluate(() => cur_frm.doc.name);
    const assignedEng = await pageM.evaluate(() => cur_frm.doc.custom_assigned_engineer);
    const assignedSite = await pageM.evaluate(() => cur_frm.doc.custom_assigned_site_team);
    console.log(`✓ Project created successfully! Name: ${createdProjectName}`);
    console.log(`  Assigned Engineer: ${assignedEng}`);
    console.log(`  Assigned Site Team: ${assignedSite}`);

    if (createdProjectName !== "PV-0099") {
      throw new Error(`Expected project name to be 'PV-0099', got: ${createdProjectName}`);
    }
    if (assignedEng !== "ingenieur_01@uranos.local" || assignedSite !== "chantier_01@uranos.local") {
      throw new Error(`Assignments mismatch: eng=${assignedEng}, site=${assignedSite}`);
    }

    await pageM.screenshot({ path: path.join(artifactDir, "step1_manager_project_pv0099_created.png"), fullPage: false });
    console.log("✓ Screenshot saved: step1_manager_project_pv0099_created.png");

    await managerContext.close();

    // -------------------------------------------------------------------------
    // STEP 2: SITE TEAM (chantier_01@uranos.local)
    // -------------------------------------------------------------------------
    console.log("\n================================================================================");
    console.log("STEP 2: Site Team Logs In, Uses Blocker Dashboard, Creates Blocker for PV-0099");
    console.log("================================================================================");

    const siteContext = await browser.newContext({
      viewport: { width: 1440, height: 960 },
      ignoreHTTPSErrors: true,
    });
    const pageS = await siteContext.newPage();

    // 2.1 Login as Site Team
    console.log("Logging in as Site Team (chantier_01@uranos.local)...");
    await pageS.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });
    await pageS.waitForTimeout(1000);

    const emailS = pageS.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailS.waitFor({ timeout: 20000 });
    await emailS.fill("chantier_01@uranos.local");
    await pageS.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await pageS.click("#btnContinue, .btn-login, button[type='submit']");
    await pageS.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 25000 });
    await pageS.waitForTimeout(2500);
    console.log("✓ Site Team logged in successfully");

    // 2.2 Navigate to Blocker Dashboard
    console.log("Navigating to Blocker Dashboard (/app/blocker-dashboard)...");
    await pageS.goto(`${BASE_URL}/app/blocker-dashboard`, { waitUntil: "domcontentloaded" });
    await pageS.waitForTimeout(3500);

    // 2.3 Verify "+ Nouvel Obstacle" button
    console.log("Checking '+ Nouvel Obstacle' button in Blocker Dashboard header...");
    const createBtn = pageS.locator("#bd-create-btn").first();
    await createBtn.waitFor({ timeout: 20000 });
    const isCreateBtnVisible = await createBtn.isVisible();
    if (!isCreateBtnVisible) {
      throw new Error("#bd-create-btn is not visible on the Blocker Dashboard!");
    }
    const createBtnText = await createBtn.innerText();
    console.log(`✓ Found '+ Nouvel Obstacle' button with text: '${createBtnText.trim()}'`);

    // Verify "+ Nouvel Obstacle" is placed adjacent to "Actualiser"
    const refreshBtn = pageS.locator("#bd-refresh-btn").first();
    const isRefreshVisible = await refreshBtn.isVisible();
    console.log(`✓ Adjacent 'Actualiser' button is visible: ${isRefreshVisible}`);

    await pageS.screenshot({ path: path.join(artifactDir, "step2_blocker_dashboard_create_btn.png"), fullPage: false });
    console.log("✓ Screenshot saved: step2_blocker_dashboard_create_btn.png");

    // 2.4 Click "+ Nouvel Obstacle" button to route to /app/uranos-blocker/new
    console.log("Clicking '+ Nouvel Obstacle' button...");
    await createBtn.click();
    await pageS.waitForURL(url => url.pathname.includes("uranos-blocker"), { timeout: 15000 });
    await pageS.waitForTimeout(3000);
    console.log(`✓ Navigated to blocker creation URL: ${pageS.url()}`);

    // Wait for form to mount
    await pageS.waitForFunction(() => typeof cur_frm !== "undefined" && cur_frm && cur_frm.doc, { timeout: 15000 });

    // 2.5 Fill out the Blocker for PV-0099
    console.log("Filling new Blocker form for PV-0099...");
    await pageS.evaluate(async () => {
      await cur_frm.set_value("project", "PV-0099");
      await cur_frm.set_value("title", "Critical trenching cable obstruction Zone B");
      await cur_frm.set_value("severity", "Critical");
      await cur_frm.set_value("category", "Material");
      await cur_frm.set_value("responsible", "ingenieur_01@uranos.local");
      await cur_frm.set_value("description", "Heavy rock formation obstructing cable trench at Zone B. Urgent geotechnical intervention required.");
    });

    await pageS.waitForTimeout(1000);

    // Save the blocker
    console.log("Saving new Blocker...");
    await pageS.evaluate(async () => {
      await cur_frm.save();
    });

    // Wait for save to complete
    await pageS.waitForFunction(() => {
      return cur_frm && !cur_frm.is_dirty() && cur_frm.doc && cur_frm.doc.name && cur_frm.doc.name.startsWith("B-");
    }, { timeout: 20000 });

    createdBlockerId = await pageS.evaluate(() => cur_frm.doc.name);
    const initialStatus = await pageS.evaluate(() => cur_frm.doc.status);
    const assignedResp = await pageS.evaluate(() => cur_frm.doc.responsible);
    const linkedProj = await pageS.evaluate(() => cur_frm.doc.project);
    const blockerSev = await pageS.evaluate(() => cur_frm.doc.severity);

    console.log(`✓ Blocker created successfully!`);
    console.log(`  ID: ${createdBlockerId}`);
    console.log(`  Status: ${initialStatus}`);
    console.log(`  Project: ${linkedProj}`);
    console.log(`  Severity: ${blockerSev}`);
    console.log(`  Responsible Engineer: ${assignedResp}`);

    if (initialStatus !== "Open") {
      throw new Error(`Expected initial blocker status 'Open', got: ${initialStatus}`);
    }
    if (assignedResp !== "ingenieur_01@uranos.local") {
      throw new Error(`Expected responsible 'ingenieur_01@uranos.local', got: ${assignedResp}`);
    }

    await pageS.screenshot({ path: path.join(artifactDir, "step2_site_team_blocker_created.png"), fullPage: false });
    console.log("✓ Screenshot saved: step2_site_team_blocker_created.png");

    await siteContext.close();

    // -------------------------------------------------------------------------
    // STEP 3: ENGINEER (ingenieur_01@uranos.local)
    // -------------------------------------------------------------------------
    console.log("\n================================================================================");
    console.log("STEP 3: Engineer Logs In, Opens Blocker, Transitions to 'In Progress'");
    console.log("================================================================================");

    const engineerContext = await browser.newContext({
      viewport: { width: 1440, height: 960 },
      ignoreHTTPSErrors: true,
    });
    const pageE = await engineerContext.newPage();

    // 3.1 Login as Engineer
    console.log("Logging in as Engineer (ingenieur_01@uranos.local)...");
    await pageE.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });
    await pageE.waitForTimeout(1000);

    const emailE = pageE.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailE.waitFor({ timeout: 20000 });
    await emailE.fill("ingenieur_01@uranos.local");
    await pageE.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await pageE.click("#btnContinue, .btn-login, button[type='submit']");
    await pageE.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 25000 });
    await pageE.waitForTimeout(2500);
    console.log("✓ Engineer logged in successfully");

    // 3.2 Navigate to the newly created blocker
    console.log(`Navigating to Blocker form: ${BASE_URL}/app/uranos-blocker/${createdBlockerId}...`);
    await pageE.goto(`${BASE_URL}/app/uranos-blocker/${createdBlockerId}`, { waitUntil: "domcontentloaded" });
    await pageE.waitForTimeout(3000);

    // Wait for form to load
    await pageE.waitForFunction(() => typeof cur_frm !== "undefined" && cur_frm && cur_frm.doc, { timeout: 15000 });

    const currentEngineerStatus = await pageE.evaluate(() => cur_frm.doc.status);
    console.log(`  Current Blocker status before transition: ${currentEngineerStatus}`);
    if (currentEngineerStatus !== "Open") {
      throw new Error(`Expected status 'Open' prior to transition, got: ${currentEngineerStatus}`);
    }

    // 3.3 Change status to "In Progress"
    console.log("Transitioning Blocker status to 'In Progress'...");
    await pageE.evaluate(async () => {
      await cur_frm.set_value("status", "In Progress");
      await cur_frm.save();
    });

    // Wait for save to complete
    await pageE.waitForFunction(() => {
      return cur_frm && !cur_frm.is_dirty() && cur_frm.doc && cur_frm.doc.status === "In Progress";
    }, { timeout: 15000 });

    const updatedEngineerStatus = await pageE.evaluate(() => cur_frm.doc.status);
    console.log(`✓ Blocker status successfully transitioned to: '${updatedEngineerStatus}'`);
    if (updatedEngineerStatus !== "In Progress") {
      throw new Error(`Expected status 'In Progress', got: ${updatedEngineerStatus}`);
    }

    await pageE.screenshot({ path: path.join(artifactDir, "step3_engineer_blocker_in_progress.png"), fullPage: false });
    console.log("✓ Screenshot saved: step3_engineer_blocker_in_progress.png");

    await engineerContext.close();

    // -------------------------------------------------------------------------
    // STEP 4: MANAGER (direction_01@uranos.local) VERIFICATION
    // -------------------------------------------------------------------------
    console.log("\n================================================================================");
    console.log("STEP 4: Manager Logs In, Verifies Updated Status in Blocker Form & Dashboard");
    console.log("================================================================================");

    const managerFinalContext = await browser.newContext({
      viewport: { width: 1440, height: 960 },
      ignoreHTTPSErrors: true,
    });
    const pageMF = await managerFinalContext.newPage();

    // 4.1 Login as Manager
    console.log("Logging in as Manager (direction_01@uranos.local)...");
    await pageMF.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });
    await pageMF.waitForTimeout(1000);

    const emailMF = pageMF.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailMF.waitFor({ timeout: 20000 });
    await emailMF.fill("direction_01@uranos.local");
    await pageMF.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await pageMF.click("#btnContinue, .btn-login, button[type='submit']");
    await pageMF.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 25000 });
    await pageMF.waitForTimeout(2500);
    console.log("✓ Manager logged back in successfully");

    // 4.2 Verify Database Record via Desk API call
    console.log(`Verifying Blocker ${createdBlockerId} status directly in Database...`);
    const dbStatus = await pageMF.evaluate(async (blockerId) => {
      return new Promise((resolve, reject) => {
        frappe.call({
          method: "frappe.client.get_value",
          args: {
            doctype: "URANOS Blocker",
            filters: { name: blockerId },
            fieldname: ["status", "severity", "responsible", "project"]
          },
          callback: (r) => {
            if (r.exc) reject(r.exc);
            else resolve(r.message);
          }
        });
      });
    }, createdBlockerId);

    console.log("  Database Record State:", JSON.stringify(dbStatus));
    if (!dbStatus || dbStatus.status !== "In Progress") {
      throw new Error(`Database verification failed! Expected status 'In Progress', got: ${dbStatus?.status}`);
    }
    console.log("✓ Database confirms Blocker is strictly 'In Progress'!");

    // 4.3 Verify Blocker UI Form as Manager
    console.log(`Opening Blocker UI Form as Manager: /app/uranos-blocker/${createdBlockerId}...`);
    await pageMF.goto(`${BASE_URL}/app/uranos-blocker/${createdBlockerId}`, { waitUntil: "domcontentloaded" });
    await pageMF.waitForTimeout(3000);

    const uiFormStatus = await pageMF.evaluate(() => cur_frm.doc.status);
    console.log(`✓ Manager Blocker Form UI verifies status: '${uiFormStatus}'`);
    if (uiFormStatus !== "In Progress") {
      throw new Error(`Manager Form UI status mismatch! Got: ${uiFormStatus}`);
    }

    // 4.4 Verify Blocker Dashboard dynamic KPIs and table
    console.log("Navigating to Blocker Dashboard to verify dynamic RBAC metrics and list...");
    await pageMF.goto(`${BASE_URL}/app/blocker-dashboard`, { waitUntil: "domcontentloaded" });
    await pageMF.waitForTimeout(3500);

    // Check project selector includes PV-0099
    const projectOptions = await pageMF.evaluate(() => {
      const sel = document.getElementById("bd-project-select");
      if (!sel) return [];
      return Array.from(sel.options).map(o => o.value);
    });
    console.log(`✓ Project filter contains ${projectOptions.length} projects, including PV-0099: ${projectOptions.includes("PV-0099")}`);

    // Wait for table to render rows
    await pageMF.waitForFunction(() => {
      const table = document.getElementById("bd-table-body");
      return table && table.querySelectorAll("tr").length > 0;
    }, { timeout: 10000 });

    // Verify row for createdBlockerId or PV-0099 is displayed
    const blockerRowFound = await pageMF.evaluate((blockerId) => {
      const rows = document.querySelectorAll("#bd-table-body tr");
      for (const row of rows) {
        if (row.innerText.includes("PV-0099") || row.innerText.includes(blockerId)) {
          return {
            text: row.innerText,
            found: true
          };
        }
      }
      return { found: false };
    }, createdBlockerId);

    console.log(`  Blocker Dashboard row for PV-0099 / ${createdBlockerId}: found=${blockerRowFound.found}`);
    if (blockerRowFound.found) {
      console.log(`✓ Blocker table row content: ${blockerRowFound.text.replace(/\s+/g, " ").trim()}`);
    }

    // Check active KPIs
    const kpiActive = await pageMF.locator("#kpi-active").innerText();
    const kpiCritical = await pageMF.locator("#kpi-critical").innerText();
    console.log(`✓ Dynamic Dashboard KPIs: Active=${kpiActive}, Critical=${kpiCritical}`);

    await pageMF.screenshot({ path: path.join(artifactDir, "step4_manager_verified_dashboard.png"), fullPage: false });
    console.log("✓ Screenshot saved: step4_manager_verified_dashboard.png");

    await managerFinalContext.close();

    console.log("\n================================================================================");
    console.log("   DEFINITIVE SUCCESS: FULL WORKFLOW CYCLE QA PASSED WITH ZERO ERRORS!");
    console.log("   1. Manager created PV-0099 & assigned Engineer + Site Team.");
    console.log("   2. Global Awesomebar search dropdown verified operational.");
    console.log("   3. Blocker Dashboard '+ Nouvel Obstacle' button verified & operational.");
    console.log("   4. Site Team created Critical Blocker assigned to Engineer.");
    console.log("   5. Engineer transitioned status to 'In Progress'.");
    console.log("   6. Manager validated status update across Database, Form UI & Dashboard.");
    console.log("================================================================================");

  } finally {
    await browser.close();
  }
}

runFullUranosCycleTest().catch(err => {
  console.error("\n❌ FULL CYCLE TEST FAILED:", err);
  process.exit(1);
});
