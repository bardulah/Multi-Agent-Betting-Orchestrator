const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

(async () => {
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox'] });
  const page = await browser.newPage();
  
  console.log('Loading hockey page...');
  await page.goto('https://www.flashscore.com/hockey/', { waitUntil: 'networkidle2' });
  
  await page.waitForTimeout(2000);
  
  console.log('Checking for match elements...');
  const count1 = await page.evaluate(() => document.querySelectorAll('.event__match').length);
  const count2 = await page.evaluate(() => document.querySelectorAll('a.eventRowLink').length);
  const count3 = await page.evaluate(() => document.querySelectorAll('[id^="g_"]').length);
  const count4 = await page.evaluate(() => document.querySelectorAll('[class*="event"]').length);
  
  console.log('.event__match:', count1);
  console.log('a.eventRowLink:', count2);
  console.log('[id^="g_"]:', count3);
  console.log('[class*="event"]:', count4);
  
  // Check page content
  const hasContent = await page.evaluate(() => document.body.textContent.includes('hockey'));
  console.log('Page has hockey content:', hasContent);
  
  // Check for specific teams
  const hasTeams = await page.evaluate(() => document.body.textContent.includes('Karlovy'));
  console.log('Page has Karlovy:', hasTeams);
  
  await browser.close();
})();
