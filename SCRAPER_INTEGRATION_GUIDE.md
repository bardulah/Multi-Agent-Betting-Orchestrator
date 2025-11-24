# Dual-Scraper Integration Guide

## Overview

The system now supports scraping matches for **two different dates**:
- **Today's matches** (current behavior)
- **Tomorrow's matches** (new feature)

## Architecture

### File Structure

```
scraper/
├── src/
│   ├── flashscore-scraper.js          # Today's matches scraper (ORIGINAL)
│   └── flashscore-scraper-future.js   # Tomorrow's matches scraper (NEW)
├── package.json                        # npm scripts for both scrapers
└── test-all-sports-future.js          # Test script for tomorrow's scraper
```

### How It Works

The two scrapers are nearly identical, with one key difference:
- **flashscore-scraper.js**: Initializes with today's date
- **flashscore-scraper-future.js**: Initializes with tomorrow's date + **clicks the next day button**

The next day button click happens automatically for each sport:
```javascript
const nextDayClicked = await this.page.evaluate(() => {
  const nextBtn = document.querySelector('button[data-day-picker-arrow="next"]');
  if (nextBtn) {
    nextBtn.click();
    return true;
  }
  return false;
});

if (nextDayClicked) {
  console.log('✓ Clicked next day button');
  await new Promise(r => setTimeout(r, 4000)); // Wait for page to update
}
```

## Usage

### From Command Line

**Scrape today's matches:**
```bash
npm run scrape                    # All sports
npm run scrape -- --sports football,tennis
```

**Scrape tomorrow's matches:**
```bash
npm run scrape:future                    # All sports
npm run scrape:future -- --sports football,tennis
```

### From Python Orchestrator

**Today's matches (default):**
```bash
python3 run.py                           # Default
python3 run.py --date today              # Explicit
```

**Tomorrow's matches:**
```bash
python3 run.py --date tomorrow
```

**With custom filter configuration:**
```bash
python3 run.py --date tomorrow --filter config/filters/balanced.yaml
```

**With interactive mode:**
```bash
# Interactive selection for today's matches
python3 run.py --interactive

# Interactive selection for tomorrow's matches
python3 run.py --interactive --date tomorrow
```

The `--date` flag works seamlessly with `--interactive`. The interactive selector will show available dates in the current match data and allow you to configure sports, leagues, and limits before analysis begins.

### From Python Code

```python
from agents.orchestrator import BettingSystemOrchestrator

orchestrator = BettingSystemOrchestrator()

# Scrape today's matches
today_matches = orchestrator.run_scraper(sports=['football'], date='today')

# Scrape tomorrow's matches
tomorrow_matches = orchestrator.run_scraper(sports=['football'], date='tomorrow')
```

## Key Differences in Output

### Match Counts
- **Today's football matches**: ~139 matches
- **Tomorrow's football matches**: ~94 matches
- Different because fewer matches scheduled for different dates

### Date Field
- **flashscore-scraper.js**: All matches have today's date (e.g., 2025-11-18)
- **flashscore-scraper-future.js**: All matches have tomorrow's date (e.g., 2025-11-19)

## Orchestrator Integration

The orchestrator automatically routes the correct scraper based on the `--date` argument:

```python
def run_scraper(self, sports: List[str] = None, date: str = 'today') -> List[Dict]:
    if date.lower() == 'tomorrow':
        scraper_script = 'scrape:future'      # Uses flashscore-scraper-future.js
    else:
        scraper_script = 'scrape'             # Uses flashscore-scraper.js

    scraper_cmd = ['npm', 'run', scraper_script]
    # ... rest of execution
```

## Testing

**Test tomorrow's scraper with all sports:**
```bash
cd scraper
npm run test-future
```

This runs `test-all-sports-future.js` which:
1. Initializes the future scraper
2. Sets date to tomorrow
3. Scrapes all configured sports
4. Displays match breakdown by sport

## Match Data Comparison

**2025-11-18 (Today) - 139 total football matches:**
```
Costa Rica vs Honduras
Guatemala vs Suriname
Haiti vs Nicaragua
... (136 more)
```

**2025-11-19 (Tomorrow) - 94 total football matches:**
```
Costa Rica vs Honduras
Guatemala vs Suriname
Haiti vs Nicaragua
... (91 more)
```

## File Structure

The system now maintains separate match files for different dates:

```
data/
├── matches.json              # Today's matches (default file)
└── matches-tomorrow.json     # Tomorrow's matches
```

**How it works:**
1. Both scrapers save to `data/matches.json` temporarily
2. Orchestrator detects the date being scraped
3. If scraping tomorrow's matches, orchestrator copies to `data/matches-tomorrow.json`
4. Interactive selector and analysis use the appropriate date-specific file

**File Management:**
- **Today**: Uses `data/matches.json`
- **Tomorrow**: Uses `data/matches-tomorrow.json`
- Old matches are preserved; running a scraper for the same date overwrites
- Running scraper for different dates keeps both files independent

## Environment Variables

Both scrapers use the same configuration:
- `PUPPETEER_HEADLESS` environment variable respected
- Both load from `config/config.yaml`
- Scraper output goes to `data/matches.json`
- Orchestrator distributes to date-specific files

## Future Enhancements

The current implementation supports 'today' and 'tomorrow'. To extend to arbitrary dates:

1. **Add date parameter to CLI:**
   ```bash
   python3 run.py --date 2025-11-20
   ```

2. **Modify orchestrator to calculate clicks needed:**
   ```python
   def run_scraper(self, sports: List[str] = None, date: str = 'today') -> List[Dict]:
       days_ahead = calculate_days_ahead(date)
       scraper_cmd.append('--date-offset')
       scraper_cmd.append(str(days_ahead))
   ```

3. **Modify flashscore-scraper.js to accept date offset:**
   ```javascript
   const dateOffset = process.argv.find(arg => arg.startsWith('--date-offset'));
   for (let i = 0; i < offset; i++) {
       await clickNextDayButton();
   }
   ```

## Notes

- The file `data/matches.json` is overwritten each time a scraper runs
  - To preserve both today's and tomorrow's data, save to different files before running second scraper

- Scraper automatically clicks next day button for each sport before extraction
  - No manual intervention needed

- Date is set in constructor, ensuring all matches from a run have consistent dates

- Both scrapers take 3-5 minutes to complete all sports
