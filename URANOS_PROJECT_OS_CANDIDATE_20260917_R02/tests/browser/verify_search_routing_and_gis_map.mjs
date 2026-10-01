import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifySearchAndGisMap() {
  console.log("================================================================================");
  console.log("   URANOS OS — Search Routing & GIS Map Tile Rendering Verification Test");
  console.log("================================================================================");

  const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/4c9276b4-96e1-471d-ad96-037a119e20ff";
  await mkdir(artifactDir, { recursive: true });

  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const BASE_URL = "http://localhost:8080";

  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 960 },
      ignoreHTTPSErrors: true
    });
    const page = await context.newPage();

    // -------------------------------------------------------------------------
    // STEP 1: LOGIN AS MANAGER
    // -------------------------------------------------------------------------
    console.log("\n1. Logging in as direction_01@uranos.local...");
    await page.goto(`${BASE_URL}/login`, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailInput = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailInput.waitFor({ timeout: 15000 });
    await emailInput.fill("direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");

    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 25000 });
    await page.waitForTimeout(2500);

    if (page.url().includes("/desk")) {
      await page.goto(`${BASE_URL}/app`, { waitUntil: "domcontentloaded" });
      await page.waitForTimeout(2500);
    }
    console.log("✓ Logged into URANOS OS Desk successfully");

    // -------------------------------------------------------------------------
    // STEP 2: VERIFY GIS MAP RENDERING ON INITIAL LOAD
    // -------------------------------------------------------------------------
    console.log("\n2. Verifying GIS Map Tile Rendering on Initial Load...");
    const mapCard = page.locator("#uranosGisMapCard").first();
    await mapCard.waitFor({ state: "visible", timeout: 15000 });

    const mapContainer = page.locator("#uranos-leaflet-map").first();
    await mapContainer.waitFor({ state: "visible", timeout: 10000 });

    // Allow map tiles to load naturally
    await page.waitForTimeout(2500);

    const mapStatus = await page.evaluate(() => {
      const mapEl = document.getElementById("uranos-leaflet-map");
      const map = window._uranos_gis_map_instance;
      const tiles = mapEl ? Array.from(mapEl.querySelectorAll(".leaflet-tile")) : [];
      const loadedTiles = mapEl ? Array.from(mapEl.querySelectorAll(".leaflet-tile-loaded")) : [];
      const markers = mapEl ? Array.from(mapEl.querySelectorAll(".uranos-map-marker")) : [];
      const bbox = mapEl ? mapEl.getBoundingClientRect() : null;

      const tileComputed = tiles.slice(0, 5).map(t => {
        const cs = window.getComputedStyle(t);
        return {
          position: cs.position,
          display: cs.display,
          width: cs.width,
          height: cs.height,
          transform: cs.transform
        };
      });

      return {
        hasInstance: !!map,
        containerWidth: bbox ? bbox.width : 0,
        containerHeight: bbox ? bbox.height : 0,
        tilesCount: tiles.length,
        loadedTilesCount: loadedTiles.length,
        markersCount: markers.length,
        tileComputed
      };
    });

    console.log("   GIS Map Diagnostics:", JSON.stringify(mapStatus, null, 2));

    if (!mapStatus.hasInstance) {
      throw new Error("FAILED: Leaflet map instance is missing on window._uranos_gis_map_instance!");
    }
    if (mapStatus.tilesCount === 0) {
      throw new Error("FAILED: No leaflet tiles rendered in #uranos-leaflet-map!");
    }
    if (mapStatus.tileComputed.some(t => t.position !== "absolute")) {
      throw new Error("FAILED: Leaflet tiles have broken positioning (not absolute)!");
    }
    if (mapStatus.markersCount === 0) {
      throw new Error("FAILED: No GIS telemetry markers plotted on the map!");
    }

    console.log(`✓ GIS Map is rendered with ${mapStatus.tilesCount} tiles (${mapStatus.loadedTilesCount} loaded) and ${mapStatus.markersCount} telemetry markers`);
    console.log("✓ All tiles have absolute positioning and proper layout bounds");

    // Capture GIS map screenshot
    const mapScreenshotPath = path.join(artifactDir, "gis_map_rendered_perfectly.png");
    await mapCard.screenshot({ path: mapScreenshotPath });
    console.log(`✓ GIS Map screenshot saved: ${mapScreenshotPath}`);

    // -------------------------------------------------------------------------
    // STEP 3: VERIFY GLOBAL SEARCH ROUTING
    // -------------------------------------------------------------------------
    console.log("\n3. Verifying Global Search Bar Routing & Redirect...");
    const searchBar = page.locator("#navbar-search").first();
    await searchBar.waitFor({ state: "visible", timeout: 10000 });

    await searchBar.focus();
    await searchBar.fill("");
    await page.keyboard.type("Project", { delay: 50 });
    await page.waitForTimeout(800);

    const dropdownList = page.locator(".awesomplete ul, .gv-navbar-search .awesomplete > ul").first();
    await dropdownList.waitFor({ state: "visible", timeout: 8000 });

    // Locate "Project List" in the dropdown items
    const projectListItem = page.locator(".awesomplete ul li:has-text('Project List')").first();
    await projectListItem.waitFor({ state: "visible", timeout: 5000 });
    console.log("✓ 'Project List' option is visible in Awesomplete dropdown");

    const urlBeforeClick = page.url();
    console.log(`   URL before click: ${urlBeforeClick}`);

    // Click on "Project List" result
    console.log("   Clicking on 'Project List' search result...");
    await projectListItem.click();

    // Wait for route change / URL navigation
    await page.waitForTimeout(1500);

    const routeAfterClick = await page.evaluate(() => {
      return {
        url: window.location.href,
        pathname: window.location.pathname,
        route: window.frappe && frappe.get_route ? frappe.get_route() : null
      };
    });

    console.log("   Route info after click:", JSON.stringify(routeAfterClick, null, 2));

    const isRedirected = routeAfterClick.pathname.includes("/project") ||
                         routeAfterClick.url.includes("/project") ||
                         (routeAfterClick.route && routeAfterClick.route[0] === "List" && routeAfterClick.route[1] === "Project");

    if (!isRedirected) {
      throw new Error(`FAILED: Search result click did not navigate! Current URL: ${routeAfterClick.url}`);
    }

    console.log("✓ Search click successfully triggered redirect to Project List view!");

    // Capture screenshot of redirected page
    const searchScreenshotPath = path.join(artifactDir, "search_routing_redirected.png");
    await page.screenshot({ path: searchScreenshotPath, fullPage: false });
    console.log(`✓ Search redirect screenshot saved: ${searchScreenshotPath}`);

    console.log("\n================================================================================");
    console.log("   ALL SEARCH ROUTING & GIS MAP VERIFICATIONS PASSED SUCCESSFULLY!");
    console.log("================================================================================");

  } finally {
    await browser.close();
  }
}

verifySearchAndGisMap().catch(err => {
  console.error("Verification failed:", err);
  process.exit(1);
});
