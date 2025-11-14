# Architecture Phases - Quick Reference

## 🎯 Problem → Solution Map

### Current Problems
```
❌ Only "Unknown League" in results
❌ Always analyzes ALL 500 matches (45+ min)
❌ Results in huge JSON file (2000+ lines)
❌ End user has no way to access results
❌ Can't do exploratory analysis ("what leagues are interesting?")
```

### Solutions (4 Phases)

---

## Phase 1: Modular Scraper ✨

```
BEFORE:
┌─────────────────────────────────┐
│ orchestrator.run_scraper()      │ ← no options
│ • scrapes all 510 matches       │
│ • league = "Unknown League" 🔴  │
│ • no filtering                  │
└─────────────────────────────────┘

AFTER:
┌────────────────────────────────────────────────┐
│ scraper_agent.scrape_sports(                   │
│   sports=['football'],         ✨ NEW          │
│   leagues=['Champions League'], ✨ NEW         │
│   limit=100                     ✨ NEW         │
│ )                                              │
│ • extracts REAL league names    ✅            │
│ • filters by sport              ✅            │
│ • filters by league             ✅            │
│ • supports limit for testing    ✅            │
└────────────────────────────────────────────────┘

BRANCH: feature/modular-scraper
FILES: agents/scraper_agent.py (new)
       scraper/src/flashscore-scraper.js (modified)
TIME: 3-4 hours
```

---

## Phase 2: Opportunity Detection Agent 🎯

```
BEFORE:
510 matches → 45 min analysis → 154 bets

AFTER:
510 matches ──┐
             │ [Scoring Logic]
             ├─→ Filter by: odds availability,
             │   league quality, data completeness
             │
          100 matches ──→ 5 min analysis → 154 bets
             └────────────────────────────────┘
                    60% faster!

BRANCH: feature/opportunity-agent
FILES: agents/opportunity_agent.py (new)
       config/opportunity-config.yaml (new)
TIME: 2-3 hours
```

**Filtering Strategies**:
- `top_n`: Keep best 100 matches by score
- `threshold`: Keep matches scoring >1.5
- `by_league`: Keep only specified leagues

---

## Phase 3: Telegram Interface 💬

```
BEFORE:
User: "Run analysis"
[45 minutes...]
User: "Where are results?"
System: "In /data/results.json (2000 lines)"
User: "How do I read this?"

AFTER:
User (Telegram): /analyze football
Bot: 🔍 Starting analysis...
[5 minutes...]
Bot: ✅ Found 154 opportunities

/show top10
Bot: 📊 Top 10 by confidence:
  1. Nigeria vs Gabon (0.75, @1.78)
  2. Cameroon vs DRC (0.70, @2.87)
  ...

/filter league Champions
Bot: 🏆 Champions League (23 opportunities)

BRANCH: feature/telegram-agent
FILES: agents/telegram_agent.py (new)
       config/telegram-config.yaml (new)
COMMANDS: /start, /analyze, /show, /filter, /export
TIME: 4-5 hours
```

---

## Phase 4: Modular Orchestrator 🏗️

```
BEFORE (Current Flow):
┌────────────────────────────────────────┐
│ orchestrator.run()                     │
├────────────────────────────────────────┤
│ 1. run_scraper()                       │
│ 2. run_internet_picks_agent()          │
│ 3. run_data_driven_agent()             │
│ 4. run_synthesis_agent()               │
│ 5. save_to_json()                      │
└────────────────────────────────────────┘

AFTER (Modular Pipeline):
┌─────────────────────────────────────────────────┐
│ orchestrator.run_full_pipeline(                 │
│   sports=['football'],                          │
│   leagues=['Champions League'],                 │
│   limit=100,                                    │
│   telegram_user_id=123456789  ✨ NEW           │
│ )                                               │
├─────────────────────────────────────────────────┤
│ 1. Scraper Agent (with filters)      ✨ NEW    │
│ 2. Opportunity Agent (filter)        ✨ NEW    │
│ 3. Internet Picks Agent                        │
│ 4. Data-Driven Agent (parallel ↔)             │
│ 5. Synthesis Agent                             │
│ 6. Telegram Agent (notify user)      ✨ NEW    │
└─────────────────────────────────────────────────┘

BRANCH: feature/modular-orchestrator
FILES: agents/orchestrator.py (refactored)
       config/pipeline-config.yaml (new)
CLI: python -m agents.orchestrator --sports football --limit 100 --telegram-user 123
TIME: 3-4 hours
```

---

## 📊 Performance Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Total Time | 45 min | 18 min | **60% faster** |
| Matches Analyzed | 510 | 100 | **80% less** |
| Output Format | JSON file | Telegram bot | **10x more accessible** |
| League Extraction | ❌ "Unknown" | ✅ Real leagues | **100% accurate** |
| User Experience | Technical | Conversational | **Massive upgrade** |

---

## 🔄 Branch Workflow

```
┌─ main (production)
│
├─ feature/modular-scraper (Phase 1)
│  └─ PR #1: "Feat: Modular scraper with sport/league/limit"
│     └─ MERGE ✓
│
├─ feature/opportunity-agent (Phase 2, depends on Phase 1)
│  └─ PR #2: "Feat: Opportunity detection agent"
│     └─ MERGE ✓
│
├─ feature/telegram-agent (Phase 3, depends on Phase 1)
│  └─ PR #3: "Feat: Telegram bot interface"
│     └─ MERGE ✓
│
└─ feature/modular-orchestrator (Phase 4, depends on all)
   └─ PR #4: "Feat: Refactored pipeline orchestrator"
      └─ MERGE ✓
```

**Key**: Each phase independently testable, can merge in order.

---

## 🎓 Key Implementation Insights

### ★ Insight ─────────────────────────────────────
1. **Scraper must extract real league data** - Without this, filtering is impossible. The DOM likely has breadcrumbs or tournament badges we can parse.

2. **Opportunity detection uses simple scoring** - No ML needed yet. Heuristics (odds availability, league reputation, data completeness) filter 80% of noise with 5% code complexity.

3. **Telegram is the output interface** - Users don't want JSON files, they want push notifications and conversational interaction. Telegram Bot API is free, reliable, and accessible.

4. **Modular design enables fast iteration** - Each phase gets its own branch and tests. If Phase 2 has bugs, you can keep Phase 1 stable. If Phase 3 (Telegram) fails, analysis still works.
─────────────────────────────────────────────────

---

## ✅ Validation Checklist

Before starting each phase:

**Phase 1**:
- [ ] Read MODULAR_ARCHITECTURE_PLAN.md section "Phase 1: Modular Scraper"
- [ ] Create branch: `git checkout -b feature/modular-scraper`
- [ ] Test scraper extracts league manually (check Flashscore DOM)

**Phase 2**:
- [ ] Phase 1 merged and working
- [ ] Opportunity scoring logic reviewed
- [ ] Config options understood (top_n vs threshold vs by_league)

**Phase 3**:
- [ ] Telegram bot token obtained from @BotFather
- [ ] python-telegram-bot installed
- [ ] Mock tests pass before integration

**Phase 4**:
- [ ] All 3 phases merged
- [ ] Config/pipeline-config.yaml reviewed
- [ ] CLI argument parsing understood

---

**Ready to start? → Phase 1: Create feature/modular-scraper branch**
