const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  await page.goto('https://www.flashscore.com/hockey/', { waitUntil: 'networkidle2' });
  await page.waitForTimeout(2000);
  
  // Get first match element structure
  const matchInfo = await page.evaluate(() => {
    const el = document.querySelector('.event__match');
    if (!el) return { error: 'No .event__match found' };
    
    return {
      html: el.outerHTML.substring(0, 500),
      hasHomeTeam: !!el.querySelector('.event__participant--home'),
      hasAwayTeam: !!el.querySelector('.event__participant--away'),
      hasTime: !!el.querySelector('.event__time'),
      children: Array.from(el.children).map(c => c.className).slice(0, 10)
    };
  });
  
  console.log(JSON.stringify(matchInfo, null, 2));
  
  await browser.close();
})();
