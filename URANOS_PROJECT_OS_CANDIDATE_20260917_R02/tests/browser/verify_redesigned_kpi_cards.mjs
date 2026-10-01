import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyRedesignedKpiCards() {
  console.log("==================================================================");
  console.log("   URANOS: Top 4 KPI Cards Redesign & Dynamic Data Integrity Test ");
  console.log("==================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/465edcf9-4f3c-45a7-b2e1-1b4e8d2dadb6";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 }
  });
  const page = await context.newPage();

  try {
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

    console.log("2. Auditing 4 Redesigned KPI Cards Structure & Styling...");
    const kpiAudit = await page.evaluate(() => {
      const cards = [
        { id: "#gv-kpi-card-capacity", labelId: "Total Capacity", valId: "#gv-kpi-capacity-val", trendId: "#gv-kpi-capacity-trend" },
        { id: "#gv-kpi-card-sites", labelId: "Active Sites", valId: "#gv-kpi-sites-val", trendId: "#gv-kpi-sites-trend" },
        { id: "#gv-kpi-card-energy", labelId: "Total Energy Today", valId: "#gv-kpi-energy-val", trendId: "#gv-kpi-energy-trend" },
        { id: "#gv-kpi-card-co2", labelId: "CO2 Avoided", valId: "#gv-kpi-co2-val", trendId: "#gv-kpi-co2-trend" }
      ];

      return cards.map(c => {
        const el = document.querySelector(c.id);
        if (!el) return { id: c.id, found: false };

        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        const iconCircle = el.querySelector(".gv-kpi-icon-circle");
        const iconStyle = iconCircle ? window.getComputedStyle(iconCircle) : null;
        const labelEl = el.querySelector(".gv-kpi-label");
        const labelStyle = labelEl ? window.getComputedStyle(labelEl) : null;
        const valEl = el.querySelector(c.valId);
        const valStyle = valEl ? window.getComputedStyle(valEl) : null;
        const trendEl = el.querySelector(c.trendId);

        return {
          id: c.id,
          found: true,
          width: rect.width,
          height: rect.height,
          padding: style.padding,
          borderRadius: style.borderRadius,
          backgroundColor: style.backgroundColor,
          border: style.border,
          boxShadow: style.boxShadow,
          iconSize: iconStyle ? `${iconStyle.width} x ${iconStyle.height}` : null,
          iconRadius: iconStyle ? iconStyle.borderRadius : null,
          label: labelEl ? labelEl.innerText.trim() : null,
          labelFontSize: labelStyle ? labelStyle.fontSize : null,
          labelFontWeight: labelStyle ? labelStyle.fontWeight : null,
          value: valEl ? valEl.innerText.trim() : null,
          valueFontSize: valStyle ? valStyle.fontSize : null,
          valueFontWeight: valStyle ? valStyle.fontWeight : null,
          trend: trendEl ? trendEl.innerText.trim() : null
        };
      });
    });

    console.log("------------------------------------------------------------------");
    console.log("Card Audit Results:");
    console.log(JSON.stringify(kpiAudit, null, 2));
    console.log("------------------------------------------------------------------");

    for (const card of kpiAudit) {
      if (!card.found) {
        throw new Error(`FAILURE: KPI Card ${card.id} not found in DOM!`);
      }
      if (!card.padding.includes("24px")) {
        throw new Error(`FAILURE: KPI Card ${card.id} expected padding 24px, got ${card.padding}`);
      }
      if (!card.borderRadius.includes("20px")) {
        throw new Error(`FAILURE: KPI Card ${card.id} expected border-radius 20px, got ${card.borderRadius}`);
      }
      if (card.height > 250) {
        throw new Error(`FAILURE: KPI Card ${card.id} is too tall (${card.height}px)!`);
      }
      if (!card.valueFontSize.includes("32px")) {
        throw new Error(`FAILURE: KPI Card ${card.id} expected 32px value font size, got ${card.valueFontSize}`);
      }
      if (card.value.includes("—") || card.value === "") {
        throw new Error(`FAILURE: KPI Card ${card.id} has empty/unpopulated dynamic data: '${card.value}'`);
      }
    }

    console.log("✓ All 4 KPI Cards meet the compact 20px radius, 24px padding modern SaaS specs!");
    console.log("✓ Live 32px massive typography and dynamic backend data verified!");

    // Capture screenshot of the newly redesigned KPI cards
    const screenshotPath = path.join(artifactDir, "redesigned_kpi_cards_verified.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`✓ Screenshot captured: ${screenshotPath}`);

    console.log("\n==================================================================");
    console.log("   KPI CARDS REDESIGN VERIFICATION PASSED SUCCESSFULLY!          ");
    console.log("==================================================================");

  } catch (err) {
    console.error("Verification failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyRedesignedKpiCards();
