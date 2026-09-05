// Screenshot helper: usage: node shot.cjs <url> <out.png> <width> <height> [waitMs] [fullPage]
// Uses CDP Page.captureScreenshot directly to bypass Playwright's font-wait hang.
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [url, out, w, h, wait = 1800, fullPage = '0'] = process.argv.slice(2);
  const candidates = [
    process.env.PW_EXECUTABLE,
    '/home/jack/.cache/ms-playwright/chromium_headless_shell-1228/chrome-headless-shell-linux64/chrome-headless-shell',
    '/snap/bin/chromium',
  ].filter(Boolean);
  const browser = await chromium.launch({
    executablePath: candidates[0],
    args: ['--no-sandbox', '--disable-dev-shm-usage', '--disable-gpu', '--no-proxy-server', '--ignore-certificate-errors'],
  });
  const page = await browser.newPage({
    viewport: { width: parseInt(w, 10), height: parseInt(h, 10) },
    deviceScaleFactor: 2,
  });
  await page.route('**/*', route => {
    const rt = route.request().resourceType();
    if (rt === 'font' || rt === 'media') route.abort().catch(() => {});
    else route.continue().catch(() => {});
  });
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(parseInt(wait, 10));
  const cdp = await page.context().newCDPSession(page);
  const shot = await cdp.send('Page.captureScreenshot', {
    format: 'png',
    captureBeyondViewport: fullPage === '1',
  }).catch(e => { console.error('SHOT_FAIL cdp ' + e.message); process.exit(1); });
  await browser.close();
  const buf = Buffer.from(shot.data, 'base64');
  fs.writeFileSync(out, buf);
  if (!fs.existsSync(out) || fs.statSync(out).size < 1000) {
    console.error('SHOT_FAIL write verify failed ' + out);
    process.exit(2);
  }
  console.log('SHOT_OK ' + out + ' ' + buf.length);
})().catch(e => { console.error('SHOT_FAIL ' + e.message); process.exit(1); });