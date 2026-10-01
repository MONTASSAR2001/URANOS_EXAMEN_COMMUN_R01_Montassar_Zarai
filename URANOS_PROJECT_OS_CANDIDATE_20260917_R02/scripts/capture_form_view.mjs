import { chromium } from "playwright";
import path from "path";

async function main() {
  const browser = await chromium.launch({
    headless: true,
    executablePath: "/usr/bin/google-chrome",
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-gpu-sandbox"]
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

  await page.goto("http://localhost:8080/login", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(1000);

  const emailField = page.locator("#loginEmail, #login_email, input[name='usr']").first();
  const isLoginVisible = await emailField.isVisible({ timeout: 5000 }).catch(() => false);
  if (isLoginVisible) {
    await emailField.fill("direction_01@uranos.local");
    await page.fill("#loginPassword, #login_password, input[name='pwd']", "Password123!");
    await page.click("#btnContinue, .btn-login, button[type='submit']");
    await page.waitForURL(url => url.pathname.includes("/app") || url.pathname.includes("/desk"), { waitUntil: "domcontentloaded", timeout: 25000 });
  }

  await page.goto("http://localhost:8080/app/project/PROJ-0016", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000);

  const formInfo = await page.evaluate(() => {
    return {
      cur_route: frappe.get_route ? frappe.get_route() : null,
      sections: Array.from(document.querySelectorAll(".form-section")).map(s => ({
        class: s.className,
        label: s.querySelector(".section-head") ? s.querySelector(".section-head").innerText.trim() : null,
        fields: Array.from(s.querySelectorAll(".frappe-control")).map(f => f.getAttribute("data-fieldname"))
      }))
    };
  });
  console.log("FORM_INFO:", JSON.stringify(formInfo, null, 2));

  const outPath = "/home/montassar/.gemini/antigravity-ide/brain/cc423a17-97c7-49ed-b2ed-3cfe56de2dc9/current_project_form_view.png";
  await page.screenshot({ path: outPath, fullPage: false });
  console.log("Screenshot written to:", outPath);
  await browser.close();
}

main().catch(console.error);
