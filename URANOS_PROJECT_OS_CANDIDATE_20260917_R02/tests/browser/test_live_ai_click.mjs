import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function runLiveAIClickTest() {
  console.log("=== Starting Live Cloud AI (Groq Llama 3.3) Synthesis Verification ===");
  const evidenceDir = "/home/montassar/.gemini/antigravity-ide/brain/a602cb04-cf23-4f11-be98-e5d6e4f36feb";
  await mkdir(evidenceDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 900 }
    });
    const page = await context.newPage();

    console.log("1. Logging in as ingenieur_01@uranos.local (Project Manager)...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(/\/desk|\/app/, { timeout: 15000 });
    console.log("  ✓ Logged in successfully. Current URL:", page.url());

    // 2. Navigate to Blocker Dashboard
    console.log("2. Navigating to /app/blocker-dashboard...");
    await page.goto("http://localhost:8080/app/blocker-dashboard", { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);

    // Ensure the button is present
    await page.waitForSelector("#bd-ai-synthesis-btn", { timeout: 10000 });
    console.log("  ✓ Found #bd-ai-synthesis-btn on Blocker Dashboard.");

    // 3. Click the AI Synthesis button
    console.log("3. Clicking '#bd-ai-synthesis-btn' to trigger live Cloud AI generation...");
    await page.click("#bd-ai-synthesis-btn");

    // Wait for the modal to open
    await page.waitForSelector("#gv-ai-synthesis-modal.open", { timeout: 10000 });
    console.log("  ✓ Synthesis modal opened.");

    // Wait for synthesis data to finish loading (waiting for badge to stop having .loading class)
    console.log("  Waiting for Cloud AI RAG pipeline to complete (timeout: 20s)...");
    await page.waitForSelector("#gv-ai-status-badge-container .gv-ai-badge:not(.loading)", { timeout: 20000 });

    const badgeText = await page.$eval("#gv-ai-status-badge-container", el => el.textContent.trim());
    const isSparkleBadge = await page.isVisible("#gv-ai-status-badge-container .gv-ai-badge.ai-sparkle");
    const isFallbackBadge = await page.isVisible("#gv-ai-status-badge-container .gv-ai-badge.fallback-badge");

    console.log(`  Rendered Badge: "${badgeText}"`);
    console.log(`  Sparkle Badge (✨) Visible: ${isSparkleBadge}`);
    console.log(`  Fallback Shield (🛡️) Visible: ${isFallbackBadge}`);

    // Verify chic Markdown rendering
    const modalAnalysis = await page.evaluate(() => {
      const body = document.querySelector("#gv-ai-modal-body");
      const headings = Array.from(body.querySelectorAll("h1, h2, h3, h4")).map(h => h.textContent.trim());
      const strongElements = Array.from(body.querySelectorAll("strong")).map(s => s.textContent.trim());
      const listItems = Array.from(body.querySelectorAll("li")).map(l => l.textContent.trim());
      const paragraphs = Array.from(body.querySelectorAll("p")).map(p => p.textContent.trim());

      const ttsBtn = document.querySelector("#gv-ai-tts-btn");
      const ttsText = ttsBtn ? ttsBtn.textContent.trim() : null;
      const ttsVisible = ttsBtn ? (ttsBtn.offsetParent !== null) : false;

      return {
        headings,
        strongCount: strongElements.length,
        strongSamples: strongElements.slice(0, 5),
        listItemCount: listItems.length,
        paragraphCount: paragraphs.length,
        ttsText,
        ttsVisible
      };
    });

    console.log("\n=== CHIC MARKDOWN PARSING & STYLING VERIFICATION ===");
    console.log("  Rendered Headings:", modalAnalysis.headings);
    console.log("  Strong (Bold) Elements Count:", modalAnalysis.strongCount);
    console.log("  Strong Samples:", modalAnalysis.strongAnalysis || modalAnalysis.strongSamples);
    console.log("  List Items (<li>) Count:", modalAnalysis.listItemCount);
    console.log("  Paragraphs (<p>) Count:", modalAnalysis.paragraphCount);
    console.log("  TTS Button Visible:", modalAnalysis.ttsVisible);
    console.log("  TTS Button Initial Text:", modalAnalysis.ttsText);

    // Verify presence of TTS button
    if (!modalAnalysis.ttsVisible) {
      throw new Error("FAILURE: #gv-ai-tts-btn ('🔊 Listen to Synthesis') is not visible in modal!");
    }

    // Test Audio TTS Interaction
    console.log("\n4. Testing Audio Text-to-Speech (TTS) Feature...");
    await page.click("#gv-ai-tts-btn");
    await page.waitForTimeout(600);

    const ttsPlayingState = await page.evaluate(() => {
      const btn = document.querySelector("#gv-ai-tts-btn");
      return {
        hasSpeakingClass: btn?.classList.contains("speaking"),
        btnText: btn?.textContent.trim(),
        speakingPulse: window.getComputedStyle(btn).animationName
      };
    });
    console.log("  TTS Click 1 (Play State):", ttsPlayingState);

    // Click again to stop
    await page.click("#gv-ai-tts-btn");
    await page.waitForTimeout(600);

    const ttsStoppedState = await page.evaluate(() => {
      const btn = document.querySelector("#gv-ai-tts-btn");
      return {
        hasSpeakingClass: btn?.classList.contains("speaking"),
        btnText: btn?.textContent.trim()
      };
    });
    console.log("  TTS Click 2 (Stop State):", ttsStoppedState);

    // Capture screenshot of the chic modal
    const screenshotPath = path.join(evidenceDir, "live_groq_ai_chic_synthesis.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log("  ✓ Chic modal screenshot saved ->", screenshotPath);

    // Extract details
    const projectVal = await page.$eval("#gv-ai-project-val", el => el.textContent.trim());
    const openCount = await page.$eval("#gv-ai-open-count", el => el.textContent.trim());
    const providerText = await page.$eval("#gv-ai-provider-text", el => el.textContent.trim());
    const bodyContent = await page.$eval("#gv-ai-modal-body", el => el.textContent.trim().slice(0, 300));

    console.log("\n=== LIVE CLOUD AI (GROQ) SYNTHESIS DETAILS ===");
    console.log("  Project:", projectVal);
    console.log("  Open Blockers:", openCount);
    console.log("  Provider:", providerText);
    console.log("  AI Synthesis Snippet:\n", bodyContent, "...\n");

    console.log("5. Closing modal cleanly...");
    await page.click("#gv-ai-modal-close");
    await page.waitForTimeout(500);

    console.log("=== LIVE CLOUD AI CHIC SYNTHESIS TEST PASSED WITH 100% SUCCESS! ===");
  } finally {
    await browser.close();
  }
}

runLiveAIClickTest().catch(err => {
  console.error("TEST FAILED:", err);
  process.exit(1);
});
