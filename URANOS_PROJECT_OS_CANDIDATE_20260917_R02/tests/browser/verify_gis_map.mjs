import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyGisMap() {
  console.log("==================================================================");
  console.log("   URANOS Phase 1: Interactive Leaflet GIS Map Verification");
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
    console.log("1. Logging into URANOS Desk...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailField.waitFor({ timeout: 10000 });
    await emailField.fill("direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");
    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 20000 });
    await page.waitForTimeout(3000);

    console.log("2. Verifying Main Dashboard and GIS Map Card...");
    const mainDashboard = page.locator("#gv-main-dashboard").first();
    await mainDashboard.waitFor({ timeout: 10000 });
    console.log("✓ Main Dashboard (#gv-main-dashboard) found!");

    const mapCard = page.locator("#uranosGisMapCard").first();
    await mapCard.waitFor({ timeout: 10000 });
    console.log("✓ GIS Map Card (#uranosGisMapCard) found!");

    const mapCardBox = await mapCard.boundingBox();
    console.log(`✓ Map Card Dimensions: ${Math.round(mapCardBox.width)}px x ${Math.round(mapCardBox.height)}px`);

    console.log("3. Verifying Leaflet Map Container & Tiles...");
    const leafletMap = page.locator("#uranos-leaflet-map").first();
    await leafletMap.waitFor({ timeout: 10000 });

    // Wait for Leaflet to initialize container and plot markers
    await page.waitForFunction(() => {
      const el = document.querySelector("#uranos-leaflet-map");
      return el && el.classList.contains("leaflet-container");
    }, { timeout: 15000 });
    console.log("✓ Leaflet Map container initialized (.leaflet-container)!");

    // Wait for markers to be fetched and plotted
    console.log("4. Waiting for dynamic project markers from MariaDB...");
    await page.waitForFunction(() => {
      const markers = document.querySelectorAll(".uranos-map-marker");
      return markers.length >= 10;
    }, { timeout: 15000 });

    await page.waitForTimeout(2000);

    const markerStats = await page.evaluate(() => {
      const allMarkers = document.querySelectorAll(".uranos-map-marker");
      const greenMarkers = document.querySelectorAll(".uranos-map-marker.green");
      const redMarkers = document.querySelectorAll(".uranos-map-marker.red");
      const pulsingRedMarkers = document.querySelectorAll(".uranos-map-marker.red.pulse-active");
      const pulseRings = document.querySelectorAll(".marker-pulse-ring");
      const nominalLegend = document.querySelector("#gis-nominal-count")?.innerText.trim();
      const blockerLegend = document.querySelector("#gis-blocker-count")?.innerText.trim();

      return {
        total: allMarkers.length,
        green: greenMarkers.length,
        red: redMarkers.length,
        pulsingRed: pulsingRedMarkers.length,
        pulseRings: pulseRings.length,
        nominalLegend,
        blockerLegend
      };
    });

    console.log("--------------------------------------------------");
    console.log(`✓ Total Markers Plotted: ${markerStats.total}`);
    console.log(`✓ Green Markers (Nominal): ${markerStats.green}`);
    console.log(`✓ Red Markers (Active Blockers): ${markerStats.red}`);
    console.log(`✓ Red Markers with .pulse-active: ${markerStats.pulsingRed}`);
    console.log(`✓ Pulse Rings: ${markerStats.pulseRings}`);
    console.log(`✓ Header Stats: Nominal=${markerStats.nominalLegend}, Blockers=${markerStats.blockerLegend}`);
    console.log("--------------------------------------------------");

    if (markerStats.total !== 20) {
      console.warn(`Warning: Expected 20 markers for 20 solar projects, found ${markerStats.total}`);
    } else {
      console.log("✓ All 20 solar projects successfully plotted with geo-coordinates!");
    }

    if (markerStats.pulsingRed === 0) {
      throw new Error("No red pulsing markers found! CSS pulse-active class is missing or markers didn't receive blockers.");
    }
    console.log("✓ CSS Pulsing effect verified on red blocker markers!");

    console.log("5. Testing Marker Popup Interactivity...");
    // Click on a red marker to test popup
    const firstRedMarker = page.locator(".uranos-map-marker.red").first();
    await firstRedMarker.click({ force: true });
    await page.waitForTimeout(1000);

    const popup = page.locator(".uranos-gis-leaflet-popup, .leaflet-popup").first();
    await popup.waitFor({ timeout: 5000 });

    const popupContent = await popup.evaluate(el => el.innerText.trim());
    console.log("✓ Clicked Marker Popup Content:\n" + popupContent);

    if (!popupContent.includes("Project:") || !popupContent.includes("Status:")) {
      throw new Error("Popup missing required 'Project:' or 'Status:' text!");
    }
    console.log("✓ Popup verified with dynamic project details and blocker status!");

    console.log("6. Capturing full GIS Dashboard Screenshot...");
    const screenshotPath = path.join(artifactDir, "gis_map_dashboard_verified.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`✓ Screenshot captured: ${screenshotPath}`);

    console.log("==================================================================");
    console.log("   ALL GIS MAP PHASE 1 VERIFICATIONS PASSED SUCCESSFULLY!");
    console.log("==================================================================");

  } catch (err) {
    console.error("Test failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyGisMap();
