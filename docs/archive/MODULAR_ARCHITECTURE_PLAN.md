# Modular Architecture & User Experience Plan
**Status**: Phase 0 - Planning Complete
**Last Updated**: 2025-11-14

---

## 📋 Executive Summary

Current system processes 503+ matches into a huge JSON file that's hard to navigate. This plan implements:
1. **Modular Scraper** - Choose sports/leagues dynamically
2. **Opportunity Detection Agent** - Filter to only interesting matchups
3. **Telegram Interface** - Accessible, conversational output for end users
4. **Refactored Pipeline** - Each component on its own branch, independently testable

**Time Estimate**: 4-5 feature branches, ~2-3 weeks implementation

---

## 🔍 Current Architecture Issues

### Issue 1: Scraper League Data
**Problem**: Line 198 in `scraper/src/flashscore-scraper.js` hardcodes `league: 'Unknown League'`

**Root Cause**: Flashscore page doesn't always expose league/tournament info in the DOM. Need to:
- Extract from breadcrumb/header
- Infer from event URL structure
- Parse from event container attributes
- Fallback to category from navigation

**Impact**: Can't filter by specific leagues (e.g., "Champions League only")

### Issue 2: No Sport Selection
**Problem**: All matches scraped regardless of user needs

**Current Flow**:
```
orchestrator.run_scraper()
  → scrapes ALL football matches
  → analyzes ALL 500+
  → generates ~150 bets
  → 45+ minutes per run
```

**Limitation**: No way to test with just 10 tennis matches or 5 specific leagues

### Issue 3: Monolithic Analysis
**Problem**: No filtering between scraping and full analysis

**Current Pipeline**:
```
Scraper (500 matches)
  ↓
Internet Picks Agent (analyzes all 500)
  ↓
Data-Driven Agent (analyzes all 500)
  ↓
Synthesis Agent (synthesizes all 500)
  ↓
Results (154 bets in JSON file)
```

**Limitation**: Can't do exploratory analysis ("what leagues look interesting?")

### Issue 4: Output Accessibility
**Problem**: Results only in `data/results.json` - requires jq or text editor to read

**Current Output**:
- JSON file with 154 nested recommendation objects
- 2000+ lines, not human-readable
- No real-time updates to user
- No way for end user to explore/filter themselves

---

## 🏗️ Proposed Modular Architecture

### Phase 1: Modular Scraper (`feature/modular-scraper`)
**Goal**: Make scraper flexible and reusable

**Changes**:
```python
# OLD: orchestrator.py
matches = self.run_scraper()  # ← runs all sports

# NEW: scraper_agent.py (Google ADK-based)
scraper = ScraperAgent(config)
matches = await scraper.scrape_sports(
    sports=['football'],                    # NEW: select sports
    leagues=['Champions League', 'Serie A'],  # NEW: select leagues
    limit=50                                 # NEW: limit for testing
)
```

**Implementation Details**:

1. **Create `agents/scraper_agent.py`** (new ADK agent)
   - Uses Google ADK Runner pattern
   - Tools: `scrape_flashscore()` → Node.js bridge
   - Supports parameters: `--sports`, `--leagues`, `--limit`
   - Returns structured data with extracted leagues

2. **Fix `scraper/src/flashscore-scraper.js`**
   - **Extract league from Flashscore DOM:**
     ```javascript
     // Look for league in breadcrumb
     const breadcrumb = el.querySelector('[class*="breadcrumb"], .path');
     // Look for league in header
     const header = el.closest('[class*="category"], [class*="section"]');
     // Parse from tournament badge
     const badge = el.querySelector('[class*="tournament"], [class*="badge"]');
     ```
   - **Support sport/league filtering:**
     ```javascript
     class FlashscoreScraper {
       async scrape(options = {}) {
         const { sports = ['football'], leagues = null, limit = null } = options;
         // Apply filters before extraction
       }
     }
     ```
   - **Command-line interface:**
     ```bash
     npm run scrape -- --sports football,tennis --leagues "Champions League" --limit 50
     ```

