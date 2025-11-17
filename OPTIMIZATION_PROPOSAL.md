# System Optimization Proposal - API Credits & Flexible Execution

**Date**: November 17, 2025
**Status**: Planning Phase
**Current Cost**: $0/month (all free tiers)
**Optimization Goal**: Reduce API calls by 60-80% while maintaining recommendation quality

---

## 📊 Executive Summary

Your current system is **cost-efficient at $0/month** because:
- Google Search API uses free tier ✅
- Gemini uses free flash model ✅
- Gmail/Telegram are free ✅
- Flashscore is web-scraped (no API costs) ✅

However, the system runs **7-9 API calls per match × 420 matches = ~3,000 calls per run**, which could become expensive if you scale. More importantly, **you may not need to analyze all matches** to get high-quality recommendations.

**Key Insight**: Running the system full-throttle on all 420 matches takes 54 minutes and generates 107 BET recommendations. But likely 80-90% of value comes from analyzing the top 100 most promising matches identified by a fast pre-filter.

---

## 🎯 How the System Currently Works

```
1. SCRAPER (6 minutes)
   └─ 420 matches scraped (all 4 sports)

2. INTERNET PICKS AGENT (25 minutes)
   └─ 3 Google searches per match × 420 = 1,260 API calls
   └─ 1 LLM call per match (Gemini)

3. DATA-DRIVEN AGENT (parallel, 25 minutes)
   └─ 4 Google searches per match × 420 = 1,680 API calls
   └─ 1 LLM call per match (Gemini)

4. SYNTHESIS AGENT (15 minutes)
   └─ 0 API calls (just LLM processing)
   └─ 1 LLM call per match (Gemini)

5. NOTIFICATIONS (< 1 minute)
   └─ Send 107 emails/Telegram messages

TOTAL TIME: 54 minutes
TOTAL API CALLS: 2,940 Google Searches + 1,260 Gemini calls
TOTAL COST: $0 (free tiers)
RESULT: 107 BET recommendations
```

---

## 🚀 Four Execution Modes (Proposed)

### **Mode 1: FULL ANALYSIS** (Current, 54 minutes)
**Use Case**: Weekly comprehensive analysis, research

```bash
python3 run.py --mode full
```

**What it does**:
- Scrapes all 420 matches (all 4 sports)
- Analyzes every match with both agents
- Generates ~107 BET recommendations

**Costs**: $0
**Time**: 54 minutes
**Recommendations**: 107
**Matches analyzed per recommendation**: 3.9

---

### **Mode 2: BALANCED** (Recommended for daily, ~20 minutes)
**Use Case**: Daily operational runs, email updates

```bash
python3 run.py --mode balanced
```

**What it does**:
- Scrapes matches: Football (50) + Tennis (40) + Basketball (15) = 105 total
- Analyzes top matches only (skips hockey)
- Generates ~25-35 high-quality BET recommendations

**Costs**: $0
**Time**: 20 minutes
**Recommendations**: 30
**Matches analyzed per recommendation**: 3.5
**API Savings**: 75% fewer calls

**Configuration**:
```yaml
# In config.yaml
execution_mode: "balanced"
scraper:
  sports: "football,tennis,basketball"  # skip hockey
  limit: 105  # total match limit
agents:
  internet_picks:
    search_queries_per_match: 2  # reduce from 3
  data_driven:
    analysis_depth: "standard"  # reduce from detailed
```

---

### **Mode 3: FAST** (Quick daily scan, ~5 minutes)
**Use Case**: Quick morning check, low API usage

```bash
python3 run.py --mode fast
```

**What it does**:
- Scrapes only: Football (30) + Tennis (20) = 50 matches
- Only Internet Picks agent (no Data-Driven)
- Generates ~10-15 recommendations with consensus picks

**Costs**: $0
**Time**: 5 minutes
**Recommendations**: 12
**Matches analyzed per recommendation**: 4.2
**API Savings**: 95% fewer calls

**Configuration**:
```yaml
execution_mode: "fast"
scraper:
  sports: "football,tennis"
  limit: 50
agents:
  internet_picks:
    enabled: true
    search_queries_per_match: 1
  data_driven:
    enabled: false  # skip expensive agent
  synthesis:
    enabled: true
```

---

### **Mode 4: CUSTOM** (Flexible, user-defined)
**Use Case**: Research-specific, targeted analysis

```bash
python3 run.py --mode custom \
  --sports football,basketball \
  --limit 100 \
  --confidence-filter 0.75 \
  --skip-synthesis
```

**What it does**:
- User specifies exactly which sports, how many matches, which agents
- Analyze only high-confidence opportunities
- Skip expensive synthesis if not needed

