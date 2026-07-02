const { chromium } = require('playwright');
const assert = require('assert');

async function testSection6() {
  const browser = await chromium.launch({ headless: false, slowMo: 50 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log("=== N-01: Login as member1 and trigger notification ===");
    
    // Login
    await page.goto('http://localhost:3000/login');
    await page.waitForTimeout(4000);
    await page.waitForSelector('input[id="login-email"]');
    await page.fill('input[id="login-email"]', 'thefadi384@gmail.com');
    await page.fill('input[id="login-password"]', 'Fadi@1234');
    await Promise.all([
      page.waitForURL('**/dashboard'),
      page.click('button[type="submit"]')
    ]);

    console.log("Logged in successfully.");
    
    // We expect a modal for work start if they haven't started.
    try {
      await page.waitForSelector('h2:has-text("Ready to start")', { timeout: 3000 });
      await page.click('button:has-text("Not Now")');
      console.log("Clicked 'Not Now' on modal.");
    } catch(e) {
      console.log("Modal didn't appear, moving on. They might already have a notification.");
    }
    
    // Wait for the bell badge
    await page.waitForTimeout(2000); // Give time for badge to update

    console.log("=== N-02: Open Notification Sheet ===");
    const bellBtn = await page.waitForSelector('button:has(.lucide-bell)');
    await bellBtn.click();
    
    // Check if it's a Sheet (typically slides from right, has a title 'Notifications')
    await page.waitForSelector('h2:has-text("Notifications")');
    console.log("Sheet opened successfully.");
    
    // N-03: Find work_start_missed
    console.log("=== N-03: Find work_start_missed ===");
    // Just looking for text in the sheet
    const hasMissed = await page.locator('text="Missed work start"').count();
    console.log(`Found 'Missed work start' notification: ${hasMissed > 0}`);
    
    console.log("=== N-04: Mark as read ===");
    // Notification should auto-mark as read after 2 seconds
    await page.waitForTimeout(5000);
    console.log("Waited 5 seconds for markAllRead to fire.");
    await page.screenshot({ path: 'notification_sheet_open.png' });
    
    console.log("=== N-05: Refresh and check unread count ===");
    await page.reload();
    await page.waitForURL('**/dashboard');
    await page.waitForTimeout(2000);
    
    const hasBadge = await page.locator('button:has(.lucide-bell) > div').count();
    console.log(`Unread badge count after refresh (0 means no badge): ${hasBadge}`);
    
    console.log("All tests completed!");

  } catch (error) {
    console.error("Test failed:", error);
    await page.screenshot({ path: 'notification_test_failed.png' });
  } finally {
    await browser.close();
  }
}

testSection6();
