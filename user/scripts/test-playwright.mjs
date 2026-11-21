import { chromium } from "@playwright/test";

async function run() {
    console.log("Launching Chrome...");
    const browser = await chromium.launch({
        executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        headless: true,
        args: ["--no-sandbox", "--disable-setuid-sandbox"]
    });
    console.log("Browser launched. Opening page...");
    const page = await browser.newPage();
    await page.goto("http://localhost:3000", { waitUntil: "networkidle" });
    const title = await page.title();
    console.log("Page title:", title);
    await browser.close();
    console.log("Success!");
}

run().catch(console.error);