3. **Create `scraper/config/scraper-config.yaml`**
   ```yaml
   scraper:
     sports:
       football:
         url: 'https://www.flashscore.com/football/'
         popular_leagues:
           - 'Champions League'
           - 'Premier League'
           - 'La Liga'
       tennis:
         url: 'https://www.flashscore.com/tennis/'
       basketball:
         url: 'https://www.flashscore.com/basketball/'
     selectors:
       league: ['.breadcrumb span', '.path a', '[class*="tournament"]']
       sport: '[class*="sport-category"]'
   ```

4. **Test cases** (`tests/test_scraper_agent.py`)
   - Scrape 10 football matches
   - Scrape specific league
   - Verify league extraction
   - Verify sport filtering

**Branch**: `feature/modular-scraper`
**Files Changed**:
- NEW: `agents/scraper_agent.py` (150 lines)
- MODIFIED: `scraper/src/flashscore-scraper.js` (add sport/league/limit support)
- NEW: `scraper/config/scraper-config.yaml`
- NEW: `tests/test_scraper_agent.py`

**Success Criteria**:
- ✅ Extract league from 90%+ of matches
- ✅ Filter by sport (football/tennis/basketball)
- ✅ Filter by league name
- ✅ Apply limit parameter (test with `--limit=10`)

---

### Phase 2: Opportunity Detection Agent (`feature/opportunity-agent`)
**Goal**: Intelligently filter matches before expensive analysis

**Problem Solved**: 500 matches → 50-100 interesting matches

**What It Does**:
```
Raw Scraped Data (500 matches)
  ↓
Opportunity Detection Agent (analyzes):
  - League popularity/odds availability
  - Match timing (live, upcoming)
  - Data completeness (is league well-documented?)
  - Statistical variability (any unusual patterns?)
  ↓
Filtered Results (50-100 high-quality matches)
  ↓
Analysis Agents (full analysis on only promising matches)
```

**Implementation**:

1. **Create `agents/opportunity_agent.py`** (ADK agent)
   ```python
   class OpportunityDetectionAgent:
       """
       Scans scraped data to identify high-potential matchups
       Uses internet search to assess league quality/relevance
       """

       async def analyze_opportunities(self, matches: List[Dict]) -> Dict:
           # Returns: {high_quality_matches, scores, reasons}
   ```

2. **Opportunity Scoring** (Python logic, no ADK needed):
   ```python
   def score_match(match):
       score = 0

       # +1.0 if has odds
       if match.get('odds'):
           score += 1.0

       # +0.5 if league is well-known
       if is_major_league(match['league']):
           score += 0.5

       # +0.5 if has recent match history
       if match.get('recent_matches'):
           score += 0.5

       # +0.3 if data is complete (teams, time, date, odds)
       if is_complete_match(match):
           score += 0.3

       return score  # 0.0 - 2.3
   ```

3. **Filtering Strategy**:
   ```python
   def filter_opportunities(matches, config):
       # Score all matches
       scored = [(m, score_match(m)) for m in matches]

       # Strategy 1: Top N matches by score
       if config.get('top_n'):
           return sorted(scored, key=lambda x: x[1], reverse=True)[:config['top_n']]

       # Strategy 2: Min score threshold
       if config.get('min_score'):
           return [m for m, s in scored if s >= config['min_score']]

       # Strategy 3: By league (advanced)
       if config.get('leagues_to_analyze'):
           leagues = config['leagues_to_analyze']
           return [m for m in matches if m['league'] in leagues]
   ```

4. **Create `config/opportunity-config.yaml`**
   ```yaml
   opportunity_detection:
     # Strategy: 'top_n', 'threshold', 'by_league'
     strategy: 'top_n'

     top_n: 100  # If top_n strategy, keep top 100

     min_score: 1.5  # If threshold strategy

     by_league:  # If by_league strategy
       - 'Champions League'
       - 'Premier League'
       - 'La Liga'

     # Don't even consider these leagues
     exclude_leagues:
       - 'Unknown League'
       - 'Friendly'
   ```

