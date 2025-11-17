const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  console.log('Inspecting hockey page structure...\n');
  
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
    
    // Get raw HTML of first match
    const firstMatchHTML = await page.evaluate(() => {
      const match = document.querySelector('.event__match');
      if (!match) return 'NO MATCH FOUND';
      return match.outerHTML.substring(0, 2000);
    });
    
    console.log('\nFirst match HTML (first 2000 chars):');
    console.log(firstMatchHTML);
    
    // Check for all potential odds containers
    const structure = await page.evaluate(() => {
      const match = document.querySelector('.event__match');
      if (!match) return { error: 'No match' };
      
      return {
        hasOddsOdd: match.querySelectorAll('.odds__odd').length,
        hasEventOdd: match.querySelectorAll('.event__odd').length,
        hasOddsWrapper: match.querySelectorAll('[class*="odds"]').length,
        allClasses: Array.from(match.querySelectorAll('div')).slice(0, 30).map(el => el.className),
        hasSpans: match.querySelectorAll('span').length,
        spanContents: Array.from(match.querySelectorAll('span')).map(s => s.textContent.trim()).filter(t => t.length > 0 && !isNaN(parseFloat(t))).slice(0, 10)
      };
    });
    
    console.log('\nStructure analysis:');
    console.log(JSON.stringify(structure, null, 2));
    
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  await browser.close();
})();
