# Improved Betting System Workflow Architecture

## Current Problem

The existing workflow runs everything in one monolithic pipeline:
1. **Scrape** all 510 matches (5-10 min)
2. **Analyze** all 510 matches with AI agents (15-25 min)
3. **Synthesize & Generate** recommendations for all matches (5-10 min)

**Total time: 25-45 minutes** for every run, even if you only want to test 10 matches.

This makes iteration slow and expensive (API costs grow linearly with match count).

---

## Proposed Solution: Modular Pipeline Architecture

### Phase 1: Scraping Layer (Standalone & Reusable)
**File**: `scraper/src/flashscore-scraper.js`
**Output**: `data/scraped_matches.json`
**Run time**: 5-10 minutes (one-time, reusable)

```bash
# Scrape once, use multiple times
node scraper/src/flashscore-scraper.js --output data/scraped_matches.json --all-sports
```

**Generates**:
```json
{
  "timestamp": "2025-11-13T14:00:00Z",
  "total_matches": 510,
  "matches": [
    {
      "id": "match_001",
      "homeTeam": "Team A",
      "awayTeam": "Team B",
      "sport": "football",
      "league": "Premier League",
      "odds": { "home_win": 1.5, "draw": 3.0, "away_win": 2.5 }
    },
    ...
  ]
}
```

### Phase 2: Analysis Layer (Configurable Scope)
**File**: `agents/orchestrator.py`
**Input**: `data/scraped_matches.json`
**Output**: `data/analyzed_matches.json`

**Key feature**: SELECT which matches to analyze

#### Option A: Analyze Specific Count
```bash
# Analyze only first 10 matches (good for testing)
python run.py --mode=analyze --input=data/scraped_matches.json --limit=10
```

#### Option B: Analyze by Sport
```bash
# Analyze only football matches
python run.py --mode=analyze --input=data/scraped_matches.json --sport=football

# Analyze football and basketball
python run.py --mode=analyze --input=data/scraped_matches.json --sports=football,basketball
```

#### Option C: Analyze by League/Competition
```bash
# Analyze only Premier League matches
python run.py --mode=analyze --input=data/scraped_matches.json --league="Premier League"
```

#### Option D: Analyze Random Sample
```bash
# Analyze random 20 matches (for quick testing)
python run.py --mode=analyze --input=data/scraped_matches.json --sample=20 --random
```

**Generates**:
```json
{
  "analyzed_at": "2025-11-13T14:30:00Z",
  "matches_analyzed": 10,
  "results": [
    {
      "match_id": "match_001",
      "internet_picks": { "picks": [...], "confidence": 0.8 },
      "data_driven": { "picks": [...], "confidence": 0.75 },
      "synthesis": { "recommendation": "BET", "pick": "home_win", "confidence": 0.78 }
    }
  ]
}
```

### Phase 3: Decision Layer (Choose What to Do)
**Decision Point**: After analysis completes, choose next action

```bash
# Option 1: Generate recommendations (full pipeline)
python run.py --mode=synthesize --input=data/analyzed_matches.json --output=data/recommendations.json

# Option 2: Review results interactively
python run.py --mode=review --input=data/analyzed_matches.json

# Option 3: Filter by confidence threshold
python run.py --mode=filter --input=data/analyzed_matches.json --min-confidence=0.75

# Option 4: Generate report
python run.py --mode=report --input=data/analyzed_matches.json
```

---

## Workflow Examples

### Use Case 1: Quick Test (5 minutes)
```bash
# Only analyze 5 random matches to verify everything works
python run.py --mode=analyze --input=data/scraped_matches.json --sample=5 --random

# No synthesis/recommendations - just see if agents work
```

### Use Case 2: Full Analysis with Fresh Scrape
```bash
# Scrape everything (run once)
node scraper/src/flashscore-scraper.js --output data/scraped_matches.json --all-sports

# Analyze just football (fast)
python run.py --mode=analyze --input=data/scraped_matches.json --sport=football

# Review results before synthesis
python run.py --mode=review --input=data/analyzed_matches.json

# Generate recommendations only for high-confidence matches
python run.py --mode=synthesize --input=data/analyzed_matches.json --min-confidence=0.7
```

### Use Case 3: Reuse Scraped Data, Multiple Analysis Runs
```bash
# Day 1: Scrape once (reusable for whole day)
node scraper/src/flashscore-scraper.js --output data/scraped_matches_nov13.json --all-sports

# Morning: Analyze football only
python run.py --mode=analyze --input=data/scraped_matches_nov13.json --sport=football --output data/analysis_football_morning.json

# Afternoon: Analyze basketball only
python run.py --mode=analyze --input=data/scraped_matches_nov13.json --sport=basketball --output data/analysis_basketball_afternoon.json

# Evening: Analyze everything (all previous analyses + anything new)
python run.py --mode=analyze --input=data/scraped_matches_nov13.json --output data/analysis_all_evening.json
```

