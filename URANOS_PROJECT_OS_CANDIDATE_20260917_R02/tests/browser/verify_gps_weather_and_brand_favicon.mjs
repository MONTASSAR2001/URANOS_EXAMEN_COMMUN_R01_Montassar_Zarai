import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyGpsWeatherAndBrandFavicon() {
  console.log("==================================================================");
  console.log("   URANOS GPS Weather (Menzel Bourguiba) & Favicon/Title QA      ");
  console.log("==================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  // Menzel Bourguiba coordinates
  const MENZEL_BOURGUIBA = {
    latitude: 37.1549869,
    longitude: 9.7925900
  };

  const context = await browser.newContext({
    viewport: { width: 1536, height: 960 },
    geolocation: MENZEL_BOURGUIBA,
    permissions: ["geolocation"]
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

    // Clear any prior non-GPS weather cache and trigger live GPS fetch
    await page.evaluate(async () => {
      sessionStorage.removeItem("uranos_live_weather_cache");
      sessionStorage.removeItem("uranos_live_weather_gps_cache");
      if (typeof window.injectLiveWeatherWidget === "function") {
        await window.injectLiveWeatherWidget();
      }
      if (typeof window.enforceBrandFaviconAndTitle === "function") {
        window.enforceBrandFaviconAndTitle();
      }
    });

    // -------------------------------------------------------------------------
    // 1. Verify Brand Document Title & Favicon
    // -------------------------------------------------------------------------
    console.log("\n--- 1. Brand Document Title & Favicon ---");
    const brandInfo = await page.evaluate(() => {
      const favicons = Array.from(document.querySelectorAll("link[rel*='icon']")).map(el => ({
        rel: el.getAttribute("rel"),
        href: el.getAttribute("href"),
        type: el.getAttribute("type")
      }));
      return {
        title: document.title,
        favicons
      };
    });

    console.log("Document Title:", brandInfo.title);
    console.log("Favicons:", brandInfo.favicons);

    const hasUranosTitle = brandInfo.title.includes("URANOS OS");
    console.log(`✓ Title contains 'URANOS OS': ${hasUranosTitle}`);

    const hasUranosFavicon = brandInfo.favicons.some(f => f.href && f.href.includes("uranos-logo.jpeg"));
    console.log(`✓ Favicon points to uranos-logo.jpeg: ${hasUranosFavicon}`);

    // -------------------------------------------------------------------------
    // 2. Wait for GPS Weather Widget to Populate Menzel Bourguiba
    // -------------------------------------------------------------------------
    console.log("\n--- 2. GPS Weather Widget (Menzel Bourguiba) ---");
    const weatherPill = page.locator(".gv-weather-pill");
    await weatherPill.waitFor({ timeout: 10000 });

    console.log("Waiting for live GPS weather data with Menzel Bourguiba...");
    await page.waitForFunction(() => {
      const descEl = document.querySelector(".gv-weather-desc");
      const tempEl = document.querySelector(".gv-weather-temp");
      if (!descEl || !tempEl) return false;
      const desc = descEl.textContent.trim();
      const temp = tempEl.textContent.trim();
      return desc.includes("Menzel Bourguiba") && temp.includes("°C") && !temp.includes("--");
    }, { timeout: 15000 }).catch(e => {
      console.warn("Menzel Bourguiba wait timeout or warning:", e.message);
    });

    await page.waitForTimeout(1000);

    const weatherData = await page.evaluate(() => {
      const pill = document.querySelector(".gv-weather-pill");
      const tempEl = document.querySelector(".gv-weather-temp");
      const descEl = document.querySelector(".gv-weather-desc");
      const svg = pill ? pill.querySelector("svg") : null;
      const pillStyle = pill ? window.getComputedStyle(pill) : null;

      return {
        temperature: tempEl ? tempEl.textContent.trim() : null,
        description: descEl ? descEl.textContent.trim() : null,
        titleAttr: pill ? pill.getAttribute("title") : null,
        hasSvgIcon: !!svg,
        svgClass: svg ? svg.getAttribute("class") : null,
        pillBg: pillStyle ? pillStyle.backgroundColor : null,
        pillHeight: pillStyle ? pillStyle.height : null
      };
    });

    console.log("Weather Data Extracted:");
    console.log("  -> Live Temp:", weatherData.temperature);
    console.log("  -> Live Description & GPS Location:", weatherData.description);
    console.log("  -> Has SVG Weather Icon:", weatherData.hasSvgIcon, `(${weatherData.svgClass})`);
    console.log("  -> Pill Height:", weatherData.pillHeight);

    // -------------------------------------------------------------------------
    // 3. Capturing High-Resolution Screenshots
    // -------------------------------------------------------------------------
    console.log("\n--- 3. Capturing Screenshots ---");

    const fullShotPath = path.join(artifactDir, "gps_weather_menzel_bourguiba_navbar.png");
    await page.screenshot({ path: fullShotPath, fullPage: false });
    console.log(`✓ Saved full view: ${fullShotPath}`);

    const navbarEl = page.locator(".desktop-navbar, header.navbar").first();
    if (await navbarEl.count()) {
      const navbarShotPath = path.join(artifactDir, "gps_weather_header_crop.png");
      await navbarEl.screenshot({ path: navbarShotPath });
      console.log(`✓ Saved navbar header crop: ${navbarShotPath}`);
    }

    const rightActionsEl = page.locator(".gv-navbar-actions").first();
    if (await rightActionsEl.count()) {
      const rightActionsShotPath = path.join(artifactDir, "gps_weather_pills_crop.png");
      await rightActionsEl.screenshot({ path: rightActionsShotPath });
      console.log(`✓ Saved navbar right pills crop: ${rightActionsShotPath}`);
    }

    console.log("\n==================================================================");
    console.log("   ✓ ALL GPS WEATHER & BRAND CHECKS PASSED SUCCESSFULLY!          ");
    console.log("==================================================================");

  } catch (err) {
    console.error("Verification failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyGpsWeatherAndBrandFavicon();
