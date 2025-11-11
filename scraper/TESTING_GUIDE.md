# Puppeteer Scraper Testing Guide

## Overview
This guide explains how to test the Flashscore.com Puppeteer scraper with Chrome DevTools for debugging and validation.

## Prerequisites

### 1. Install Chrome/Chromium
```bash
# Ubuntu/Debian
sudo apt-get install chromium-browser

# macOS
brew install chromium

# Or download Chrome from:
# https://www.google.com/chrome/
```

### 2. Install Dependencies
```bash
cd scraper
npm install
```

## Testing Methods

### Method 1: Test with DevTools (Recommended)

Run the interactive test script that opens Chrome with DevTools:

```bash
cd scraper
node test-scraper-devtools.js
```

**What it does:**
- Opens Chrome with DevTools automatically
- Navigates to Flashscore.com
- Tests all CSS selectors
- Extracts sample matches
- Tests odds extraction
- Keeps browser open for manual inspection

**While running:**
1. Browser window will open with DevTools
2. Inspect the Elements tab to verify selectors
3. Check Console for any JavaScript errors
4. Test manual clicking on matches
5. Press Ctrl+C when done

### Method 2: Full Scraper Test

Run the complete scraper:

```bash
cd scraper
node src/flashscore-scraper.js
```

**Expected output:**
- Scraped matches saved to `../data/matches.json`
- Console logs showing progress

### Method 3: Structure Validation (No Browser Required)

Run the validation script to check code structure:

```bash
node validate-scraper-structure.js
```

## Common Issues & Solutions

### Issue 1: "Chrome not found"
**Solution:** Install Chrome/Chromium or update the executablePath in launch options:

```javascript
await puppeteer.launch({
  executablePath: '/usr/bin/chromium-browser', // or '/usr/bin/google-chrome'
  // ... other options
});
```

### Issue 2: "No matches found"
**Possible causes:**
- Flashscore changed their HTML structure
- Page didn't fully load
- Selectors are outdated

**Solution:** Open DevTools and inspect:
1. Right-click on a match → Inspect Element
2. Find the correct CSS selector
3. Update selectors in `flashscore-scraper.js`

### Issue 3: 403 Forbidden / Bot Detection
**Solution:** The scraper uses `puppeteer-extra-plugin-stealth` to avoid detection. If still blocked:
- Add delays between requests
- Rotate user agents
- Use residential proxies
- Add cookies from a real browser session

### Issue 4: Timeout errors
**Solution:** Increase timeouts in config.yaml:
```yaml
scraper:
  timeout: 60000  # 60 seconds
```

## Selector Reference

Current selectors used (as of implementation):

| Element | Selector | Description |
|---------|----------|-------------|
| Match row | `.event__match` | Individual match container |
| Home team | `.event__participant--home` | Home team name |
| Away team | `.event__participant--away` | Away team name |
| Time | `.event__time` | Match time/status |
| League | `.event__title--type` | League/tournament name |
| Odds row | `.ui-table__row` | Bookmaker odds row |
| Bookmaker | `.oddsCell__bookmaker` | Bookmaker name |
| Odds value | `.oddsValueInner` | Individual odd value |

## Debugging Tips

### 1. Visual Debugging
Set `headless: false` to see what's happening:
```javascript
await puppeteer.launch({
  headless: false,
  devtools: true,  // Open DevTools automatically
  slowMo: 100      // Slow down by 100ms per action
});
```

### 2. Screenshot Debugging
Take screenshots at key points:
```javascript
await page.screenshot({ path: 'debug-screenshot.png', fullPage: true });
```

### 3. Console Logging
Listen to console messages from the page:
```javascript
page.on('console', msg => console.log('PAGE LOG:', msg.text()));
```

### 4. Network Monitoring
Track network requests:
```javascript
page.on('request', request => {
  console.log('Request:', request.url());
});

page.on('response', response => {
  console.log('Response:', response.status(), response.url());
});
```

## Testing Checklist

Before deploying, verify:

- [ ] Browser launches successfully
- [ ] Flashscore.com loads completely
- [ ] Match elements are found (>0 matches)
- [ ] Home/away team names extracted correctly
- [ ] Match times extracted correctly
- [ ] League names extracted correctly
- [ ] Clicking on match works
- [ ] Odds tab can be found and clicked
- [ ] Bookmaker odds are extracted
- [ ] Results saved to JSON correctly
- [ ] Browser closes cleanly
- [ ] No memory leaks (run multiple times)

## Sandbox Limitations

**Note:** This sandbox environment has restrictions:
- Cannot install Chrome/Chromium via apt-get (403 errors)
- Cannot download Chrome via Puppeteer (403 errors)
- External network requests may be blocked

**To properly test:**
1. Clone this repository to your local machine
2. Install Chrome locally
3. Run the test scripts there

## Sample Test Output

Successful test should show:
```
🔍 Testing Flashscore Scraper with DevTools

============================================================
Launching Chrome with DevTools...
✓ Browser launched with DevTools

📊 Testing Flashscore.com structure...

[Test 1] Navigating to Flashscore Football page...
✓ Page loaded

[Test 2] Inspecting page structure...
  matches: 45 elements found (selector: .event__match)
  homeTeam: 45 elements found (selector: .event__participant--home)
  awayTeam: 45 elements found (selector: .event__participant--away)
  time: 45 elements found (selector: .event__time)
  league: 12 elements found (selector: .event__title--type)

[Test 3] Extracting sample match data...
✓ Found 45 matches
  Match 1: Manchester City vs Liverpool (19:45)
  Match 2: Arsenal vs Chelsea (20:00)
  Match 3: Barcelona vs Real Madrid (21:00)

✓ Test results saved to: test-results.json

[Test 4] Testing odds extraction...
Clicking on first match...
✓ Odds tab found, clicking...
✓ Found 15 odds rows
Sample odds:
  1. bet365
  2. William Hill
  3. Betfair

============================================================
✅ Test complete!

💡 DevTools is open - inspect the page to verify selectors
💡 Press Ctrl+C when done inspecting
```

## Next Steps

After successful testing:
1. Update selectors if needed
2. Test all sports (football, basketball, tennis, hockey)
3. Run full scraper with `node src/flashscore-scraper.js`
4. Verify output in `../data/matches.json`
5. Integrate with Python agents for betting analysis

## Resources

- [Puppeteer Documentation](https://pptr.dev/)
- [puppeteer-extra-plugin-stealth](https://github.com/berstend/puppeteer-extra/tree/master/packages/puppeteer-extra-plugin-stealth)
- [Chrome DevTools Protocol](https://chromedevtools.github.io/devtools-protocol/)
- [Flashscore.com](https://www.flashscore.com/) (target site)
