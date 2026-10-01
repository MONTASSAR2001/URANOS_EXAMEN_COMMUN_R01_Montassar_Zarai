import { chromium } from "playwright";
import path from "path";

async function verifyDailySiteReportAesthetics() {
  console.log("==================================================================");
  console.log("   URANOS Group Daily Site Report & Form View Aesthetic Audit");
  console.log("==================================================================");

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  const page = await context.newPage();

  page.on("console", msg => {
    if (msg.type() === "error") {
      console.log(`[BROWSER ERROR] ${msg.text()}`);
    }
  });

  console.log("1. Authenticating as Administrator...");
  await page.goto("http://localhost:8080/login", { waitUntil: "networkidle" });
  await page.fill("#loginEmail", "Administrator");
  await page.fill("#loginPassword", "Password123!");
  await page.click("#btnContinue");
  await page.waitForURL(/\/app|\/desk/, { timeout: 15000 });
  console.log("✓ Logged in successfully!");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";

  // -------------------------------------------------------------------------
  // Audit 1: /app/uranos-daily-site-report (List View)
  // -------------------------------------------------------------------------
  console.log("2. Navigating to /app/uranos-daily-site-report (List View)...");
  await page.goto("http://localhost:8080/app/uranos-daily-site-report", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  const listAudit = await page.evaluate(() => {
    const tableCard = document.querySelector(".frappe-list .result");
    const headRow = document.querySelector(".frappe-list .list-row-head");
    const firstRow = document.querySelector(".frappe-list .list-row");

    const cardStyle = tableCard ? window.getComputedStyle(tableCard) : null;
    const headStyle = headRow ? window.getComputedStyle(headRow) : null;
    const rowStyle = firstRow ? window.getComputedStyle(firstRow) : null;

    return {
      cardBg: cardStyle ? cardStyle.backgroundColor : null,
      cardBorderRadius: cardStyle ? cardStyle.borderRadius : null,
      cardBoxShadow: cardStyle ? cardStyle.boxShadow : null,
      headPadding: headStyle ? headStyle.padding : null,
      headBg: headStyle ? headStyle.backgroundColor : null,
      rowPadding: rowStyle ? rowStyle.padding : null,
      rowMargin: rowStyle ? rowStyle.margin : null,
      rowMinHeight: rowStyle ? rowStyle.minHeight : null,
      rowCursor: rowStyle ? rowStyle.cursor : null,
      totalRows: document.querySelectorAll(".frappe-list .list-row").length
    };
  });

  console.log("✓ Daily Site Report List View Audit Result:", JSON.stringify(listAudit, null, 2));

  // Assertions for List View
  if (!listAudit.cardBorderRadius || !listAudit.cardBorderRadius.includes("16px")) {
    throw new Error(`Expected card border radius 16px, got ${listAudit.cardBorderRadius}`);
  }
  if (!listAudit.rowPadding || !listAudit.rowPadding.includes("16px 24px")) {
    throw new Error(`Expected row padding 16px 24px, got ${listAudit.rowPadding}`);
  }

  const listScreenshotPath = path.join(artifactDir, "verified_daily_site_report_list.png");
  await page.screenshot({ path: listScreenshotPath, fullPage: true });
  console.log(`✓ List screenshot captured to: ${listScreenshotPath}`);

  // -------------------------------------------------------------------------
  // Audit 2: /app/uranos-daily-site-report/ev4okkj1kf (Form View)
  // -------------------------------------------------------------------------
  console.log("3. Navigating to /app/uranos-daily-site-report/ev4okkj1kf (Form View)...");
  await page.goto("http://localhost:8080/app/uranos-daily-site-report/ev4okkj1kf", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  const formAudit = await page.evaluate(() => {
    const input = document.querySelector(".form-page .frappe-control input:not([type=\"checkbox\"]), .form-page .frappe-control select");
    const label = document.querySelector(".form-page .control-label");
    const inputStyle = input ? window.getComputedStyle(input) : null;
    const labelStyle = label ? window.getComputedStyle(label) : null;

    return {
      inputFound: !!input,
      padding: inputStyle ? inputStyle.padding : null,
      fontSize: inputStyle ? inputStyle.fontSize : null,
      height: inputStyle ? inputStyle.height : null,
      borderRadius: inputStyle ? inputStyle.borderRadius : null,
      border: inputStyle ? inputStyle.border : null,
      bg: inputStyle ? inputStyle.backgroundColor : null,
      labelFound: !!label,
      labelFontSize: labelStyle ? labelStyle.fontSize : null,
      labelFontWeight: labelStyle ? labelStyle.fontWeight : null,
      labelColor: labelStyle ? labelStyle.color : null,
      labelTextTransform: labelStyle ? labelStyle.textTransform : null,
      labelLetterSpacing: labelStyle ? labelStyle.letterSpacing : null
    };
  });

  console.log("✓ Form View Controls Audit Result:", JSON.stringify(formAudit, null, 2));

  // Focus on an input to test the 4px focus ring
  const focusSelector = ".form-page .frappe-control[data-fieldname=\"project\"] input, .form-page .frappe-control input";
  await page.focus(focusSelector);
  await page.waitForTimeout(400);

  const formFocusAudit = await page.evaluate(() => {
    const activeEl = document.activeElement;
    const activeStyle = window.getComputedStyle(activeEl);
    return {
      activeTag: activeEl.tagName,
      focusBorderColor: activeStyle.borderColor,
      focusBoxShadow: activeStyle.boxShadow,
      focusBg: activeStyle.backgroundColor
    };
  });
  console.log("✓ Form Focus State Result:", JSON.stringify(formFocusAudit, null, 2));

  // Assertions for Form View
  if (!formAudit.fontSize || !formAudit.fontSize.includes("15px")) {
    throw new Error(`Expected form input font size 15px, got ${formAudit.fontSize}`);
  }
  if (!formAudit.height || !formAudit.height.includes("48px")) {
    throw new Error(`Expected form input height 48px, got ${formAudit.height}`);
  }
  if (!formFocusAudit.focusBoxShadow || !formFocusAudit.focusBoxShadow.includes("4px")) {
    throw new Error(`Expected 4px focus ring, got ${formFocusAudit.focusBoxShadow}`);
  }

  const formScreenshotPath = path.join(artifactDir, "verified_daily_site_report_form.png");
  await page.screenshot({ path: formScreenshotPath, fullPage: true });
  console.log(`✓ Form screenshot captured to: ${formScreenshotPath}`);

  await browser.close();
  console.log("==================================================================");
  console.log("   ALL DAILY SITE REPORT & FORM AESTHETIC AUDITS PASSED 100%!");
  console.log("==================================================================");
}

verifyDailySiteReportAesthetics().catch(err => {
  console.error("FATAL ERROR in Playwright Verification:", err);
  process.exit(1);
});
