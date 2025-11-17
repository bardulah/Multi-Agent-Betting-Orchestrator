const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  console.log('Testing hockey odds extraction...\n');
  
  const browser = await puppeteer.launch({ 
    headless: 'new', 
    args: ['--no-sandbox'],
    timeout: 30000,
    protocolTimeout: 30000
  });
  
  const page = await browser.newPage();
  
  try {
    console.log('Loading hockey page...');
    await page.goto('https://www.flashscore.com/hockey/', { 
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    
    console.log('Waiting for matches to load...');
    await page.waitForSelector('.event__match', { timeout: 15000 });
    
    console.log('Clicking odds tab...');
    const clicked = await page.evaluate(() => {
      const allTabs = document.querySelectorAll('.filters__tab, div[class*="filter"]');
      console.log(`Found ${allTabs.length} tab elements`);
      
      const oddsTab = Array.from(allTabs).find(tab => {
        const text = tab.textContent.trim().toLowerCase();
        return text === 'odds' || text.includes('odds');
      });
      
      if (oddsTab) {
        console.log('Found odds tab');
        oddsTab.click();
        return true;
      }
      return false;
    });
    
    if (clicked) {
      console.log('✓ Odds tab clicked, waiting 6 seconds for odds to load...');
      await new Promise(r => setTimeout(r, 6000));
    }
    
    // Check odds
    const oddsInfo = await page.evaluate(() => {
      const firstMatch = document.querySelector('.event__match');
      if (!firstMatch) return { error: 'No match found' };
      
      const matches = document.querySelectorAll('.event__match');
      console.log(`Total matches in DOM: ${matches.length}`);
      
      // Check first match
      const homeTeam = firstMatch.querySelector('.event__participant--home')?.textContent.trim();
      const awayTeam = firstMatch.querySelector('.event__participant--away')?.textContent.trim();
      
      const allOdds = firstMatch.querySelectorAll('.odds__odd');
      const validOdds = firstMatch.querySelectorAll('.odds__odd:not(.no-odds)');
      
      console.log(`First match: ${homeTeam} vs ${awayTeam}`);
      console.log(`Total odds divs: ${allOdds.length}`);
      console.log(`Valid odds divs: ${validOdds.length}`);
      
      // Extract values
      const values = Array.from(validOdds).map((odd, idx) => {
        const span = odd.querySelector('span');
        const text = span ? span.textContent.trim() : 'NO SPAN';
        const classes = odd.className;
        return { idx, text, classes, hasSpan: !!span };
      });
      
      return { homeTeam, awayTeam, oddsCount: allOdds.length, validOddsCount: validOdds.length, values };
    });
    
    console.log('\nResults:');
    console.log(JSON.stringify(oddsInfo, null, 2));
    
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  await browser.close();
})();
