import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyInteractiveWeatherAndModal() {
  console.log("==================================================================");
  console.log("   URANOS GPS Weather (Menzel Bourguiba) & Interactive Modal QA   ");
  console.log("==================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  // Standard HTTP context (to verify bulletproof HTTP fallback to Menzel Bourguiba)
  const context = await browser.newContext({
    viewport: { width: 1536, height: 960 }
  });
  const page = await context.newPage();

  page.on("console", msg => {
    if (msg.text().includes("[URANOS") || msg.text().includes("Weather") || msg.type() === "error") {
      console.log(`[BROWSER ${msg.type()}]:`, msg.text());
    }
  });

  async function loginAs(userEmail, password = "Password123!") {
    console.log(`\nLogging in as ${userEmail}...`);
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    if (!page.url().includes("/login")) {
      await page.evaluate(() => {
        document.cookie.split(";").forEach(c => {
          document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/");
        });
      });
      await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(1000);
    }

    if (page.url().includes("/login")) {
      const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
      await emailField.waitFor({ timeout: 10000 });
      await emailField.fill(userEmail);
      await page.fill("#loginPassword, #login_password, input[name='pwd']", password);
      await page.click("#btnContinue, .btn-login, button[type='submit']");
      await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 20000 });
      console.log(`✓ Logged in as ${userEmail}`);
    }
  }

  try {
    await loginAs("direction_01@uranos.local");

    console.log("\nNavigating to Desk (/app)...");
    await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await page.waitForTimeout(2000);

    // -------------------------------------------------------------------------
    // 1. Verify Weather Widget reads "Menzel Bourguiba"
    // -------------------------------------------------------------------------
    console.log("\n--- 1. Verifying Weather Pill text ---");
    const weatherPill = page.locator("#gvWeatherPill, .gv-weather-pill").first();
    await weatherPill.waitFor({ timeout: 10000 });

    console.log("Waiting for live weather widget to populate...");
    await page.waitForFunction(() => {
      const descEl = document.querySelector(".gv-weather-desc");
      const tempEl = document.querySelector(".gv-weather-temp");
      if (!descEl || !tempEl) return false;
      const desc = descEl.textContent.trim();
      const temp = tempEl.textContent.trim();
      return desc.includes("Menzel Bourguiba") && temp.includes("°C") && !temp.includes("--");
    }, { timeout: 15000 });

    const pillData = await page.evaluate(() => {
      const tempEl = document.querySelector(".gv-weather-temp");
      const descEl = document.querySelector(".gv-weather-desc");
      return {
        temp: tempEl ? tempEl.textContent.trim() : null,
        desc: descEl ? descEl.textContent.trim() : null
      };
    });

    console.log(`✓ Weather Pill verified: ${pillData.temp} | ${pillData.desc}`);
    if (!pillData.desc.includes("Menzel Bourguiba")) {
      throw new Error(`Weather widget does not read Menzel Bourguiba: ${pillData.desc}`);
    }

    // -------------------------------------------------------------------------
    // 2. Click Weather Pill to open Interactive Modal Dialog
    // -------------------------------------------------------------------------
    console.log("\n--- 2. Clicking Weather Pill to open Details Modal ---");
    await weatherPill.click();
    await page.waitForTimeout(800);

    const modalDialog = page.locator(".gv-weather-dialog-wrapper, .modal.show").first();
    await modalDialog.waitFor({ timeout: 5000 });
    console.log("✓ Modal Dialog opened successfully!");

    // -------------------------------------------------------------------------
    // 3. Verify Detailed Modal Fields
    // -------------------------------------------------------------------------
    console.log("\n--- 3. Verifying Detailed Telemetry in Modal ---");
    const modalDetails = await page.evaluate(() => {
      const wrapper = document.querySelector(".gv-weather-modal-content");
      if (!wrapper) return null;

      const heroTemp = wrapper.querySelector(".gv-weather-hero-temp")?.textContent.trim();
      const heroDesc = wrapper.querySelector(".gv-weather-hero-desc")?.textContent.trim();

      const cards = Array.from(wrapper.querySelectorAll(".gv-weather-metric-card")).map(card => ({
        label: card.querySelector(".gv-weather-card-label")?.textContent.trim(),
        value: card.querySelector(".gv-weather-card-value")?.textContent.trim()
      }));

      return {
        heroTemp,
        heroDesc,
        cards
      };
    });

    console.log("Modal Details Extracted:", JSON.stringify(modalDetails, null, 2));

    const exactLocCard = modalDetails.cards.find(c => c.label.includes("Exact Location"));
    const gpsCard = modalDetails.cards.find(c => c.label.includes("GPS Coordinates"));
    const condCard = modalDetails.cards.find(c => c.label.includes("Condition"));
    const windCard = modalDetails.cards.find(c => c.label.includes("Wind Speed"));
    const humCard = modalDetails.cards.find(c => c.label.includes("Humidity"));

    console.log(`✓ Exact Location: ${exactLocCard?.value}`);
    console.log(`✓ Coordinates: ${gpsCard?.value}`);
    console.log(`✓ Condition & Temp: ${condCard?.value}`);
    console.log(`✓ Wind Speed: ${windCard?.value}`);
    console.log(`✓ Relative Humidity: ${humCard?.value}`);

    if (!exactLocCard?.value.includes("Menzel Bourguiba")) {
      throw new Error(`Location in modal does not include Menzel Bourguiba: ${exactLocCard?.value}`);
    }

    // -------------------------------------------------------------------------
    // 4. Capture Screenshots of Open Modal & Navbar
    // -------------------------------------------------------------------------
    console.log("\n--- 4. Capturing Screenshots ---");

    // Full screen showing the modal over the executive dashboard
    const modalShotPath = path.join(artifactDir, "weather_details_modal_open.png");
    await page.screenshot({ path: modalShotPath, fullPage: false });
    console.log(`✓ Saved modal screenshot: ${modalShotPath}`);

    // Modal dialog crop
    const modalContent = page.locator(".gv-weather-dialog-wrapper .modal-content").first();
    if (await modalContent.count()) {
      const cropShotPath = path.join(artifactDir, "weather_modal_crop.png");
      await modalContent.screenshot({ path: cropShotPath });
      console.log(`✓ Saved modal dialog crop: ${cropShotPath}`);
    }

    console.log("\n==================================================================");
    console.log("   ✓ ALL INTERACTIVE WEATHER MODAL CHECKS PASSED WITH SUCCESS!   ");
    console.log("==================================================================");

  } catch (err) {
    console.error("Verification failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyInteractiveWeatherAndModal();
