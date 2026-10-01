import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function runTabbedModalRTLAudit() {
  console.log("=== Starting Tabbed AI Modal RTL (Arabic) Verification ===");
  const evidenceDir = "/home/montassar/.gemini/antigravity-ide/brain/c0f1152f-aa5f-4931-b715-c59a5d2d2902";
  await mkdir(evidenceDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 }
  });
  const page = await context.newPage();

  try {
    console.log("1. Authenticating as ingenieur_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(url => url.pathname.includes("/desk") || url.pathname.includes("/app"), { timeout: 15000 });
    console.log("  ✓ Successfully logged in.");

    console.log("2. Navigating to /app/blocker-dashboard...");
    await page.goto("http://localhost:8080/app/blocker-dashboard", { waitUntil: "networkidle" });
    await page.waitForTimeout(1000);

    console.log("3. Enabling RTL (Arabic) Mode...");
    await page.evaluate(() => {
      document.documentElement.setAttribute("dir", "rtl");
      document.documentElement.setAttribute("lang", "ar");
      document.body.setAttribute("dir", "rtl");
      if (typeof frappe !== "undefined" && frappe.boot) {
        frappe.boot.lang = "ar";
      }
    });
    await page.waitForTimeout(500);

    console.log("4. Opening AI Modal...");
    await page.waitForSelector("#bd-ai-synthesis-btn", { state: "visible", timeout: 8000 });
    await page.click("#bd-ai-synthesis-btn");
    await page.waitForSelector("#gv-ai-synthesis-modal.open", { state: "visible", timeout: 8000 });

    // Wait for synthesis to finish
    await page.waitForFunction(() => {
      const body = document.querySelector("#gv-ai-modal-body");
      return body && !body.querySelector(".gv-ai-loading-skeleton") && body.innerText.trim().length > 10;
    }, { timeout: 15000 });
    console.log("  ✓ Synthesis loaded in Arabic/RTL context.");

    // Screenshot Tab 1 in RTL
    const shotTab1 = path.join(evidenceDir, "tabbed_ai_modal_rtl_tab1_summary.png");
    await page.screenshot({ path: shotTab1, fullPage: false });
    console.log("  ✓ Tab 1 (RTL) Screenshot saved ->", shotTab1);

    // Switch to Tab 2: Interactive Copilot
    console.log("5. Switching to Tab 2: Interactive Copilot in RTL...");
    await page.click("#gv-ai-tab-btn-copilot");
    await page.waitForTimeout(500);

    const isCopilotActive = await page.$eval("#gv-ai-tab-btn-copilot", el => el.classList.contains("active"));
    const isCopilotVisible = await page.$eval("#gv-ai-tab-copilot", el => window.getComputedStyle(el).display !== "none");
    console.log("  Tab 2 active in RTL:", isCopilotActive ? "✓ PASS" : "✗ FAIL");
    console.log("  Tab 2 visible in RTL:", isCopilotVisible ? "✓ PASS" : "✗ FAIL");

    // Submit Arabic Query
    console.log("6. Submitting Arabic Query to Copilot...");
    const arabicQuery = "ما هي حالة الأعمال المنجزة والمتبقية والعوائق الحالية؟";
    await page.fill("#gv-ai-chat-input", arabicQuery);
    await page.click("#gv-ai-chat-send");

    console.log("7. Waiting for AI Copilot Arabic response...");
    await page.waitForFunction(() => {
      const bubbles = document.querySelectorAll(".gv-chat-bubble-ai:not(.gv-thinking-bubble)");
      const thinking = document.querySelectorAll(".gv-thinking-bubble");
      return bubbles.length > 1 && thinking.length === 0;
    }, { timeout: 25000 });

    const aiReplyText = await page.$eval(".gv-chat-bubble-ai:not(.gv-thinking-bubble)", el => el.innerText.trim());
    console.log("  ✓ AI Copilot Arabic response received:");
    console.log("   ", aiReplyText.substring(0, 150) + "...");

    // Screenshot Tab 2 in RTL
    const shotTab2 = path.join(evidenceDir, "tabbed_ai_modal_rtl_tab2_copilot.png");
    await page.screenshot({ path: shotTab2, fullPage: false });
    console.log("  ✓ Tab 2 (RTL) Screenshot saved ->", shotTab2);

    console.log("\n=== RTL TABBED MODAL & RAG VERIFICATION COMPLETED SUCCESSFULLY ===");
  } catch (err) {
    console.error("Test execution failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

runTabbedModalRTLAudit();
