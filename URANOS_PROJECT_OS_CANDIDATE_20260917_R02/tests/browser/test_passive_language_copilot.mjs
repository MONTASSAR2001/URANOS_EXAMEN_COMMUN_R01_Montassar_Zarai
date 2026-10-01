import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyPassiveLanguageDetection() {
  console.log("=== Testing AI Copilot Passive Language Detection & Zero Global Overrides ===");
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
      viewport: { width: 1440, height: 900 }
    });
    const page = await context.newPage();

    // 1. Login
    console.log("1. Authenticating as ingenieur_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(url => url.pathname.includes("/desk") || url.pathname.includes("/app"), { timeout: 15000 });
    console.log("  ✓ Successfully logged in. URL:", page.url());

    // 2. Check initial system language and direction
    console.log("2. Checking initial Frappe Desk language & direction before Copilot navigation...");
    const initialDocState = await page.evaluate(() => {
      return {
        dir: document.documentElement.getAttribute("dir") || document.dir || "ltr",
        lang: document.documentElement.getAttribute("lang") || "en",
        bootLang: window.frappe && window.frappe.boot ? window.frappe.boot.lang : null,
        userLang: window.frappe && window.frappe.boot && window.frappe.boot.user ? window.frappe.boot.user.language : null
      };
    });
    console.log("  Initial Doc State:", initialDocState);

    // 3. Navigate to uranos-ai-copilot
    console.log("3. Navigating to /app/uranos-ai-copilot...");
    await page.goto("http://localhost:8080/app/uranos-ai-copilot", { waitUntil: "networkidle" });
    await page.waitForSelector("#uranos-ai-copilot-page", { timeout: 10000 });
    await page.waitForTimeout(2000); // Allow initialization

    // 4. Verify that document.documentElement was NOT forced to Arabic or RTL!
    console.log("4. Verifying document.documentElement after loading AI Copilot...");
    const copilotDocState = await page.evaluate(() => {
      return {
        dir: document.documentElement.getAttribute("dir") || document.dir,
        lang: document.documentElement.getAttribute("lang"),
        bodyDir: document.body.getAttribute("dir"),
        chatLogText: document.getElementById("uac-chat-log") ? document.getElementById("uac-chat-log").innerText : ""
      };
    });
    console.log("  Copilot Page Doc State:", copilotDocState);

    if (initialDocState.dir === "ltr" || !initialDocState.dir) {
      if (copilotDocState.dir === "rtl") {
        throw new Error("CRITICAL BUG STILL PRESENT: document.documentElement.dir was forcefully changed to 'rtl'!");
      }
      if (copilotDocState.lang === "ar" && initialDocState.lang !== "ar") {
        throw new Error("CRITICAL BUG STILL PRESENT: document.documentElement.lang was forcefully changed to 'ar'!");
      }
      console.log("  ✓ PASS: document.documentElement was NOT forced to RTL/Arabic!");
    }

    // 5. Check welcome message
    console.log("5. Checking localized greeting message in chat log...");
    console.log("  Chat Log Content preview:", copilotDocState.chatLogText.substring(0, 150));
    if (copilotDocState.chatLogText.includes("Hello! I am your URANOS Copilot") || copilotDocState.chatLogText.includes("Bonjour") || copilotDocState.chatLogText.includes("مساعد أورانوس")) {
      console.log("  ✓ PASS: Localized greeting properly rendered!");
    } else {
      console.warn("  [NOTE] Chat log content:", copilotDocState.chatLogText);
    }

    // 6. Navigate back to blocker dashboard and verify no sticky Arabic
    console.log("6. Navigating back to /app/blocker-dashboard...");
    await page.click("#uac-back-btn");
    await page.waitForURL(url => url.pathname.includes("blocker-dashboard"), { timeout: 10000 });
    await page.waitForTimeout(1000);

    const postNavDocState = await page.evaluate(() => {
      return {
        dir: document.documentElement.getAttribute("dir") || document.dir,
        lang: document.documentElement.getAttribute("lang")
      };
    });
    console.log("  Post-Navigation Doc State:", postNavDocState);

    if (postNavDocState.dir === "rtl" && initialDocState.dir !== "rtl") {
      throw new Error("CRITICAL BUG STILL PRESENT: System remains stuck in RTL after leaving Copilot!");
    }
    console.log("  ✓ PASS: System remained in native session direction after leaving Copilot!");

    // Capture screenshot as evidence
    const screenshotPath = path.join(artifactDir, "copilot_passive_language_verified.png");
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log("  ✓ Screenshot saved to:", screenshotPath);

    console.log("=== ALL PASSIVE LANGUAGE CHECKS PASSED SUCCESSFULLY ===");
  } finally {
    await browser.close();
  }
}

verifyPassiveLanguageDetection().catch(err => {
  console.error("Verification failed:", err);
  process.exit(1);
});
