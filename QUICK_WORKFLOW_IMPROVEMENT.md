# Quick Workflow Improvement (Phase 1 - 1 Hour)

## Problem We're Solving

Currently, every test run takes 25-45 minutes because it:
1. Scrapes 510 matches (5-10 min)
2. Analyzes all 510 (15-25 min)
3. Processes everything

**Goal**: Be able to test with just 10 matches in 2-5 minutes

## Solution: Add `--limit` Parameter

This is the fastest way to get faster feedback loops.

### Step 1: Update `run.py`
Add argument parsing at the top:

```python
import argparse

# In main():
parser = argparse.ArgumentParser(description='Betting analysis system')
parser.add_argument('--limit', type=int, default=None,
                    help='Limit to first N matches (e.g., --limit=10)')
parser.add_argument('--sample', type=int, default=None,
                    help='Random sample of N matches (e.g., --sample=20)')
args = parser.parse_args()

# Use args.limit and args.sample in orchestrator
```

### Step 2: Update `orchestrator.py`

In the `run_betting_analysis()` function:

```python
def run_betting_analysis(config, limit=None, sample=None):
    """
    Analyze matches from scraped data

    Args:
        config: Configuration dict
        limit: If set, only analyze first N matches
        sample: If set, analyze random N matches
    """

    # Load scraped matches
    matches = load_matches_from_file(config)

    # Apply limit filter
    if limit:
        matches = matches[:limit]
        logger.info(f"Limited to first {limit} matches")

    # Apply random sample
    if sample:
        import random
        matches = random.sample(matches, min(sample, len(matches)))
        logger.info(f"Selected random {len(matches)} matches")

    # Process matches as normal
    results = []
    for match in matches:
        result = process_match(match, config)
        results.append(result)

    return results
```

### Step 3: Test Usage

```bash
# Full analysis (current behavior)
python run.py

# Test with first 5 matches only (~2-3 min)
python run.py --limit=5

# Test with first 10 matches (~3-5 min)
python run.py --limit=10

# Random 20 matches (~5-8 min)
python run.py --sample=20

# Random 10 matches from football only (~2-5 min, if you also add --sport)
python run.py --sample=10 --sport=football
```

## Time Comparison

| Scenario | Matches | Time | Improvement |
|----------|---------|------|-------------|
| Current | 510 | 25-45 min | - |
| With `--limit=5` | 5 | 2-3 min | **85% faster** ✅ |
| With `--limit=10` | 10 | 3-5 min | **80% faster** ✅ |
| With `--limit=50` | 50 | 8-12 min | **60% faster** ✅ |

## Why This Matters

When testing the fixes:
- **Old way**: Run full 45-min test, wait for results
- **New way**: Run 5-match test in 3 min, verify working, then decide to run full test if needed

## Implementation Steps

1. **Copy-paste** the argparse code into `run.py` (5 min)
2. **Add** the limit/sample logic to `orchestrator.py` (5 min)
3. **Test** with `--limit=5` to verify it works (10 min)
4. **Done!** You now have fast iteration (total: 20 min)

## Example Usage Pattern

```bash
# 1. Quick sanity check (2 min)
python run.py --limit=3

# 2. See if fixes working (5 min)
python run.py --limit=10

# 3. If good, run fuller analysis (15 min)
python run.py --limit=100

# 4. Finally, commit and run full (45 min)
python run.py
```

## Next Improvements (Later)

Once `--limit` works, adding these is easy:
- `--sport=football` - Analyze only football
- `--sports=football,basketball` - Multiple sports
- `--sample=20` - Random sample
- `--min-confidence=0.75` - Filter by threshold

But **`--limit` alone saves you 80% of wait time!**

## Files to Modify

1. `/opt/deployment/repos/adk/run.py` - Add argparse
2. `/opt/deployment/repos/adk/agents/orchestrator.py` - Add limit logic

That's it! Two files, minimal changes, huge time savings.
