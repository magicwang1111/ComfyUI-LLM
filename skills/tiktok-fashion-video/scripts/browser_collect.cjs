const fs = require('node:fs');

async function main() {
  const config = JSON.parse(fs.readFileSync(0, 'utf8'));
  if (!config.login && !/^\d{19}$/.test(config.pid)) throw new Error('PID must be an exact 19-digit string');
  const { chromium } = require(config.playwright_module);
  const context = await chromium.launchPersistentContext(config.profile_dir, {
    headless: !config.login,
    channel: config.channel || undefined,
    viewport: { width: 1440, height: 1100 },
    timeout: 30000,
  });
  try {
    const page = context.pages()[0] || await context.newPage();
    if (config.login) {
      await page.goto('https://seller.us.tiktokshopglobalselling.com/', { waitUntil: 'domcontentloaded', timeout: 60000 });
      await context.waitForEvent('close', { timeout: 0 });
      process.stdout.write(JSON.stringify({ stage: 'login_browser_closed' }));
      return;
    }
    const url = `https://seller.us.tiktokshopglobalselling.com/product/edit/${config.pid}?shop_region=US`;
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    try {
      await page.locator('[id^="main_image_item_"] img').first().waitFor({ timeout: 45000 });
    } catch {
      throw new Error('未读取到商品图片：请检查商品 PID、店铺访问权限，以及浏览器登录是否需要验证码。');
    }
    const product = await page.evaluate(() => ({
      url: location.href,
      title: document.querySelector('h1')?.innerText.split('\n')[0].trim(),
      images: Array.from(document.images)
        .map(image => ({ url: image.src, id: image.closest('[id]')?.id }))
        .filter(image => /^main_image_item_\d+$/.test(image.id || '')),
    }));
    const actualPid = new URL(product.url).pathname.match(/^\/product\/edit\/(\d+)$/)?.[1];
    if (actualPid !== config.pid || !product.title || !product.images.length) {
      throw new Error('商品详情页与请求 PID 不匹配，或未返回完整商品资料。');
    }
    product.images.sort((a, b) => Number(a.id.split('_').at(-1)) - Number(b.id.split('_').at(-1)));
    product.images = [...new Map(product.images.map(image => [image.id, image])).values()].slice(0, 9);
    process.stdout.write(JSON.stringify({ ...product, pid: config.pid }));
  } finally {
    await context.close();
  }
}

main().catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});
