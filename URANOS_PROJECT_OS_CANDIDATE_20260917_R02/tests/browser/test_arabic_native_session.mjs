import { chromium } from "playwright";
import path from "node:path";

async function verifyArabicNativeSession() {
  console.log("=== Testing Native Frappe Arabic Session Adaptation ===");
  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/97174a4e-bfcc-44e2-9cb9-920468c21f67";

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

    console.log("1. Authenticating as ingenieur_01@uranos.local (Arabic Profile)...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.fill("#loginEmail", "ingenieur_01@uranos.local");
    await page.fill("#loginPassword", "Password123!");
    await page.click("#btnContinue");
    await page.waitForURL(url => url.pathname.includes("/desk") || url.pathname.includes("/app"), { timeout: 15000 });

    console.log("2. Verifying native Frappe Arabic boot state...");
    const bootState = await page.evaluate(() => {
      return {
        dir: document.documentElement.getAttribute("dir"),
        lang: document.documentElement.getAttribute("lang"),
        bootLang: window.frappe && window.frappe.boot ? window.frappe.boot.lang : null,
        userLang: window.frappe && window.frappe.boot && window.frappe.boot.user ? window.frappe.boot.user.language : null
      };
    });
    console.log("  Native Arabic Boot State:", bootState);

    console.log("3. Navigating to /app/uranos-ai-copilot...");
    await page.goto("http://localhost:8080/app/uranos-ai-copilot", { waitUntil: "networkidle" });
    await page.waitForSelector("#uranos-ai-copilot-page", { timeout: 10000 });
    await page.waitForTimeout(2000);

    const copilotArabicState = await page.evaluate(() => {
      const chatLog = document.getElementById("uac-chat-log");
      return {
        dir: document.documentElement.getAttribute("dir"),
        chatLogText: chatLog ? chatLog.innerText : ""
      };
    });
    console.log("  Copilot Arabic State:", copilotArabicState);

    const screenshotPath = path.join(artifactDir, "copilot_native_arabic_session.png");
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log("  ✓ Screenshot saved to:", screenshotPath);
    console.log("=== ARABIC NATIVE SESSION TEST FINISHED ===");
  } finally {
    await browser.close();
  }
}

verifyArabicNativeSession().catch(err => {
  console.error("Test failed:", err);
  process.exit(1);
});
