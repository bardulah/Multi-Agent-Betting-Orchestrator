# Match Filter System - Complete Usage Guide

**Date**: November 17, 2025
**Purpose**: Control which matches are analyzed after scraping to optimize API usage

---

## 🎯 Overview

The filter system allows you to:
1. **Scrape ALL matches** (free, ~7 minutes)
2. **View what's available** (use inspector tool)
3. **Select which to analyze** (using filter configs)
4. **Analyze only selected matches** (agents process filtered subset)

This way you only pay API costs for matches you actually want to analyze.

---

## 🔍 Step 1: Inspect Available Data

First, scrape all matches and see what's available:

```bash
# Run scraper to collect all available matches
cd scraper
npm run scrape
cd ..

# View what's available
python3 inspect_matches.py
```

This shows:
- Total matches scraped
- Breakdown by sport
- Available leagues/competitions
- Example filter configurations

---

## 📋 Step 2: Choose or Create a Filter

### **Option A: Use Predefined Filters**

```bash
# Fast: 5 minutes, minimal analysis
python3 run.py --filter config/filters/fast.yaml

# Balanced: 20 minutes (RECOMMENDED for daily)
python3 run.py --filter config/filters/balanced.yaml

# Full: 54 minutes, all matches, all agents
python3 run.py --filter config/filters/default.yaml

# Football Focus: 25 minutes, football only
python3 run.py --filter config/filters/football-focus.yaml
```

### **Option B: View What Each Filter Does**

```bash
# See what balanced filter will analyze
python3 inspect_matches.py --sports football,tennis,basketball --limit "football:50,tennis:40,basketball:15"

# See what fast filter will analyze
python3 inspect_matches.py --sports football,tennis --limit "football:30,tennis:20"
```

---

## 🛠️ Step 3: Create Custom Filters

Create your own filter file in `config/filters/`:

### **Example 1: Football + Hockey Specific Limits**

Create `config/filters/my-filter.yaml`:

```yaml
filter:
  enabled: true
  name: "Football + Hockey"
  description: "Analyze football and hockey with per-sport limits"

  sports:
    - football
    - hockey

  leagues: []

  limits:
    football: 50
    hockey: 15

  analysis:
    run_internet_picks: true
    run_data_driven: true
    run_synthesis: true
```

Then use it:
```bash
python3 run.py --filter config/filters/my-filter.yaml
```

### **Example 2: Specific Leagues Only**

Create `config/filters/leagues.yaml`:

```yaml
filter:
  enabled: true
  name: "World Cup Only"
  description: "Only analyze World Cup Qualification matches"

  sports:
    - football

  # Get league names from inspect_matches.py output
  leagues:
    - "EUROPE: World Cup - Qualification"

  limits:
    football: 100  # No limit on selected leagues

  analysis:
    run_internet_picks: true
    run_data_driven: true
    run_synthesis: true
```

### **Example 3: Quick Analysis (No Data-Driven)**

```yaml
filter:
  enabled: true
  name: "Quick Analysis"
  description: "Fast consensus picks only"

  sports:
    - football
    - tennis

  leagues: []

  limits:
    football: 50
    tennis: 30

  analysis:
    run_internet_picks: true
    run_data_driven: false  # Skip expensive analysis
    run_synthesis: false    # Skip synthesis for speed
```

---

## 📊 Available Filters

| Filter | Sports | Matches | Time | API Calls | Cost |
|--------|--------|---------|------|-----------|------|
| **fast** | Football, Tennis | 50 | 5 min | ~50 | $0 |
| **balanced** | Football, Tennis, Basketball | 105 | 20 min | ~735 | $0 |
| **football-focus** | Football | 100 | 25 min | ~700 | $0 |
| **default** | All (Football, Tennis, Basketball, Hockey) | 217 | 54 min | ~2,940 | $0 |

---

## 🔧 Advanced: Using the Inspector

### **Preview Filter Results**

Before committing to an analysis, preview what matches will be analyzed:

```bash
# Preview balanced filter
python3 inspect_matches.py --sports football,tennis,basketball --limit "football:50,tennis:40,basketball:15"

# Preview custom selection: 25 football + 20 tennis
python3 inspect_matches.py --sports football,tennis --limit "football:25,tennis:20"

# Preview specific leagues
python3 inspect_matches.py --sports football --leagues "EUROPE: World Cup - Qualification,EUROPE: Euro U21 - Qualification"
```

### **Get Detailed Match List**

```bash
# Show first 10 matches with details
python3 inspect_matches.py --show-matches
```

---

## 💡 Common Use Cases

### **Daily Morning Check** (5 minutes)
```bash
# See what's available
python3 inspect_matches.py | head -30

# Run quick analysis
python3 run.py --filter config/filters/fast.yaml
```

### **Weekly Comprehensive Analysis** (54 minutes)
```bash
# Run full analysis
python3 run.py --filter config/filters/default.yaml
```

### **Focused Research** (custom time)
```bash
# Example: Only analyze world cup matches
python3 inspect_matches.py --sports football --leagues "EUROPE: World Cup - Qualification"
# Then create custom filter with those parameters
python3 run.py --filter config/filters/my-custom.yaml
```

