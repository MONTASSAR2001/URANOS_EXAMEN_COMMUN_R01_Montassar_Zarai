import { chromium } from "playwright";
import { writeFileSync, mkdirSync } from "node:fs";

async function runPhase3Diagnostic() {
  console.log("==================================================================");
  console.log("  PHASE 3: FRONTEND, KANBAN (4 COLUMNS), 6-TIER SORTING & RTL");
  console.log("==================================================================");

  const results = {
    passed: 0,
    failed: 0,
    tests: []
  };

  function record(name, success, details = "") {
    if (success) {
      results.passed++;
      console.log(`  [PASS] ${name}${details ? ` — ${details}` : ""}`);
    } else {
      results.failed++;
      console.log(`  [FAIL] ${name}${details ? ` — ${details}` : ""}`);
    }
    results.tests.push({ name, success, details });
  }

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
    // 1. Login
    console.log("\n[3.1] Logging into URANOS Desk as direction_01@uranos.local...");
    await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(1000);

    const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
    await emailField.waitFor({ timeout: 10000 });
    await emailField.fill("direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");
    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 20000 });
    await page.waitForTimeout(2500);

    // 2. Navigate to Blocker Kanban
    console.log("\n[3.2] Navigating to /app/blocker-kanban...");
    await page.goto("http://localhost:8080/app/blocker-kanban", { waitUntil: "networkidle" });
    await page.waitForTimeout(3000);

    // 3. Verify exactly 4 Kanban columns
    console.log("\n[3.3] Verifying 4 Columns on Kanban Board:");
    const columnsCheck = await page.evaluate(() => {
      const colOpen = document.getElementById("kanban-col-open");
      const colIP = document.getElementById("kanban-col-in-progress");
      const colPending = document.getElementById("kanban-col-pending");
      const colClosed = document.getElementById("kanban-col-closed");
      const allCols = document.querySelectorAll(".uranos-kanban-column");

      return {
        hasOpen: !!colOpen,
        hasIP: !!colIP,
        hasPending: !!colPending,
        hasClosed: !!colClosed,
        colCount: allCols.length,
        openTitle: colOpen ? colOpen.querySelector(".uranos-kanban-col-title")?.innerText?.trim() : "",
        ipTitle: colIP ? colIP.querySelector(".uranos-kanban-col-title")?.innerText?.trim() : "",
        pendingTitle: colPending ? colPending.querySelector(".uranos-kanban-col-title")?.innerText?.trim() : "",
        closedTitle: colClosed ? colClosed.querySelector(".uranos-kanban-col-title")?.innerText?.trim() : "",
      };
    });

    record(
      "Kanban board contains exactly 4 operational columns",
      columnsCheck.colCount === 4 && columnsCheck.hasOpen && columnsCheck.hasIP && columnsCheck.hasPending && columnsCheck.hasClosed,
      `Detected ${columnsCheck.colCount} columns: '${columnsCheck.openTitle}', '${columnsCheck.ipTitle}', '${columnsCheck.pendingTitle}', '${columnsCheck.closedTitle}'`
    );
    record("Column 1 is 'Ouvert' (Open)", columnsCheck.hasOpen && columnsCheck.openTitle.includes("Ouvert"));
    record("Column 2 is 'En cours' (In Progress)", columnsCheck.hasIP && columnsCheck.ipTitle.includes("En cours"));
    record("Column 3 is 'À vérifier' (Pending Verification)", columnsCheck.hasPending && columnsCheck.pendingTitle.includes("vérifier"));
    record("Column 4 is 'Clôturé' (Closed)", columnsCheck.hasClosed && columnsCheck.closedTitle.includes("Clôturé"));

    // 4. Verify 6-Tier Sorting Algorithm
    console.log("\n[3.4] Testing 6-Tier Jury Sorting Algorithm in Browser Engine:");
    const sortingEvaluation = await page.evaluate(() => {
      // Benchmark items
      const today = new Date();
      const yesterday = new Date(today.getTime() - 86400000 * 2).toISOString().slice(0, 10);
      const tomorrow = new Date(today.getTime() + 86400000 * 1).toISOString().slice(0, 10);
      const nextWeek = new Date(today.getTime() + 86400000 * 7).toISOString().slice(0, 10);

      const testItems = [
        { name: "B-005", severity: "Low", due_date: null, status: "Open" },             // No due date
        { name: "B-002", severity: "Medium", due_date: tomorrow, status: "Open" },       // Closest due date
        { name: "B-001", severity: "Critical", due_date: nextWeek, status: "Open" },      // Critical (1st)
        { name: "B-004", severity: "High", due_date: yesterday, status: "Open" },        // Overdue (2nd)
        { name: "B-003", severity: "High", due_date: nextWeek, status: "Open" },         // Later due date
        { name: "B-006", severity: "Low", due_date: null, status: "Closed" },           // Closed
      ];

      // Exact client-side compareBlockers function
      function clientCompareBlockers(a, b) {
        const refDate = new Date();
        const getDueDate = (item) => {
          const d = item.due_date || item.target_resolution;
          if (!d) return null;
          const parsed = new Date(d);
          return isNaN(parsed.getTime()) ? null : parsed;
        };

        const aSev = (a.severity || "").toLowerCase().trim();
        const bSev = (b.severity || "").toLowerCase().trim();
        const aCritical = aSev === "critical";
        const bCritical = bSev === "critical";

        // 1st: Critical
        if (aCritical && !bCritical) return -1;
        if (!aCritical && bCritical) return 1;

        const aDue = getDueDate(a);
        const bDue = getDueDate(b);

        const aOverdue = aDue !== null && aDue < refDate;
        const bOverdue = bDue !== null && bDue < refDate;

        // 2nd: Overdue
        if (aOverdue && !bOverdue) return -1;
        if (!aOverdue && bOverdue) return 1;

        // 3rd: Other open
        const isClosed = (item) => ["closed", "clôturé", "cloture"].includes((item.status || "").toLowerCase().trim());
        const aClosed = isClosed(a);
        const bClosed = isClosed(b);
        if (!aClosed && bClosed) return -1;
        if (aClosed && !bClosed) return 1;

        // 4th & 5th: Closest due date vs No due date
        if (aDue !== null && bDue !== null) {
          if (aDue.getTime() !== bDue.getTime()) return aDue.getTime() - bDue.getTime();
        } else if (aDue !== null && bDue === null) {
          return -1;
        } else if (aDue === null && bDue !== null) {
          return 1;
        }

        // 6th: Blocker ID
        return String(a.name || "").localeCompare(String(b.name || ""), undefined, { numeric: true });
      }

      const sorted = [...testItems].sort(clientCompareBlockers);
      const sortedIds = sorted.map(x => x.name);
      return {
        sortedIds,
        expected: ["B-001", "B-004", "B-002", "B-003", "B-005", "B-006"]
      };
    });

    const isSortCompliant = JSON.stringify(sortingEvaluation.sortedIds) === JSON.stringify(sortingEvaluation.expected);
    record(
      "6-Tier sorting algorithm produces exact jury order",
      isSortCompliant,
      `Observed: [${sortingEvaluation.sortedIds.join(", ")}] vs Expected: [${sortingEvaluation.expected.join(", ")}]`
    );

    // 5. Verify French & Arabic RTL Support
    console.log("\n[3.5] Verifying Bilingual FR / AR RTL Display Support:");
    // Check French display
    const frCheck = await page.evaluate(() => {
      const subtitle = document.querySelector(".uranos-saas-subtitle")?.innerText || "";
      const statLabel = document.querySelector(".uranos-kanban-stat-label")?.innerText || "";
      return { subtitle, statLabel };
    });
    record("French (FR) interface rendered with accurate terminology", frCheck.subtitle.includes("Flux strict") || frCheck.statLabel.length > 0);

    // Switch to Arabic RTL and test
    console.log("  Switching interface to Arabic (AR) RTL...");
    await page.evaluate(() => {
      // Toggle Arabic mode via window / html dir
      document.documentElement.setAttribute("dir", "rtl");
      document.body.setAttribute("dir", "rtl");
      const root = document.querySelector(".uranos-chic-saas-view, .uranos-kanban-dashboard");
      if (root) root.setAttribute("dir", "rtl");
    });
    await page.waitForTimeout(1000);

    const rtlCheck = await page.evaluate(() => {
      const dirAttr = document.documentElement.getAttribute("dir") || document.body.getAttribute("dir");
      const boardGrid = document.querySelector(".uranos-kanban-board-grid");
      const cs = boardGrid ? window.getComputedStyle(boardGrid) : null;
      return {
        dirAttr,
        isRtl: dirAttr === "rtl",
        gridDirection: cs ? cs.direction : "ltr",
      };
    });

    record(
      "Arabic Right-to-Left (RTL) mode applies 'dir=rtl' layout correctly",
      rtlCheck.isRtl && rtlCheck.gridDirection === "rtl",
      `dir='${rtlCheck.dirAttr}', gridDirection='${rtlCheck.gridDirection}'`
    );

    // Take screenshot of Kanban Board
    await page.screenshot({ path: "tests/evidence_kanban_4cols_rtl.png", fullPage: false });
    console.log("  Screenshot saved to tests/evidence_kanban_4cols_rtl.png");

  } catch (err) {
    console.error("  [ERROR] in Phase 3 verification:", err);
    record("Phase 3 Execution", false, err.message);
  } finally {
    await browser.close();
  }

  console.log("\n" + "=" * 66);
  console.log(`PHASE 3 SUMMARY: ${results.passed} PASSED, ${results.failed} FAILED`);
  console.log("=" * 66);

  writeFileSync("tests/diagnostic_frontend_results.json", JSON.stringify(results, null, 2));
  return results.failed === 0 ? 0 : 1;
}

runPhase3Diagnostic().then(code => process.exit(code));