5. **Test cases** (`tests/test_opportunity_agent.py`)
   - Score matches correctly
   - Filter by top_n
   - Filter by threshold
   - Filter by league list
   - Handle missing data gracefully

**Branch**: `feature/opportunity-agent`
**Files Changed**:
- NEW: `agents/opportunity_agent.py` (200 lines)
- NEW: `config/opportunity-config.yaml`
- NEW: `tests/test_opportunity_agent.py`
- MODIFIED: `agents/orchestrator.py` (add opportunity agent to pipeline)

**Success Criteria**:
- ✅ Reduce 500 matches → 50-100 matches
- ✅ Scoring logic filters high-quality matches
- ✅ All 3 filtering strategies work
- ✅ 10x faster to analyze (15 min → 1.5 min)

---

### Phase 3: Telegram Agent Interface (`feature/telegram-agent`)
**Goal**: Make results accessible via conversational Telegram bot

**Current Output Problem**:
```
User: "Run analysis"
System: [45 minutes later] → results.json (2000 lines)
User: "How do I read this?"
```

**New Experience**:
```
User (Telegram): "/analyze football"
Bot: "🔍 Starting analysis... 503 matches found"
[5 min] Bot: "✅ Found 154 betting opportunities"
User: "/show top10"
Bot: "📊 Top 10 by confidence:
  1. Nigeria vs Gabon (0.75 confidence, 1.78 odds)
  2. ..."
User: "/league Champions"
Bot: "🏆 Champions League matches: 23 opportunities"
```

**Implementation**:

1. **Create `agents/telegram_agent.py`** (ADK agent)
   ```python
   class TelegramAgent:
       """
       Handles Telegram bot interactions
       - Long polling for updates
       - Real-time message formatting
       - User command routing
       """
   ```

2. **User Commands**:
   ```
   /start                  → Show help + status
   /analyze [sport]        → Start analysis pipeline
   /show [filter]          → Display results (all, top10, league X)
   /filter league [name]   → Filter by league
   /filter sport [name]    → Filter by sport
   /confidence [min]       → Show only high-confidence bets
   /odds [min-max]         → Filter by odds range
   /status                 → Current analysis status
   /export csv/json        → Export results
   ```

3. **Message Formatting**:
   ```python
   def format_bet_for_telegram(bet: Dict) -> str:
       return f"""
   ⚽ {bet['homeTeam']} vs {bet['awayTeam']}
   🏆 {bet['league']} • {bet['time']}

   🎯 Recommendation: {bet['recommendation']}
   📈 Pick: {bet['recommended_pick']} @ {bet['recommended_odds']}
   💪 Confidence: {bet['confidence']*100:.0f}%

   📝 {bet['reasoning'][:500]}...
   """
   ```

4. **Create `config/telegram-config.yaml`**
   ```yaml
   telegram:
     token: ${TELEGRAM_BOT_TOKEN}  # Set via env var
     polling:
       timeout: 30
       allowed_updates: ['message', 'callback_query']

     commands:
       analyze:
         description: 'Start analysis pipeline'
         params: ['sport', 'league', 'limit']

       show:
         description: 'Display results'
         params: ['filter', 'limit']

     formatting:
       results_per_page: 5
       preview_length: 500  # chars
   ```

5. **Database for User Preferences** (simple JSON):
   ```python
   user_preferences = {
       "123456789": {  # Telegram user ID
           "sports": ["football"],
           "leagues": ["Champions League"],
           "min_confidence": 0.7,
           "min_odds": 1.5,
           "notifications": True
       }
   }
   ```

6. **Real-time Updates**:
   ```python
   async def send_analysis_progress(user_id, message):
       # Called by orchestrator during analysis
       await telegram_agent.send_message(
           user_id,
           f"📊 {message}",
           parse_mode='Markdown'
       )
   ```

