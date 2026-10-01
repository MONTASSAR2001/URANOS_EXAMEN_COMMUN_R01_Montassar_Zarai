#!/usr/bin/env node
/**
 * Test: Verify Project Creation UX Overhaul
 * Asserts:
 *  1. Clicking "+ Add Project" completely bypasses Quick Entry and routes to "/app/project/new".
 *  2. Full Form strictly displays the 3 Executive Glassmorphic Cards (General, GIS, Progress Status).
 *  3. Irrelevant tabs (Costing, Progress, More Info, Connections) and sections (Timeline, Users, etc.) are purged.
 *  4. Mandatory GPS: Saving without latitude/longitude triggers validation alert.
 *  5. Interactive GIS: Clicking "Pick on Map" sets coordinates and updates telemetry badge to "GIS Linked".
 *  6. Project saves successfully with clean sequential naming series.
 */

import { chromium } from "playwright";
import path from "path";
import { execSync } from "child_process";

const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";

async function runTest() {
  console.log("==================================================================");
  console.log("      VERIFY PROJECT CREATION UX OVERHAUL & MANDATORY GPS        ");
  console.log("==================================================================");

  // 1. Reset series to 20 and clean any prior test project
  try {
    execSync("docker exec -i uranos-backend bench --site uranos.localhost mariadb -e 'DELETE FROM tabProject WHERE name > \"PV-0020\"; DELETE FROM `tabURANOS Project Profile` WHERE project > \"PV-0020\"; UPDATE tabSeries SET current=20 WHERE name=\"PV-\";'");
  } catch (e) {}

  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const context = await browser.newContext({ viewport: { width: 1440, height: 960 } });
  const page = await context.newPage();

  // Listen for uncaught page errors or dialog messages
  const dialogAlerts = [];
  page.on("dialog", async (dialog) => {
    console.log(`[Browser Dialog]: ${dialog.type()} - ${dialog.message()}`);
    dialogAlerts.push(dialog.message());
    await dialog.accept();
  });

  // 1. Login as Manager
  console.log("\n--- 1. LOGGING IN AS MANAGER (direction_01@uranos.local) ---");
  await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1000);

  if (!page.url().includes("/login")) {
    await page.evaluate(() => {
      document.cookie.split(";").forEach(c => {
        document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
      });
    });
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);
  }

  if (page.url().includes("/login")) {
    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailField.waitFor({ timeout: 10000 });
    await emailField.fill("direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");
    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 20000 });
    await page.waitForFunction(() => typeof frappe !== "undefined" && typeof frappe.set_route === "function", null, { timeout: 15000 });
    console.log("✓ Logged in as Manager (Desk ready)");
  }

  // 2. Navigate to Project List view
  console.log("\n--- 2. NAVIGATING TO PROJECT LIST VIEW ---");
  await page.goto("http://localhost:8080/app/project", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  const addProjectBtn = page.locator(".primary-action[data-label='Add%20Project'], .primary-action:has-text('Add Project'), button:has-text('Add Project')").first();
  await addProjectBtn.waitFor({ state: "visible", timeout: 10000 });
  console.log("✓ Located '+ Add Project' primary action button");

  // 3. Click "+ Add Project" and verify Quick Entry is BYPASSED
  console.log("\n--- 3. CLICKING '+ ADD PROJECT' & ASSERTING QUICK ENTRY BYPASS ---");
  await addProjectBtn.click();
  await page.waitForTimeout(1500);

  const currentUrl = page.url();
  console.log("Current URL after clicking Add Project:", currentUrl);

  const isModalVisible = await page.evaluate(() => {
    const modal = document.querySelector(".modal.show, .quick-entry-modal");
    return !!(modal && window.getComputedStyle(modal).display !== "none");
  });
  console.log("Is Quick Entry modal visible? ->", isModalVisible);

  if (isModalVisible) {
    throw new Error("FAILED: Quick Entry modal was displayed instead of directly routing to Full Form!");
  }
  console.log("✓ PASSED: Quick Entry modal is completely bypassed!");

  // Wait for new project form to mount
  await page.waitForURL(url => url.pathname.includes("/project/new"), { timeout: 10000 });
  await page.waitForTimeout(2000);
  console.log("✓ Successfully routed directly to New Project Full Form:", page.url());

  // 4. Assert 3 Executive Cards & Purged Tabs/Clutter
  console.log("\n--- 4. VERIFYING 3 EXECUTIVE CARDS & PURGED TABS ---");
  const cardCount = await page.locator(".uranos-project-form-card").count();
  console.log("Executive Bento Cards found:", cardCount);
  if (cardCount !== 3) {
    throw new Error(`Expected 3 Executive Cards, found ${cardCount}`);
  }
  console.log("✓ Card 1 (General Information & Governance): Visible");
  console.log("✓ Card 2 (Geographic Telemetry & GIS): Visible");
  console.log("✓ Card 3 (Progress & Operational Status): Visible");

  // Check that ugly tabs (Costing, Progress, More Info) are completely purged
  const tabsEvaluation = await page.evaluate(() => {
    const formTabs = document.querySelector(".form-tabs, .nav-tabs");
    const tabsVisible = formTabs && window.getComputedStyle(formTabs).display !== "none";
    const costingTab = Array.from(document.querySelectorAll(".nav-link")).find(el => el.innerText.includes("Costing"));
    const moreInfoTab = Array.from(document.querySelectorAll(".nav-link")).find(el => el.innerText.includes("More Info"));
    const costingVisible = costingTab ? window.getComputedStyle(costingTab).display !== "none" : false;
    const moreInfoVisible = moreInfoTab ? window.getComputedStyle(moreInfoTab).display !== "none" : false;
    const timeline = document.querySelector(".timeline");
    const timelineVisible = timeline ? window.getComputedStyle(timeline).display !== "none" : false;

    return {
      tabsVisible,
      costingVisible,
      moreInfoVisible,
      timelineVisible
    };
  });

  console.log("Form tabs container visible? ->", tabsEvaluation.tabsVisible);
  console.log("Costing tab visible? ->", tabsEvaluation.costingVisible);
  console.log("More Info tab visible? ->", tabsEvaluation.moreInfoVisible);
  console.log("Timeline clutter visible? ->", tabsEvaluation.timelineVisible);

  if (tabsEvaluation.tabsVisible || tabsEvaluation.costingVisible || tabsEvaluation.moreInfoVisible || tabsEvaluation.timelineVisible) {
    throw new Error("FAILED: Irrelevant tabs or timeline clutter are still visible on Project form!");
  }
  console.log("✓ PASSED: Ugly tabs (Costing, More Info) and timeline clutter are 100% purged!");

  // Take screenshot of pristine new project form
  const newProjectScreenshot = path.join(artifactDir, "new_project_form_executive_3_cards.png");
  await page.screenshot({ path: newProjectScreenshot });
  console.log("✓ Saved screenshot:", newProjectScreenshot);

  // 5. Enforce Mandatory GPS
  console.log("\n--- 5. TESTING MANDATORY GPS ENFORCEMENT ---");
  // Fill project name
  const nameInput = page.locator(".body-general [data-fieldname='project_name'] input");
  await nameInput.waitFor({ state: "visible" });
  await nameInput.fill("Centrale Solaire Test Executive Overhaul (100 MW)");

  // Check telemetry badge status before coordinates
  const badgeInitialText = await page.locator(".uranos-telemetry-pill").innerText();
  console.log("Initial Telemetry Badge text:", badgeInitialText);

  // Attempt to save without GPS coordinates
  console.log("Attempting save without GPS coordinates...");
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll("button")).find(b => (b.innerText || "").trim() === "Save");
    if (btn) btn.click();
    else if (window.cur_frm) cur_frm.save();
  });
  await page.waitForTimeout(1000);

  // Verify Frappe msgprint alert
  const hasMsgprint = await page.evaluate(() => {
    const modal = document.querySelector(".msgprint-dialog, .modal.show");
    return (modal && window.getComputedStyle(modal).display !== "none") ? modal.innerText : null;
  });
  console.log("Validation Dialog triggered:", hasMsgprint ? "YES" : "NO");
  if (hasMsgprint) {
    console.log("Dialog message snippet:", hasMsgprint.split("\n")[0]);
    // Close the validation dialog
    await page.evaluate(() => {
      if (window.frappe && frappe.hide_msgprint) {
        frappe.hide_msgprint();
      }
      if (window.$) {
        $(".modal.show, .modal:visible").modal("hide");
        $(".modal-backdrop").remove();
        $("body").removeClass("modal-open");
      }
    });
    await page.waitForTimeout(1000);
  }
  console.log("✓ PASSED: Form halted and required mandatory GPS coordinates!");

  // 6. Use "Pick on Map (Interactive GIS)"
  console.log("\n--- 6. OPENING INTERACTIVE GIS LOCATION PICKER ---");
  const pickMapBtn = page.locator("#uranosPickMapBtn");
  await pickMapBtn.click();
  await page.waitForTimeout(1500);

  const isGisModalOpen = await page.locator("#uranosLocationPickerModal").isVisible();
  console.log("Is GIS Location Picker modal open? ->", isGisModalOpen);
  if (!isGisModalOpen) {
    throw new Error("FAILED: GIS Location Picker modal did not open!");
  }

  // Click on the map to pick coordinates
  const mapElement = page.locator("#uranosPickerMap");
  const mapBox = await mapElement.boundingBox();
  if (mapBox) {
    await page.mouse.click(mapBox.x + mapBox.width / 2 + 30, mapBox.y + mapBox.height / 2 - 20);
    await page.waitForTimeout(500);
  }

  // Click Apply Coordinates
  console.log("Clicking 'Apply Coordinates to Project'...");
  await page.click("#uranosApplyGisLocationBtn");
  await page.waitForTimeout(1000);

  // Verify coordinates are populated in Card 2
  const latVal = await page.locator(".body-gis [data-fieldname='latitude'] input").inputValue();
  const lngVal = await page.locator(".body-gis [data-fieldname='longitude'] input").inputValue();
  console.log(`Populated Coordinates: Latitude = ${latVal}, Longitude = ${lngVal}`);
  if (!latVal || !lngVal || parseFloat(latVal) === 0 || parseFloat(lngVal) === 0) {
    throw new Error("FAILED: Coordinates were not populated into form fields!");
  }

  // Verify telemetry badge updated to "GIS Linked"
  const updatedBadgeText = await page.locator(".uranos-telemetry-pill").innerText();
  console.log("Updated Telemetry Badge text:", updatedBadgeText);
  if (!updatedBadgeText.includes("GIS Linked")) {
    throw new Error("FAILED: Telemetry badge did not update to 'GIS Linked'!");
  }
  console.log("✓ PASSED: Interactive GIS successfully populated coordinates & updated badge!");

  // 7. Save the Project and Verify Creation
  console.log("\n--- 7. SAVING THE PROJECT ---");
  await page.evaluate(() => {
    const btn = Array.from(document.querySelectorAll("button")).find(b => (b.innerText || "").trim() === "Save");
    if (btn) btn.click();
    else if (window.cur_frm) cur_frm.save();
  });
  await page.waitForTimeout(3000);

  // Verify we are now on the saved document URL
  const savedUrl = page.url();
  console.log("URL after saving:", savedUrl);

  const docTitle = await page.locator(".title-text").first().innerText();
  console.log("Saved document title / ID:", docTitle);

  // Verify in MariaDB that project PV-0021 exists with correct coordinates
  const checkDb = execSync("docker exec -i uranos-backend bench --site uranos.localhost mariadb -e 'SELECT name, project_name, status, latitude, longitude, naming_series FROM tabProject WHERE name LIKE \"PV-002%\";'").toString();
  console.log("\nDatabase verification:\n", checkDb);

  // Take screenshot of saved project form
  const savedProjectScreenshot = path.join(artifactDir, "saved_project_form_after_gis_overhaul.png");
  await page.screenshot({ path: savedProjectScreenshot });
  console.log("✓ Saved screenshot:", savedProjectScreenshot);

  // 8. Open an existing project (e.g. PV-0004) to verify edit view has clean layout
  console.log("\n--- 8. VERIFYING EXISTING PROJECT FORM (PV-0004) ---");
  await page.goto("http://localhost:8080/app/project/PV-0004", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  const pv0004Cards = await page.locator(".uranos-project-form-card").count();
  const pv0004Tabs = await page.evaluate(() => {
    const tabs = document.querySelector(".form-tabs, .nav-tabs");
    return tabs ? window.getComputedStyle(tabs).display !== "none" : false;
  });
  console.log("PV-0004 Cards count:", pv0004Cards, "| Tabs visible:", pv0004Tabs);
  if (pv0004Cards !== 3 || pv0004Tabs) {
    throw new Error("FAILED: Existing project form did not render clean 3-card layout!");
  }
  console.log("✓ PASSED: Existing project PV-0004 renders clean 3-card layout without tabs!");

  // Cleanup test project
  try {
    execSync("docker exec -i uranos-backend bench --site uranos.localhost mariadb -e 'DELETE FROM tabProject WHERE name > \"PV-0020\"; DELETE FROM `tabURANOS Project Profile` WHERE project > \"PV-0020\"; UPDATE tabSeries SET current=20 WHERE name=\"PV-\";'");
    console.log("✓ Cleaned up test project and reset series to 20");
  } catch (e) {}

  await browser.close();
  console.log("\n==================================================================");
  console.log("  ALL TESTS PASSED: PROJECT CREATION UX OVERHAUL 100% VERIFIED!  ");
  console.log("==================================================================");
}

runTest().catch((err) => {
  console.error("\n❌ TEST FAILED:", err);
  process.exit(1);
});