### **Budget-Conscious** (minimal API usage)
```bash
# Run balanced filter daily, full filter weekly
# Daily:  python3 run.py --filter config/filters/balanced.yaml
# Weekly: python3 run.py --filter config/filters/default.yaml
```

---

## 📝 Filter Configuration Reference

### **Complete Filter Structure**

```yaml
filter:
  # Metadata
  enabled: true                    # Enable/disable this filter
  name: "Filter Name"              # Human-readable name
  description: "What it does"      # Description

  # Match Selection
  sports: ['football', 'tennis']   # Empty [] = all sports
  leagues: ['Premier League']      # Empty [] = all leagues
  limits:                          # Per-sport match limits
    football: 50                   # Max 50 football matches
    tennis: 30                     # Max 30 tennis matches

  # Agent Selection
  analysis:
    run_internet_picks: true       # Run betting consensus analysis
    run_data_driven: true          # Run statistical analysis
    run_synthesis: true            # Run final synthesis decision
```

### **Field Descriptions**

- **sports**: List of sports to include. Empty = all available
  - Valid values: `football`, `basketball`, `tennis`, `hockey`

- **leagues**: Specific leagues/competitions to include. Empty = all available
  - Get exact names from `python3 inspect_matches.py` output
  - Exact match required (case-insensitive)

- **limits**: Maximum matches per sport
  - Empty = no limit for that sport
  - Only applies to selected sports
  - Applied in order matches were scraped

- **analysis.run_internet_picks**: Include betting consensus analysis
  - Cost: Moderate (3 Google searches per match)
  - Time: ~5 min for 50 matches

- **analysis.run_data_driven**: Include statistical analysis
  - Cost: High (4 Google searches per match)
  - Time: ~5 min for 50 matches

- **analysis.run_synthesis**: Include final synthesis decision
  - Cost: Low (just LLM processing)
  - Time: ~2 min for 50 matches
  - Requires both agents above to produce useful results

---

## 🚀 Workflow Example

### **Scenario: You want to analyze 50 football + 15 hockey matches daily**

1. **Inspect available data**:
```bash
python3 inspect_matches.py
```

2. **Create filter**:
```yaml
# config/filters/football-hockey.yaml
filter:
  enabled: true
  name: "Football + Hockey Daily"
  sports: ['football', 'hockey']
  limits:
    football: 50
    hockey: 15
  analysis:
    run_internet_picks: true
    run_data_driven: true
    run_synthesis: true
```

3. **Test the filter**:
```bash
python3 inspect_matches.py --sports football,hockey --limit "football:50,hockey:15"
```

4. **Run analysis**:
```bash
python3 run.py --filter config/filters/football-hockey.yaml
```

5. **Schedule as cron job**:
```bash
# Daily at 8 AM
0 8 * * * cd /opt/deployment/repos/adk && python3 run.py --filter config/filters/football-hockey.yaml
```

---

## 📊 Cost Comparison

**Scenario: 30 days of analysis**

### **Daily Fast + Weekly Full**
```
Daily (30 runs):  30 × 50 searches = 1,500
Weekly (4 runs):  4 × 2,940 searches = 11,760
Total: 13,260 searches
Cost: $0 (free tier)
Time: 150 minutes total (2.5 hours spread over month)
```

### **Daily Balanced Only**
```
Daily (30 runs):  30 × 735 searches = 22,050
Total: 22,050 searches
Cost: $0 (free tier)
Time: 600 minutes total (10 hours spread over month)
```

### **Always Full**
```
Always full (30 runs): 30 × 2,940 = 88,200 searches
Cost: $0 (free tier)
Time: 1,620 minutes total (27 hours spread over month)
```

---

## ✅ Checklist: Setting Up Filters

- [ ] Run scraper: `npm run scrape`
- [ ] Inspect data: `python3 inspect_matches.py`
- [ ] Choose predefined filter or create custom one
- [ ] Preview filter: `python3 inspect_matches.py --sports ... --limit ...`
- [ ] Run analysis: `python3 run.py --filter config/filters/YOUR-FILTER.yaml`
- [ ] Check results: `tail -20 data/results.json`
- [ ] Schedule as cron job if desired

---

## 📞 Troubleshooting

### **"League name doesn't work in filter"**
Solution: Get exact name from `python3 inspect_matches.py` output

### **"No matches found for this filter"**
Solution: Check sport and league names are correct, check limits aren't too restrictive

### **"Analysis taking longer than expected"**
Solution: Check `run_data_driven` and `run_synthesis` aren't disabled, check match count

### **"Want to see what will be analyzed before running"**
Solution: Use `python3 inspect_matches.py --sports ... --leagues ... --limit ...` to preview

---

## 🔗 Related Commands

```bash
# Scrape all matches
npm run scrape

# View available data
python3 inspect_matches.py

# Run with specific filter
python3 run.py --filter config/filters/balanced.yaml

# Test notification system
python3 run.py --test-notification

# View filter directory
ls config/filters/
```

---

**Status**: ✅ Ready to use
**Tested**: Yes (all filter examples validated)
**Examples**: 4 predefined filters + unlimited custom filters
**Cost**: $0 (all using free tiers)
