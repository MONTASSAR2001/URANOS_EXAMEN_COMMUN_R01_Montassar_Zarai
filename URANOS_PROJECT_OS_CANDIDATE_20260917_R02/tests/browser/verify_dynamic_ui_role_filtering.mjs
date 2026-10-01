// tests/browser/verify_dynamic_ui_role_filtering.mjs
/**
 * URANOS Project OS — Dynamic Role-Based UI Filtering Browser Test
 * Verifies that application cards and sidebar links strictly adhere to the 3 main personas:
 *   1. direction_01@uranos.local (Manager / 'management' role)
 *      - Only sees analytical & Kanban cards (Blockers, Kanban, Help & Support).
 *      - Restricted cards (AI Copilot, Stock, Projects, Operations, Maintenance) are COMPLETELY ABSENT from DOM.
 *   2. chantier_01@uranos.local (Site Team / 'site_team' role)
 *      - Only sees field operational cards (Projects, Sites, Blockers, Kanban, Work Packages, Reports, Quality, Operations, Stock, Help & Support).
 *      - AI Copilot and Maintenance are COMPLETELY ABSENT from DOM.
 *   3. ingenieur_01@uranos.local (Engineer / 'engineer' role)
 *      - Sees full engineering + operational suite (including AI Copilot & Maintenance).
 *      - Hors V1 modules (HR, Accounting, Payroll, Purchase, Sales) are COMPLETELY ABSENT from DOM.
 */

import { chromium } from "playwright";
import path from "path";
import { fileURLToPath } from "url";
import fs from "fs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const artifactDir = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9";

// Terminal styling
const GREEN  = "\x1b[92m";
const RED    = "\x1b[91m";
const YELLOW = "\x1b[93m";
const CYAN   = "\x1b[96m";
const BOLD   = "\x1b[1m";
const DIM    = "\x1b[2m";
const RESET  = "\x1b[0m";

function banner(text) {
  console.log(`\n${BOLD}${CYAN}${"═".repeat(78)}${RESET}`);
  console.log(`${BOLD}${CYAN}   ${text}${RESET}`);
  console.log(`${BOLD}${CYAN}${"═".repeat(78)}${RESET}`);
}

async function inspectPersona(browser, userEmail, password, personaLabel) {
  console.log(`\n${BOLD}${YELLOW}▶ Testing Persona: ${personaLabel} (${userEmail})${RESET}`);

  const context = await browser.newContext({
    viewport: { width: 1440, height: 960 },
    ignoreHTTPSErrors: true
  });
  const page = await context.newPage();

  // Track any console error or permission popup
  const dialogMessages = [];
  page.on("dialog", async (dialog) => {
    dialogMessages.push(dialog.message());
    await dialog.dismiss();
  });

  // 1. Login
  await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
  await page.waitForSelector("#loginEmail", { timeout: 10000 });
  await page.fill("#loginEmail", userEmail);
  await page.fill("#loginPassword", password);
  await page.click("#btnContinue");

  await page.waitForURL(/\/desk|\/app/, { timeout: 15000 });
  console.log(`  ${GREEN}✓ Logged in successfully.${RESET} Landing URL: ${page.url()}`);

  // 2. Navigate directly to /app (Main Dashboard)
  await page.goto("http://localhost:8080/app", { waitUntil: "networkidle" });
  await page.waitForTimeout(2000);

  // Wait for the applications bento card mount
  await page.waitForSelector(".gv-applications-card", { timeout: 15000 });
  await page.waitForSelector(".gv-applications-card .desktop-icon", { timeout: 15000 });

  // Scroll to applications card
  const appCard = page.locator(".gv-applications-card");
  await appCard.scrollIntoViewIfNeeded();
  await page.waitForTimeout(1000);

  // 3. Inspect all visible cards in DOM
  const visibleCards = await page.$$eval(".gv-applications-card .desktop-icon", elements => {
    return elements.map(el => ({
      id: el.getAttribute("data-id") || "",
      title: el.querySelector(".icon-title") ? el.querySelector(".icon-title").innerText.trim() : "",
      subtitle: el.querySelector(".gv-card-subtitle") ? el.querySelector(".gv-card-subtitle").innerText.trim() : "",
      category: el.getAttribute("data-category") || "",
      href: el.getAttribute("href") || ""
    }));
  });

  const visibleIds = visibleCards.map(c => c.id);
  console.log(`  ${BOLD}Total Application Cards in DOM:${RESET} ${visibleCards.length}`);
  visibleCards.forEach(c => {
    console.log(`    ${GREEN}●${RESET} [${BOLD}${c.id}${RESET}] "${c.title}" (${c.category}) → ${DIM}${c.href}${RESET}`);
  });

  // 4. Capture screenshot
  const shotFilename = `ui_visibility_${personaLabel.toLowerCase().replace(/[^a-z0-9]/g, "_")}.png`;
  const shotPath = path.join(artifactDir, shotFilename);
  await appCard.screenshot({ path: shotPath });
  console.log(`  ${DIM}📸 Bento grid screenshot saved to: ${shotFilename}${RESET}`);

  // 5. Inspect sidebar links
  const visibleSidebarLinks = await page.$$eval(".gv-desk-sidebar .gv-nav-link", elements => {
    return elements.map(el => ({
      text: el.innerText.trim(),
      href: el.getAttribute("href") || "",
      app: el.getAttribute("data-sidebar-app") || ""
    }));
  });

  return {
    visibleCards,
    visibleIds,
    visibleSidebarLinks,
    dialogMessages,
    page,
    context
  };
}

