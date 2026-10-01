import { chromium } from "playwright";
import path from "node:path";
import { mkdir, writeFile } from "node:fs/promises";

async function verifyAiCopilotAndDailyPdfReport() {
  console.log("==================================================================");
  console.log("   URANOS: Advanced RAG Accuracy & Daily PDF Report E2E Verification");
  console.log("==================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";
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
    // ── 1. Authenticate as Manager ──
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
    console.log("✓ Successfully authenticated and loaded Main Dashboard");

    // ── 2. Verify Daily Executive PDF Report Generation ──
    console.log("2. Auditing Daily Executive PDF Report Button...");
    const pdfBtn = page.locator("#uranosGenerateExecutivePdfBtn").first();
    await pdfBtn.waitFor({ state: "visible", timeout: 10000 });
    console.log("✓ Found #uranosGenerateExecutivePdfBtn on Dashboard!");

    // Test the API endpoint directly through authenticated context
    console.log("3. Testing /api/method/uranos_project_os.services.api.generate_daily_report endpoint...");
    const pdfResponse = await context.request.get("http://localhost:8080/api/method/uranos_project_os.services.api.generate_daily_report");
    console.log(`HTTP Status: ${pdfResponse.status()}`);
    const headers = pdfResponse.headers();
    console.log(`Content-Type: ${headers["content-type"]}`);
    console.log(`Content-Disposition: ${headers["content-disposition"]}`);
    const pdfBuffer = await pdfResponse.body();
    console.log(`Downloaded Buffer Length: ${pdfBuffer.length} bytes`);

    if (pdfResponse.status() !== 200) {
      throw new Error(`FAILURE: Daily PDF endpoint returned HTTP status ${pdfResponse.status()}`);
    }
    if (!headers["content-type"]?.includes("application/pdf")) {
      throw new Error(`FAILURE: Expected application/pdf, got ${headers["content-type"]}`);
    }
    if (!headers["content-disposition"]?.includes("URANOS_Daily_Executive_Report")) {
      throw new Error(`FAILURE: Content-Disposition missing expected filename: ${headers["content-disposition"]}`);
    }
    if (pdfBuffer.slice(0, 4).toString() !== "%PDF") {
      throw new Error("FAILURE: Returned file does not begin with '%PDF' magic header!");
    }
    console.log("✓ Daily Executive PDF Report generated successfully with valid %PDF-1.4 binary!");
    
    // Save PDF artifact for inspection
    const pdfPath = path.join(artifactDir, "URANOS_Daily_Executive_Report_Verified.pdf");
    await writeFile(pdfPath, pdfBuffer);
    console.log(`✓ Saved verified PDF artifact to: ${pdfPath}`);

    // ── 3. Test AI Synthesis Button & Modal on Dashboard ──
    console.log("4. Testing AI Synthesis Button (#gv-hero-ai-btn) on Dashboard...");
    const aiSynthesisBtn = page.locator("#gv-hero-ai-btn").first();
    await aiSynthesisBtn.waitFor({ state: "visible", timeout: 10000 });
    await aiSynthesisBtn.click();
    console.log("✓ Clicked #gv-hero-ai-btn");

    // Wait for the modal to be visible
    const synthesisModal = page.locator("#uranosAISynthesisModal");
    await synthesisModal.waitFor({ state: "visible", timeout: 5000 });
    console.log("✓ AI Synthesis Modal rendered!");

    // Wait for Groq AI response in the modal (up to 20s)
    console.log("Waiting for Groq AI to stream 3-bullet executive summary...");
    const contentArea = page.locator("#uranosAISynthesisContent");
    await page.waitForFunction(() => {
      const el = document.getElementById("uranosAISynthesisContent");
      return el && (el.innerText.includes("Fleet") || el.innerText.includes("MW") || el.innerText.includes("Synthesis Error"));
    }, { timeout: 30000 });

    const modalText = await contentArea.innerText();
    console.log("---------------- Groq AI Synthesis Output ----------------");
    console.log(modalText);
    console.log("----------------------------------------------------------");

    if (!modalText.includes("642.0 MW") && !modalText.includes("770.4 MWp")) {
      throw new Error("FAILURE: AI synthesis did not include grounded fleet capacity metrics!");
    }
    if (modalText.includes("PV-01")) {
      throw new Error("FAILURE: AI synthesis hallucinated 'PV-01' instead of 4-digit PV-#### format!");
    }

    const modalShotPath = path.join(artifactDir, "uranos_executive_ai_briefing_modal.png");
    await page.screenshot({ path: modalShotPath });
    console.log(`✓ Captured modal screenshot: ${modalShotPath}`);

    // Close modal
    await page.locator("#uranosAISynthesisModal .close, #uranosAISynthesisModal button:has-text('Dismiss')").first().click();
    await page.waitForTimeout(1000);

    // ── 4. Test URANOS Copilot Full Page & Groq RAG Accuracy for PV-0004 ──
    console.log("5. Navigating to URANOS Copilot Page (/app/uranos-ai-copilot)...");
    await page.goto("http://localhost:8080/app/uranos-ai-copilot/PV-0004", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);

    // Check project selector has PV-0004
    const projectDropdown = page.locator("#uac-project-select");
    await projectDropdown.waitFor({ state: "visible", timeout: 10000 });
    const selectOptions = await projectDropdown.locator("option").allInnerTexts();
    console.log(`Project Options Count: ${selectOptions.length}`);
    console.log("First 3 options:", selectOptions.slice(0, 3));

    const hasPV01 = selectOptions.some(opt => opt.startsWith("PV-01 (") || opt === "PV-01");
    if (hasPV01) {
      throw new Error("FAILURE: Dropdown still contains invalid 'PV-01' instead of 'PV-0001'!");
    }

    // Set value to PV-0004 if not already
    await projectDropdown.selectOption({ value: "PV-0004" });
    await page.waitForTimeout(1000);

    console.log("6. Submitting test query to URANOS Copilot for PV-0004...");
    const chatInput = page.locator("#uac-chat-input").first();
    await chatInput.waitFor({ state: "visible", timeout: 5000 });
    await chatInput.fill("Can you check the critical blocker on PV-0004 and tell me its status, reporter, and plant capacity?");
    
    const sendBtn = page.locator("#uac-chat-send").first();
    await sendBtn.click();
    console.log("✓ Sent query to Groq RAG Copilot");

    // Wait for response bubble
    console.log("Waiting for Groq AI RAG response in chat window...");
    await page.waitForFunction(() => {
      const bodies = Array.from(document.querySelectorAll(".gv-chat-markdown-body"));
      if (bodies.length < 2) return false;
      const lastMsg = bodies[bodies.length - 1];
      const text = lastMsg.innerText || "";
      return text.includes("B-00001") || text.includes("STEG") || text.includes("100");
    }, { timeout: 30000 });

    const chatResponseText = await page.evaluate(() => {
      const bodies = Array.from(document.querySelectorAll(".gv-chat-markdown-body"));
      return bodies.length ? bodies[bodies.length - 1].innerText : "";
    });

    console.log("---------------- Copilot Groq RAG Response ----------------");
    console.log(chatResponseText);
    console.log("-----------------------------------------------------------");

    // Verify Grounding Invariants
    const checks = [
      { name: "Blocker B-00001", pass: chatResponseText.includes("B-00001") },
      { name: "Status In Progress", pass: /In Progress/i.test(chatResponseText) },
      { name: "Reporter or Engineer", pass: /chantier_01|ingenieur_01|STEG/i.test(chatResponseText) },
      { name: "Plant Capacity (100 MW or 120 MWp)", pass: chatResponseText.includes("100") || chatResponseText.includes("120") },
      { name: "No PV-01 Hallucination", pass: !chatResponseText.includes("PV-01 ") && !chatResponseText.includes("PV-01\n") }
    ];

    console.log("Grounding Verification Results:");
    checks.forEach(c => {
      console.log(`  ${c.pass ? "✓ PASS" : "✗ FAIL"}: ${c.name}`);
      if (!c.pass) throw new Error(`FAILURE: Check failed for ${c.name}`);
    });

    const copilotShotPath = path.join(artifactDir, "uranos_ai_copilot_pv0004_response.png");
    await page.screenshot({ path: copilotShotPath });
    console.log(`✓ Captured Copilot screenshot: ${copilotShotPath}`);

    console.log("==================================================================");
    console.log("  ALL TESTS PASSED! RAG Accuracy & Daily PDF Report Verified!     ");
    console.log("==================================================================");
  } catch (err) {
    console.error("Test execution encountered an error:", err);
    const errShotPath = path.join(artifactDir, "error_state.png");
    await page.screenshot({ path: errShotPath }).catch(() => {});
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyAiCopilotAndDailyPdfReport();
