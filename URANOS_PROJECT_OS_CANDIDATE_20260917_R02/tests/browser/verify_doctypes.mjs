import { chromium } from "playwright";

async function verifyDocTypes() {
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || "/usr/bin/google-chrome";
  const browser = await chromium.launch({
    headless: true,
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });

  const page = await browser.newPage();
  await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
  await page.fill("#loginEmail", "Administrator");
  await page.fill("#loginPassword", "Password123!");
  await page.click("#btnContinue");
  await page.waitForURL(/\/desk|\/app/);

  const res = await page.evaluate(async () => {
    const fetchDoc = (doctype, fields) => new Promise(resolve => {
      frappe.call({
        method: "frappe.client.get_list",
        args: { doctype, fields, limit_page_length: 5 },
        callback: r => resolve({ success: true, count: r.message ? r.message.length : 0, first: r.message ? r.message[0] : null }),
        error: err => resolve({ success: false, error: err })
      });
    });

    const wpRes = await fetchDoc("URANOS Work Package", ["name", "code", "title", "project", "status", "qty_planned", "uom"]);
    const ncrRes = await fetchDoc("URANOS NCR", ["name", "project", "status", "severity"]);

    return { wpRes, ncrRes };
  });

  console.log("DocTypes verification:", JSON.stringify(res, null, 2));
  await browser.close();
}

verifyDocTypes();
