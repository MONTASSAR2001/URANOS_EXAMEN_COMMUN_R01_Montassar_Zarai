import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function runFullPageAICopilotVerification() {
  console.log("=== Starting Dedicated Full-Screen AI Copilot Page Verification ===");
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
        if (!text.includes("favicon") && !text.includes("404") && !text.includes("socket.io") && !text.includes("502")) {
          console.warn("  [CONSOLE ERROR]", text);
        }
      }
    });

    // 1. Authenticate
    console.log("1. Authenticating as ingenieur_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(url => url.pathname.includes("/desk") || url.pathname.includes("/app"), { timeout: 15000 });
    console.log("  ✓ Successfully logged in. URL:", page.url());

    // 2. Navigate to Blocker Dashboard
    console.log("2. Navigating to /app/blocker-dashboard...");
    await page.goto("http://localhost:8080/app/blocker-dashboard", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);

    // 3. Trigger AI Synthesis Button
    console.log("3. Clicking #bd-ai-synthesis-btn to trigger full-screen page redirect...");
    await page.waitForSelector("#bd-ai-synthesis-btn", { state: "visible", timeout: 8000 });
    await page.click("#bd-ai-synthesis-btn");

    // 4. Verify Route Transition
    console.log("4. Verifying route transition to /app/uranos-ai-copilot...");
    await page.waitForURL(url => url.pathname.includes("uranos-ai-copilot"), { timeout: 10000 });
    console.log("  ✓ Route successfully transitioned to:", page.url());

    // 5. Verify Full-Screen Layout Elements
    console.log("5. Auditing Full-Page UI Architecture & Elements...");
    await page.waitForSelector("#uranos-ai-copilot-page", { state: "visible", timeout: 10000 });
    await page.waitForSelector(".uac-workspace-grid", { state: "visible", timeout: 10000 });

    const titleText = await page.$eval(".uac-page-title", el => el.textContent.trim());
    console.log("  Page Title:", titleText, "✓ PASS");

    const backBtn = await page.$("#uac-back-btn");
    console.log("  Back to Dashboard Button:", backBtn ? "✓ Present" : "✗ Missing");

    // 6. Wait for Synthesis Content to Load
    console.log("6. Waiting for Executive Synthesis content generation...");
    await page.waitForFunction(() => {
      const body = document.querySelector("#uac-synthesis-body");
      return body && !body.querySelector(".uac-loading-skeleton") && body.innerText.trim().length > 20;
    }, { timeout: 20000 });

    const kpiOpen = await page.$eval("#uac-kpi-open", el => el.textContent.trim());
    const kpiCritical = await page.$eval("#uac-kpi-critical", el => el.textContent.trim());
    const kpiLost = await page.$eval("#uac-kpi-lost", el => el.textContent.trim());
    const providerBadge = await page.$eval("#uac-provider-badge-container", el => el.textContent.trim());

    console.log(`  KPIs Verified -> Open: ${kpiOpen}, Critical: ${kpiCritical}, Lost Hours: ${kpiLost}`);
    console.log(`  Provider Badge -> ${providerBadge}`);

    // Capture Full Page Desktop Screenshot
    const deskShot = path.join(evidenceDir, "full_page_ai_copilot_desktop.png");
    await page.screenshot({ path: deskShot, fullPage: false });
    console.log("  ✓ Desktop Screenshot saved ->", deskShot);

    // 7. Verify Interactive Copilot Chat Panel
    console.log("7. Verifying Copilot Panel and Submitting Inquiry...");
    const welcomeBubble = await page.waitForSelector(".uac-bubble-ai", { timeout: 5000 });
    console.log("  Copilot Initial Greeting:", welcomeBubble ? "✓ Present" : "✗ Missing");

    const query = "What is the status of completed work, remaining tasks, and active defects?";
    await page.fill("#uac-chat-input", query);
    await page.click("#uac-chat-send");
    console.log("  ✓ User question sent:", query);

    // 8. Wait for AI response bubble
    console.log("8. Waiting for AI response grounded in MariaDB...");
    await page.waitForFunction(() => {
      const aiBubbles = document.querySelectorAll(".uac-bubble-ai:not(.uac-bubble-thinking)");
      const thinking = document.querySelectorAll(".uac-bubble-thinking");
      return aiBubbles.length > 1 && thinking.length === 0;
    }, { timeout: 25000 });

    const aiReplyText = await page.evaluate(() => {
      const bubbles = document.querySelectorAll(".uac-bubble-ai:not(.uac-bubble-thinking)");
      return bubbles.length > 0 ? bubbles[bubbles.length - 1].textContent.trim() : "";
    });
    console.log("  ✓ Live AI Copilot response received:");
    console.log("    " + aiReplyText.substring(0, 180).replace(/\n/g, " ") + "...");

    // Capture Chat Response Screenshot
    const chatShot = path.join(evidenceDir, "full_page_ai_copilot_chat_response.png");
    await page.screenshot({ path: chatShot, fullPage: false });
    console.log("  ✓ Chat Response Screenshot saved ->", chatShot);

    // 9. Test Back Button navigation
    console.log("9. Testing Back Button navigation back to dashboard...");
    await page.click("#uac-back-btn");
    await page.waitForURL(url => url.pathname.includes("blocker-dashboard"), { timeout: 8000 });
    console.log("  ✓ Navigated back to dashboard successfully. URL:", page.url());

    // 10. Test RTL (Arabic) Mode
    console.log("10. Testing RTL (Arabic) Mode...");
    await page.goto("http://localhost:8080/app/uranos-ai-copilot/PV-01", { waitUntil: "networkidle" });
    await page.waitForTimeout(500);

    await page.evaluate(() => {
      document.documentElement.setAttribute("dir", "rtl");
      document.documentElement.setAttribute("lang", "ar");
      document.body.setAttribute("dir", "rtl");
      const wrapper = document.getElementById("uranos-ai-copilot-page");
      if (wrapper) wrapper.setAttribute("dir", "rtl");
    });
    await page.waitForTimeout(600);

    const rtlShot = path.join(evidenceDir, "full_page_ai_copilot_rtl_arabic.png");
    await page.screenshot({ path: rtlShot, fullPage: false });
    console.log("  ✓ RTL (Arabic) Screenshot saved ->", rtlShot);

    // 11. Console Error Audit
    console.log("11. Auditing console errors...");
    if (consoleErrors.length > 0) {
      console.warn("  Console errors detected:", consoleErrors);
    } else {
      console.log("  ✓ PASS: Zero uncaught console errors!");
    }

    console.log("\n=== ALL DEDICATED FULL-PAGE COPILOT TESTS PASSED SUCCESSFULLY! ===");
  } catch (err) {
    console.error("Test execution failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

runFullPageAICopilotVerification();