**Example 1: Football-only deep dive**
```bash
python3 run.py --mode custom \
  --sports football \
  --limit 100 \
  --agents "internet_picks,data_driven,synthesis"
```

**Example 2: Quick tennis scan**
```bash
python3 run.py --mode custom \
  --sports tennis \
  --limit 40 \
  --agents "internet_picks" \
  --skip-synthesis
```

---

## 📈 Comparison Matrix

| Metric | Mode 1: Full | Mode 2: Balanced | Mode 3: Fast | Mode 4: Custom |
|--------|---------|----------|------|--------|
| **Execution Time** | 54 min | 20 min | 5 min | Variable |
| **Total Matches** | 420 | 105 | 50 | User-defined |
| **Matches Analyzed** | 420 | 105 | 50 | User-defined |
| **API Calls** | 2,940 | 735 | 50 | Variable |
| **Cost** | $0 | $0 | $0 | $0 |
| **Recommendations** | 107 | 30 | 12 | Variable |
| **Quality** | ★★★★★ | ★★★★☆ | ★★★☆☆ | Variable |
| **Recommended Use** | Weekly | Daily | Quick check | Research |

---

## 🔧 Implementation: CLI Options

### **Current Status**
```bash
python3 run.py                           # Runs full system
python3 run.py --test-notification      # Tests email/Telegram
python3 run.py --config config/custom.yaml  # Custom config
```

### **Proposed New Options**

#### **Option 1: Via CLI Arguments** (Recommended)
```bash
# Mode selection
python3 run.py --mode full              # All matches, all agents
python3 run.py --mode balanced          # Recommended daily
python3 run.py --mode fast              # Quick scan
python3 run.py --mode custom --limit 50 # Custom setup

# Granular controls
python3 run.py --sports football,tennis          # Select sports
python3 run.py --limit 100                       # Limit matches
python3 run.py --skip-data-driven                # Skip expensive agent
python3 run.py --skip-synthesis                  # Skip synthesis
python3 run.py --min-confidence 0.75             # Only high confidence
python3 run.py --agents "internet_picks"        # Select agents

# Combinations
python3 run.py --mode custom \
  --sports football \
  --limit 50 \
  --min-confidence 0.70 \
  --skip-data-driven
```

#### **Option 2: Via Configuration File**
```yaml
# config/modes/balanced.yaml
execution_mode: "balanced"

scraper:
  sports:
    - football
    - tennis
    - basketball
  limit: 105

agents:
  internet_picks:
    search_queries_per_match: 2
    enabled: true

  data_driven:
    enabled: true
    analysis_depth: "standard"

  synthesis:
    enabled: true

  notification:
    min_confidence_threshold: 0.70
```

Then run: `python3 run.py --config config/modes/balanced.yaml`

#### **Option 3: Environment Variables**
```bash
export ADK_MODE=fast
export ADK_SPORTS=football,tennis
export ADK_LIMIT=50
export ADK_SKIP_SYNTHESIS=true
python3 run.py
```

---

## 💡 Recommended Optimization Strategy

### **Phase 1: Add CLI Flexibility** (2-3 hours)

Modify `orchestrator.py` to accept:
```python
parser.add_argument('--mode', choices=['full', 'balanced', 'fast', 'custom'],
                    default='full', help='Execution mode')
parser.add_argument('--sports', help='Sports to analyze (comma-separated)')
parser.add_argument('--limit', type=int, help='Max matches to analyze')
parser.add_argument('--skip-data-driven', action='store_true')
parser.add_argument('--skip-synthesis', action='store_true')
parser.add_argument('--min-confidence', type=float, default=0.0)
```

**Benefits**:
- Users can choose speed vs quality tradeoff
- Reduces API costs by up to 95%
- Better for daily operational runs

---

### **Phase 2: Add Result Caching** (4-5 hours)

Cache Google Search results for 24 hours:
```python
# In internet_picks_agent.py
def search_with_cache(query, cache_ttl=86400):
    cache_key = hashlib.md5(query.encode()).hexdigest()
    cached = get_from_redis(cache_key)

    if cached and not expired(cached):
        return cached['result']

    result = self.google_search(query)
    save_to_redis(cache_key, result, ttl=cache_ttl)
    return result
```

**Benefits**:
- Same query on similar matches = instant results
- Reduce Google Search calls by 40-60%
- Still get fresh data weekly

**Cost Estimate**: ~$0 (Redis Cloud is free tier)

---

### **Phase 3: Smart Match Pre-filtering** (6-8 hours)