7. **Test cases** (`tests/test_telegram_agent.py`)
   - Mock Telegram API
   - Test command parsing
   - Test message formatting
   - Test user preference storage
   - Test real-time updates

**Branch**: `feature/telegram-agent`
**Files Changed**:
- NEW: `agents/telegram_agent.py` (300 lines)
- NEW: `config/telegram-config.yaml`
- NEW: `data/user_preferences.json` (template)
- NEW: `tests/test_telegram_agent.py`
- MODIFIED: `agents/orchestrator.py` (integration points)

**Dependencies**:
```bash
pip install python-telegram-bot
```

**Success Criteria**:
- ✅ Bot responds to /start command
- ✅ /analyze command triggers pipeline
- ✅ Results formatted and sent to user
- ✅ User can filter results via commands
- ✅ Real-time progress updates

---

### Phase 4: Refactored Orchestrator (`feature/modular-orchestrator`)
**Goal**: Combine all components into flexible pipeline

**New Orchestrator Design**:
```python
class BettingSystemOrchestrator:
    """
    Modular orchestrator supporting multiple execution paths
    """

    async def run_full_pipeline(
        self,
        sports: List[str] = None,
        leagues: List[str] = None,
        limit: int = None,
        telegram_user_id: int = None
    ) -> Dict:
        """
        Complete pipeline:
        1. Scrape (with filters)
        2. Detect opportunities (filter)
        3. Analyze (internet picks + data-driven)
        4. Synthesize (create recommendations)
        5. Notify (telegram or email)
        """

        # Step 1: Scrape
        matches = await self.scraper_agent.scrape_sports(
            sports=sports or ['football'],
            leagues=leagues,
            limit=limit
        )
        self.log_progress(f"📍 Scraped {len(matches)} matches")

        # Step 2: Filter opportunities
        opportunities = await self.opportunity_agent.analyze_opportunities(matches)
        self.log_progress(f"✅ Found {len(opportunities)} opportunities")

        # Step 3: Analyze (parallel)
        internet_picks = await self.internet_picks_agent.analyze_all(opportunities)
        data_driven = await self.data_driven_agent.analyze_all(opportunities)

        # Step 4: Synthesize
        recommendations = await self.synthesis_agent.synthesize_all(
            matches=opportunities,
            internet_picks=internet_picks,
            data_driven=data_driven
        )

        # Step 5: Notify
        if telegram_user_id:
            await self.telegram_agent.send_results(
                user_id=telegram_user_id,
                recommendations=recommendations
            )

        return recommendations
```

**New CLI Interface**:
```bash
# Run full analysis (football, all leagues, limit to 100)
python -m agents.orchestrator \
  --sports football \
  --limit 100 \
  --telegram-user 123456789

# Quick test mode (10 matches)
python -m agents.orchestrator \
  --sports football \
  --leagues "Champions League" \
  --limit 10

# Analysis only (skip scraping, use cached data)
python -m agents.orchestrator \
  --skip-scraper \
  --data-file data/last_scrape.json
```

**Configuration Management**:
```yaml
# config/pipeline-config.yaml
pipeline:
  steps:
    - name: scraper
      enabled: true
      config: scraper-config.yaml

    - name: opportunity_detection
      enabled: true
      config: opportunity-config.yaml

    - name: analysis
      enabled: true
      parallel: true  # internet_picks + data_driven in parallel

    - name: synthesis
      enabled: true

    - name: notification
      enabled: true
      channels: ['telegram', 'json_file']  # Can be extended
```

**Branch**: `feature/modular-orchestrator`
**Files Changed**:
- MODIFIED: `agents/orchestrator.py` (complete refactor)
- NEW: `config/pipeline-config.yaml`
- MODIFIED: `__main__.py` (CLI argument parsing)
- NEW: `tests/test_orchestrator_pipeline.py` (integration tests)

