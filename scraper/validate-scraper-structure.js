#!/usr/bin/env node
/**
 * Scraper Structure Validation
 *
 * Validates the scraper code structure without requiring a browser.
 * Tests code syntax, dependencies, and configuration.
 */

const fs = require('fs').promises;
const path = require('path');

async function validateStructure() {
  console.log('🔍 Validating Scraper Structure\n');
  console.log('='.repeat(60));

  const results = {
    passed: 0,
    failed: 0,
    warnings: 0
  };

  // Test 1: Check main scraper file exists
  console.log('\n[Test 1] Checking main scraper file...');
  try {
    const scraperPath = path.join(__dirname, 'src/flashscore-scraper.js');
    await fs.access(scraperPath);
    const content = await fs.readFile(scraperPath, 'utf8');

    console.log('  ✓ flashscore-scraper.js exists');
    console.log(`  ✓ File size: ${(content.length / 1024).toFixed(2)} KB`);
    results.passed++;
  } catch (error) {
    console.log('  ❌ flashscore-scraper.js not found');
    results.failed++;
  }

  // Test 2: Check dependencies
  console.log('\n[Test 2] Checking dependencies...');
  try {
    const packagePath = path.join(__dirname, 'package.json');
    const packageJson = JSON.parse(await fs.readFile(packagePath, 'utf8'));

    const requiredDeps = [
      'puppeteer',
      'puppeteer-extra',
      'puppeteer-extra-plugin-stealth',
      'yaml'
    ];

    for (const dep of requiredDeps) {
      if (packageJson.dependencies && packageJson.dependencies[dep]) {
        console.log(`  ✓ ${dep}: ${packageJson.dependencies[dep]}`);
        results.passed++;
      } else {
        console.log(`  ❌ Missing dependency: ${dep}`);
        results.failed++;
      }
    }
  } catch (error) {
    console.log('  ❌ Cannot read package.json');
    results.failed++;
  }

  // Test 3: Check configuration file
  console.log('\n[Test 3] Checking configuration...');
  try {
    const configPath = path.join(__dirname, '../config/config.yaml');
    const configContent = await fs.readFile(configPath, 'utf8');

    console.log('  ✓ config.yaml exists');

    // Check for required config sections
    const requiredSections = ['sports', 'scraper'];
    for (const section of requiredSections) {
      if (configContent.includes(section + ':')) {
        console.log(`  ✓ Section '${section}' found`);
        results.passed++;
      } else {
        console.log(`  ⚠️  Section '${section}' not found`);
        results.warnings++;
      }
    }
  } catch (error) {
    console.log('  ❌ config.yaml not found or unreadable');
    results.failed++;
  }

  // Test 4: Validate scraper class structure
  console.log('\n[Test 4] Validating scraper class structure...');
  try {
    // Import the scraper (will fail if syntax errors)
    const FlashscoreScraper = require('./src/flashscore-scraper.js');

    console.log('  ✓ Scraper class imports successfully');
    console.log('  ✓ No syntax errors detected');

    // Check if it's a proper class/function
    if (typeof FlashscoreScraper === 'function') {
      console.log('  ✓ FlashscoreScraper is a valid class/constructor');
      results.passed++;

      // Check methods exist (by checking prototype)
      const methods = [
        'initialize',
        'scrapeAll',
        'scrapeFootball',
        'scrapeBasketball',
        'scrapeTennis',
        'scrapeHockey',
        'extractMatchData',
        'saveResults',
        'close'
      ];

      for (const method of methods) {
        if (FlashscoreScraper.prototype[method]) {
          console.log(`  ✓ Method '${method}' exists`);
          results.passed++;
        } else {
          console.log(`  ⚠️  Method '${method}' not found`);
          results.warnings++;
        }
      }
    } else {
      console.log('  ❌ FlashscoreScraper is not a valid class');
      results.failed++;
    }
  } catch (error) {
    console.log(`  ❌ Failed to import scraper: ${error.message}`);
    results.failed++;
  }

  // Test 5: Check data output directory
  console.log('\n[Test 5] Checking data directory...');
  try {
    const dataPath = path.join(__dirname, '../data');
    try {
      await fs.access(dataPath);
      console.log('  ✓ Data directory exists');
      results.passed++;
    } catch {
      console.log('  ⚠️  Data directory does not exist, will be created on first run');
      results.warnings++;

      // Try to create it
      await fs.mkdir(dataPath, { recursive: true });
      console.log('  ✓ Created data directory');
      results.passed++;
    }
  } catch (error) {
    console.log('  ❌ Cannot access/create data directory');
    results.failed++;
  }

  // Test 6: Validate selectors in code
  console.log('\n[Test 6] Checking CSS selectors...');
  try {
    const scraperPath = path.join(__dirname, 'src/flashscore-scraper.js');
    const content = await fs.readFile(scraperPath, 'utf8');

    const selectors = [
      '.event__match',
      '.event__participant--home',
      '.event__participant--away',
      '.event__time',
      '.event__title--type'
    ];

    for (const selector of selectors) {
      if (content.includes(selector)) {
        console.log(`  ✓ Selector '${selector}' found in code`);
        results.passed++;
      } else {
        console.log(`  ❌ Selector '${selector}' not found`);
        results.failed++;
      }
    }
  } catch (error) {
    console.log('  ❌ Cannot validate selectors');
    results.failed++;
  }

  // Test 7: Check for common bugs
  console.log('\n[Test 7] Checking for common bugs...');
  try {
    const scraperPath = path.join(__dirname, 'src/flashscore-scraper.js');
    const content = await fs.readFile(scraperPath, 'utf8');

    // Bug 1: Missing 'this.' in method calls
    if (content.includes('await scrapeTennis()') && !content.includes('await this.scrapeTennis()')) {
      console.log('  ❌ Found: "await scrapeTennis()" should be "await this.scrapeTennis()"');
      results.failed++;
    } else {
      console.log('  ✓ No missing "this." in scrapeTennis call');
      results.passed++;
    }

    // Bug 2: Check for proper async/await usage
    const asyncMethods = ['initialize', 'scrapeAll', 'scrapeFootball'];
    let allAsync = true;
    for (const method of asyncMethods) {
      const regex = new RegExp(`async\\s+${method}\\s*\\(`);
      if (!regex.test(content)) {
        console.log(`  ⚠️  Method '${method}' might not be async`);
        results.warnings++;
        allAsync = false;
      }
    }
    if (allAsync) {
      console.log('  ✓ All major methods are async');
      results.passed++;
    }

    // Bug 3: Check for proper error handling
    const errorHandlingCount = (content.match(/try\s*{/g) || []).length;
    if (errorHandlingCount > 5) {
      console.log(`  ✓ Good error handling: ${errorHandlingCount} try/catch blocks`);
      results.passed++;
    } else {
      console.log(`  ⚠️  Limited error handling: only ${errorHandlingCount} try/catch blocks`);
      results.warnings++;
    }

  } catch (error) {
    console.log('  ❌ Cannot check for bugs');
    results.failed++;
  }

  // Summary
  console.log('\n' + '='.repeat(60));
  console.log('📊 Validation Summary:');
  console.log(`  ✅ Passed:   ${results.passed}`);
  console.log(`  ❌ Failed:   ${results.failed}`);
  console.log(`  ⚠️  Warnings: ${results.warnings}`);

  if (results.failed === 0) {
    console.log('\n✅ All critical tests passed!');
    console.log('💡 Scraper structure is valid');
    console.log('📝 Next step: Test with actual browser using test-scraper-devtools.js');
    return 0;
  } else {
    console.log('\n❌ Some tests failed - please fix the issues above');
    return 1;
  }
}

// Run validation
if (require.main === module) {
  validateStructure()
    .then(exitCode => process.exit(exitCode))
    .catch(error => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}

module.exports = validateStructure;