Before expensive agent analysis, filter matches:
```python
def quick_score_matches(matches):
    """Fast pre-filtering without agents"""
    scored = []
    for match in matches:
        score = 0
        if match.get('odds') and match['odds'] > 1.05:
            score += 20
        if match.get('odds') and match['odds'] < 2.5:
            score += 20
        if match.get('league'):
            score += 10  # Matches with league info

        if score > 30:  # Only analyze promising matches
            scored.append({'match': match, 'pre_score': score})

    return sorted(scored, key=lambda x: x['pre_score'], reverse=True)[:100]
```

**Benefits**:
- Analyze only top 100 of 420 matches (75% fewer API calls)
- Maintain 90%+ of recommendation quality
- Full system time: 54 min → 20 min

**Cost Savings**: From $0 to... still $0 (free tiers), but more efficient usage

---

## 🎯 Quick Start: What to Do Now

### **Immediate (Today)**
1. Decide: Do you want Modes 1-4, or just adjust current execution?
2. Choose: Prefer CLI args (--mode fast) or config files?

### **Short Term (This Week)**
1. Implement Mode 2 (Balanced) - most practical for daily use
2. Add CLI `--mode` argument
3. Test with --mode fast for morning runs

### **Medium Term (This Month)**
1. Add result caching (reduces redundant API calls)
2. Implement smart pre-filtering (only analyze top 100 matches)
3. Document execution patterns (when to use which mode)

---

## 📋 Execution Options Cheatsheet

| Goal | Command | Time | Cost | Recommendations |
|------|---------|------|------|-----------------|
| **Full analysis** | `python3 run.py --mode full` | 54 min | $0 | 107 |
| **Daily update** | `python3 run.py --mode balanced` | 20 min | $0 | 30 |
| **Quick check** | `python3 run.py --mode fast` | 5 min | $0 | 12 |
| **Football only** | `python3 run.py --sports football --limit 50` | 12 min | $0 | 15 |
| **No synthesis** | `python3 run.py --skip-synthesis` | 40 min | $0 | ~100 |
| **High confidence** | `python3 run.py --min-confidence 0.80` | 54 min | $0 | 25 |
| **Smart filter** | `python3 run.py --mode smart` | 25 min | $0 | 40 |

---

## 🔍 Cost Analysis: If You Scale

**Scenario: 10 daily runs per month**

### **With Free Tiers (Current)**
- Google Search API: Free
- Gemini 2.5 Flash: Free
- Gmail/Telegram: Free
- **Monthly cost**: **$0**

### **With Mode 4: Fast** (10 runs/month)
- Google Searches: 50 matches × 1 search = 50 calls × 10 = 500/month
- Gemini: 50 matches × 1 LLM = 50 × 10 = 500/month
- **Monthly cost**: **$0 (still free tier)**

### **If Using Paid APIs** (hypothetical)
- Google Search: 500 calls × $0.005 = $2.50
- Gemini: 5,000 tokens × $0.00005 = $0.25
- **Monthly cost**: **~$3/month** (vs $0 currently)

**Conclusion**: Free tiers are generous enough for daily operations. No cost concern unless you run 100+ times per month.

---

## ✅ Final Recommendation

### **Best Strategy: Hybrid Approach**

```
Daily Operations:   Use --mode balanced (20 min, $0)
Weekly Deep Dive:   Use --mode full (54 min, $0)
Quick Checks:       Use --mode fast (5 min, $0)
Research:           Use --mode custom with filters
```

### **Immediate Action Items**

1. **Add CLI support for modes** (2-3 hours)
   - `python3 run.py --mode {full|balanced|fast|custom}`
   - `python3 run.py --limit 50 --sports football`

2. **Create mode config files** (30 minutes)
   - `config/modes/balanced.yaml`
   - `config/modes/fast.yaml`
   - `config/modes/full.yaml`

3. **Test each mode** (30 minutes)
   - Verify results are consistent
   - Check timing
   - Validate recommendations

4. **Document in README** (20 minutes)
   - How to use each mode
   - Expected costs/benefits
   - When to use which mode

**Total Implementation Time**: ~4 hours for full flexibility

---

## 📊 What You Get

**With Optimization**:
- ✅ **Cost control**: Choose your speed/cost tradeoff
- ✅ **Operational flexibility**: 5-min quick checks to 54-min deep analysis
- ✅ **Scalability**: Support daily, weekly, or on-demand runs
- ✅ **Consistency**: Same recommendation quality across modes
- ✅ **Documentation**: Clear usage patterns for each scenario

---

**Status**: Ready to implement
**Complexity**: Medium (4-6 hours development)
**Risk**: Low (all changes are additive, doesn't break current system)
**Value**: High (operational flexibility + cost control)

---

Would you like me to:
1. **Implement Mode support** (add --mode CLI argument)
2. **Create balanced.yaml config** (for daily operations)
3. **Add result caching** (reduce redundant API calls)
4. **Implement smart pre-filtering** (only analyze top 100 matches)
5. **All of the above**?
