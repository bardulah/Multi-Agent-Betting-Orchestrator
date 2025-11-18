const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  const page = await browser.newPage();

  console.log('Loading Flashscore football page...\n');
  await page.goto('https://www.flashscore.com/football/', { waitUntil: 'networkidle2' });

  await page.waitForSelector('.event__match', { timeout: 5000 }).catch(() => {});
  await new Promise(r => setTimeout(r, 2000));

  // Detailed date picker analysis
  const pickerInfo = await page.evaluate(() => {
    console.log('=== ANALYZING DATE PICKER ===\n');

    // Find all buttons with "next" or "prev"
    const allButtons = Array.from(document.querySelectorAll('button'));
    const dateButtons = allButtons.filter(b => {
      const html = b.outerHTML.toLowerCase();
      const attrs = b.getAttribute('data-day-picker-arrow') || '';
      return attrs.includes('next') || attrs.includes('prev') || html.includes('next') || html.includes('prev');
    });

    console.log(`Found ${dateButtons.length} date navigation buttons:`);
    dateButtons.forEach((btn, i) => {
      console.log(`${i + 1}. ${btn.getAttribute('data-day-picker-arrow')} - ${btn.outerHTML.substring(0, 100)}`);
    });

    // Find current date display
    const matchElements = document.querySelectorAll('.event__match');
    const firstMatch = matchElements[0];
    if (firstMatch) {
      const timeEl = firstMatch.querySelector('.event__time');
      const dateEl = firstMatch.querySelector('[class*="date"]');
      console.log(`\nFirst match time element: ${timeEl ? timeEl.textContent : 'not found'}`);
    }

    // Look for date input fields
    const dateInputs = document.querySelectorAll('input[type="date"], input[class*="date"], [class*="DayPicker"]');
    console.log(`\nDate input fields found: ${dateInputs.length}`);
    Array.from(dateInputs).forEach((inp, i) => {
      console.log(`${i + 1}. ${inp.outerHTML.substring(0, 100)}`);
    });

    // Check if the button actually works
    console.log('\n=== CURRENT STATE ===');
    console.log(`Total matches on page: ${matchElements.length}`);

    return {
      buttonCount: dateButtons.length,
      matchCount: matchElements.length,
      url: window.location.href
    };
  });

  console.log('\nResult:', pickerInfo);

  // Now try clicking the button and see what changes
  console.log('\n\n=== TESTING BUTTON CLICK ===');

  const before = await page.evaluate(() => document.querySelectorAll('.event__match').length);
  console.log(`Matches BEFORE: ${before}`);

  // Click next day button
  await page.click('button[data-day-picker-arrow="next"]').catch(e => console.log(`Click error: ${e.message}`));

  console.log('Waiting 3 seconds after click...');
  await new Promise(r => setTimeout(r, 3000));

  const after = await page.evaluate(() => document.querySelectorAll('.event__match').length);
  console.log(`Matches AFTER: ${after}`);
  console.log(`URL AFTER: ${await page.url()}`);

  // Check if matches changed
  const firstMatchAfter = await page.evaluate(() => {
    const matches = document.querySelectorAll('.event__match');
    if (matches.length > 0) {
      const teams = matches[0].querySelector('.event__participant--home');
      return teams ? teams.textContent : 'unknown';
    }
    return 'no matches';
  });

  console.log(`First match team AFTER: ${firstMatchAfter}`);

  await browser.close();
})();
