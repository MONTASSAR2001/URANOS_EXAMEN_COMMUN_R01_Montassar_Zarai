import { chromium } from "playwright";
import path from "path";

async function verifyChildTableModal() {
  console.log("==================================================================");
  console.log("   URANOS Group Child Table Editing Row Modal Verification");
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

  console.log("1. Authenticating as Administrator...");
  await page.goto("http://localhost:8080/login", { waitUntil: "networkidle" });
  await page.fill("#loginEmail", "Administrator");
  await page.fill("#loginPassword", "Password123!");
  await page.click("#btnContinue");
  await page.waitForURL(/\/app|\/desk/, { timeout: 15000 });
  console.log("✓ Logged in successfully!");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";

  console.log("2. Navigating to Daily Site Report Form (/app/uranos-daily-site-report/ev4okkj1kf)...");
  await page.goto("http://localhost:8080/app/uranos-daily-site-report/ev4okkj1kf", { waitUntil: "networkidle" });
  await page.waitForTimeout(3000);

  console.log("3. Scrolling to Evidence Child Table and Clicking 'Add Row'...");
  await page.evaluate(() => {
    const el = document.querySelector('[data-fieldname="evidence"]');
    if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
  });
  await page.waitForTimeout(1000);

  const addRowBtn = page.locator('[data-fieldname="evidence"] .grid-add-row, [data-fieldname="evidence"] button:has-text("Add Row")').first();
  if (await addRowBtn.isVisible()) {
    await addRowBtn.click();
  } else {
    await page.evaluate(() => {
      cur_frm.fields_dict.evidence.grid.add_new_row(null, null, true);
    });
  }
  await page.waitForTimeout(1500);

  console.log("4. Auditing Modal Container & Input Styles...");
  const modalAudit = await page.evaluate(() => {
    const modal = document.querySelector('.grid-row-open .form-in-grid, .form-in-grid, .grid-row-form');
    const heading = document.querySelector('.grid-form-heading');
    // caption is unfocused because Frappe automatically focuses the first input (file)
    const captionInput = document.querySelector('.form-in-grid .frappe-control[data-fieldname="caption"] input');
    const label = document.querySelector('.form-in-grid .frappe-control[data-fieldname="caption"] .control-label');

    const modalStyle = modal ? window.getComputedStyle(modal) : null;
    const headingStyle = heading ? window.getComputedStyle(heading) : null;
    const inputStyle = captionInput ? window.getComputedStyle(captionInput) : null;
    const labelStyle = label ? window.getComputedStyle(label) : null;

    return {
      modalFound: !!modal,
      modalBg: modalStyle ? modalStyle.backgroundColor : null,
      modalBorderRadius: modalStyle ? modalStyle.borderRadius : null,
      modalBoxShadow: modalStyle ? modalStyle.boxShadow : null,
      headingBg: headingStyle ? headingStyle.backgroundColor : null,
      headingBorderBottom: headingStyle ? headingStyle.borderBottom : null,
      inputFound: !!captionInput,
      inputBg: inputStyle ? inputStyle.backgroundColor : null,
      inputBorder: inputStyle ? inputStyle.border : null,
      inputBorderRadius: inputStyle ? inputStyle.borderRadius : null,
      inputPadding: inputStyle ? inputStyle.padding : null,
      inputFontSize: inputStyle ? inputStyle.fontSize : null,
      inputColor: inputStyle ? inputStyle.color : null,
      labelColor: labelStyle ? labelStyle.color : null,
      labelFontWeight: labelStyle ? labelStyle.fontWeight : null
    };
  });

  console.log("✓ Modal Audit Result:", JSON.stringify(modalAudit, null, 2));

  // Assertions for Modal Container
  if (!modalAudit.modalFound) {
    throw new Error("Child table editing modal/form not found in DOM!");
  }
  if (modalAudit.modalBg !== "rgb(255, 255, 255)") {
    throw new Error(`Expected modal background pure white rgb(255, 255, 255), got ${modalAudit.modalBg}`);
  }
  if (!modalAudit.inputBg || (!modalAudit.inputBg.includes("241, 245, 249") && !modalAudit.inputBg.includes("248, 250, 252"))) {
    throw new Error(`Expected distinct input background (#f1f5f9 / #f8fafc), got ${modalAudit.inputBg}`);
  }
  if (!modalAudit.inputBorderRadius || !modalAudit.inputBorderRadius.includes("8px")) {
    throw new Error(`Expected 8px border radius, got ${modalAudit.inputBorderRadius}`);
  }

  console.log("5. Testing Chic Focus State on Modal Input (Caption field)...");
  await page.evaluate(() => {
    const aw = document.querySelector(".awesomplete > ul");
    if (aw) aw.style.display = "none";
    const el = document.querySelector('.form-in-grid [data-fieldname="caption"] input');
    if (el) {
      el.value = "Daily inspection photos - Inverter Station 04";
      el.focus();
    }
  });
  await page.waitForTimeout(400);

  const focusAudit = await page.evaluate(() => {
    const activeEl = document.activeElement;
    const activeStyle = window.getComputedStyle(activeEl);
    return {
      activeTag: activeEl.tagName,
      activeFieldname: activeEl.closest('.frappe-control')?.getAttribute('data-fieldname'),
      focusBg: activeStyle.backgroundColor,
      focusBorderColor: activeStyle.borderColor,
      focusBoxShadow: activeStyle.boxShadow
    };
  });
  console.log("✓ Focus State Result:", JSON.stringify(focusAudit, null, 2));

  if (focusAudit.focusBg !== "rgb(255, 255, 255)") {
    throw new Error(`Expected focus background white, got ${focusAudit.focusBg}`);
  }
  if (!focusAudit.focusBoxShadow || !focusAudit.focusBoxShadow.includes("4px")) {
    throw new Error(`Expected 4px focus ring, got ${focusAudit.focusBoxShadow}`);
  }

  // 6. Capture Screenshots
  console.log("6. Capturing visual proof artifacts...");
  const screenshotPath = path.join(artifactDir, "verified_child_table_editing_row_modal.png");
  await page.screenshot({ path: screenshotPath, fullPage: true });
  console.log(`✓ Full-page screenshot saved to: ${screenshotPath}`);

  const modalHandle = await page.$('.grid-row-open .form-in-grid, .form-in-grid');
  if (modalHandle) {
    const modalScreenshotPath = path.join(artifactDir, "verified_child_table_modal_snip.png");
    await modalHandle.screenshot({ path: modalScreenshotPath });
    console.log(`✓ Modal snipped screenshot saved to: ${modalScreenshotPath}`);
  }

  await browser.close();
  console.log("==================================================================");
  console.log("   ALL CHILD TABLE EDITING ROW MODAL AUDITS PASSED 100%!");
  console.log("==================================================================");
}

verifyChildTableModal().catch(err => {
  console.error("FATAL ERROR in Modal Verification:", err);
  process.exit(1);
});
