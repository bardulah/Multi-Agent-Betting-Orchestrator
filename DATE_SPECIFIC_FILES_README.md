# Date-Specific Match Files Architecture

## Overview

The system now maintains **separate match files for each date**, enabling seamless multi-date analysis without file overwrites.

## File Structure

```
data/
├── matches.json              # Today's matches (2025-11-18)
└── matches-tomorrow.json     # Tomorrow's matches (2025-11-19)
```

## How It Works

### File Path Resolution

The orchestrator uses `get_matches_file_path(date)` to determine which file to use:

```python
def get_matches_file_path(date: str = 'today') -> Path:
    """Map date to file path"""
    base_path = Path('data/matches.json')

    if date.lower() == 'tomorrow':
        return base_path.parent / f"{base_path.stem}-tomorrow.json"
    else:
        return base_path  # 'data/matches.json'
```

**Mapping:**
- `date='today'` → `data/matches.json`
- `date='tomorrow'` → `data/matches-tomorrow.json`

### Scraper Execution Flow

```
1. User runs: python3 run.py --date tomorrow
                                     ↓
2. Orchestrator calls: run_scraper(date='tomorrow')
                                     ↓
3. Executes: npm run scrape:future
                                     ↓
4. Scraper saves to: data/matches.json (temporary location)
                                     ↓
5. Orchestrator copies to: data/matches-tomorrow.json
                                     ↓
6. Original data/matches.json is available for next scrape
```

### Loading Existing Data

When interactive mode or direct analysis is requested:

```
1. User runs: python3 run.py --interactive --date tomorrow
                                     ↓
2. Orchestrator calls: load_matches_from_file(date='tomorrow')
                                     ↓
3. InteractiveSelector receives date parameter
                                     ↓
4. Selector resolves file: data/matches-tomorrow.json
                                     ↓
5. If file exists: Load and display
   If missing: Prompt to run scraper
```

## Usage Patterns

### Scrape and Analyze Today

```bash
# Scrapes to data/matches.json
python3 run.py
```

### Scrape and Analyze Tomorrow

```bash
# Scrapes to data/matches-tomorrow.json
python3 run.py --date tomorrow
```

### Use Existing Data (No Scraping)

If `data/matches-tomorrow.json` exists:

```bash
# Loads from data/matches-tomorrow.json (no scraping)
python3 run.py --interactive --date tomorrow
```

### Multiple Dates Simultaneously

```bash
# Scrape today
python3 run.py --date today

# Scrape tomorrow (today's data is preserved)
python3 run.py --date tomorrow

# Now have both:
# - data/matches.json (today)
# - data/matches-tomorrow.json (tomorrow)
```

## Interactive Selector Integration

The `InteractiveSelector` now accepts a `date` parameter:

```python
# Load today's selector
selector = InteractiveSelector(date='today')

# Load tomorrow's selector
selector = InteractiveSelector(date='tomorrow')
```

### Date-Aware Error Messages

If the selected date's file doesn't exist:

```
❌ Matches file not found: data/matches-tomorrow.json
   For tomorrow matches, run the scraper:
   python3 run.py --date tomorrow
```

## File Management

### Creating New Date Files

Files are created automatically:
1. When orchestrator runs a scraper for a new date
2. Scraped data is copied to the date-specific file
3. No manual file management needed

### Preserving Multiple Dates

To keep data for multiple dates:
1. Run scraper for each date with `--date` flag
2. Each creates/updates its own file
3. Files don't interfere with each other

### Cleaning Up

To remove data for a specific date:

```bash
# Remove today's matches
rm data/matches.json

# Remove tomorrow's matches
rm data/matches-tomorrow.json
```

## Implementation Details

### Modified Files

1. **agents/orchestrator.py**
   - Added `get_matches_file_path(date)` method
   - Modified `load_matches_from_file(date)` to use date-specific paths
   - Modified `run_scraper(date)` to copy results to date-specific file
   - Updated `run()` method to pass date parameter

2. **utils/interactive_selector.py**
   - Added `date` parameter to `__init__()`
   - Added `_resolve_matches_file(base_file, date)` method
   - Updated error messages to guide users

3. **scraper/src/flashscore-scraper-future.js**
   - Automatically initializes with tomorrow's date

4. **scraper/package.json**
   - Added `"scrape:future"` npm script

## Error Handling

### Missing File Scenarios

**Scenario 1: No file for requested date**
```
User: python3 run.py --date tomorrow
System: File not found → Runs scraper → Creates data/matches-tomorrow.json
```

**Scenario 2: Interactive mode with missing file**
```
User: python3 run.py --interactive --date tomorrow
System: File not found → Shows helpful error → Exit
Fix: python3 run.py --date tomorrow (then retry interactive)
```

## Future Extensions

### Supporting Multiple Specific Dates

The system can be extended to support any date:

```python
def get_matches_file_path(date: str) -> Path:
    if date == 'today':
        return Path('data/matches.json')
    elif date == 'tomorrow':
        return Path('data/matches-tomorrow.json')
    else:
        # Date format: 2025-11-20
        return Path(f'data/matches-{date}.json')
```

### Archival Strategy

For long-term data storage:

```bash
# Archive old matches
mkdir -p data/archive
mv data/matches-2025-11-*.json data/archive/

# Or compress
tar -czf data/archive/matches-2025-11.tar.gz data/matches-*.json
```

## Testing

### Verify Files Exist

```bash
ls -lah data/matches*.json
```

### Check File Contents

```bash
# Count matches by date
jq '.matches | length' data/matches.json
jq '.matches | length' data/matches-tomorrow.json

# Compare dates
jq '.matches[0].date' data/matches.json
jq '.matches[0].date' data/matches-tomorrow.json
```

### Test File Path Logic

```python
from pathlib import Path

def get_matches_file_path(date: str = 'today') -> Path:
    base_path = Path('data/matches.json')
    if date.lower() == 'tomorrow':
        return base_path.parent / f"{base_path.stem}-tomorrow.json"
    else:
        return base_path

# Test
assert get_matches_file_path('today') == Path('data/matches.json')
assert get_matches_file_path('tomorrow') == Path('data/matches-tomorrow.json')
```

## Key Benefits

✅ **No Overwrites**: Each date has its own file
✅ **Clean Architecture**: Date-aware file paths at orchestrator level
✅ **User Friendly**: Automatic file management
✅ **Extensible**: Easy to add more dates in future
✅ **Backward Compatible**: Still works with single `matches.json` for today

## Summary

The date-specific file architecture enables:
- Running scrapers for multiple dates without data loss
- Clean separation of concerns at the orchestrator level
- Seamless integration with interactive mode
- Future extensibility to arbitrary dates
