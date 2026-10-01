import { chromium } from "playwright";
import path from "path";

async function verifyInputsBeautification() {
  console.log("==================================================================");
  console.log("   URANOS Group Inputs & Filters SaaS Beautification Audit");
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
  // Audit 1: /app/project (List View Filter Inputs)
  // -------------------------------------------------------------------------
  console.log("2. Navigating to /app/project (List View Filters)...");
  await page.goto("http://localhost:8080/app/project", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  const filterAudit = await page.evaluate(() => {
    const idInput = document.querySelector("input[placeholder=\"ID\"]");
    const nameInput = document.querySelector("input[placeholder=\"Project Name\"]");
    const statusSelect = document.querySelector(".standard-filter-section select");

    const idStyle = idInput ? window.getComputedStyle(idInput) : null;
    const nameStyle = nameInput ? window.getComputedStyle(nameInput) : null;
    const statusStyle = statusSelect ? window.getComputedStyle(statusSelect) : null;

    return {
      idInputFound: !!idInput,
      idPadding: idStyle ? idStyle.padding : null,
      idFontSize: idStyle ? idStyle.fontSize : null,
      idHeight: idStyle ? idStyle.height : null,
      idBorder: idStyle ? idStyle.border : null,
      idBg: idStyle ? idStyle.backgroundColor : null,
      nameInputFound: !!nameInput,
      namePadding: nameStyle ? nameStyle.padding : null,
      nameFontSize: nameStyle ? nameStyle.fontSize : null,
      nameHeight: nameStyle ? nameStyle.height : null,
      nameBorder: nameStyle ? nameStyle.border : null,
      nameBg: nameStyle ? nameStyle.backgroundColor : null,
      statusHeight: statusStyle ? statusStyle.height : null
    };
  });

  console.log("✓ List View Filters Audit Result:", JSON.stringify(filterAudit, null, 2));

  // Focus Project Name to test focus state
  await page.focus("input[placeholder=\"Project Name\"]");
  await page.waitForTimeout(400);

  const filterFocusAudit = await page.evaluate(() => {
    const activeEl = document.activeElement;
    const activeStyle = window.getComputedStyle(activeEl);
    return {
      activeTag: activeEl.tagName,
      activePlaceholder: activeEl.placeholder,
      focusBorderColor: activeStyle.borderColor,
      focusBoxShadow: activeStyle.boxShadow,
      focusBg: activeStyle.backgroundColor
    };
  });
  console.log("✓ Filter Focus State Result:", JSON.stringify(filterFocusAudit, null, 2));

  const filterScreenshotPath = path.join(artifactDir, "refined_list_view_filters.png");
  await page.screenshot({ path: filterScreenshotPath, fullPage: true });
  console.log(`✓ High-resolution screenshot captured to: ${filterScreenshotPath}`);

  // -------------------------------------------------------------------------
  // Audit 2: /app/project/PV-20 (Form View Controls & Inputs)
  // -------------------------------------------------------------------------
  console.log("3. Navigating to /app/project/PV-20 (Form View)...");
  await page.goto("http://localhost:8080/app/project/PV-20", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  const formAudit = await page.evaluate(() => {
    const projNameInput = document.querySelector("input[data-fieldname=\"project_name\"]");
    const statusSelect = document.querySelector("select[data-fieldname=\"status\"]");
    const style = projNameInput ? window.getComputedStyle(projNameInput) : null;
    const selectStyle = statusSelect ? window.getComputedStyle(statusSelect) : null;

    return {
      projNameFound: !!projNameInput,
      padding: style ? style.padding : null,
      fontSize: style ? style.fontSize : null,
      height: style ? style.height : null,
      border: style ? style.border : null,
      borderRadius: style ? style.borderRadius : null,
      bg: style ? style.backgroundColor : null,
      selectHeight: selectStyle ? selectStyle.height : null,
      selectPadding: selectStyle ? selectStyle.padding : null
    };
  });

  console.log("✓ Form View Controls Audit Result:", JSON.stringify(formAudit, null, 2));

  // Focus on form input to test chic focus ring
  await page.focus("input[data-fieldname=\"project_name\"]");
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

  const formScreenshotPath = path.join(artifactDir, "refined_form_view_inputs.png");
  await page.screenshot({ path: formScreenshotPath, fullPage: true });
  console.log(`✓ High-resolution screenshot captured to: ${formScreenshotPath}`);

  // Assertions
  if (!formAudit.fontSize || !formAudit.fontSize.includes("14.5px")) {
    throw new Error(`Expected form input font size 14.5px, got ${formAudit.fontSize}`);
  }
  if (!formAudit.height || !formAudit.height.includes("42px")) {
    throw new Error(`Expected form input height 42px, got ${formAudit.height}`);
  }
  if (!filterAudit.idHeight || !filterAudit.idHeight.includes("42px")) {
    throw new Error(`Expected filter input height 42px, got ${filterAudit.idHeight}`);
  }

  await browser.close();
  console.log("==================================================================");
  console.log("   ALL INPUTS & FILTERS BEAUTIFICATION AUDITS PASSED 100%!");
  console.log("==================================================================");
}

verifyInputsBeautification().catch(err => {
  console.error("FATAL ERROR in Playwright Verification:", err);
  process.exit(1);
});
