// Retry wrapper: node retry.cjs <url> <out.png> <w> <h> <wait>
// Reverts to plain page.screenshot with short timeout; retries up to 8x.
const { chromium } = require('playwright');
const fs = require('fs');
const exec = require('child_process').execSync;

(async () => {
  const [url, out, w, h, wait = '4000'] = process.argv.slice(2);
  const voters = [
    '/home/jack/.cache/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-linux64/chrome-headless-shell',
    '/snap/bin/chromium',
  ];
  for (let attempt = 1; attempt <= 8; attempt++) {
    let browser;
    try {
      browser = await chromium.launch({
        executablePath: voters[attempt % voters.length],
        args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--no-proxy-server', '--ignore-certificate-errors'],
      });
      const page = await browser.newPage({
        viewport: { width: parseInt(w, 10), height: parseInt(h, 10) },
        deviceScaleFactor: 2,
      });
      await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 }).catch(() => {});
      await page.waitForTimeout(parseInt(wait, 10));
      const buf = await page.screenshot({ timeout: 10000 });
      await browser.close();
      fs.writeFileSync(out, buf);
      if (fs.existsSync(out) && fs.statSync(out).size > 5000) {
        console.log('SHOT_OK ' + out + ' ' + buf.length + ' attempt ' + attempt);
        process.exit(0);
      }
    } catch (e) {
      if (browser) await browser.close().catch(() => {});
      console.log('attempt ' + attempt + ' failed: ' + String(e.message).slice(0, 120));
    }
  }
  console.error('SHOT_FAIL all attempts');
  process.exit(1);
})();