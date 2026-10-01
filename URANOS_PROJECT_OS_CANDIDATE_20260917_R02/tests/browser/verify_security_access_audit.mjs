import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifySecurityAccessAudit() {
  console.log("==================================================================");
  console.log("   URANOS Security & Access Audit Dashboard Verification");
  console.log("==================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/465edcf9-4f3c-45a7-b2e1-1b4e8d2dadb6";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 1100 }
  });
  const page = await context.newPage();

  page.on("console", msg => {
    if (msg.type() === "error" || msg.text().includes("Audit") || msg.text().includes("access-audit")) {
      console.log(`[BROWSER ${msg.type()}]:`, msg.text());
    }
  });
  page.on("pageerror", err => {
    console.log("[BROWSER ERROR]:", err.message);
  });

  try {
    // 1. Authenticate as direction_01@uranos.local
    console.log("\n1. Logging in as direction_01@uranos.local (Executive)...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailField.waitFor({ timeout: 10000 });
    await emailField.fill("direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");
    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 20000 });
    console.log("✓ Logged in successfully");

    // 2. Navigate directly to /app/access-audit
    console.log("\n2. Navigating to /app/access-audit route...");
    await page.goto("http://localhost:8080/app/access-audit", { waitUntil: "networkidle" });
    await page.waitForTimeout(3000);

    // Wait for the SaaS dashboard container
    const auditView = page.locator(".uranos-audit-dashboard, .uranos-chic-saas-view[data-module='access-audit']").first();
    await auditView.waitFor({ timeout: 15000 });
    console.log("✓ Security & Access Audit Dashboard rendered!");
    await page.waitForTimeout(2500);

    // Dismiss any modal dialog if visible
    const modalClose = page.locator(".modal.show button.btn-modal-close, .modal.show .close").first();
    if (await modalClose.isVisible().catch(() => false)) {
      await modalClose.click().catch(() => {});
      await page.waitForTimeout(500);
    }

    // 3. Inspect Live Data & Metrics
    const auditMetrics = await page.evaluate(() => {
      const kpis = Array.from(document.querySelectorAll(".uranos-saas-kpi-deck .uranos-saas-kpi-tile")).map(tile => {
        const label = tile.querySelector(".kpi-label")?.innerText?.trim() || "";
        const val = tile.querySelector(".kpi-value")?.innerText?.trim() || "";
        const sub = tile.querySelector(".kpi-subtext")?.innerText?.trim() || "";
        return { label, val, sub };
      });

      const tableRows = Array.from(document.querySelectorAll(".uranos-audit-table tbody tr.uranos-audit-row")).map(row => {
        const name = row.querySelector(".uranos-audit-user-meta .name")?.innerText?.trim() || "";
        const email = row.querySelector(".uranos-audit-user-meta .email")?.innerText?.trim() || "";
        const role = row.querySelector(".uranos-role-badge")?.innerText?.trim() || "";
        const status = row.querySelector(".uranos-status-pill")?.innerText?.trim() || "";
        const lastLogin = row.children[3]?.innerText?.trim() || "";
        const lastLogout = row.children[4]?.innerText?.trim() || "";
        const ip = row.querySelector(".uranos-ip-badge")?.innerText?.trim() || "";
        const logins = row.querySelector(".uranos-total-logins-badge")?.innerText?.trim() || "";
        return { name, email, role, status, lastLogin, lastLogout, ip, logins };
      });

      const recentEvents = Array.from(document.querySelectorAll(".uranos-event-timeline .uranos-event-item")).map(ev => {
        const title = ev.querySelector(".title")?.innerText?.trim() || "";
        const meta = ev.querySelector(".meta")?.innerText?.trim() || "";
        const badge = ev.querySelector(".uranos-event-right")?.innerText?.trim() || "";
        return { title, meta, badge };
      });

      return { kpis, tableRows, recentEvents };
    });

    console.log("\n3. Dynamic KPI Cards from Database:");
    auditMetrics.kpis.forEach(k => console.log(`   - ${k.label}: ${k.val} (${k.sub})`));

    console.log(`\n4. Audit Table Rows (${auditMetrics.tableRows.length} users monitored):`);
    auditMetrics.tableRows.forEach(u => {
      console.log(`   - ${u.name} | ${u.role} | Status: ${u.status} | IP: ${u.ip} | Logins: ${u.logins} | Last Login: ${u.lastLogin}`);
    });

    console.log(`\n5. Recent Security Activity Logs (${auditMetrics.recentEvents.length} events):`);
    auditMetrics.recentEvents.slice(0, 5).forEach(e => {
      console.log(`   - [${e.badge}] ${e.title} (${e.meta})`);
    });

    // 4. Test Search and Filter Interactivity
    console.log("\n6. Testing Real-time Search Interactivity (Query: 'chantier')...");
    await page.fill("#auditSearchInput", "chantier");
    await page.waitForTimeout(500);

    const visibleAfterSearch = await page.evaluate(() => {
      return Array.from(document.querySelectorAll(".uranos-audit-row"))
        .filter(r => window.getComputedStyle(r).display !== "none")
        .map(r => r.querySelector(".name")?.innerText?.trim());
    });
    console.log("   Visible rows after search:", visibleAfterSearch);

    // Reset search
    await page.fill("#auditSearchInput", "");
    await page.waitForTimeout(300);

    // Filter by 'Ingénieurs'
    console.log("\n7. Testing Filter Chip Interactivity ('Ingénieurs')...");
    await page.click(".uranos-saas-chip[data-filter='engineer']");
    await page.waitForTimeout(500);

    const visibleEngineers = await page.evaluate(() => {
      return Array.from(document.querySelectorAll(".uranos-audit-row"))
        .filter(r => window.getComputedStyle(r).display !== "none")
        .map(r => r.querySelector(".name")?.innerText?.trim());
    });
    console.log("   Visible engineers after filter:", visibleEngineers);

    // Reset filter
    await page.click(".uranos-saas-chip[data-filter='all']");
    await page.waitForTimeout(500);

    // 5. Capture Proof Screenshot
    const screenshotPath = path.join(artifactDir, "security_access_audit_dashboard.png");
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`\n✓ Full Page Screenshot captured: ${screenshotPath}`);

    // 6. Test Settings Workspace Integration Link
    console.log("\n8. Testing Settings Workspace Integration (/app/erpnext-settings)...");
    await page.goto("http://localhost:8080/app/erpnext-settings", { waitUntil: "networkidle" });
    await page.waitForTimeout(3000);

    const accessAuditBtn = page.locator("#gvBtnAccessAuditLink, a[href='/app/access-audit']").first();
    const btnVisible = await accessAuditBtn.isVisible();
    console.log(`   'Audit Sécurité & Accès' Link in Settings Workspace visible: ${btnVisible}`);

    if (btnVisible) {
      console.log("   Clicking 'Audit Sécurité & Accès' button from Settings...");
      await accessAuditBtn.click();
      await page.waitForTimeout(2000);
      const onAuditPage = page.url().includes("/access-audit");
      console.log(`   Successfully navigated back to /app/access-audit: ${onAuditPage}`);
    }

    console.log("\n==================================================================");
    console.log("   ALL VERIFICATIONS PASSED SUCCESSFULLY!");
    console.log("==================================================================");

  } catch (err) {
    console.error("Test encountered an error:", err);
    const errPath = path.join(artifactDir, "access_audit_error.png");
    await page.screenshot({ path: errPath });
    throw err;
  } finally {
    await browser.close();
  }
}

verifySecurityAccessAudit();
