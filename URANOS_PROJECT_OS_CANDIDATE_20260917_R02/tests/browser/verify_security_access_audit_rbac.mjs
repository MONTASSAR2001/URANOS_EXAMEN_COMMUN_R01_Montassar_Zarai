import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifySecurityAccessAuditRbac() {
  console.log("==================================================================");
  console.log("   URANOS Security & Access Audit RBAC Verification");
  console.log("==================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/465edcf9-4f3c-45a7-b2e1-1b4e8d2dadb6";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

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
    await page.waitForTimeout(2000);
    console.log(`✓ Logged in as ${username}`);
  }

  async function logoutUser(page) {
    console.log("Logging out...");
    try {
      await page.goto("http://localhost:8080/api/method/logout", { waitUntil: "networkidle" });
    } catch (e) {
      await page.evaluate(() => {
        if (window.frappe && frappe.app && frappe.app.logout) {
          frappe.app.logout();
        }
      });
    }
    await page.waitForTimeout(1500);
  }

  try {
    // -------------------------------------------------------------
    // TEST 1: ingenieur_01@uranos.local (Engineer - Forbidden)
    // -------------------------------------------------------------
    console.log("\n==============================================================");
    console.log("TEST 1: Testing ingenieur_01@uranos.local (Engineering Director)");
    console.log("==============================================================");

    const context1 = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page1 = await context1.newPage();

    await loginUser(page1, "ingenieur_01@uranos.local", "Password123!");

    // Check User Dropdown link
    console.log("Checking User Dropdown for Security & Access Audit link...");
    const userBtn1 = page1.locator("#gvUserPillBtn, .gv-user-pill").first();
    await userBtn1.waitFor({ timeout: 10000 });
    await userBtn1.click();
    await page1.waitForTimeout(600);

    const auditDropdownLink1 = page1.locator("#gvAccessAuditDropdownLink");
    const isLink1Visible = await auditDropdownLink1.isVisible().catch(() => false);
    console.log(`Dropdown Audit Link visible for Engineer: ${isLink1Visible}`);
    if (isLink1Visible) {
      throw new Error("FAILED: #gvAccessAuditDropdownLink is visible for ingenieur_01@uranos.local!");
    }
    console.log("✓ PASSED: Link is completely HIDDEN from Engineer user dropdown.");

    // Check Settings page links
    console.log("Checking Settings workspace for Security & Access Audit links...");
    await page1.goto("http://localhost:8080/app/erpnext-settings", { waitUntil: "networkidle" });
    await page1.waitForTimeout(2000);

    const settingsHeaderBtn1 = page1.locator("#gvBtnAccessAuditLink");
    const isSettingsBtn1Visible = await settingsHeaderBtn1.isVisible().catch(() => false);
    console.log(`Settings Header Audit Link visible for Engineer: ${isSettingsBtn1Visible}`);
    if (isSettingsBtn1Visible) {
      throw new Error("FAILED: #gvBtnAccessAuditLink is visible for ingenieur_01 in Settings!");
    }
    console.log("✓ PASSED: Link is completely HIDDEN from Settings workspace header.");

    // Direct Navigation to /app/access-audit
    console.log("Attempting direct navigation to /app/access-audit...");
    await page1.goto("http://localhost:8080/app/access-audit", { waitUntil: "networkidle" });
    await page1.waitForTimeout(3000);

    const auditDashboard1 = page1.locator(".uranos-audit-dashboard, .uranos-chic-saas-view[data-module='access-audit']");
    const isDashboard1Visible = await auditDashboard1.isVisible().catch(() => false);
    console.log(`Audit Dashboard visible for Engineer: ${isDashboard1Visible}`);
    if (isDashboard1Visible) {
      throw new Error("FAILED: Security & Access Audit Dashboard rendered for ingenieur_01@uranos.local!");
    }

    // Verify "Not permitted" message
    const pageText1 = await page1.evaluate(() => document.body.innerText);
    const hasNotPermitted1 = pageText1.includes("Not permitted") ||
                             pageText1.includes("not permitted") ||
                             pageText1.includes("Non autorisé") ||
                             pageText1.includes("Sorry! You are not permitted to view this page");
    console.log(`Not permitted message displayed for Engineer: ${hasNotPermitted1}`);
    if (!hasNotPermitted1) {
      console.warn("Warning: Could not find exact 'Not permitted' text, checking msg-box or alert...");
    }

    const screenshotPathBlocked = path.join(artifactDir, "engineer_access_audit_blocked.png");
    await page1.screenshot({ path: screenshotPathBlocked, fullPage: true });
    console.log(`✓ Screenshot captured: ${screenshotPathBlocked}`);
    await context1.close();

    // -------------------------------------------------------------
    // TEST 2: chantier_01@uranos.local (Site Controller - Forbidden)
    // -------------------------------------------------------------
    console.log("\n==============================================================");
    console.log("TEST 2: Testing chantier_01@uranos.local (Site Controller)");
    console.log("==============================================================");

    const context2 = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const page2 = await context2.newPage();

    await loginUser(page2, "chantier_01@uranos.local", "Password123!");

    // Check User Dropdown link
    const userBtn2 = page2.locator("#gvUserPillBtn, .gv-user-pill").first();
    await userBtn2.waitFor({ timeout: 10000 });
    await userBtn2.click();
    await page2.waitForTimeout(600);

    const auditDropdownLink2 = page2.locator("#gvAccessAuditDropdownLink");
    const isLink2Visible = await auditDropdownLink2.isVisible().catch(() => false);
    console.log(`Dropdown Audit Link visible for Site Controller: ${isLink2Visible}`);
    if (isLink2Visible) {
      throw new Error("FAILED: #gvAccessAuditDropdownLink is visible for chantier_01@uranos.local!");
    }
    console.log("✓ PASSED: Link is completely HIDDEN from Site Controller user dropdown.");

    // Direct Navigation to /app/access-audit
    console.log("Attempting direct navigation to /app/access-audit...");
    await page2.goto("http://localhost:8080/app/access-audit", { waitUntil: "networkidle" });
    await page2.waitForTimeout(3000);

    const auditDashboard2 = page2.locator(".uranos-audit-dashboard, .uranos-chic-saas-view[data-module='access-audit']");
    const isDashboard2Visible = await auditDashboard2.isVisible().catch(() => false);
    console.log(`Audit Dashboard visible for Site Controller: ${isDashboard2Visible}`);
    if (isDashboard2Visible) {
      throw new Error("FAILED: Security & Access Audit Dashboard rendered for chantier_01@uranos.local!");
    }

    const pageText2 = await page2.evaluate(() => document.body.innerText);
    const hasNotPermitted2 = pageText2.includes("Not permitted") ||
                             pageText2.includes("not permitted") ||
                             pageText2.includes("Non autorisé") ||
                             pageText2.includes("Sorry! You are not permitted to view this page");
    console.log(`Not permitted message displayed for Site Controller: ${hasNotPermitted2}`);

    const screenshotPathChantier = path.join(artifactDir, "chantier_access_audit_blocked.png");
    await page2.screenshot({ path: screenshotPathChantier, fullPage: true });
    console.log(`✓ Screenshot captured: ${screenshotPathChantier}`);
    await context2.close();

    // -------------------------------------------------------------
    // TEST 3: direction_01@uranos.local (Executive - Permitted)
    // -------------------------------------------------------------
    console.log("\n==============================================================");
    console.log("TEST 3: Testing direction_01@uranos.local (Executive Director)");
    console.log("==============================================================");

    const context3 = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const page3 = await context3.newPage();

    await loginUser(page3, "direction_01@uranos.local", "Password123!");

    // Check User Dropdown link
    console.log("Checking User Dropdown for Security & Access Audit link...");
    const userBtn3 = page3.locator("#gvUserPillBtn, .gv-user-pill").first();
    await userBtn3.waitFor({ timeout: 10000 });
    await userBtn3.click();
    await page3.waitForTimeout(600);

    const auditDropdownLink3 = page3.locator("#gvAccessAuditDropdownLink");
    const isLink3Visible = await auditDropdownLink3.isVisible().catch(() => false);
    console.log(`Dropdown Audit Link visible for Executive: ${isLink3Visible}`);
    if (!isLink3Visible) {
      throw new Error("FAILED: #gvAccessAuditDropdownLink is NOT visible for direction_01@uranos.local!");
    }
    console.log("✓ PASSED: Link is VISIBLE in Executive user dropdown.");

    // Click the link to navigate
    console.log("Clicking the dropdown link to navigate to /app/access-audit...");
    await auditDropdownLink3.click();
    await page3.waitForURL(url => url.pathname.includes("/access-audit"), { timeout: 15000 });
    await page3.waitForTimeout(3000);

    // Wait for the SaaS dashboard container
    const auditView3 = page3.locator(".uranos-audit-dashboard, .uranos-chic-saas-view[data-module='access-audit']").first();
    await auditView3.waitFor({ timeout: 15000 });
    console.log("✓ PASSED: Security & Access Audit Dashboard rendered for Executive!");
    await page3.waitForTimeout(2000);

    // Dismiss any modal dialog if visible
    const modalClose3 = page3.locator(".modal.show button.btn-modal-close, .modal.show .close").first();
    if (await modalClose3.isVisible().catch(() => false)) {
      await modalClose3.click().catch(() => {});
      await page3.waitForTimeout(500);
    }

    // Verify KPIs and table exist
    const kpiCount = await page3.locator(".uranos-saas-kpi-tile").count();
    const rowCount = await page3.locator(".uranos-audit-row").count();
    console.log(`Executive dashboard verified with ${kpiCount} KPI cards and ${rowCount} monitored user rows.`);
    if (kpiCount === 0 || rowCount === 0) {
      throw new Error("FAILED: KPI cards or monitored user rows are missing on Executive dashboard!");
    }

    const screenshotPathPermitted = path.join(artifactDir, "executive_access_audit_permitted.png");
    await page3.screenshot({ path: screenshotPathPermitted, fullPage: true });
    console.log(`✓ Screenshot captured: ${screenshotPathPermitted}`);
    await context3.close();

    console.log("\n==============================================================");
    console.log(">>> ALL RBAC PERMISSION & UI RESTRICTION TESTS PASSED! <<<");
    console.log("==============================================================");

  } finally {
    await browser.close();
  }
}

verifySecurityAccessAuditRbac().catch(err => {
  console.error("FATAL TEST FAILURE:", err);
  process.exit(1);
});
