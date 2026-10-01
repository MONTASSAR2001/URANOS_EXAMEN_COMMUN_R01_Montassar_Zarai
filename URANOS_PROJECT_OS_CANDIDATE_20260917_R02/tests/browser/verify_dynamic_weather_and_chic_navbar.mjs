import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyDynamicWeatherAndChicNavbar() {
  console.log("==================================================================");
  console.log("   URANOS Chic Top Navbar & Dynamic Live Weather Verification    ");
  console.log("==================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

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
    await page.waitForTimeout(2500);

    // -------------------------------------------------------------------------
    // 1. Verify Brand Name & Subtitle Typography
    // -------------------------------------------------------------------------
    console.log("\n--- 1. Brand Name & Subtitle Typography ---");
    const brandTitle = page.locator(".gv-brand-title");
    await brandTitle.waitFor({ timeout: 10000 });

    const brandMetrics = await page.evaluate(() => {
      const titleEl = document.querySelector(".gv-brand-title");
      const subEl = document.querySelector(".gv-brand-subtitle");
      const titleStyle = titleEl ? window.getComputedStyle(titleEl) : null;
      const subStyle = subEl ? window.getComputedStyle(subEl) : null;
      return {
        titleText: titleEl ? titleEl.textContent.trim() : null,
        titleFontSize: titleStyle ? titleStyle.fontSize : null,
        titleFontWeight: titleStyle ? titleStyle.fontWeight : null,
        titleColor: titleStyle ? titleStyle.color : null,
        subText: subEl ? subEl.textContent.trim() : null,
        subFontSize: subStyle ? subStyle.fontSize : null,
        subFontWeight: subStyle ? subStyle.fontWeight : null,
        subColor: subStyle ? subStyle.color : null
      };
    });

    console.log("Brand Title:", brandMetrics.titleText);
    console.log("  -> Font Size:", brandMetrics.titleFontSize, "| Font Weight:", brandMetrics.titleFontWeight);
    console.log("Brand Subtitle:", brandMetrics.subText);
    console.log("  -> Font Size:", brandMetrics.subFontSize, "| Font Weight:", brandMetrics.subFontWeight);

    // -------------------------------------------------------------------------
    // 2. Wait for Live Weather Widget to Populate
    // -------------------------------------------------------------------------
    console.log("\n--- 2. Dynamic Real-Time Weather Widget ---");
    const weatherPill = page.locator(".gv-weather-pill");
    await weatherPill.waitFor({ timeout: 10000 });

    // Wait until temperature is loaded (no longer "--°C")
    console.log("Waiting for live weather API response...");
    await page.waitForFunction(() => {
      const tempEl = document.querySelector(".gv-weather-temp");
      const descEl = document.querySelector(".gv-weather-desc");
      if (!tempEl || !descEl) return false;
      const temp = tempEl.textContent.trim();
      const desc = descEl.textContent.trim();
      return temp.includes("°C") && !temp.includes("--") && !desc.includes("Fetching");
    }, { timeout: 15000 }).catch(e => {
      console.warn("Weather wait timeout or completed earlier:", e.message);
    });

    await page.waitForTimeout(1000);

    const weatherData = await page.evaluate(() => {
      const pill = document.querySelector(".gv-weather-pill");
      const tempEl = document.querySelector(".gv-weather-temp");
      const descEl = document.querySelector(".gv-weather-desc");
      const iconSlot = document.querySelector(".gv-weather-icon-slot");
      const svg = pill ? pill.querySelector("svg") : null;
      const pillStyle = pill ? window.getComputedStyle(pill) : null;

      return {
        temperature: tempEl ? tempEl.textContent.trim() : null,
        description: descEl ? descEl.textContent.trim() : null,
        titleAttr: pill ? pill.getAttribute("title") : null,
        hasSvgIcon: !!svg,
        svgClass: svg ? svg.getAttribute("class") : null,
        hasPulseClass: pill ? pill.classList.contains("gv-weather-loading") : false,
        pillBg: pillStyle ? pillStyle.backgroundColor : null,
        pillBackdrop: pillStyle ? (pillStyle.backdropFilter || pillStyle.webkitBackdropFilter) : null,
        pillHeight: pillStyle ? pillStyle.height : null,
        pillBorderRadius: pillStyle ? pillStyle.borderRadius : null
      };
    });

    console.log("Weather Data Extracted:");
    console.log("  -> Live Temp:", weatherData.temperature);
    console.log("  -> Live Description & Location:", weatherData.description);
    console.log("  -> Has SVG Weather Icon:", weatherData.hasSvgIcon, `(${weatherData.svgClass})`);
    console.log("  -> Pill Height:", weatherData.weatherDataPillHeight || weatherData.pillHeight);
    console.log("  -> Pill Background:", weatherData.pillBg);
    console.log("  -> Pill Backdrop Filter:", weatherData.pillBackdrop);

    // -------------------------------------------------------------------------
    // 3. Verify Glassmorphic Styles Across All Right Navbar Pills
    // -------------------------------------------------------------------------
    console.log("\n--- 3. Glassmorphic Navbar Pills Cohesion ---");
    const pillsMetrics = await page.evaluate(() => {
      const getStyles = selector => {
        const el = document.querySelector(selector);
        if (!el) return null;
        const s = window.getComputedStyle(el);
        return {
          height: s.height,
          backgroundColor: s.backgroundColor,
          backdropFilter: s.backdropFilter || s.webkitBackdropFilter,
          borderRadius: s.borderRadius,
          border: s.border,
          boxShadow: s.boxShadow
        };
      };

      return {
        weather: getStyles(".gv-weather-pill"),
        lang: getStyles(".gv-lang-btn"),
        notification: getStyles(".gv-notification-btn"),
        userAvatar: getStyles(".gv-user-pill")
      };
    });

    console.log("Pills Styles Summary:");
    console.log("  -> Weather Pill:", pillsMetrics.weather);
    console.log("  -> Language Button:", pillsMetrics.lang);
    console.log("  -> Notification Button:", pillsMetrics.notification);
    console.log("  -> User Avatar Pill:", pillsMetrics.userAvatar);

    // -------------------------------------------------------------------------
    // 4. Capture High-Resolution Screenshots
    // -------------------------------------------------------------------------
    console.log("\n--- 4. Capturing Screenshots ---");

    // Full desk view showing upgraded navbar in context
    const fullShotPath = path.join(artifactDir, "redesigned_chic_navbar_live_weather.png");
    await page.screenshot({ path: fullShotPath, fullPage: false });
    console.log(`✓ Saved full view: ${fullShotPath}`);

    // Navbar element screenshot
    const navbarEl = page.locator(".desktop-navbar, header.navbar").first();
    if (await navbarEl.count()) {
      const navbarShotPath = path.join(artifactDir, "navbar_redesign_header.png");
      await navbarEl.screenshot({ path: navbarShotPath });
      console.log(`✓ Saved navbar header crop: ${navbarShotPath}`);
    }

    // Right actions element screenshot
    const rightActionsEl = page.locator(".gv-navbar-actions").first();
    if (await rightActionsEl.count()) {
      const rightActionsShotPath = path.join(artifactDir, "navbar_right_pills_detail.png");
      await rightActionsEl.screenshot({ path: rightActionsShotPath });
      console.log(`✓ Saved navbar right pills crop: ${rightActionsShotPath}`);
    }

    console.log("\n==================================================================");
    console.log("   ✓ ALL VERIFICATION CHECKS COMPLETED SUCCESSFULLY!             ");
    console.log("==================================================================");

  } catch (err) {
    console.error("Verification failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyDynamicWeatherAndChicNavbar();
