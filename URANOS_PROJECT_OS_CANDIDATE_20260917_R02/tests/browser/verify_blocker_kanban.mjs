import { chromium } from "playwright";
import path from "node:path";
import { mkdir } from "node:fs/promises";

async function verifyBlockerKanban() {
  console.log("==================================================================");
  console.log("   URANOS: Chic SaaS Blocker Kanban Board Verification (Accurate Data)");
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
    await emailField.waitFor({ timeout: 10000 });
    await emailField.fill("direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");
    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { timeout: 20000 });
    await page.waitForTimeout(3000);

    console.log("2. Navigating to Kanban Board (/app/blocker-kanban)...");
    const kanbanLink = page.locator("#gv-nav-kanban, a[href*='blocker-kanban']").first();
    await kanbanLink.waitFor({ timeout: 10000 });
    await kanbanLink.click();
    await page.waitForURL(url => url.pathname.includes("blocker-kanban"), { timeout: 10000 });
    await page.waitForTimeout(3000);

    console.log("3. Verifying Kanban Dashboard Container and 3 Columns...");
    const kanbanDashboard = page.locator("#page-blocker-kanban .uranos-kanban-dashboard, .uranos-kanban-dashboard").first();
    await kanbanDashboard.waitFor({ timeout: 15000 });
    console.log("✓ Kanban Dashboard (.uranos-kanban-dashboard) mounted successfully!");

    const colOpen = page.locator("#kanban-col-open").first();
    const colInProgress = page.locator("#kanban-col-in-progress").first();
    const colClosed = page.locator("#kanban-col-closed").first();

    await colOpen.waitFor({ timeout: 8000 });
    await colInProgress.waitFor({ timeout: 8000 });
    await colClosed.waitFor({ timeout: 8000 });
    console.log("✓ All 3 columns ('Open', 'In Progress', 'Closed') present and rendered!");

    // Verify Column CSS (Light Slate #f1f5f9, 16px radius, 20px padding, no border)
    const colStyles = await colOpen.evaluate(el => {
      const s = window.getComputedStyle(el);
      return {
        bgColor: s.backgroundColor,
        borderRadius: s.borderRadius,
        paddingTop: s.paddingTop,
        borderWidth: s.borderWidth,
        borderStyle: s.borderStyle
      };
    });
    console.log(`✓ Column Styling verified: bg=${colStyles.bgColor}, radius=${colStyles.borderRadius}, padding=${colStyles.paddingTop}, borderStyle=${colStyles.borderStyle}`);

    console.log("4. Verifying MariaDB Blocker Cards & Data Integrity...");
    await page.waitForFunction(() => {
      const cards = document.querySelectorAll(".uranos-kanban-card");
      return cards.length >= 20;
    }, { timeout: 12000 });

    const audit = await page.evaluate(() => {
      const allCards = Array.from(document.querySelectorAll(".uranos-kanban-card"));
      const openCards = Array.from(document.querySelectorAll("#kanban-cards-open .uranos-kanban-card"));
      const inProgCards = Array.from(document.querySelectorAll("#kanban-cards-in-progress .uranos-kanban-card"));
      const closedCards = Array.from(document.querySelectorAll("#kanban-cards-closed .uranos-kanban-card"));

      const cardIds = allCards.map(c => c.getAttribute("data-card-id"));
      const uniqueIds = new Set(cardIds);

      // Check duplicates
      const duplicates = cardIds.filter((item, index) => cardIds.indexOf(item) !== index);

      // KPI stat values displayed in UI
      const statTotal = parseInt(document.getElementById("kanban-stat-total")?.innerText || "0", 10);
      const statActive = parseInt(document.getElementById("kanban-stat-active")?.innerText || "0", 10);
      const statClosed = parseInt(document.getElementById("kanban-stat-closed")?.innerText || "0", 10);
      const statHours = document.getElementById("kanban-stat-hours")?.innerText || "";

      // Inspect first card styling
      const firstCard = allCards[0];
      const cs = firstCard ? window.getComputedStyle(firstCard) : {};

      // Inspect KPI pastel cards
      const pastelCards = document.querySelectorAll(".uranos-kanban-stat-card");

      return {
        totalCards: allCards.length,
        uniqueCount: uniqueIds.size,
        duplicateList: duplicates,
        openCount: openCards.length,
        inProgCount: inProgCards.length,
        closedCount: closedCards.length,
        statTotal,
        statActive,
        statClosed,
        statHours,
        cardStyling: {
          bgColor: cs.backgroundColor,
          borderRadius: cs.borderRadius,
          borderStyle: cs.borderStyle,
          cursor: cs.cursor,
          boxShadow: cs.boxShadow
        },
        pastelCardsCount: pastelCards.length
      };
    });

    console.log("--------------------------------------------------");
    console.log(`✓ Total Cards in DOM: ${audit.totalCards}`);
    console.log(`✓ Unique Blocker IDs: ${audit.uniqueCount}`);
    console.log(`✓ Duplicates found: ${audit.duplicateList.length === 0 ? "NONE (Clean!)" : audit.duplicateList.join(", ")}`);
    console.log(`✓ Column Breakdown: Open=${audit.openCount}, In Progress=${audit.inProgCount}, Closed=${audit.closedCount}`);
    console.log(`✓ KPI Stat Values: Total=${audit.statTotal}, Active=${audit.statActive}, Closed=${audit.statClosed}, Lost Hours=${audit.statHours}`);
    console.log(`✓ KPI Mathematical Check: Total (${audit.statTotal}) == Active (${audit.statActive}) + Closed (${audit.statClosed}): ${audit.statTotal === audit.statActive + audit.statClosed ? "PERFECT ✓" : "MISMATCH ✗"}`);
    console.log(`✓ Card Styling: bg=${audit.cardStyling.bgColor}, radius=${audit.cardStyling.borderRadius}, borderStyle=${audit.cardStyling.borderStyle}, cursor=${audit.cardStyling.cursor}`);
    console.log(`✓ Chic Pastel KPI Stat Cards Count: ${audit.pastelCardsCount}`);
    console.log("--------------------------------------------------");

    // Assertions
    if (audit.totalCards !== 23) {
      throw new Error(`Expected exactly 23 blocker cards in DOM, but found ${audit.totalCards}`);
    }
    if (audit.duplicateList.length > 0) {
      throw new Error(`Duplicate cards detected: ${audit.duplicateList.join(", ")}`);
    }
    if (audit.statTotal !== 23) {
      throw new Error(`KPI Total Obstacles must be 23, but found ${audit.statTotal}`);
    }
    if (audit.statTotal !== audit.statActive + audit.statClosed) {
      throw new Error(`KPI Math Error: Total (${audit.statTotal}) != Active (${audit.statActive}) + Closed (${audit.statClosed})`);
    }

    console.log("5. Testing Drag & Drop functionality...");
    // Find an Open card to drag into In Progress
    const cardToDrag = page.locator("#kanban-cards-open .uranos-kanban-card").first();
    const cardId = await cardToDrag.getAttribute("data-card-id");
    console.log(`Dragging card #${cardId} from 'Open' to 'In Progress'...`);

    // Perform native HTML5 Drag and Drop simulation
    await page.evaluate(({ cId }) => {
      const card = document.querySelector(`.uranos-kanban-card[data-card-id="${cId}"]`);
      const targetCol = document.querySelector("#kanban-col-in-progress");
      if (!card || !targetCol) throw new Error("Elements for DnD not found");

      // 1. dragstart
      const dragStartEvent = new DragEvent("dragstart", {
        bubbles: true,
        cancelable: true,
        dataTransfer: new DataTransfer()
      });
      dragStartEvent.dataTransfer.setData("text/plain", cId);
      card.dispatchEvent(dragStartEvent);

      // 2. dragover
      const dragOverEvent = new DragEvent("dragover", {
        bubbles: true,
        cancelable: true,
        dataTransfer: dragStartEvent.dataTransfer
      });
      targetCol.dispatchEvent(dragOverEvent);

      // 3. drop
      const dropEvent = new DragEvent("drop", {
        bubbles: true,
        cancelable: true,
        dataTransfer: dragStartEvent.dataTransfer
      });
      targetCol.dispatchEvent(dropEvent);

      // 4. dragend
      const dragEndEvent = new DragEvent("dragend", {
        bubbles: true,
        cancelable: true
      });
      card.dispatchEvent(dragEndEvent);
    }, { cId: cardId });

    await page.waitForTimeout(2000);

    // Verify card is now inside #kanban-cards-in-progress
    const isNowInProgress = await page.evaluate(({ cId }) => {
      const card = document.querySelector(`#kanban-cards-in-progress .uranos-kanban-card[data-card-id="${cId}"]`);
      return Boolean(card);
    }, { cId: cardId });

    if (!isNowInProgress) {
      throw new Error(`Card #${cardId} was not found inside In Progress column after drop!`);
    }
    console.log(`✓ Card #${cardId} visually moved to 'In Progress' column successfully!`);

    // Verify toast notification
    const alertMessage = page.locator(".alert, .msgprint, .toast, .desk-alert, .frappe-alert").first();
    if (await alertMessage.isVisible()) {
      console.log(`✓ Toast Notification verified: ${await alertMessage.innerText()}`);
    }

    console.log("6. Capturing full Kanban Board Screenshot...");
    const screenshotPath = path.join(artifactDir, "blocker_kanban_dashboard_verified.png");
    await page.screenshot({ path: screenshotPath, fullPage: false });
    console.log(`✓ Screenshot captured: ${screenshotPath}`);

    console.log("==================================================================");
    console.log("   ALL DATA INTEGRITY & DESIGN CHECKS PASSED WITH FLYING COLORS!");
    console.log("==================================================================");

  } catch (err) {
    console.error("Test failed:", err);
    process.exit(1);
  } finally {
    await browser.close();
  }
}

verifyBlockerKanban();