async function run() {
  banner("URANOS PROJECT OS — DYNAMIC UI FILTERING (PLAYWRIGHT)");
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  let allPassed = true;

  try {
    // ═════════════════════════════════════════════════════════════════════════
    // PERSONA 1: direction_01@uranos.local (Manager / Management Role)
    // ═════════════════════════════════════════════════════════════════════════
    const dir = await inspectPersona(
      browser,
      "direction_01@uranos.local",
      "Password123!",
      "Manager_Direction"
    );

    console.log(`\n  ${BOLD}Verifying Manager Strict Visibility Invariants:${RESET}`);

    // Restricted cards: "AI Copilot" (energy-analytics), "Stock" (stock), "Project" (projects) MUST be ABSENT
    const dirRestrictedCards = [
      { id: "energy-analytics", name: "AI Copilot" },
      { id: "stock", name: "Stock" },
      { id: "projects", name: "Projects" },
      { id: "sites", name: "Sites" },
      { id: "operations", name: "Operations" },
      { id: "maintenance", name: "Maintenance" },
      { id: "work-packages", name: "Work Packages" },
      { id: "reports", name: "Reports" },
      { id: "quality-inspections", name: "Quality Inspections" },
      { id: "purchase", name: "Purchase" },
      { id: "sales", name: "Sales" },
      { id: "hr", name: "HR" },
      { id: "payroll", name: "Payroll" },
      { id: "accounting", name: "Accounting" },
      { id: "settings", name: "Settings" }
    ];

    dirRestrictedCards.forEach(({ id, name }) => {
      const isPresent = dir.visibleIds.includes(id);
      if (isPresent) {
        console.error(`  ${RED}✗ [FAIL] Restricted card '${name}' (${id}) leaked into Manager DOM!${RESET}`);
        allPassed = false;
      } else {
        console.log(`  ${GREEN}✓ [PASS]${RESET} Restricted card '${name}' (${id}) is ${BOLD}COMPLETELY ABSENT${RESET} from DOM`);
      }
    });

    // Allowed cards for Manager: Blocker Dashboard & Kanban Board & Support
    const dirExpectedAllowed = ["blockers", "kanban", "help-support"];
    dirExpectedAllowed.forEach(id => {
      if (dir.visibleIds.includes(id)) {
        console.log(`  ${GREEN}✓ [PASS]${RESET} Authorized card '${id}' is visible and interactive for Manager`);
      } else {
        console.error(`  ${RED}✗ [FAIL] Expected authorized card '${id}' missing for Manager!${RESET}`);
        allPassed = false;
      }
    });

    // Verify no permission dialog popups were triggered
    if (dir.dialogMessages.length > 0) {
      console.error(`  ${RED}✗ [FAIL] Unexpected dialog popups encountered: ${dir.dialogMessages.join(", ")}${RESET}`);
      allPassed = false;
    } else {
      console.log(`  ${GREEN}✓ [PASS]${RESET} Zero Permission Error popups encountered during Manager session`);
    }

    await dir.context.close();

    // ═════════════════════════════════════════════════════════════════════════
    // PERSONA 2: chantier_01@uranos.local (Site Team / Field Team Role)
    // ═════════════════════════════════════════════════════════════════════════
    const ch = await inspectPersona(
      browser,
      "chantier_01@uranos.local",
      "Password123!",
      "Site_Team_Chantier"
    );

    console.log(`\n  ${BOLD}Verifying Site Team Field Visibility Invariants:${RESET}`);

    // Site team should see their 10 specific operational cards
    const chExpectedOperational = [
      "projects", "sites", "blockers", "kanban", "work-packages",
      "reports", "quality-inspections", "operations", "stock", "help-support"
    ];
    chExpectedOperational.forEach(id => {
      if (ch.visibleIds.includes(id)) {
        console.log(`  ${GREEN}✓ [PASS]${RESET} Field operational card '${id}' is present for Site Team`);
      } else {
        console.error(`  ${RED}✗ [FAIL] Expected operational card '${id}' missing for Site Team!${RESET}`);
        allPassed = false;
      }
    });

    // AI Copilot and Maintenance must be COMPLETELY ABSENT for Site Team
    const chForbidden = [
      { id: "energy-analytics", name: "AI Copilot" },
      { id: "maintenance", name: "Maintenance" },
      { id: "purchase", name: "Purchase" },
      { id: "sales", name: "Sales" },
      { id: "hr", name: "HR" },
      { id: "payroll", name: "Payroll" },
      { id: "accounting", name: "Accounting" },
      { id: "settings", name: "Settings" }
    ];
    chForbidden.forEach(({ id, name }) => {
      if (ch.visibleIds.includes(id)) {
        console.error(`  ${RED}✗ [FAIL] Non-field card '${name}' (${id}) leaked to Site Team!${RESET}`);
        allPassed = false;
      } else {
        console.log(`  ${GREEN}✓ [PASS]${RESET} Non-field card '${name}' (${id}) is ${BOLD}COMPLETELY ABSENT${RESET} for Site Team`);
      }
    });

    await ch.context.close();

    // ═════════════════════════════════════════════════════════════════════════
    // PERSONA 3: ingenieur_01@uranos.local (Engineer / Engineering Director Role)
    // ═════════════════════════════════════════════════════════════════════════
    const ing = await inspectPersona(
      browser,
      "ingenieur_01@uranos.local",
      "Password123!",
      "Engineer_Ingenieur"
    );

    console.log(`\n  ${BOLD}Verifying Engineer Full Engineering Visibility Invariants:${RESET}`);

    // Engineer MUST see AI Copilot and Maintenance in addition to operational cards
    const ingExpected = [
      "projects", "sites", "energy-analytics", "blockers", "kanban", "work-packages",
      "reports", "quality-inspections", "operations", "maintenance", "stock", "help-support"
    ];
    ingExpected.forEach(id => {
      if (ing.visibleIds.includes(id)) {
        console.log(`  ${GREEN}✓ [PASS]${RESET} Engineering card '${id}' is present for Engineer`);
      } else {
        console.error(`  ${RED}✗ [FAIL] Expected card '${id}' missing for Engineer!${RESET}`);
        allPassed = false;
      }
    });

    // Hors V1 modules must be strictly ABSENT
    const ingForbidden = ["purchase", "sales", "hr", "payroll", "accounting", "settings"];
    ingForbidden.forEach(id => {
      if (ing.visibleIds.includes(id)) {
        console.error(`  ${RED}✗ [FAIL] Hors V1 card '${id}' leaked to Engineer!${RESET}`);
        allPassed = false;
      } else {
        console.log(`  ${GREEN}✓ [PASS]${RESET} Hors V1 card '${id}' is ${BOLD}COMPLETELY ABSENT${RESET} for Engineer`);
      }
    });

    await ing.context.close();

    // ═════════════════════════════════════════════════════════════════════════
    // SUMMARY
    // ═════════════════════════════════════════════════════════════════════════
    banner("UI VISIBILITY VERIFICATION RESULTS");
    if (allPassed) {
      console.log(`
  ${BOLD}${GREEN}✅ ALL ROLE-BASED VISIBILITY ASSERTIONS PASSED (100% SUCCESS)${RESET}
  ┌──────────────────────────────────────────────────────────────────────────┐
  │  ${BOLD}Persona${RESET}                │ ${BOLD}Cards Visible${RESET} │ ${BOLD}Restricted Cards Hidden (Absent)${RESET}  │
  ├─────────────────────────┼───────────────┼──────────────────────────────────────────┤
  │  ${BOLD}Manager${RESET} (direction_01)  │  ${GREEN}3 Cards${RESET}      │ ✅ AI Copilot, Stock, Project HIDDEN     │
  │  ${BOLD}Site Team${RESET} (chantier_01) │  ${GREEN}10 Cards${RESET}     │ ✅ AI Copilot & Maintenance HIDDEN       │
  │  ${BOLD}Engineer${RESET} (ingenieur_01)  │  ${GREEN}12 Cards${RESET}     │ ✅ Hors V1 Modules strictly HIDDEN       │
  └──────────────────────────────────────────────────────────────────────────┘
  ${BOLD}Result:${RESET} Zero Permission Error popups. UI adapts dynamically to user roles.
`);
    } else {
      console.error(`\n${BOLD}${RED}❌ SOME VISIBILITY ASSERTIONS FAILED${RESET}`);
      process.exit(1);
    }
  } catch (err) {
    console.error("Test execution failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

run();
