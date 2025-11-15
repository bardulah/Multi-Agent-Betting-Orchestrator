const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  console.log('Starting direct hockey page test...\n');
  
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
    
    console.log('Page loaded. Checking DOM...\n');
    
    // Check various selectors
    const results = await page.evaluate(() => {
      return {
        eventMatches: document.querySelectorAll('.event__match').length,
        eventRows: document.querySelectorAll('.event__row').length,
        eventRowLinks: document.querySelectorAll('a.eventRowLink').length,
        eventParticipants: document.querySelectorAll('.event__participant').length,
        allDivs: document.querySelectorAll('div[class*="event"]').length,
        pageText: document.body.innerText.substring(0, 200)
      };
    });
    
    console.log('Results:');
    console.log(`  .event__match: ${results.eventMatches}`);
    console.log(`  .event__row: ${results.eventRows}`);
    console.log(`  a.eventRowLink: ${results.eventRowLinks}`);
    console.log(`  .event__participant: ${results.eventParticipants}`);
    console.log(`  div[class*="event"]: ${results.allDivs}`);
    console.log(`\nFirst 200 chars of page text:\n${results.pageText}\n`);
    
    // Try to get raw HTML
    const html = await page.content();
    const hasFlashscore = html.includes('flashscore');
    const hasEvent = html.includes('event__');
    console.log(`Page contains "flashscore": ${hasFlashscore}`);
    console.log(`Page contains "event__": ${hasEvent}`);
    console.log(`Total HTML size: ${html.length} bytes`);
    
  } catch (error) {
    console.error('Error:', error.message);
  }
  
  await browser.close();
})();
