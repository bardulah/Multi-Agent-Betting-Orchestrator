const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  console.log('Finding odds with actual values...\n');

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

    console.log('3. Clicking Odds tab...');
    await page.evaluate(() => {
      const filterTabs = document.querySelectorAll('.filters__tab');
      for (let tab of filterTabs) {
        if (tab.textContent.trim().toLowerCase().includes('odds')) {
          tab.click();
          return true;
        }
      }
    });

    console.log('4. Waiting 6 seconds for odds to load...');
    await new Promise(r => setTimeout(r, 6000));

    const oddsAnalysis = await page.evaluate(() => {
      const matches = document.querySelectorAll('.event__match');
      const results = [];

      for (let i = 0; i < Math.min(10, matches.length); i++) {
        const match = matches[i];
        const homeTeam = match.querySelector('.event__participant--home')?.textContent.trim();
        const awayTeam = match.querySelector('.event__participant--away')?.textContent.trim();

        // Try different selectors for odds
        const oddsDivs = match.querySelectorAll('.odds__odd');
        const oddsValues = Array.from(oddsDivs).map(odd => {
          const text = odd.textContent.trim();
          return text;
        });

        // Also try the event__odds wrapper
        const eventOdds = match.querySelector('.event__odds');
        const hasEventOdds = !!eventOdds;

        // Try to find span with numbers
        const spans = match.querySelectorAll('span');
        const numericSpans = Array.from(spans)
          .map(span => {
            const text = span.textContent.trim();
            const num = parseFloat(text);
            return !isNaN(num) && text !== '-' ? num : null;
          })
          .filter(v => v !== null);

        results.push({
          matchNum: i + 1,
          homeTeam,
          awayTeam,
          oddsDivCount: oddsDivs.length,
          oddsValues,
          hasEventOdds,
          numericSpans,
          hasAnyOdds: oddsValues.some(v => v !== '-') || numericSpans.length > 0
        });
      }

      return results;
    });

    console.log('\nOdds Analysis:');
    oddsAnalysis.forEach(match => {
      console.log(`\n${match.matchNum}. ${match.homeTeam} vs ${match.awayTeam}`);
      console.log(`   Odds divs: ${match.oddsDivCount}`);
      console.log(`   Odds values: ${JSON.stringify(match.oddsValues)}`);
      console.log(`   Has .event__odds: ${match.hasEventOdds}`);
      console.log(`   Numeric spans: ${JSON.stringify(match.numericSpans)}`);
      console.log(`   Has data: ${match.hasAnyOdds}`);
    });

  } catch (error) {
    console.error('Error:', error.message);
  }

  await browser.close();
})();
