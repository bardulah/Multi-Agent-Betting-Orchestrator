const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

puppeteer.use(StealthPlugin());

async function testDateNavigation() {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  console.log('\n╔════════════════════════════════════════════╗');
  console.log('║ DATE NAVIGATION DEBUGGING TEST              ║');
  console.log('╚════════════════════════════════════════════╝\n');

  // Load football page
  console.log('1. Loading Flashscore football page...');
  await page.goto('https://www.flashscore.com/football/', {
    waitUntil: 'networkidle2'
  });
  console.log('   ✓ Page loaded\n');

  // Get initial date and match count
  const getPageState = async () => {
    return await page.evaluate(() => {
      // Extract current date from date picker
      const datePicker = document.querySelector('[data-testid="wcl-dayPickerButton"]');
      const dateText = datePicker?.textContent?.trim() || 'unknown';

      // Count matches
      const matchCount = document.querySelectorAll('.event__match').length;

      // Sample first match
      const firstMatch = document.querySelector('.event__match');
      let firstMatchTeams = '';
      if (firstMatch) {
        const home = firstMatch.querySelector('.event__participant--home');
        const away = firstMatch.querySelector('.event__participant--away');
        firstMatchTeams = `${home?.textContent?.trim() || '?'} vs ${away?.textContent?.trim() || '?'}`;
      }

      return { dateText, matchCount, firstMatchTeams };
    });
  };

  const initial = await getPageState();
  console.log('2. INITIAL STATE:');
  console.log(`   Date shown: "${initial.dateText}"`);
  console.log(`   Match count: ${initial.matchCount}`);
  console.log(`   First match: ${initial.firstMatchTeams}\n`);

  // Try clicking next arrow button
  console.log('3. Attempting to navigate forward (clicking next arrow)...');
  const navigated = await page.evaluate(() => {
    const nextBtn = document.querySelector('button[data-day-picker-arrow="next"]');
    if (!nextBtn) {
      return { success: false, reason: 'next button not found' };
    }
    console.log('   Button found, clicking...');
    nextBtn.click();
    return { success: true, reason: null };
  });

  if (!navigated.success) {
    console.log(`   ✗ Failed: ${navigated.reason}\n`);
  } else {
    console.log('   ✓ Clicked next button\n');

    // Wait for page to potentially update
    console.log('4. Waiting 4 seconds for page to update...');
    await new Promise(r => setTimeout(r, 4000));

    // Check new state
    const afterNav = await getPageState();
    console.log('5. STATE AFTER NAVIGATION:');
    console.log(`   Date shown: "${afterNav.dateText}"`);
    console.log(`   Match count: ${afterNav.matchCount}`);
    console.log(`   First match: ${afterNav.firstMatchTeams}\n`);

    // Analyze change
    console.log('6. ANALYSIS:');
    if (afterNav.dateText !== initial.dateText) {
      console.log(`   ✓ Date CHANGED: "${initial.dateText}" → "${afterNav.dateText}"`);
    } else {
      console.log(`   ✗ Date UNCHANGED: still "${initial.dateText}"`);
    }

    if (afterNav.matchCount !== initial.matchCount) {
      console.log(`   ✓ Match count CHANGED: ${initial.matchCount} → ${afterNav.matchCount}`);
    } else {
      console.log(`   ✗ Match count UNCHANGED: still ${initial.matchCount}`);
    }

    if (afterNav.firstMatchTeams !== initial.firstMatchTeams) {
      console.log(`   ✓ First match CHANGED`);
    } else {
      console.log(`   ✗ First match UNCHANGED`);
    }
  }

  console.log('\n7. DEBUGGING INFO:');
  const debugInfo = await page.evaluate(() => {
    return {
      nextButtonExists: !!document.querySelector('button[data-day-picker-arrow="next"]'),
      prevButtonExists: !!document.querySelector('button[data-day-picker-arrow="prev"]'),
      datePickerSelector: !!document.querySelector('[data-testid="wcl-dayPickerButton"]'),
      otherDateButtons: Array.from(document.querySelectorAll('button'))
        .filter(btn => btn.textContent?.match(/\d{1,2}\/\d{1,2}/))
        .map(btn => btn.textContent?.trim())
        .slice(0, 5)
    };
  });

  console.log(`   Next button exists: ${debugInfo.nextButtonExists}`);
  console.log(`   Prev button exists: ${debugInfo.prevButtonExists}`);
  console.log(`   Date picker element: ${debugInfo.datePickerSelector}`);
  console.log(`   Other date-like buttons: ${debugInfo.otherDateButtons.join(', ')}`);

  await browser.close();
  console.log('\n✓ Test complete\n');
}

testDateNavigation().catch(console.error);
