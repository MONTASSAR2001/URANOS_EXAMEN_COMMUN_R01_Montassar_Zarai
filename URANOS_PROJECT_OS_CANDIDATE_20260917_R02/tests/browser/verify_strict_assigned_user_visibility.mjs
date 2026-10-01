import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyStrictAssignedUserVisibility() {
  console.log("==================================================================");
  console.log("   URANOS OS — Strict Assigned-User Visibility Verification");
  console.log("==================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/4c9276b4-96e1-471d-ad96-037a119e20ff";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  async function createCleanPage() {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 960 },
      ignoreHTTPSErrors: true,
    });
    const page = await context.newPage();
    return { context, page };
  }

  async function loginUser(page, username, password) {
    console.log(`\nLogging in as ${username}...`);
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailField.waitFor({ timeout: 10000 });
    await emailField.fill(username);
    await page.fill("#loginPassword, #login_password, input[name='pwd']", password);
    await page.click("#btnContinue, .btn-login, button[type='submit']");
    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 20000 });
    await page.waitForTimeout(2500);
    console.log(`✓ Logged in successfully as ${username}`);
  }

  async function countGisMapMarkers(page) {
    console.log("Navigating to /desk to check GIS Map markers...");
    await page.goto("http://localhost:8080/desk", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);

    const mapCard = page.locator("#uranosGisMapCard").first();
    await mapCard.waitFor({ timeout: 15000 });

    // Wait for markers to be fetched and rendered
    await page.waitForFunction(() => {
      const markers = document.querySelectorAll(".uranos-map-marker");
      return markers.length > 0;
    }, { timeout: 15000 });

    await page.waitForTimeout(1500);

    const markerCount = await page.evaluate(() => {
      const markers = document.querySelectorAll(".uranos-map-marker");
      return markers.length;
    });

    console.log(`  -> Plotted GIS Map markers count: ${markerCount}`);
    return markerCount;
  }

  async function countProjectListRows(page) {
    console.log("Navigating to /app/project to check List View projects...");
    await page.goto("http://localhost:8080/app/project", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);

    // Clear any client-side default/residual filters to show all assigned projects
    await page.evaluate(async () => {
      if (window.cur_list && window.cur_list.filter_area) {
        const filters = cur_list.filter_area.get();
        if (filters && filters.length > 0) {
          cur_list.filter_area.clear(false);
          cur_list.refresh();
        }
      }
    });
    await page.waitForTimeout(2000);

    // Wait for list view data to load
    await page.waitForFunction(() => {
      if (window.cur_list && window.cur_list.data) {
        return window.cur_list.data.length > 0;
      }
      return document.querySelectorAll(".list-row-container, .list-row").length > 0;
    }, { timeout: 15000 });

    await page.waitForTimeout(1000);

    const listCount = await page.evaluate(() => {
      if (window.cur_list && Array.isArray(window.cur_list.data)) {
        return window.cur_list.data.length;
      }
      return document.querySelectorAll(".list-row-container, .list-row").length;
    });

    console.log(`  -> Project List View row count: ${listCount}`);
    return listCount;
  }

  try {
    // -------------------------------------------------------------
    // STEP 1: MANAGER (direction_01@uranos.local) -> 20 Projects
    // -------------------------------------------------------------
    console.log("\n==============================================================");
    console.log("STEP 1: Verify Manager sees ALL 20 projects on Map and List");
    console.log("==============================================================");
    {
      const { context, page } = await createCleanPage();
      await loginUser(page, "direction_01@uranos.local", "Password123!");

      const mapCount = await countGisMapMarkers(page);
      if (mapCount !== 20) {
        throw new Error(`Manager GIS Map marker count mismatch: Expected 20, got ${mapCount}`);
      }
      console.log(`✓ Manager GIS Map correctly shows 20 markers`);

      const listCount = await countProjectListRows(page);
      if (listCount !== 20) {
        throw new Error(`Manager Project List row count mismatch: Expected 20, got ${listCount}`);
      }
      console.log(`✓ Manager Project List correctly shows 20 projects`);

      await page.screenshot({ path: path.join(artifactDir, "1_manager_20_projects.png"), fullPage: false });
      await context.close();
    }

    // -------------------------------------------------------------
    // STEP 2: ENGINEER (ingenieur_01@uranos.local) -> exactly 3 Projects
    // -------------------------------------------------------------
    console.log("\n==============================================================");
    console.log("STEP 2: Verify Engineer sees EXACTLY 3 assigned projects on Map and List");
    console.log("==============================================================");
    {
      const { context, page } = await createCleanPage();
      await loginUser(page, "ingenieur_01@uranos.local", "Password123!");

      const mapCount = await countGisMapMarkers(page);
      if (mapCount !== 3) {
        throw new Error(`Engineer GIS Map marker count mismatch: Expected 3, got ${mapCount}`);
      }
      console.log(`✓ Engineer GIS Map correctly shows exactly 3 markers`);

      const listCount = await countProjectListRows(page);
      if (listCount !== 3) {
        throw new Error(`Engineer Project List row count mismatch: Expected 3, got ${listCount}`);
      }
      console.log(`✓ Engineer Project List correctly shows exactly 3 projects`);

      await page.screenshot({ path: path.join(artifactDir, "2_engineer_3_projects.png"), fullPage: false });
      await context.close();
    }

    // -------------------------------------------------------------
    // STEP 3: SITE TEAM (chantier_01@uranos.local) -> exactly 1 Project
    // -------------------------------------------------------------
    console.log("\n==============================================================");
    console.log("STEP 3: Verify Site Team sees EXACTLY 1 assigned project on Map and List");
    console.log("==============================================================");
    {
      const { context, page } = await createCleanPage();
      await loginUser(page, "chantier_01@uranos.local", "Password123!");

      const mapCount = await countGisMapMarkers(page);
      if (mapCount !== 1) {
        throw new Error(`Site Team GIS Map marker count mismatch: Expected 1, got ${mapCount}`);
      }
      console.log(`✓ Site Team GIS Map correctly shows exactly 1 marker`);

      const listCount = await countProjectListRows(page);
      if (listCount !== 1) {
        throw new Error(`Site Team Project List row count mismatch: Expected 1, got ${listCount}`);
      }
      console.log(`✓ Site Team Project List correctly shows exactly 1 project`);

      await page.screenshot({ path: path.join(artifactDir, "3_site_team_1_project.png"), fullPage: false });
      await context.close();
    }

    // -------------------------------------------------------------
    // STEP 4: MANAGER ASSIGNS NEW PROJECT TO SITE TEAM
    // -------------------------------------------------------------
    console.log("\n==============================================================");
    console.log("STEP 4: Manager assigns PV-0005 to Site Team in Project UI Card 1");
    console.log("==============================================================");
    {
      const { context, page } = await createCleanPage();
      await loginUser(page, "direction_01@uranos.local", "Password123!");

      console.log("Opening Project PV-0005 form to verify UI injection...");
      await page.goto("http://localhost:8080/app/project/PV-0005", { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(3000);

      // Verify Card 1 (General Information & Governance) is present
      const cardGeneral = page.locator(".uranos-project-form-card.card-general").first();
      await cardGeneral.waitFor({ timeout: 15000 });
      console.log("✓ Card 1 (General Information & Governance) found!");

      // Verify Assigned Engineer and Assigned Site Team fields are inside Card 1
      const engineerFieldInCard = page.locator(".body-general [data-fieldname='custom_assigned_engineer']").first();
      await engineerFieldInCard.waitFor({ timeout: 10000 });
      console.log("✓ 'custom_assigned_engineer' is cleanly injected inside Card 1!");

      const siteTeamFieldInCard = page.locator(".body-general [data-fieldname='custom_assigned_site_team']").first();
      await siteTeamFieldInCard.waitFor({ timeout: 10000 });
      console.log("✓ 'custom_assigned_site_team' is cleanly injected inside Card 1!");

      // Manager assigns chantier_01@uranos.local to PV-0005
      console.log("Assigning chantier_01@uranos.local to PV-0005 via Desk UI / API...");
      await page.evaluate(async () => {
        await new Promise((resolve, reject) => {
          frappe.call({
            method: "frappe.client.set_value",
            args: {
              doctype: "Project",
              name: "PV-0005",
              fieldname: "custom_assigned_site_team",
              value: "chantier_01@uranos.local"
            },
            callback: (r) => {
              if (r.exc) reject(r.exc);
              else resolve(r.message);
            }
          });
        });
      });

      console.log("✓ Assigned chantier_01@uranos.local to PV-0005 successfully!");
      await page.screenshot({ path: path.join(artifactDir, "4_manager_assigned_site_team.png"), fullPage: false });
      await context.close();
    }

    // -------------------------------------------------------------
    // STEP 5: SITE TEAM LOGS BACK IN -> EXACTLY 2 PROJECTS ON MAP AND LIST
    // -------------------------------------------------------------
    console.log("\n==============================================================");
    console.log("STEP 5: Site Team logs back in -> asserts EXACTLY 2 projects on Map and List");
    console.log("==============================================================");
    {
      const { context, page } = await createCleanPage();
      await loginUser(page, "chantier_01@uranos.local", "Password123!");

      const mapCount = await countGisMapMarkers(page);
      if (mapCount !== 2) {
        throw new Error(`Site Team GIS Map marker count mismatch after assignment: Expected 2, got ${mapCount}`);
      }
      console.log(`✓ Site Team GIS Map correctly updated to show EXACTLY 2 markers!`);

      const listCount = await countProjectListRows(page);
      if (listCount !== 2) {
        throw new Error(`Site Team Project List row count mismatch after assignment: Expected 2, got ${listCount}`);
      }
      console.log(`✓ Site Team Project List correctly updated to show EXACTLY 2 projects!`);

      await page.screenshot({ path: path.join(artifactDir, "5_site_team_2_projects.png"), fullPage: false });
      await context.close();
    }

    console.log("\n==============================================================");
    console.log("🎉 ALL TESTS PASSED! Strict Assigned-User Visibility verified!");
    console.log("==============================================================");

  } finally {
    await browser.close();
  }
}

verifyStrictAssignedUserVisibility().catch((err) => {
  console.error("FATAL ERROR in verifyStrictAssignedUserVisibility:", err);
  process.exit(1);
});