### Use Case 4: Iterative Development & Testing
```bash
# 1. Scrape (once)
node scraper/src/flashscore-scraper.js --output data/raw_matches.json --all-sports

# 2. Test with 5 matches
python run.py --mode=analyze --input=data/raw_matches.json --sample=5

# 3. Verify output structure
cat data/analyzed_matches.json | jq '.results[0]'

# 4. If good, test with 20
python run.py --mode=analyze --input=data/raw_matches.json --sample=20

# 5. If good, run full analysis
python run.py --mode=analyze --input=data/raw_matches.json
```

---

## Implementation Details

### New Command-Line Interface
```python
# args.py - Define all CLI options
parser.add_argument('--mode', choices=['scrape', 'analyze', 'review', 'synthesize', 'filter', 'report'],
                    default='full', help='Execution mode')
parser.add_argument('--input', type=str, help='Input file (scraped matches)')
parser.add_argument('--output', type=str, help='Output file')
parser.add_argument('--limit', type=int, help='Limit to N matches')
parser.add_argument('--sport', type=str, help='Filter by sport')
parser.add_argument('--sports', type=str, help='Filter by sports (comma-separated)')
parser.add_argument('--league', type=str, help='Filter by league')
parser.add_argument('--sample', type=int, help='Random sample of N matches')
parser.add_argument('--random', action='store_true', help='Randomize order')
parser.add_argument('--min-confidence', type=float, help='Minimum confidence threshold')
```

### File Organization
```
/opt/deployment/repos/adk/
├── data/
│   ├── scraped_matches.json           # ← Scraper output (reusable)
│   ├── scraped_matches_nov13.json     # ← Dated versions for tracking
│   ├── analyzed_matches.json          # ← Analysis output
│   ├── recommendations.json           # ← Final recommendations
│   └── history.json                   # ← Historical tracking
├── scraper/
│   └── src/flashscore-scraper.js      # ← Standalone scraper
├── agents/
│   ├── orchestrator.py                # ← Main agent orchestrator
│   ├── cli.py                         # ← Command-line interface
│   └── ...
└── run.py                             # ← Updated to use new CLI
```

### Time Savings

**Current workflow**: 25-45 min total
- Scrape: 5-10 min (unavoidable)
- Analyze: 15-25 min (ALL matches)
- Total: 20-35 min

**New workflow (sample test)**: 2-5 min total
- Scrape: 0 min (reuse from yesterday)
- Analyze: 2-5 min (5-10 matches only)
- **Savings: 80-90%**

**New workflow (full analysis)**: 20-35 min total (same as before, but now you have options!)
- Scrape: 0 min (reuse)
- Analyze: 20-35 min (all matches)
- **But you can stop early, analyze by sport, or test with samples first**

---

## Implementation Priority

### Phase 1 (Quick Win - 1-2 hours)
- [ ] Add CLI argument parsing to `run.py`
- [ ] Separate scraper into standalone module
- [ ] Add `--limit` and `--sample` options
- [ ] Test with 5, 10, 20 matches

### Phase 2 (Medium Effort - 2-3 hours)
- [ ] Add `--sport`, `--league`, `--sports` filters
- [ ] Add `--mode` parameter (analyze only vs full)
- [ ] Implement match filtering logic
- [ ] Add sample randomization

### Phase 3 (Enhanced Features - 2-3 hours)
- [ ] Add `--mode=review` for interactive review
- [ ] Add `--mode=filter` for confidence filtering
- [ ] Add `--mode=report` for reporting
- [ ] Add output formatting options (JSON, CSV, table)

### Phase 4 (Nice-to-Have - 1-2 hours)
- [ ] Cached scraper results with TTL
- [ ] Match reconciliation (compare old vs new scrapes)
- [ ] Parallel analysis (run multiple --sport in parallel)
- [ ] Resume capability (restart interrupted analyses)

---

## Configuration File

**New section for `config/config.yaml`**:
```yaml
workflow:
  # Default mode if not specified
  default_mode: "full"  # full, scrape-only, analyze-only, etc.

  # Scraper settings
  scraper:
    output_file: "data/scraped_matches.json"
    cache_ttl: 3600  # Reuse scraper output for 1 hour
    auto_scrape_on_startup: false

  # Analysis settings
  analysis:
    default_limit: null  # null = all matches
    default_sample: null  # null = no sampling
    parallel_agents: true
    timeout_per_match: 30  # seconds

  # Reporting
  reporting:
    output_format: "json"  # json, csv, table
    include_metadata: true
    include_debug_logs: false
```

---

## Benefits Summary

1. **Faster Iteration**: Test with 5-10 matches in 2-5 minutes instead of 30 minutes
2. **Cost Efficient**: Only analyze matches you care about (fewer API calls)
3. **Flexibility**: Run scraper once, analyze multiple ways
4. **Debuggability**: See what's happening at each stage
5. **Reusability**: Share scraped data, replay with different parameters
6. **Reliability**: Can resume interrupted runs, cache intermediate results
7. **User Choice**: Data collection separate from analysis - YOU decide the scope

---

## Next Steps

1. **For immediate testing**: Use `--limit=10` with current code (easiest)
2. **For structured implementation**: Start with Phase 1 (1-2 hours work)
3. **For production**: Complete all phases for full flexibility

This gives you the ability to:
- Test fixes quickly (5 min instead of 30 min)
- Iterate on analysis logic without re-scraping
- Choose analysis scope on each run
- Build more sophisticated workflows later
