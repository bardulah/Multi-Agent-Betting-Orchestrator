const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  console.log('Checking if basketball has odds on Flashscore...\n');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox'],
    timeout: 30000,
    protocolTimeout: 30000
  });

  const page = await browser.newPage();

  try {
    console.log('Loading basketball page...');
    await page.goto('https://www.flashscore.com/basketball/', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    console.log('Waiting for matches to load...');
    await page.waitForSelector('.event__match', { timeout: 15000 });

    console.log('Looking for odds tab...');
    const tabsInfo = await page.evaluate(() => {
      const tabs = document.querySelectorAll('.filters__tab');
      return Array.from(tabs).map(t => ({
        text: t.textContent.trim(),
        classes: t.className
      })).filter((t, i) => i < 10);
    });

    console.log('Tabs found:');
    tabsInfo.forEach((t, i) => {
      console.log(`  ${i + 1}. "${t.text}"`);
    });

    console.log('\nChecking if odds tab exists...');
    const hasOddsTab = tabsInfo.some(t => t.text.toLowerCase().includes('odds'));
    console.log(`Has odds tab: ${hasOddsTab}`);

    // Try to click odds
    console.log('\nClicking odds tab if exists...');
    const clickedTab = await page.evaluate(() => {
      const tabs = document.querySelectorAll('.filters__tab');
      const oddsTab = Array.from(tabs).find(t => t.textContent.toLowerCase().includes('odds'));
      if (oddsTab) {
        oddsTab.click();
        return true;
      }
      return false;
    });

    if (clickedTab) {
      console.log('Clicked odds tab, waiting 3 seconds...');
      await new Promise(r => setTimeout(r, 3000));

      const oddsData = await page.evaluate(() => {
        const matches = document.querySelectorAll('.event__match');
        let withOdds = 0;

        for (let i = 0; i < Math.min(5, matches.length); i++) {
          const odds = matches[i].querySelectorAll('[class*="odds"]');
          if (odds.length > 0) withOdds++;
        }

        return { totalMatches: matches.length, withOdds };
      });

      console.log(`Result: ${oddsData.withOdds}/${oddsData.totalMatches} matches with odds`);
    } else {
      console.log('No odds tab found - basketball may not have odds betting on Flashscore');
    }

  } catch (error) {
    console.error('Error: ' + error.message);
  }

  await browser.close();
})();