**Success Criteria**:
- ✅ All 4 phases integrated seamlessly
- ✅ CLI works with all parameter combinations
- ✅ Pipeline can skip steps (e.g., use cached scraper data)
- ✅ Telegram notifications work end-to-end
- ✅ Full pipeline runs in <15 minutes

---

## 🔄 Implementation Workflow

### Branch Strategy
Each phase gets its own feature branch, independently testable:

```
main (production)
├── feature/modular-scraper
│   └── PR #1: "Feat: Modular scraper with sport/league/limit support"
├── feature/opportunity-agent
│   └── PR #2: "Feat: Opportunity detection agent for filtering"
├── feature/telegram-agent
│   └── PR #3: "Feat: Telegram bot interface for results"
└── feature/modular-orchestrator
    └── PR #4: "Feat: Refactored pipeline orchestrator"
```

### Testing Strategy
Each branch has complete unit + integration tests:

```
feature/modular-scraper/
├── tests/
│   ├── test_scraper_agent.py         (unit tests)
│   └── test_scraper_integration.py   (with Node.js)
├── test_scraper_manually.sh          (manual testing guide)
└── PR description includes test results

feature/opportunity-agent/
├── tests/
│   ├── test_opportunity_scoring.py   (unit tests)
│   ├── test_opportunity_filtering.py (unit tests)
│   └── test_opportunity_with_scraper.py (integration with Phase 1)
└── PR includes before/after metrics

feature/telegram-agent/
├── tests/
│   ├── test_telegram_commands.py      (mock Telegram API)
│   ├── test_telegram_formatting.py    (output format tests)
│   └── test_telegram_integration.py   (end-to-end)
└── TELEGRAM_SETUP.md (instructions to get bot token)

feature/modular-orchestrator/
├── tests/
│   └── test_orchestrator_pipeline.py  (all phases together)
└── ORCHESTRATOR_USAGE.md (complete usage guide)
```

### Local Testing Checklist

**Phase 1 (Scraper)**:
- [ ] Scrape 10 football matches
- [ ] Verify league extracted (not "Unknown League")
- [ ] Test --limit parameter
- [ ] Test --sports filter
- [ ] Test --leagues filter

**Phase 2 (Opportunity)**:
- [ ] Run on Phase 1 output
- [ ] Verify scoring: poor matches scored low
- [ ] Verify filtering: 500 → 50-100 matches
- [ ] Test all 3 filtering strategies
- [ ] Compare time: before vs after

**Phase 3 (Telegram)**:
- [ ] Create Telegram test bot
- [ ] Test /start command
- [ ] Mock analysis results
- [ ] Send formatted message
- [ ] Test /show command variations
- [ ] Verify message pagination

**Phase 4 (Orchestrator)**:
- [ ] Run full pipeline with --limit=20
- [ ] Verify all 5 steps execute
- [ ] Check output quality
- [ ] Time complete run
- [ ] Test CLI parameter combinations

---

## 📊 Performance Impact

### Current System
```
Scraper:        5 min (510 matches from Flashscore)
Internet Picks: 15 min (510 matches to Google search)
Data-Driven:    15 min (510 matches to analysis)
Synthesis:      10 min (510 matches consolidated)
Notification:   <1 min
─────────────────────────────────
TOTAL:          45+ minutes
OUTPUT:         results.json (2000+ lines)
```

### After Implementation
```
Scraper:            5 min (510 matches, but 90 selected)
Opportunity Filter: <1 min (score & filter 510 → 90)
Internet Picks:     5 min (90 matches, 3x faster)
Data-Driven:        5 min (90 matches, 3x faster)
Synthesis:          2 min (90 matches, 5x faster)
Telegram:           <1 min (send formatted to user)
─────────────────────────────────
TOTAL:              ~18 minutes (60% faster)
OUTPUT:             Telegram bot (searchable, filterable, interactive)
```

