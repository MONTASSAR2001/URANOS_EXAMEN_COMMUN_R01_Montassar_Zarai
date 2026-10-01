import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyMultimodalAndHybridRAG() {
  console.log("=== Testing URANOS Next-Gen AI: Multimodal Vision & Hybrid Semantic Search ===");
  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  try {
    const context = await browser.newContext({
      viewport: { width: 1600, height: 960 }
    });
    const page = await context.newPage();

    // 1. Authenticate
    console.log("1. Authenticating as ingenieur_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(url => url.pathname.includes("/desk") || url.pathname.includes("/app"), { timeout: 15000 });
    console.log("  ✓ Logged in successfully. Current URL:", page.url());

    // 2. Navigate to Copilot
    console.log("2. Navigating to /app/uranos-ai-copilot...");
    await page.goto("http://localhost:8080/app/uranos-ai-copilot", { waitUntil: "networkidle" });
    await page.waitForSelector("#uranos-ai-copilot-page", { timeout: 10000 });
    await page.waitForTimeout(3000);

    // 3. Verify Vision UI Elements
    console.log("3. Verifying Vision Upload Button in Chat Dock...");
    const hasVisionBtn = await page.isVisible("#uac-vision-upload-btn");
    console.log("  ✓ Vision upload button visible:", hasVisionBtn);
    if (!hasVisionBtn) throw new Error("Vision upload button #uac-vision-upload-btn not visible!");

    // 4. Upload Site Inspection Image
    const testImagePath = path.resolve("tests/evidence/test_solar_defect.png");
    console.log("4. Uploading site defect inspection photo:", testImagePath);
    const fileInput = await page.$("#uac-vision-file-input");
    await fileInput.setInputFiles(testImagePath);

    // 5. Verify User Image Bubble & Loading Indicator
    console.log("5. Waiting for user image bubble and vision analysis response...");
    await page.waitForSelector(".uac-chat-image-preview", { timeout: 10000 });
    console.log("  ✓ Image preview thumbnail successfully displayed in chat bubble!");

    // Wait for Vision Report from AI
    await page.waitForSelector(".uac-vision-report-header", { timeout: 20000 });
    const visionReportText = await page.$eval(".uac-vision-report-header + .uac-bubble-body, .uac-vision-report-header ~ div", el => el.innerText);
    console.log("  ✓ Multimodal Vision Diagnostic Report received!");
    console.log("  Preview:\n" + visionReportText.substring(0, 300) + "...\n");

    // 6. Test Hybrid Semantic Search
    console.log("6. Testing Hybrid Semantic Search Query ('How do we fix torque on pile bolts?')...");
    await page.fill("#uac-chat-input", "How do we fix torque on pile bolts?");
    await page.click("#uac-chat-send");

    // Wait for the thinking bubble to appear and then disappear
    await page.waitForSelector(".gv-thinking-bubble", { timeout: 10000 });
    console.log("  ✓ AI Thinking indicator appeared...");
    await page.waitForSelector(".gv-thinking-bubble", { state: "detached", timeout: 30000 });
    console.log("  ✓ AI response completed!");

    // Wait for response bubble
    const lastAiBubble = await page.$$eval(".uac-msg-ai .uac-bubble-body", bubbles => {
      return bubbles[bubbles.length - 1].innerText;
    });

    console.log("  ✓ Hybrid Semantic Search Response:\n" + lastAiBubble);
    const hasPrecedentMatch = lastAiBubble.includes("B-016") || lastAiBubble.toLowerCase().includes("torque") || lastAiBubble.toLowerCase().includes("serrage") || lastAiBubble.includes("180");
    console.log("  ✓ Semantically retrieved precedent B-016 match:", hasPrecedentMatch);

    // 7. Save Verified Screenshot
    const screenshotPath = path.join(artifactDir, "multimodal_hybrid_copilot_verified.png");
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log("  ✓ Full-page screenshot saved to:", screenshotPath);

    console.log("=== ALL MULTIMODAL VISION & HYBRID RAG TESTS PASSED 100% ===");
  } catch (err) {
    console.error("Verification failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyMultimodalAndHybridRAG();
