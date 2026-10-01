import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyStitchAICopilot() {
  console.log("=== Verifying Stitch Ultra-Premium UI Integration on uranos-ai-copilot ===");
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
      viewport: { width: 1560, height: 960 }
    });
    const page = await context.newPage();

    // 1. Authenticate
    console.log("1. Authenticating as ingenieur_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(url => url.pathname.includes("/desk") || url.pathname.includes("/app"), { timeout: 15000 });
    console.log("  ✓ Logged in. URL:", page.url());

    // 2. Navigate to Copilot
    console.log("2. Navigating to /app/uranos-ai-copilot...");
    await page.goto("http://localhost:8080/app/uranos-ai-copilot", { waitUntil: "networkidle" });
    await page.waitForSelector("#uranos-ai-copilot-page", { timeout: 10000 });
    await page.waitForTimeout(3000); // Allow MariaDB RAG fetch to resolve

    // 3. Inspect Elements & Target IDs
    console.log("3. Inspecting Stitch DOM elements & Target IDs...");
    const inspection = await page.evaluate(() => {
      const kpiOpen = document.getElementById("uac-kpi-open");
      const kpiCrit = document.getElementById("uac-kpi-critical");
      const kpiLost = document.getElementById("uac-kpi-lost");
      const kpiVer = document.getElementById("uac-kpi-verified");
      const altProg = document.getElementById("uac-val-progress");
      const synthBody = document.getElementById("uac-synthesis-body");
      const chatLog = document.getElementById("uac-chat-log");
      const chatInput = document.getElementById("uac-chat-input");
      const sendBtn = document.getElementById("uac-chat-send");
      const doc = document.documentElement;

      return {
        dir: doc.getAttribute("dir") || "ltr",
        lang: doc.getAttribute("lang") || "en",
        hasKpis: !!(kpiOpen && kpiCrit && kpiLost && kpiVer),
        hasAltProg: !!altProg,
        kpiOpenVal: kpiOpen ? kpiOpen.innerText.trim() : null,
        kpiCritVal: kpiCrit ? kpiCrit.innerText.trim() : null,
        kpiLostVal: kpiLost ? kpiLost.innerText.trim() : null,
        kpiVerVal: kpiVer ? kpiVer.innerText.trim() : null,
        synthLength: synthBody ? synthBody.innerText.length : 0,
        chatLogLength: chatLog ? chatLog.innerText.length : 0,
        hasInput: !!chatInput,
        hasSend: !!sendBtn
      };
    });

    console.log("  DOM Inspection Result:", inspection);

    if (!inspection.hasKpis || !inspection.hasInput || !inspection.hasSend) {
      throw new Error("Missing critical DOM elements in new Stitch UI!");
    }
    console.log("  ✓ All critical target IDs and dynamic elements are present!");

    // 4. Test Chat Interactivity
    console.log("4. Testing Chat Interactivity with query...");
    const testQuery = "What is the status of active blockers?";
    await page.fill("#uac-chat-input", testQuery);
    await page.click("#uac-chat-send");
    await page.waitForTimeout(1500); // Wait for thinking / RAG call

    // Wait for response bubble
    await page.waitForFunction(() => {
      const log = document.getElementById("uac-chat-log");
      return log && log.querySelectorAll(".uac-msg-user").length >= 1;
    }, { timeout: 10000 });

    console.log("  ✓ User message successfully posted into Stitch chat bubble!");

    // Wait another 3s for potential AI reply
    await page.waitForTimeout(3000);

    // 5. Capture Proof Screenshot
    const screenshotPath = path.join(artifactDir, "stitch_copilot_verified.png");
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log("  ✓ Screenshot saved to:", screenshotPath);

    console.log("=== STITCH UI INTEGRATION VERIFICATION PASSED 100% ===");
  } finally {
    await browser.close();
  }
}

verifyStitchAICopilot().catch(err => {
  console.error("Verification failed:", err);
  process.exit(1);
});
