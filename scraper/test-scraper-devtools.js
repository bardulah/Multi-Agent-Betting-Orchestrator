#!/usr/bin/env node
/**
 * Puppeteer Scraper Test with Chrome DevTools
 *
 * This script tests the Flashscore scraper with browser DevTools enabled
 * for debugging and inspection.
 *
 * Requirements:
 * - Chrome/Chromium installed
 * - Run in environment with display (or use Xvfb for headless server)
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs').promises;
const path = require('path');

puppeteer.use(StealthPlugin());

async function testScraperWithDevTools() {
  console.log('🔍 Testing Flashscore Scraper with DevTools\n');
  console.log('=' .repeat(60));

  let browser = null;
  let page = null;

  try {
    // Launch browser with DevTools
    console.log('Launching Chrome with DevTools...');
    browser = await puppeteer.launch({
      headless: false,  // Run with visible browser
      devtools: true,   // Open DevTools automatically
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--window-size=1920,1080',
        '--disable-blink-features=AutomationControlled'
      ],
      defaultViewport: {
        width: 1920,
        height: 1080
      }
    });

    page = await browser.newPage();

    // Set realistic user agent
    await page.setUserAgent(
      'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
    );

    console.log('✓ Browser launched with DevTools');
    console.log('\n📊 Testing Flashscore.com structure...\n');

    // Test 1: Navigate to Flashscore Football
    console.log('[Test 1] Navigating to Flashscore Football page...');
    await page.goto('https://www.flashscore.com/football/', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });
    console.log('✓ Page loaded');

    // Wait a bit for dynamic content
    await page.waitForTimeout(3000);

    // Test 2: Inspect page structure
    console.log('\n[Test 2] Inspecting page structure...');

    const selectors = {
      matches: '.event__match',
      homeTeam: '.event__participant--home',
      awayTeam: '.event__participant--away',
      time: '.event__time',
      league: '.event__title--type'
    };

    for (const [name, selector] of Object.entries(selectors)) {
      const elements = await page.$$(selector);
      console.log(`  ${name}: ${elements.length} elements found (selector: ${selector})`);

      if (elements.length === 0) {
        console.log(`    ⚠️  WARNING: No elements found for ${name}`);
        console.log(`    💡 Inspect DevTools to find correct selector`);
      }
    }

    // Test 3: Extract sample match data
    console.log('\n[Test 3] Extracting sample match data...');
    const matchElements = await page.$$('.event__match');

    if (matchElements.length > 0) {
      console.log(`✓ Found ${matchElements.length} matches`);

      // Extract first 3 matches
      const sampleMatches = [];
      for (let i = 0; i < Math.min(3, matchElements.length); i++) {
        try {
          const homeTeam = await matchElements[i].$eval('.event__participant--home', el => el.textContent.trim()).catch(() => 'N/A');
          const awayTeam = await matchElements[i].$eval('.event__participant--away', el => el.textContent.trim()).catch(() => 'N/A');
          const time = await matchElements[i].$eval('.event__time', el => el.textContent.trim()).catch(() => 'N/A');

          sampleMatches.push({ homeTeam, awayTeam, time });
          console.log(`  Match ${i + 1}: ${homeTeam} vs ${awayTeam} (${time})`);
        } catch (error) {
          console.log(`  ❌ Failed to extract match ${i + 1}: ${error.message}`);
        }
      }

      // Save sample data
      const outputPath = path.join(__dirname, 'test-results.json');
      await fs.writeFile(outputPath, JSON.stringify({
        testDate: new Date().toISOString(),
        url: page.url(),
        totalMatchesFound: matchElements.length,
        sampleMatches,
        selectors
      }, null, 2));
      console.log(`\n✓ Test results saved to: ${outputPath}`);
    } else {
      console.log('❌ No matches found - selectors may need updating');
      console.log('💡 Use DevTools (F12) to inspect the page and find correct selectors');
    }

    // Test 4: Test clicking on a match to see odds
    console.log('\n[Test 4] Testing odds extraction...');
    if (matchElements.length > 0) {
      try {
        console.log('Clicking on first match...');
        await matchElements[0].click();
        await page.waitForTimeout(2000);

        // Look for odds tab
        const oddsTab = await page.$('a[href*="odds"]').catch(() => null);
        if (oddsTab) {
          console.log('✓ Odds tab found, clicking...');
          await oddsTab.click();
          await page.waitForTimeout(2000);

          // Try to extract odds
          const oddsRows = await page.$$('.ui-table__row');
          console.log(`✓ Found ${oddsRows.length} odds rows`);

          if (oddsRows.length > 0) {
            console.log('Sample odds:');
            for (let i = 0; i < Math.min(3, oddsRows.length); i++) {
              const bookmaker = await oddsRows[i].$eval('.oddsCell__bookmaker', el => el.textContent.trim()).catch(() => 'N/A');
              console.log(`  ${i + 1}. ${bookmaker}`);
            }
          }
        } else {
          console.log('⚠️  No odds tab found - may need to inspect page structure');
        }
      } catch (error) {
        console.log(`❌ Odds extraction failed: ${error.message}`);
      }
    }

    console.log('\n' + '='.repeat(60));
    console.log('✅ Test complete!');
    console.log('\n💡 DevTools is open - inspect the page to verify selectors');
    console.log('💡 Press Ctrl+C when done inspecting');

    // Keep browser open for inspection
    await new Promise(resolve => {
      process.on('SIGINT', () => {
        console.log('\n\nClosing browser...');
        resolve();
      });
    });

  } catch (error) {
    console.error('\n❌ Test failed:', error.message);
    console.error('\nFull error:', error);
  } finally {
    if (browser) {
      await browser.close();
      console.log('Browser closed');
    }
  }
}

// Run test
if (require.main === module) {
  testScraperWithDevTools().catch(console.error);
}

module.exports = testScraperWithDevTools;
