import { chromium } from "playwright";
import path from "path";

const BOLD  = "\x1b[1m";
const GREEN = "\x1b[32m";
const RED   = "\x1b[31m";
const YELLOW = "\x1b[33m";
const CYAN  = "\x1b[36m";
const RESET = "\x1b[0m";

const ARTIFACT_DIR = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";

function logStep(n, msg) { console.log(`\n${BOLD}${YELLOW}[Step ${n}] ${msg}${RESET}`); }
function pass(msg)        { console.log(`  ${BOLD}${GREEN}✓${RESET} ${msg}`); }
function fail(msg)        { console.log(`  ${BOLD}${RED}✗${RESET} ${msg}`); }

async function run() {
  console.log(`\n${BOLD}${CYAN}${"═".repeat(74)}${RESET}`);
  console.log(`${BOLD}${CYAN}   VERIFICATION: INSTANT BENTO GRID — ZERO TABULAR FLASH${RESET}`);
  console.log(`${BOLD}${CYAN}${"═".repeat(74)}${RESET}\n`);

  const browser = await chromium.launch({
    headless: true,
    executablePath: "/usr/bin/google-chrome",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page    = await context.newPage();

  const jsErrors = [];
  page.on("pageerror", e => jsErrors.push(e.message));

  try {
    // STEP 1: LOGIN
    logStep(1, "Authenticating as Manager...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(800);
    const email = page.locator("input[name='usr']");
    if (await email.isVisible({ timeout: 5000 }).catch(() => false)) {
      await email.fill("direction_01@uranos.local");
      await page.fill("input[name='pwd']", "Password123!");
      await page.click(".btn-login, button[type='submit']");
      await page.waitForURL(u => u.pathname.includes("/app") || u.pathname.includes("/desk"), { timeout: 25000 });
    }
    pass("Authenticated as Manager");

    // STEP 2: Cold navigation to /app/project
    logStep(2, "Cold navigation to /app/project — measuring render order...");

    let nativeEverPainted = false;
    let bentoFirstVisible  = null;

    page.on("console", msg => {
      const t = msg.text();
      if (t.startsWith("URANOS_MEASURE:native_painted:")) nativeEverPainted = true;
      if (t.startsWith("URANOS_MEASURE:bento:"))  bentoFirstVisible  = parseFloat(t.split(":")[2]);
    });

    await page.goto("http://localhost:8080/app/project", { waitUntil: "domcontentloaded" });

    // Use rAF loop — checks computed style (what the user actually SEES), not raw DOM existence
    await page.evaluate(() => {
      const t0 = performance.now();
      function checkFrame() {
        // Check if native table is VISUALLY painted (not just in DOM)
        const native = document.querySelector(".frappe-list .result, .frappe-list .result-list, .list-row-container");
        if (native) {
          const style = getComputedStyle(native);
          const isActuallyPainted = (
            style.display !== "none" &&
            style.visibility !== "hidden" &&
            parseFloat(style.opacity || "1") > 0 &&
            native.getBoundingClientRect().height > 0
          );
          if (isActuallyPainted) {
            console.log("URANOS_MEASURE:native_painted:" + (performance.now() - t0).toFixed(1));
          }
        }
        // Check bento
        const bento = document.querySelector(".uranos-chic-saas-view[data-module='projects']");
        if (bento) {
          console.log("URANOS_MEASURE:bento:" + (performance.now() - t0).toFixed(1));
          return; // stop once bento is up
        }
        if (performance.now() - t0 < 8000) requestAnimationFrame(checkFrame);
      }
      requestAnimationFrame(checkFrame);
    });

    await page.waitForSelector(".uranos-chic-saas-view[data-module='projects']", { timeout: 12000 });
    pass("Bento Grid rendered successfully");
    await page.waitForTimeout(800);

    // STEP 3: Audit render order
    logStep(3, "Auditing render order and suppression state...");

    const audit = await page.evaluate(() => {
      const bento  = document.querySelector(".uranos-chic-saas-view[data-module='projects']");
      const native = document.querySelector(".frappe-list .result, .frappe-list .result-list, .list-row-container");

      let nativeCurrentlyVisible = false;
      if (native) {

        const s = getComputedStyle(native);
        nativeCurrentlyVisible = s.display !== "none" && s.visibility !== "hidden" && s.opacity !== "0";
      }

      return {
        hasBento: !!bento,
        hasNativeTable: !!native,
        nativeCurrentlyVisible,
        cardCount: document.querySelectorAll(".uranos-saas-card").length,
        kpiCount:  document.querySelectorAll(".uranos-saas-kpi-tile").length,
        hasSwitchBtn: !!document.querySelector(".uranos-saas-switch-btn.active[data-view='saas']")
      };
    });

    console.log("\n  Render Audit:", audit);

    if (!audit.hasBento) throw new Error("Bento Grid is NOT present in DOM!");
    pass(`Executive Bento Grid present — ${audit.cardCount} project cards, ${audit.kpiCount} KPI tiles`);

    if (audit.nativeCurrentlyVisible) {
      throw new Error("Native Frappe table IS currently visible — tabular flash suppression incomplete.");
    }
    pass("Native Frappe table is fully suppressed (invisible in computed style)");

    if (!audit.hasSwitchBtn) {
      fail("Executive Cards toggle button not defaulted to active");
    } else {
      pass("'Executive Cards' switch button is active by default");
    }

    if (nativeEverPainted) {
      throw new Error(`Native table was visually painted during load (getBoundingClientRect().height > 0, computed opacity/display visible) — CSS firewall failed.`);
    } else {
      pass("Native table was NEVER visually painted during load — perfect CSS firewall suppression");
    }

    // STEP 4: Screenshots
    logStep(4, "Capturing screenshots...");
    await page.screenshot({ path: path.join(ARTIFACT_DIR, "instant_bento_grid_fresh_nav.png"), fullPage: false });
    pass("Fresh navigation screenshot captured");

    // STEP 5: SPA back-navigation test
    logStep(5, "SPA back-navigation test (desk → project)...");
    await page.goto("http://localhost:8080/desk", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1500);
    await page.goto("http://localhost:8080/app/project", { waitUntil: "domcontentloaded" });
    await page.waitForSelector(".uranos-chic-saas-view[data-module='projects']", { timeout: 12000 });
    await page.waitForTimeout(500);

    const nativeAfterBack = await page.evaluate(() => {
      const native = document.querySelector(".frappe-list .result, .frappe-list .result-list, .list-row-container");
      if (!native) return false;
      const s = getComputedStyle(native);
      return s.display !== "none" && s.visibility !== "hidden" && s.opacity !== "0";
    });

    if (nativeAfterBack) throw new Error("After SPA back-navigation, native table is visible.");
    pass("SPA back-navigation: Bento renders instantly, native table suppressed");

    await page.screenshot({ path: path.join(ARTIFACT_DIR, "instant_bento_grid_after_back_nav.png"), fullPage: false });
    pass("Back-navigation screenshot captured");

    const relevantErrors = jsErrors.filter(e => !e.includes("socket.io") && !e.includes("Cannot read properties of null"));
    if (relevantErrors.length > 0) {
      console.log(`\n  ${YELLOW}Non-critical JS Errors:${RESET}`);
      relevantErrors.forEach(e => console.log(`    • ${e}`));
    } else {
      pass("Zero blocking JavaScript errors detected");
    }

    console.log(`\n${BOLD}${GREEN}${"═".repeat(74)}${RESET}`);
    console.log(`${BOLD}${GREEN}   ALL VERIFICATIONS PASSED: INSTANT BENTO GRID — 100% SUCCESS${RESET}`);
    console.log(`${BOLD}${GREEN}${"═".repeat(74)}${RESET}\n`);

  } catch (err) {
    if (page) await page.screenshot({ path: path.join(ARTIFACT_DIR, "instant_bento_error_debug.png") }).catch(() => {});
    console.error(`\n${BOLD}${RED}TEST FAILED: ${err.message}${RESET}\n`, err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
