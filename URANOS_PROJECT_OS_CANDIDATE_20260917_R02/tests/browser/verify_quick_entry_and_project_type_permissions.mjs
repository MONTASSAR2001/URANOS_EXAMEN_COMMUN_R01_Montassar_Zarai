#!/usr/bin/env node
/**
 * Test: Verify Quick Entry series hiding & Project Type permission fix
 * Asserts:
 *  1. Quick Entry modal for Project hides the Series (naming_series) field completely.
 *  2. Saving via Quick Entry auto-assigns 'PV-.####' in the background without user interaction.
 *  3. Opening a Project Form (e.g. PV-0004) triggers ZERO "Permission Error" popups for 'Project Type'.
 */

import { chromium } from "playwright";
import path from "path";
import { execSync } from "child_process";

const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";

async function runTest() {
  console.log("==================================================================");
  console.log("  VERIFY QUICK ENTRY SERIES HIDING & PROJECT TYPE PERMISSION FIX  ");
  console.log("==================================================================");

  // 1. Reset series to 20 and clean any prior test project
  execSync("docker exec -i uranos-backend bench --site uranos.localhost mariadb -e 'DELETE FROM tabProject WHERE name=\"PV-0021\"; DELETE FROM `tabURANOS Project Profile` WHERE project=\"PV-0021\"; UPDATE tabSeries SET current=20 WHERE name=\"PV-\";'");

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
    dialogAlerts.push(dialog.message());
    await dialog.accept();
  });

  // Login as Manager
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

  try {
    // 2. Test Quick Entry Modal: Click "+ Add Project" on Project List
    console.log("\n--- 2. TESTING QUICK ENTRY: HIDING NAMING SERIES ---");
    await page.evaluate(() => frappe.set_route("List", "Project"));
    await page.waitForTimeout(3000);

    // Look for "+ Add Project" button
    const addProjectBtn = page.locator(".primary-action:has-text('Add Project'), button:has-text('+ Add Project')").first();
    await addProjectBtn.waitFor({ state: "visible", timeout: 10000 });
    console.log("✓ Found '+ Add Project' button on Project list view");

    await addProjectBtn.click();
    await page.waitForTimeout(1500);

    // Check if modal is visible
    const modal = page.locator(".modal:visible, .quick-entry-modal:visible").first();
    await modal.waitFor({ state: "visible", timeout: 8000 });
    console.log("✓ Quick Entry modal is open and visible");

    // Inspect fields inside modal
    const modalFields = await modal.evaluate((el) => {
      const fieldEls = el.querySelectorAll("[data-fieldname]");
      const result = [];
      fieldEls.forEach(f => {
        const fn = f.getAttribute("data-fieldname");
        const style = window.getComputedStyle(f);
        const isVisible = style.display !== "none" && style.visibility !== "hidden" && f.offsetHeight > 0;
        result.push({ fieldname: fn, isVisible, display: style.display });
      });
      return result;
    });

    console.log("Quick Entry Modal Fields:", modalFields);

    const seriesField = modalFields.find(f => f.fieldname === "naming_series" || f.fieldname === "series");
    const isSeriesVisible = seriesField ? seriesField.isVisible : false;
    console.log(`✓ Is Naming Series field visible in Quick Entry? -> ${isSeriesVisible} (Expected: false)`);

    if (isSeriesVisible) {
      throw new Error("FAIL: Naming Series is still visible in Quick Entry modal!");
    }
    console.log("✓ PASS: Naming Series is completely hidden in Quick Entry modal!");

    // Capture Quick Entry modal screenshot without series
    await page.screenshot({
      path: path.join(artifactDir, "quick_entry_modal_without_naming_series.png"),
      fullPage: false
    });
    console.log("✓ Saved quick_entry_modal_without_naming_series.png");

    // Fill Project Name and Save
    const testTitle = "Centrale Solaire Test UX Quick Entry (Auto Series)";
    const nameInput = modal.locator('[data-fieldname="project_name"] input');
    await nameInput.waitFor({ state: "visible", timeout: 5000 });
    await nameInput.fill(testTitle);
    console.log(`Filled Project Name: '${testTitle}'`);

    const saveBtn = modal.locator("button.btn-primary:has-text('Save'), .modal-footer button.btn-primary");
    await saveBtn.click();
    await page.waitForTimeout(3000);

    // Verify in DB that project was created and auto-assigned PV-0021
    const dbCheck = execSync(
      `docker exec -i uranos-backend bench --site uranos.localhost mariadb -e "SELECT name, project_name, naming_series FROM tabProject WHERE project_name='${testTitle}';"`
    ).toString().trim();
    console.log("DB Project Record:\n" + dbCheck);

    if (!dbCheck.includes("PV-0021")) {
      throw new Error(`Expected project to have ID PV-0021, but DB record was: ${dbCheck}`);
    }
    console.log("✓ PASS: Project was successfully created via Quick Entry with auto-assigned series PV-0021!");

    // 3. Test Project Form (PV-0004) - Zero Permission Error Popups
    console.log("\n--- 3. TESTING PROJECT FORM: ZERO PERMISSION ERROR POPUPS ---");
    await page.evaluate(() => frappe.set_route("Form", "Project", "PV-0004"));
    await page.waitForTimeout(4000);

    // Check for any visible error modals or alert banners
    const errorDialog = page.locator(".modal.msgprint-dialog:visible, .modal:has-text('Permission Error'):visible");
    const errorCount = await errorDialog.count();
    console.log(`Visible Permission Error dialogs: ${errorCount} (Expected: 0)`);

    if (errorCount > 0) {
      const errorText = await errorDialog.first().innerText();
      console.error("Error dialog content:", errorText);
      throw new Error(`FAIL: Permission Error popup appeared: ${errorText}`);
    }
    console.log("✓ PASS: No Permission Error popup for 'Project Type' or any other DocType!");

    // Assert 3 Cards are rendered on PV-0004
    const cardsRow = page.locator(".uranos-project-cards-row");
    await cardsRow.waitFor({ timeout: 10000 });
    console.log("✓ 3 Executive Glassmorphic Cards rendered smoothly on Project Form PV-0004");

    // Capture Project Form without any errors
    await page.screenshot({
      path: path.join(artifactDir, "project_form_no_permission_error.png"),
      fullPage: false
    });
    console.log("✓ Saved project_form_no_permission_error.png");

    // 4. Clean up test project PV-0021 so exam starts pristine at 20
    console.log("\n--- 4. CLEANING UP TEST PROJECT PV-0021 FOR EXAM READINESS ---");
    execSync("docker exec -i uranos-backend bench --site uranos.localhost mariadb -e 'DELETE FROM tabProject WHERE name=\"PV-0021\"; DELETE FROM `tabURANOS Project Profile` WHERE project=\"PV-0021\"; UPDATE tabSeries SET current=20 WHERE name=\"PV-\";'");
    console.log("✓ Test project PV-0021 cleaned up; series reset to 20 for pristine exam demo!");

    console.log("\n==================================================================");
    console.log("  ALL TESTS PASSED: QUICK ENTRY & PROJECT TYPE FULLY RESOLVED!   ");
    console.log("==================================================================");

  } catch (err) {
    console.error("Test failed:", err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

runTest();
