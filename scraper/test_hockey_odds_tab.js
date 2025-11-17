const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  console.log('Testing hockey odds tab interaction...\n');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox'],
    timeout: 30000,
    protocolTimeout: 30000
  });

  const page = await browser.newPage();

  try {
    console.log('1. Loading hockey page...');
    await page.goto('https://www.flashscore.com/hockey/', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    console.log('2. Checking page URL...');
    const url1 = page.url();
    console.log(`   Current URL: ${url1}`);

    console.log('3. Waiting for matches to load...');
    await page.waitForSelector('.event__match', { timeout: 15000 });

    console.log('4. Looking for all tabs and filters...');
    const tabsInfo = await page.evaluate(() => {
      const filterElements = document.querySelectorAll('[class*="filter"]');
      const buttonElements = document.querySelectorAll('button');
      const tabElements = document.querySelectorAll('[role="tab"], [role="button"]');

      const results = {
        filterCount: filterElements.length,
        buttonCount: buttonElements.length,
        tabCount: tabElements.length,
        filterSamples: Array.from(filterElements).slice(0, 5).map(el => ({
          text: el.textContent.trim().substring(0, 30),
          classList: el.className.substring(0, 100)
        })),
        buttonSamples: Array.from(buttonElements).slice(0, 5).map(el => ({
          text: el.textContent.trim().substring(0, 30),
          classList: el.className.substring(0, 100)
        }))
      };

      return results;
    });

    console.log('\nTabs and filters found:');
    console.log(JSON.stringify(tabsInfo, null, 2));

    console.log('\n5. Checking if odds are visible without clicking...');
    const oddsInfo = await page.evaluate(() => {
      const matches = document.querySelectorAll('.event__match');
      let totalOddsElements = 0;
      let matchesWithOdds = 0;

      matches.forEach((match, idx) => {
        const odds = match.querySelectorAll('[class*="odds"]');
        if (odds.length > 0) {
          matchesWithOdds++;
          totalOddsElements += odds.length;
        }
      });

      return {
        totalMatches: matches.length,
        matchesWithOdds,
        totalOddsElements,
        hasAnyOdds: totalOddsElements > 0
      };
    });

    console.log(`   Odds info: ${JSON.stringify(oddsInfo)}`);

  } catch (error) {
    console.error('Error:', error.message);
  }

  await browser.close();
})();
