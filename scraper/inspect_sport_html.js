const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox'],
    timeout: 30000,
    protocolTimeout: 30000
  });

  const sports = [
    { name: 'football', url: 'https://www.flashscore.com/football/' },
    { name: 'basketball', url: 'https://www.flashscore.com/basketball/' },
    { name: 'tennis', url: 'https://www.flashscore.com/tennis/' },
    { name: 'hockey', url: 'https://www.flashscore.com/hockey/' }
  ];

  for (const sport of sports) {
    console.log('\n' + '='.repeat(80));
    console.log('SPORT: ' + sport.name.toUpperCase());
    console.log('='.repeat(80));

    const page = await browser.newPage();

    try {
      console.log('Loading ' + sport.name + ' page...');
      await page.goto(sport.url, { waitUntil: 'networkidle2', timeout: 30000 });

      await page.waitForSelector('.event__match', { timeout: 15000 });

      const info = await page.evaluate(() => {
        const firstMatch = document.querySelector('.event__match');
        if (!firstMatch) return { error: 'No match found' };

        // Get full HTML
        const html = firstMatch.outerHTML;

        // Check for league patterns
        const leagueSelectors = [
          '.event__league',
          '.event__leagueLabel',
          '[class*="league"]',
          '[class*="tournament"]',
          '[class*="category"]'
        ];

        const foundSelectors = {};
        leagueSelectors.forEach(sel => {
          const found = firstMatch.querySelectorAll(sel);
          if (found.length > 0) {
            foundSelectors[sel] = {
              count: found.length,
              sample: found[0].textContent.trim().substring(0, 100)
            };
          }
        });

        // Check for odds
        const oddsDivs = firstMatch.querySelectorAll('[class*="odds"]');

        // Check for time selectors
        const timeSelectors = [
          '.event__time',
          '.event__stage',
          '[class*="time"]',
          '[class*="status"]'
        ];

        const timeFound = {};
        timeSelectors.forEach(sel => {
          const found = firstMatch.querySelectorAll(sel);
          if (found.length > 0) {
            timeFound[sel] = {
              count: found.length,
              sample: found[0].textContent.trim().substring(0, 100)
            };
          }
        });

        return {
          htmlSize: html.length,
          leagueSelectors: Object.keys(foundSelectors).length > 0 ? foundSelectors : 'NONE FOUND',
          oddsDivs: oddsDivs.length,
          timeSelectors: Object.keys(timeFound).length > 0 ? timeFound : 'NONE FOUND',
          htmlSnippet: html.substring(0, 500)
        };
      });

      console.log('\nHTML Analysis:');
      console.log(JSON.stringify(info, null, 2));

    } catch (error) {
      console.log('Error: ' + error.message);
    }

    await page.close();
  }

  await browser.close();
})();
