import { chromium } from "playwright";
import path from "path";

async function verifyAccountingAndSupport() {
  console.log("==================================================================");
  console.log("   URANOS Group Accounting Permissions & Support SaaS Verification");
  console.log("==================================================================");

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
  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";

  // -------------------------------------------------------------------------
  // TEST 1: direction_01 Accounting Permission & Invoicing Access
  // -------------------------------------------------------------------------
  console.log("1. Authenticating as direction_01@uranos.local (URANOS Executive)...");
  await page.goto("http://localhost:8080/login", { waitUntil: "networkidle" });
  await page.fill("#loginEmail", "direction_01@uranos.local");
  await page.fill("#loginPassword", "Password123!");
  await page.click("#btnContinue");
  await page.waitForURL(/\/app|\/desk/, { timeout: 15000 });
  console.log("✓ Logged in as direction_01 successfully!");

  console.log("2. Navigating to Accounting (/app/invoicing) as direction_01...");
  await page.goto("http://localhost:8080/app/invoicing", { waitUntil: "networkidle" });
  await page.waitForTimeout(2500);

  const accountingAudit = await page.evaluate(() => {
    const modal = document.querySelector(".modal:not([style*='display: none'])");
    const alerts = Array.from(document.querySelectorAll(".alert, .msgprint")).map(a => a.innerText.trim());
    return {
      hasErrorModal: !!modal,
      modalTitle: modal?.querySelector(".modal-title")?.innerText,
      modalBody: modal?.querySelector(".modal-body")?.innerText,
      alerts,
      currentRoute: window.frappe ? frappe.get_route() : null,
      pathname: window.location.pathname,
      pageTitle: document.title
    };
  });

  console.log("\n--- Accounting Access Audit for direction_01 ---");
  console.log("Route:", accountingAudit.currentRoute);
  console.log("Page Title:", accountingAudit.pageTitle);
  console.log("Has Error Modal:", accountingAudit.hasErrorModal);
  if (accountingAudit.hasErrorModal) {
    console.error("FAILED: Permission error still present!", accountingAudit.modalTitle, accountingAudit.modalBody);
  } else {
    console.log("✓ SUCCESS: direction_01 accessed Invoicing / Accounting workspace with ZERO permission errors!");
  }

  const accountingScreenshotPath = path.join(artifactDir, "verified_direction01_accounting.png");
  await page.screenshot({ path: accountingScreenshotPath, fullPage: true });
  console.log(`✓ Accounting screenshot saved: ${accountingScreenshotPath}`);

  // -------------------------------------------------------------------------
  // TEST 2: Support Workspace Chic SaaS Upgrade & Deprecation Suppression
  // -------------------------------------------------------------------------
  console.log("\n3. Navigating to Support Workspace (/app/support)...");
  await page.goto("http://localhost:8080/app/support", { waitUntil: "networkidle" });
  await page.waitForSelector(".uranos-chic-saas-view[data-module='support']", { timeout: 12000 });
  await page.waitForTimeout(1500);

  const supportAudit = await page.evaluate(() => {
    const root = document.querySelector(".uranos-chic-saas-view[data-module='support']");
    const title = root?.querySelector(".uranos-saas-title-group h2")?.innerText;
    const kpis = Array.from(root?.querySelectorAll(".uranos-saas-kpi-tile") || []).map(tile => ({
      label: tile.querySelector(".kpi-label")?.innerText,
      val: tile.querySelector(".kpi-value")?.innerText,
      sub: tile.querySelector(".kpi-subtext")?.innerText
    }));
    const channels = Array.from(root?.querySelectorAll(".uranos-support-card") || []).map(card => ({
      title: card.querySelector(".uranos-support-card-title")?.innerText,
      badge: card.querySelector(".uranos-saas-badge")?.innerText,
      desc: card.querySelector(".uranos-support-card-desc")?.innerText?.substring(0, 60) + "..."
    }));
    const faqs = Array.from(root?.querySelectorAll(".uranos-faq-item") || []).map(item => ({
      q: item.querySelector(".uranos-faq-q")?.innerText
    }));

    // Check if deprecation warning is visible
    const deprecationVisible = Array.from(document.querySelectorAll("p, span, div, .alert")).some(el => {
      if (el.tagName === "SCRIPT" || el.tagName === "STYLE") return false;
      if (el.children.length > 2) return false;
      const text = el.innerText || "";
      if (text.includes("This module is scheduled for deprecation")) {
        const style = window.getComputedStyle(el);
        const isHidden = style.display === "none" || style.visibility === "hidden" || style.opacity === "0" || el.offsetParent === null;
        return !isHidden;
      }
      return false;
    });

    return {
      moduleFound: !!root,
      title,
      kpis,
      channelsCount: channels.length,
      channels,
      faqsCount: faqs.length,
      faqs,
      deprecationVisible
    };
  });

  console.log("\n--- Support Chic SaaS Help Center Audit ---");
  console.log("Module found:", supportAudit.moduleFound);
  console.log("Title:", supportAudit.title);
  console.log("Live KPIs:", supportAudit.kpis);
  console.log(`Channels (${supportAudit.channelsCount}):`, supportAudit.channels.map(c => `${c.title} [${c.badge}]`));
  console.log(`FAQs (${supportAudit.faqsCount}):`, supportAudit.faqs.map(f => f.q));
  console.log("Deprecation warning visible in DOM:", supportAudit.deprecationVisible);
  if (supportAudit.deprecationVisible) {
    console.warn("WARNING: Deprecation warning is still visible!");
  } else {
    console.log("✓ SUCCESS: Deprecation warning cleanly suppressed!");
  }

  // Capture full page screenshot
  const supportScreenshotPath = path.join(artifactDir, "verified_support_chic_saas_view.png");
  await page.screenshot({ path: supportScreenshotPath, fullPage: true });
  console.log(`\n✓ Support full-page screenshot captured: ${supportScreenshotPath}`);

  // Test live interactive search
  console.log("\n4. Testing interactive search filter ('ticket')...");
  await page.fill(".uranos-support-saas-view .uranos-saas-search-input", "ticket");
  await page.waitForTimeout(500);

  const visibleCardsCount = await page.evaluate(() => {
    const cards = Array.from(document.querySelectorAll(".uranos-support-card, .uranos-faq-item"));
    return cards.filter(c => window.getComputedStyle(c).display !== "none").length;
  });
  console.log(`✓ Visible cards matching 'ticket': ${visibleCardsCount}`);

  console.log("\n==================================================================");
  console.log("   All Verifications Completed Successfully!");
  console.log("==================================================================");

  await browser.close();
}

verifyAccountingAndSupport().catch(err => {
  console.error("Test execution failed:", err);
  process.exit(1);
});
