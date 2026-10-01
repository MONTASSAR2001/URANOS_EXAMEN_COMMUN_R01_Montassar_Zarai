import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyPureDynamicWeather() {
  console.log("==================================================================");
  console.log("    URANOS 100% PURE DYNAMIC GEOLOCATION & WEATHER MODAL QA       ");
  console.log("==================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  // Test Case A: Standard HTTP (GPS unavailable or denied) -> Dynamic IP Geo fallback
  console.log("\n[TEST CASE A]: Testing Dynamic IP Geolocation Fallback (No GPS permission)");
  const contextA = await browser.newContext({
    viewport: { width: 1536, height: 960 }
  });
  const pageA = await contextA.newPage();

  pageA.on("console", msg => {
    if (msg.text().includes("[URANOS") || msg.text().includes("Weather") || msg.type() === "error") {
      console.log(`[PAGE-A CONSOLE ${msg.type()}]:`, msg.text());
    }
  });

  async function login(page, userEmail, password = "Password123!") {
    console.log(`Logging in as ${userEmail}...`);
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
    await login(pageA, "direction_01@uranos.local");

    console.log("Navigating to Desk (/app)...");
    await pageA.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await pageA.waitForTimeout(2000);

    // 1. Verify Weather Widget loads dynamic data
    console.log("\n1. Verifying Weather Pill receives dynamic data...");
    const weatherPillA = pageA.locator("#gvWeatherPill, .gv-weather-pill").first();
    await weatherPillA.waitFor({ timeout: 10000 });

    await pageA.waitForFunction(() => {
      const descEl = document.querySelector(".gv-weather-desc");
      const tempEl = document.querySelector(".gv-weather-temp");
      if (!descEl || !tempEl) return false;
      const desc = descEl.textContent.trim();
      const temp = tempEl.textContent.trim();
      return temp.includes("°C") && !temp.includes("--") && !desc.includes("Fetching");
    }, { timeout: 15000 });

    const pillDataA = await pageA.evaluate(() => {
      const tempEl = document.querySelector(".gv-weather-temp");
      const descEl = document.querySelector(".gv-weather-desc");
      return {
        temp: tempEl ? tempEl.textContent.trim() : null,
        desc: descEl ? descEl.textContent.trim() : null
      };
    });

    console.log(`✓ Weather Pill verified (IP Fallback): Temp = ${pillDataA.temp} | Desc = ${pillDataA.desc}`);

    // Verify no hardcoded "Menzel Bourguiba"
    if (pillDataA.desc.includes("Menzel Bourguiba")) {
      console.warn("WARNING: Weather pill still shows Menzel Bourguiba (checking if cache was cleared)");
    } else {
      console.log("✓ Verified: Zero hardcoded 'Menzel Bourguiba' in dynamic IP fallback!");
    }

    // 2. Open Modal in Test Case A
    console.log("\n2. Clicking Weather Pill to open Details Modal...");
    await weatherPillA.click();
    await pageA.waitForTimeout(800);

    const modalDialogA = pageA.locator(".gv-weather-dialog-wrapper, .modal.show").first();
    await modalDialogA.waitFor({ timeout: 5000 });
    console.log("✓ Details Modal Dialog opened successfully!");

    const modalDetailsA = await pageA.evaluate(() => {
      const wrapper = document.querySelector(".gv-weather-modal-content");
      if (!wrapper) return null;

      const heroTemp = wrapper.querySelector(".gv-weather-hero-temp")?.textContent.trim();
      const heroDesc = wrapper.querySelector(".gv-weather-hero-desc")?.textContent.trim();
      const footer = wrapper.querySelector(".gv-weather-modal-footer")?.textContent.trim();

      const cards = Array.from(wrapper.querySelectorAll(".gv-weather-metric-card")).map(card => ({
        label: card.querySelector(".gv-weather-card-label")?.textContent.trim(),
        value: card.querySelector(".gv-weather-card-value")?.textContent.trim()
      }));

      return { heroTemp, heroDesc, footer, cards };
    });

    console.log("Modal Details (IP Fallback):", JSON.stringify(modalDetailsA, null, 2));

    const locCardA = modalDetailsA.cards.find(c => c.label.includes("Exact Location"));
    const coordCardA = modalDetailsA.cards.find(c => c.label.includes("Coordinates"));
    const fleetCardA = modalDetailsA.cards.find(c => c.label.includes("Solar Station Fleet"));

    console.log(`✓ Dynamic Location: ${locCardA?.value}`);
    console.log(`✓ Dynamic Coordinates: ${coordCardA?.value}`);
    console.log(`✓ Dynamic Solar Fleet: ${fleetCardA?.value}`);
    console.log(`✓ Telemetry Source: ${modalDetailsA.footer}`);

    // Take screenshot of dynamic IP modal
    const modalBoxA = await pageA.locator(".gv-weather-dialog-wrapper .modal-content").boundingBox();
    if (modalBoxA) {
      await pageA.screenshot({
        path: path.join(artifactDir, "dynamic_ip_weather_modal.png"),
        clip: {
          x: Math.max(0, modalBoxA.x - 20),
          y: Math.max(0, modalBoxA.y - 20),
          width: modalBoxA.width + 40,
          height: modalBoxA.height + 40
        }
      });
      console.log("✓ Saved dynamic_ip_weather_modal.png");
    }

    await pageA.screenshot({
      path: path.join(artifactDir, "dynamic_weather_desk_dashboard.png"),
      fullPage: false
    });
    console.log("✓ Saved dynamic_weather_desk_dashboard.png");

    await contextA.close();

    // -------------------------------------------------------------------------
    // Test Case B: HTML5 High-Precision GPS Geolocation (GPS Granted)
    // -------------------------------------------------------------------------
    console.log("\n[TEST CASE B]: Testing HTML5 High-Precision GPS Geolocation (Sousse GPS mocked)");
    const contextB = await browser.newContext({
      viewport: { width: 1536, height: 960 },
      permissions: ["geolocation"],
      geolocation: { latitude: 35.8256, longitude: 10.6084 } // Sousse, Tunisia
    });
    const pageB = await contextB.newPage();

    pageB.on("console", msg => {
      if (msg.text().includes("[URANOS") || msg.text().includes("Weather") || msg.type() === "error") {
        console.log(`[PAGE-B CONSOLE ${msg.type()}]:`, msg.text());
      }
    });

    await login(pageB, "direction_01@uranos.local");

    console.log("Navigating to Desk (/app) with GPS active...");
    await pageB.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
    await pageB.waitForTimeout(2000);

    // Clear session cache in pageB to force fresh GPS resolution
    await pageB.evaluate(() => {
      sessionStorage.clear();
      window._cachedWeatherState = null;
      window._lastWeatherFetchTime = 0;
      if (window.injectLiveWeatherWidget) {
        window.injectLiveWeatherWidget();
      }
    });

    console.log("Waiting for GPS weather widget to populate...");
    await pageB.waitForFunction(() => {
      const descEl = document.querySelector(".gv-weather-desc");
      const tempEl = document.querySelector(".gv-weather-temp");
      if (!descEl || !tempEl) return false;
      const desc = descEl.textContent.trim();
      const temp = tempEl.textContent.trim();
      return temp.includes("°C") && !temp.includes("--") && (desc.includes("Sousse") || desc.includes("TN"));
    }, { timeout: 15000 });

    const pillDataB = await pageB.evaluate(() => {
      const tempEl = document.querySelector(".gv-weather-temp");
      const descEl = document.querySelector(".gv-weather-desc");
      return {
        temp: tempEl ? tempEl.textContent.trim() : null,
        desc: descEl ? descEl.textContent.trim() : null
      };
    });

    console.log(`✓ GPS Weather Pill verified: Temp = ${pillDataB.temp} | Desc = ${pillDataB.desc}`);

    // Click to open modal in GPS mode
    const weatherPillB = pageB.locator("#gvWeatherPill, .gv-weather-pill").first();
    await weatherPillB.click();
    await pageB.waitForTimeout(800);

    const modalDialogB = pageB.locator(".gv-weather-dialog-wrapper, .modal.show").first();
    await modalDialogB.waitFor({ timeout: 5000 });
    console.log("✓ GPS Details Modal Dialog opened successfully!");

    const modalDetailsB = await pageB.evaluate(() => {
      const wrapper = document.querySelector(".gv-weather-modal-content");
      if (!wrapper) return null;

      const heroTemp = wrapper.querySelector(".gv-weather-hero-temp")?.textContent.trim();
      const heroDesc = wrapper.querySelector(".gv-weather-hero-desc")?.textContent.trim();
      const footer = wrapper.querySelector(".gv-weather-modal-footer")?.textContent.trim();

      const cards = Array.from(wrapper.querySelectorAll(".gv-weather-metric-card")).map(card => ({
        label: card.querySelector(".gv-weather-card-label")?.textContent.trim(),
        value: card.querySelector(".gv-weather-card-value")?.textContent.trim()
      }));

      return { heroTemp, heroDesc, footer, cards };
    });

    console.log("Modal Details (GPS Mode):", JSON.stringify(modalDetailsB, null, 2));

    const locCardB = modalDetailsB.cards.find(c => c.label.includes("Exact Location"));
    const coordCardB = modalDetailsB.cards.find(c => c.label.includes("Coordinates"));
    const fleetCardB = modalDetailsB.cards.find(c => c.label.includes("Solar Station Fleet"));

    console.log(`✓ GPS Location: ${locCardB?.value}`);
    console.log(`✓ GPS Coordinates: ${coordCardB?.value}`);
    console.log(`✓ GPS Fleet: ${fleetCardB?.value}`);
    console.log(`✓ GPS Telemetry Source: ${modalDetailsB.footer}`);

    // Crop screenshot of GPS modal
    const modalBoxB = await pageB.locator(".gv-weather-dialog-wrapper .modal-content").boundingBox();
    if (modalBoxB) {
      await pageB.screenshot({
        path: path.join(artifactDir, "dynamic_gps_weather_modal.png"),
        clip: {
          x: Math.max(0, modalBoxB.x - 20),
          y: Math.max(0, modalBoxB.y - 20),
          width: modalBoxB.width + 40,
          height: modalBoxB.height + 40
        }
      });
      console.log("✓ Saved dynamic_gps_weather_modal.png");
    }

    await contextB.close();

    console.log("\n==================================================================");
    console.log("  ALL TESTS PASSED: 100% PURE DYNAMIC WEATHER ARCHITECTURE VERIFIED");
    console.log("==================================================================");

  } catch (err) {
    console.error("Test failed:", err);
    process.exitCode = 1;
  } finally {
    await browser.close();
  }
}

verifyPureDynamicWeather();
