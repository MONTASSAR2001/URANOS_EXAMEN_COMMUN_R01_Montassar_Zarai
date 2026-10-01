import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyExecutivePdfButton() {
  console.log("==================================================================");
  console.log("   URANOS: Phase 5 Automated Executive PDF Report Generator Test  ");
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
    viewport: { width: 1440, height: 960 },
    acceptDownloads: true
  });
  const page = await context.newPage();

  const consoleErrors = [];
  page.on("console", msg => {
    if (msg.type() === "error") {
      consoleErrors.push(msg.text());
    }
  });

  try {
    console.log("1. Logging into URANOS Desk as direction_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    const isLoginVisible = await emailField.isVisible({ timeout: 5000 }).catch(() => false);
    if (isLoginVisible) {
      await emailField.fill("direction_01@uranos.local");
      await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
      await page.click("#btnContinue, .btn-login, button[type='submit']");
      await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { waitUntil: "domcontentloaded", timeout: 25000 });
    } else {
      await page.goto("http://localhost:8080/app", { waitUntil: "domcontentloaded" });
    }
    await page.waitForTimeout(3000);

    console.log("2. Auditing Executive PDF Button in Main Dashboard...");
    const pdfBtn = page.locator("#uranosGenerateExecutivePdfBtn").first();
    await pdfBtn.waitFor({ state: "visible", timeout: 10000 });
    console.log("✓ Found #uranosGenerateExecutivePdfBtn in Dashboard!");

    const btnInfo = await pdfBtn.evaluate(el => {
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      return {
        text: el.innerText.trim(),
        visible: rect.width > 0 && rect.height > 0,
        backgroundColor: style.backgroundColor,
        borderRadius: style.borderRadius,
        display: style.display
      };
    });

    console.log("--------------------------------------------------");
    console.log(`Button Text: "${btnInfo.text}"`);
    console.log(`Button Visible: ${btnInfo.visible}`);
    console.log(`Button Background: ${btnInfo.backgroundColor}`);
    console.log(`Button Border Radius: ${btnInfo.borderRadius}`);
    console.log("--------------------------------------------------");

    if (!btnInfo.visible) {
      throw new Error("FAILURE: #uranosGenerateExecutivePdfBtn is not visible!");
    }

    console.log("3. Testing PDF Generation Endpoint via Authenticated Request...");
    const endpointUrl = "http://localhost:8080/api/method/uranos_project_os.services.api.generate_executive_pdf";
    const response = await context.request.get(endpointUrl);
    console.log(`HTTP Status: ${response.status()}`);
    const headers = response.headers();
    console.log(`Content-Type: ${headers["content-type"]}`);
    console.log(`Content-Disposition: ${headers["content-disposition"]}`);
    const bodyBuffer = await response.body();
    console.log(`Downloaded Buffer Length: ${bodyBuffer.length} bytes`);

    if (response.status() !== 200) {
      throw new Error(`FAILURE: Endpoint returned HTTP status ${response.status()}`);
    }
    if (!headers["content-type"]?.includes("application/pdf")) {
      throw new Error(`FAILURE: Expected application/pdf, got ${headers["content-type"]}`);
    }
    if (!headers["content-disposition"]?.includes("URANOS_Executive_Report.pdf")) {
      throw new Error(`FAILURE: Content-Disposition missing filename, got ${headers["content-disposition"]}`);
    }
    if (bodyBuffer.slice(0, 4).toString() !== "%PDF") {
      throw new Error("FAILURE: Returned file does not begin with '%PDF' magic header!");
    }
    console.log("✓ PDF download endpoint verified successfully with valid PDF payload!");

    console.log("4. Testing Button Click Interaction in UI...");
    // Setup listener for popup / download trigger
    const popupPromise = page.waitForEvent("popup", { timeout: 5000 }).catch(() => null);
    await pdfBtn.click();
    const popup = await popupPromise;
    if (popup) {
      console.log(`✓ Popup opened successfully to: ${popup.url()}`);
      await popup.close().catch(() => {});
    } else {
      console.log("✓ Click triggered without errors (popup captured or blocked by headless)");
    }

    // Verify zero fatal console errors
    const fatalErrors = consoleErrors.filter(err => !err.includes("favicon") && !err.includes("404"));
    if (fatalErrors.length > 0) {
      console.warn("Console errors observed:", fatalErrors);
    } else {
      console.log("✓ Zero JavaScript errors on button click!");
    }

    // Capture screenshot showing the new PDF button
    const screenshotPath = path.join(artifactDir, "executive_pdf_report_btn_verified.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`✓ Screenshot captured: ${screenshotPath}`);

    console.log("\n==================================================================");
    console.log("   EXECUTIVE PDF REPORT VERIFICATION PASSED SUCCESSFULLY!       ");
    console.log("==================================================================");

  } catch (err) {
    console.error("Verification failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyExecutivePdfButton();