### Advantages
- **66% faster**: 45 min → 18 min
- **User accessible**: Telegram vs JSON file
- **Filtered results**: Only 90 high-quality matches vs 500
- **Modular testing**: Test each phase independently
- **Reusable**: Each agent is standalone component

---

## 🛠️ Technical Decisions Explained

### Why Each Technology?

**Telegram over Email/Discord**:
- ✅ No setup required (users already have it)
- ✅ Real-time updates (push notifications)
- ✅ Interactive (buttons, inline keyboards)
- ✅ Works on mobile
- ✅ Free (no email service needed)

**Opportunity Agent (new) vs Existing System**:
- ✅ Saves 60% analysis time
- ✅ Filters out low-quality matches
- ✅ Simple heuristic-based (no ML needed yet)
- ✅ Can be enhanced later with ML scoring

**ADK for Scraper/Telegram**:
- ✅ Consistent architecture (all agents are ADK-based)
- ✅ Built-in tools/logging
- ✅ Easy to add more agents later
- ✅ Google-maintained (reliable)

**Separate Branches for Each Phase**:
- ✅ Merge one feature at a time
- ✅ Each can be tested independently
- ✅ Easier debugging if issues arise
- ✅ User can decide pacing

---

## 📝 Implementation Schedule

| Phase | Complexity | Est. Time | Branch | Dependencies |
|-------|-----------|-----------|--------|--------------|
| 1: Scraper | Medium | 3-4 hrs | `feature/modular-scraper` | None |
| 2: Opportunity | Low | 2-3 hrs | `feature/opportunity-agent` | Phase 1 |
| 3: Telegram | Medium | 4-5 hrs | `feature/telegram-agent` | Phase 1 |
| 4: Orchestrator | Medium | 3-4 hrs | `feature/modular-orchestrator` | All phases |

**Total**: ~12-16 hours (1-2 weeks, depending on testing depth)

---

## ✅ Success Metrics

**Phase 1 (Scraper)**:
- ✅ Extract league from 90%+ of matches
- ✅ Support sport/league/limit filtering
- ✅ 10-match test run completes in <2 min

**Phase 2 (Opportunity)**:
- ✅ Reduce matches from 500 → 50-100
- ✅ High-quality matches have higher scores
- ✅ 60% faster analysis on filtered set

**Phase 3 (Telegram)**:
- ✅ Bot responds within 2 seconds
- ✅ Format all bet types correctly
- ✅ User can filter results via commands

**Phase 4 (Orchestrator)**:
- ✅ Full pipeline with --limit=20 completes in <5 min
- ✅ All 4 phases integrate seamlessly
- ✅ Results sent to Telegram successfully

---

## 🚀 Future Enhancements

After Phase 4 is complete:
- [ ] Machine learning scoring for opportunity detection
- [ ] Historical performance tracking (which bets won?)
- [ ] User notification preferences (quiet hours, alert threshold)
- [ ] Database instead of JSON files
- [ ] Web dashboard (alternative to Telegram)
- [ ] Webhook support (POST results to external systems)
- [ ] Schedule automatic runs (daily at 3pm)
- [ ] Multi-user support (multiple Telegram users)

---

## 📚 References

**Google ADK Documentation**:
- Agent Development Kit: https://ai.google.dev/agentic/agents
- Runner & Tools: https://ai.google.dev/agentic/agents

**Telegram Bot API**:
- Full API Reference: https://core.telegram.org/bots/api
- Python Library: https://python-telegram-bot.readthedocs.io/

**Current Codebase**:
- Scraper: `/scraper/src/flashscore-scraper.js` (lines 75-226)
- Orchestrator: `/agents/orchestrator.py` (lines 26-350)
- Config: `/config/config.yaml`

---

**Next Steps**:
1. ✅ Review this plan
2. → Start Phase 1: Create feature/modular-scraper branch
3. → Fix league extraction in scraper
4. → Create ScraperAgent ADK wrapper
5. → Test with --limit=10 parameter
