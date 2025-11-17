const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  console.log('Testing clicking the Odds tab...\n');

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

    console.log('2. Waiting for matches to load...');
    await page.waitForSelector('.event__match', { timeout: 15000 });

    console.log('3. Finding and clicking Odds tab...');
    const clickedSuccess = await page.evaluate(() => {
      // Find all filter tabs
      const filterTabs = document.querySelectorAll('.filters__tab');
      console.log(`Found ${filterTabs.length} filter tabs`);

      for (let tab of filterTabs) {
        const text = tab.textContent.trim().toLowerCase();
        console.log(`Tab text: "${text}"`);

        if (text === 'odds' || text.includes('odds')) {
          console.log('Found Odds tab! Clicking...');
          tab.click();
          return true;
        }
      }
      return false;
    });

    if (clickedSuccess) {
      console.log('✓ Odds tab clicked');
      console.log('4. Waiting 4 seconds for content to load...');
      await new Promise(r => setTimeout(r, 4000));

      const oddsInfo = await page.evaluate(() => {
        const matches = document.querySelectorAll('.event__match');
        console.log(`Total matches visible: ${matches.length}`);

        let matchesWithOdds = 0;
        let totalOddsElements = 0;
        const firstMatchOdds = [];

        for (let i = 0; i < Math.min(3, matches.length); i++) {
          const match = matches[i];
          const oddsDivs = match.querySelectorAll('[class*="odds"]');
          const homeTeam = match.querySelector('.event__participant--home')?.textContent.trim();
          const awayTeam = match.querySelector('.event__participant--away')?.textContent.trim();

          console.log(`Match ${i + 1}: ${homeTeam} vs ${awayTeam} - ${oddsDivs.length} odds elements`);

          if (oddsDivs.length > 0) {
            matchesWithOdds++;
            totalOddsElements += oddsDivs.length;

            if (i === 0) {
              Array.from(oddsDivs).forEach((odd, idx) => {
                firstMatchOdds.push({
                  idx,
                  html: odd.outerHTML.substring(0, 150),
                  text: odd.textContent.trim().substring(0, 50)
                });
              });
            }
          }
        }

        return {
          matchesWithOdds,
          totalOddsElements,
          firstMatchOdds
        };
      });

      console.log('\nOdds data:');
      console.log(JSON.stringify(oddsInfo, null, 2));
    } else {
      console.log('✗ Odds tab not found');
    }

  } catch (error) {
    console.error('Error:', error.message);
  }

  await browser.close();
})();
