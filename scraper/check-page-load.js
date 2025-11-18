const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  console.log('Loading Flashscore football page...');
  await page.goto('https://www.flashscore.com/football/', { waitUntil: 'networkidle2' });

  console.log('Waiting 5 seconds...');
  await new Promise(r => setTimeout(r, 5000));

  const pageInfo = await page.evaluate(() => {
    const tabs = document.querySelectorAll('.filters__tab');
    const matches = document.querySelectorAll('.event__match');

    return {
      tabCount: tabs.length,
      tabs: Array.from(tabs).map(t => t.textContent?.trim()).slice(0, 5),
      matchCount: matches.length,
      pageTitle: document.title,
      url: window.location.href
    };
  });

  console.log('\nPage Info:');
  console.log(`  Title: ${pageInfo.pageTitle}`);
  console.log(`  URL: ${pageInfo.url}`);
  console.log(`  Match count: ${pageInfo.matchCount}`);
  console.log(`  Tab count: ${pageInfo.tabCount}`);
  console.log(`  Tabs: ${pageInfo.tabs.join(', ')}`);

  await browser.close();
})();
