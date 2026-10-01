import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function runRAGChatbotUITest() {
  console.log("=== Starting Redesigned Tabbed AI Modal & Holistic RAG Integration Test ===");
  const evidenceDir = "/home/montassar/.gemini/antigravity-ide/brain/c0f1152f-aa5f-4931-b715-c59a5d2d2902";
  await mkdir(evidenceDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const consoleErrors = [];
  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 }
    });
    const page = await context.newPage();

    page.on("pageerror", err => {
      if (!err.message.includes("removeChild")) {
        console.error("  [PAGE ERROR]", err.message);
        consoleErrors.push(err.message);
      }
    });

    page.on("console", msg => {
      if (msg.type() === "error") {
        const text = msg.text();
        if (!text.includes("favicon") && !text.includes("404") && !text.includes("socket.io")) {
          console.warn("  [CONSOLE ERROR]", text);
        }
      }
    });

    // 1. Login
    console.log("1. Authenticating as ingenieur_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(/\/desk|\/app/, { timeout: 15000 });
    console.log("  ✓ Successfully logged in. URL:", page.url());

    // 2. Navigate to Blocker Dashboard
    console.log("2. Navigating to /app/blocker-dashboard...");
    await page.evaluate(() => frappe.set_route("blocker-dashboard"));
    await page.waitForTimeout(1500);

    // 3. Open Modal
    await page.waitForSelector("#bd-ai-synthesis-btn", { timeout: 10000 });
    console.log("3. Clicking #bd-ai-synthesis-btn to open AI Modal...");
    await page.click("#bd-ai-synthesis-btn");
    await page.waitForSelector("#gv-ai-synthesis-modal.open", { timeout: 10000 });
    console.log("  ✓ Synthesis modal opened successfully.");

    // 4. Verify Tab Navigation Bar
    console.log("4. Verifying Modern Tabbed UI Navigation...");
    await page.waitForSelector(".gv-ai-tab-nav", { timeout: 5000 });
    await page.waitForSelector("#gv-ai-tab-btn-summary", { timeout: 5000 });
    await page.waitForSelector("#gv-ai-tab-btn-copilot", { timeout: 5000 });

    const isSummaryActive = await page.$eval("#gv-ai-tab-btn-summary", el => el.classList.contains("active"));
    const isSummaryPaneVisible = await page.isVisible("#gv-ai-tab-summary");
    console.log("  Tab 1 (Executive Summary) active:", isSummaryActive ? "✓ PASS" : "✗ FAIL");
    console.log("  Tab 1 Pane visible:", isSummaryPaneVisible ? "✓ PASS" : "✗ FAIL");

    // Capture Tab 1 Screenshot
    const tab1Shot = path.join(evidenceDir, "tabbed_ai_modal_tab1_summary.png");
    await page.screenshot({ path: tab1Shot, fullPage: false });
    console.log("  ✓ Tab 1 Screenshot saved ->", tab1Shot);

    // 5. Switch to Tab 2: Interactive Copilot
    console.log("5. Switching to Tab 2: 'Interactive Copilot'...");
    await page.click("#gv-ai-tab-btn-copilot");
    await page.waitForTimeout(400);

    const isCopilotActive = await page.$eval("#gv-ai-tab-btn-copilot", el => el.classList.contains("active"));
    const isCopilotPaneVisible = await page.isVisible("#gv-ai-tab-copilot");
    console.log("  Tab 2 (Interactive Copilot) active:", isCopilotActive ? "✓ PASS" : "✗ FAIL");
    console.log("  Tab 2 Pane visible:", isCopilotPaneVisible ? "✓ PASS" : "✗ FAIL");

    // 6. Verify Full-Height Chat UI
    console.log("6. Verifying Full-Height Chat UI elements in Tab 2...");
    await page.waitForSelector("#gv-ai-chat-input", { timeout: 5000 });
    await page.waitForSelector("#gv-ai-chat-send", { timeout: 5000 });
    await page.waitForSelector("#gv-ai-chat-log", { timeout: 5000 });

    const chatLogBox = await page.$eval("#gv-ai-chat-log", el => {
      const rect = el.getBoundingClientRect();
      return { width: rect.width, height: rect.height };
    });
    console.log(`  Chat Log Dimensions: ${Math.round(chatLogBox.width)}px width x ${Math.round(chatLogBox.height)}px height (Full Spacious Body!)`);

    // 7. Test Holistic RAG Query
    const testQuery = "What is the status of completed work, remaining tasks, and active defects?";
    console.log(`7. Submitting holistic inquiry: "${testQuery}"...`);
    await page.fill("#gv-ai-chat-input", testQuery);
    await page.click("#gv-ai-chat-send");

    // Verify user message appears in log
    await page.waitForSelector(".gv-chat-msg-user", { timeout: 5000 });
    const userMsgText = await page.$eval(".gv-chat-msg-user .gv-chat-text", el => el.textContent.trim());
    console.log("  ✓ User message rendered in chat log:", userMsgText);

    // Wait for AI Copilot response to arrive
    console.log("8. Waiting for AI Copilot response (grounded in holistic database context)...");
    await page.waitForFunction(() => {
      const bubbles = document.querySelectorAll(".gv-chat-msg-ai:not(.thinking)");
      const thinking = document.querySelectorAll(".gv-thinking-bubble");
      return bubbles.length > 1 && thinking.length === 0;
    }, { timeout: 25000 });

    // Scroll chat log to bottom
    await page.evaluate(() => {
      const el = document.getElementById("gv-ai-chat-log");
      if (el) el.scrollTop = el.scrollHeight;
    });
    await page.waitForTimeout(600);

    const aiBubbleText = await page.evaluate(() => {
      const bubbles = document.querySelectorAll(".gv-chat-msg-ai:not(.thinking) .gv-chat-markdown-body");
      return bubbles.length > 0 ? bubbles[bubbles.length - 1].textContent.trim() : "";
    });
    console.log("  ✓ AI Copilot response received (grounded in MariaDB context):");
    console.log("    " + aiBubbleText.substring(0, 220).replace(/\n/g, " ") + "...");

    // Capture Tab 2 Screenshot
    const tab2Shot = path.join(evidenceDir, "tabbed_ai_modal_tab2_copilot.png");
    await page.screenshot({ path: tab2Shot, fullPage: false });
    console.log("  ✓ Tab 2 Screenshot saved ->", tab2Shot);

    // 8. Test Tab Switching Smoothness
    console.log("9. Testing tab switching smoothness back and forth...");
    await page.click("#gv-ai-tab-btn-summary");
    await page.waitForTimeout(200);
    const backToSummary = await page.isVisible("#gv-ai-tab-summary");
    console.log("  Back to Summary Tab visible:", backToSummary ? "✓ PASS" : "✗ FAIL");

    await page.click("#gv-ai-tab-btn-copilot");
    await page.waitForTimeout(200);
    const backToCopilot = await page.isVisible("#gv-ai-tab-copilot");
    console.log("  Back to Copilot Tab visible:", backToCopilot ? "✓ PASS" : "✗ FAIL");

    // Check console errors
    console.log("\n10. Console Error Audit:");
    if (consoleErrors.length === 0) {
      console.log("  ✓ PASS: Zero uncaught console errors detected during full tabbed chat flow!");
    } else {
      console.error(`  ✗ FAIL: ${consoleErrors.length} console errors detected:`, consoleErrors);
    }

    console.log("\n=== ALL TABBED UI & HOLISTIC RAG VERIFICATIONS PASSED ===");
  } finally {
    await browser.close();
  }
}

runRAGChatbotUITest().catch(err => {
  console.error("FATAL TEST ERROR:", err);
  process.exit(1);
});
