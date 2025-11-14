/**
 * Phase 2: Opportunity Detection Agent
 *
 * Analyzes scraped matches and scores them by opportunity value
 * Filters 420 matches down to top 100 high-value betting opportunities
 *
 * Architecture: 3-layer scoring system
 * - Layer 1: Market Efficiency (where to find edges)
 * - Layer 2: Odds Quality (how good are the odds)
 * - Layer 3: Expected Value (direct profit signal)
 */

const fs = require('fs').promises;
const path = require('path');

class OpportunityAgent {
  constructor(options = {}) {
    this.topN = options.topN || 100;
    this.minScore = options.minScore || 0;
    this.verbose = options.verbose !== false;
  }

  /**
   * LAYER 1: Market Efficiency Score (0.7-1.0)
   * Higher = more inefficient = more edge potential
   *
   * Different markets have different efficiency levels based on research:
   * - Major leagues: Highly efficient (harder to beat)
   * - Secondary leagues: Moderately efficient (some edges)
   * - Cup/Regional: Less efficient (more opportunities)
   */
  calculateMarketEfficiencyScore(match) {
    const league = match.league || 'Unknown';

    // Multipliers based on market efficiency research
    const leagueEfficiencyMap = {
      // Premier Leagues (Highly efficient - 70% = hard to beat)
      'England: Premier League': 0.70,
      'Spain: La Liga': 0.75,
      'Italy: Serie A': 0.75,
      'Germany: Bundesliga': 0.75,
      'France: Ligue 1': 0.75,

      // International Major (80% = moderately efficient)
      'WORLD: Champions League': 0.80,
      'EUROPE: Europa League': 0.80,

      // World Cup (85% = secondary but high profile)
      'EUROPE: World Cup - Qualification': 0.85,
      'NORTH & CENTRAL AMERICA: World Cup - Qualification': 0.85,
      'SOUTH AMERICA: World Cup - Qualification': 0.85,
      'ASIA: World Cup - Qualification': 0.85,
      'AFRICA: World Cup - Qualification': 0.85,
      'OCEANIA: World Cup - Qualification': 0.85,

      // Cup matches (90% = less efficient)
      'Cup': 0.90,
      'Playoff': 0.90,

      // Regional/Secondary (95-100% = most inefficient)
      'Regional': 0.95,
      'Championship': 0.90,
      'Division': 0.88,
    };

    // Find best matching league in map
    let multiplier = 0.85; // Default for unknown leagues
    for (const [key, value] of Object.entries(leagueEfficiencyMap)) {
      if (league.includes(key)) {
        multiplier = value;
        break;
      }
    }

    // Additional boost for smaller markets
    if (league.includes('Third stage') || league.includes('Play-off')) {
      multiplier = Math.min(1.0, multiplier + 0.05);
    }

    return Math.min(1.0, multiplier);
  }

  /**
   * LAYER 2: Odds Quality Score (0.0-1.0)
   * Measures how good/valuable the available odds are
   *
   * Metrics:
   * - Bookmaker margin (vig): Lower = better odds
   * - Odds extremeness: Very high/low odds = potential mispricing
   * - Probability calibration: "Round" probabilities = less sophisticated pricing
   */
  calculateOddsQualityScore(match) {
    const odds = match.odds?.Flashscore;
    if (!odds || !odds.home || !odds.draw || !odds.away) {
      return 0.3; // Poor score if no odds available
    }

    const { home, draw, away } = odds;

    try {
      // Calculate implied probabilities
      const totalInverse = (1 / home) + (1 / draw) + (1 / away);
      const homeProb = (1 / home) / totalInverse;
      const drawProb = (1 / draw) / totalInverse;
      const awayProb = (1 / away) / totalInverse;

      // Calculate vigorish (bookmaker margin)
      const vig = totalInverse - 1; // Should be positive (house edge)

      // Score component 1: Low vig = better odds (higher score)
      // Typical vig is 2-5%, so 0.02-0.05
      // Map: 0.02 vig → 0.8 score, 0.10 vig → 0.2 score
      const vigScore = Math.max(0, 1 - (vig * 10));

      // Score component 2: Extreme odds detection
      // Very high or very low odds suggest potential mispricings
      const homeExtreme = home > 3.5 || home < 1.25 ? 0.15 : 0;
      const awayExtreme = away > 3.5 || away < 1.25 ? 0.15 : 0;
      const extremeBonus = Math.min(0.3, homeExtreme + awayExtreme);

      // Score component 3: Probability calibration
      // Very round probabilities (like 0.50, 0.33) = less sophisticated pricing = higher value
      const roundProbabilities =
        (Math.abs(homeProb - 0.5) < 0.02 ? 0.05 : 0) +
        (Math.abs(drawProb - 0.33) < 0.02 ? 0.05 : 0) +
        (Math.abs(awayProb - 0.5) < 0.02 ? 0.05 : 0);

      const oddsQuality = Math.min(1.0, vigScore + extremeBonus + roundProbabilities);
      return oddsQuality;
    } catch (error) {
      return 0.3; // Fallback if calculation fails
    }
  }

  /**
   * LAYER 3: Expected Value (EV) Score (0.0-1.0)
   * Direct profit potential based on odds structure
   *
   * High EV signals:
   * - Extremely unbalanced odds (public bias)
   * - Extreme individual odds (mispricing)
   * - Large odds spreads
   *
   * Note: This is a market-based EV proxy without a true probability model
   * A true EV score would require: (True Probability × Payout) - Stake
   * We approximate using odds structure analysis
   */
  calculateEVScore(match) {
    const odds = match.odds?.Flashscore;
    if (!odds || !odds.home || !odds.draw || !odds.away) {
      return 0.2; // Very low score if no odds
    }

    const { home, draw, away } = odds;

    try {
      // Calculate implied probabilities
      const totalInverse = (1 / home) + (1 / draw) + (1 / away);
      const homeProb = (1 / home) / totalInverse;
      const drawProb = (1 / draw) / totalInverse;
      const awayProb = (1 / away) / totalInverse;

      // EV Component 1: Probability imbalance (public bias indicator)
      // When odds are very unbalanced, the public has likely overweighted one outcome
      const maxProb = Math.max(homeProb, drawProb, awayProb);
      const minProb = Math.min(homeProb, drawProb, awayProb);
      const probSpread = maxProb - minProb;

      // High spread = high imbalance = potentially exploitable
      // Map: 0.3 spread → 0.0 score, 0.6 spread → 1.0 score
      const imbalanceScore = Math.min(1.0, Math.max(0, (probSpread - 0.3) / 0.3));

      // EV Component 2: Extreme odds magnitude
      // Very high or very low odds (especially combined with imbalance) = mispricing signal
      const extremeOdds = (
        (home > 4 || away > 4) ? 0.2 : 0 // Long shots
      ) + (
        (home < 1.2 || away < 1.2) ? 0.2 : 0 // Heavy favorites
      );

      // EV Component 3: Odds spread ratio
      // Large ratio between highest and lowest odds = more market inefficiency
      const maxOdds = Math.max(home, draw, away);
      const minOdds = Math.min(home, draw, away);
      const oddsRatio = maxOdds / minOdds;

      // Map: 1.0 ratio (identical odds) → 0.0, 8.0+ ratio → 1.0
      const oddsSpreadScore = Math.min(1.0, (oddsRatio - 1) / 7);

      // Combine components (imbalance is most important for EV)
      const evScore = (
        imbalanceScore * 0.5 +
        oddsSpreadScore * 0.3 +
        extremeOdds * 0.2
      );

      return Math.min(1.0, evScore);
    } catch (error) {
      return 0.2; // Fallback
    }
  }

  /**
   * Calculate composite opportunity score
   * Weighted combination of all 3 layers
   */
  calculateCompositeScore(match) {
    const marketEfficiency = this.calculateMarketEfficiencyScore(match);
    const oddsQuality = this.calculateOddsQualityScore(match);
    const evScore = this.calculateEVScore(match);

    // Weighted formula (from research)
    const composite = (
      marketEfficiency * 0.3 +  // 30%: Where can we find edges?
      oddsQuality * 0.3 +        // 30%: How good are the odds?
      evScore * 0.4              // 40%: What's the profit signal?
    );

    // Scale to 0-100
    return Math.round(composite * 100);
  }

  /**
   * Generate betting recommendation based on score
   */
  generateRecommendation(score) {
    if (score >= 80) {
      return {
        action: 'STRONG BUY',
        confidence: 'High',
        riskLevel: 'Medium',
        reason: 'High EV + good odds + market inefficiency detected'
      };
    } else if (score >= 60) {
      return {
        action: 'BUY',
        confidence: 'Medium',
        riskLevel: 'Medium-High',
        reason: 'Decent opportunity with reasonable odds and market signals'
      };
    } else if (score >= 40) {
      return {
        action: 'HOLD',
        confidence: 'Low',
        riskLevel: 'High',
        reason: 'Marginal opportunity - consider other options first'
      };
    } else {
      return {
        action: 'SKIP',
        confidence: 'Very Low',
        riskLevel: 'Very High',
        reason: 'Insufficient edge detected - avoid'
      };
    }
  }

  /**
   * Add scoring data to each match
   */
  scoreMatches(matches) {
    return matches.map((match, index) => ({
      ...match,
      opportunity: {
        marketEfficiencyScore: this.calculateMarketEfficiencyScore(match),
        oddsQualityScore: this.calculateOddsQualityScore(match),
        evScore: this.calculateEVScore(match),
        compositeScore: this.calculateCompositeScore(match),
        recommendation: this.generateRecommendation(this.calculateCompositeScore(match)),
        scoringBreakdown: {
          marketEfficiency: `Market efficiency rating (0.7-1.0 scale)`,
          oddsQuality: `Bookmaker margin and odds extremeness analysis`,
          evScore: `Expected value based on odds structure`
        }
      }
    }));
  }

  /**
   * Filter and rank opportunities
   */
  filterAndRank(matches) {
    // Score all matches
    const scoredMatches = this.scoreMatches(matches);

    // Filter by minimum score
    const filtered = scoredMatches.filter(m => m.opportunity.compositeScore >= this.minScore);

    // Sort by composite score (descending)
    const sorted = filtered.sort(
      (a, b) => b.opportunity.compositeScore - a.opportunity.compositeScore
    );

    // Take top N
    const topMatches = sorted.slice(0, this.topN);

    // Add rank
    return topMatches.map((match, index) => ({
      ...match,
      opportunity: {
        ...match.opportunity,
        rank: index + 1
      }
    }));
  }

  /**
   * Main analysis function
   */
  async analyze(inputPath, outputPath) {
    try {
      if (this.verbose) {
        console.log('\n🤖 OPPORTUNITY AGENT - PHASE 2 ANALYSIS');
        console.log('═'.repeat(70));
      }

      // Read input data
      if (this.verbose) console.log(`\n📂 Reading matches from: ${inputPath}`);
      const fileContent = await fs.readFile(inputPath, 'utf8');
      const data = JSON.parse(fileContent);
      const matches = data.matches || [];

      if (this.verbose) {
        console.log(`📊 Total matches to analyze: ${matches.length}`);
        console.log(`🎯 Top N opportunities to find: ${this.topN}`);
        console.log(`⚙️  Minimum score filter: ${this.minScore}`);
      }

      // Analyze and rank
      if (this.verbose) console.log('\n⏳ Calculating opportunity scores...');
      const opportunities = this.filterAndRank(matches);

      if (this.verbose) {
        console.log(`\n✅ Analysis complete!`);
        console.log(`   Top opportunities found: ${opportunities.length}`);

        // Show distribution
        const distribution = {
          strong: opportunities.filter(m => m.opportunity.compositeScore >= 80).length,
          good: opportunities.filter(m => m.opportunity.compositeScore >= 60 && m.opportunity.compositeScore < 80).length,
          fair: opportunities.filter(m => m.opportunity.compositeScore >= 40 && m.opportunity.compositeScore < 60).length,
          weak: opportunities.filter(m => m.opportunity.compositeScore < 40).length
        };

        console.log(`\n📈 Score distribution:`);
        console.log(`   80-100 (STRONG BUY): ${distribution.strong}`);
        console.log(`   60-80  (BUY):        ${distribution.good}`);
        console.log(`   40-60  (HOLD):       ${distribution.fair}`);
        console.log(`   0-40   (SKIP):       ${distribution.weak}`);
      }

      // Prepare output
      const output = {
        analysisDate: new Date().toISOString(),
        sourceFile: inputPath,
        totalMatches: matches.length,
        opportunitiesFound: opportunities.length,
        topN: this.topN,
        minScore: this.minScore,
        opportunities: opportunities
      };

      // Write output
      if (this.verbose) console.log(`\n💾 Saving results to: ${outputPath}`);
      await fs.writeFile(outputPath, JSON.stringify(output, null, 2));

      if (this.verbose) {
        console.log(`✅ Results saved successfully!`);
        console.log('═'.repeat(70) + '\n');
      }

      return output;
    } catch (error) {
      console.error('❌ Error during analysis:', error.message);
      throw error;
    }
  }

  /**
   * Print summary of top opportunities
   */
  async printSummary(resultsPath, topCount = 10) {
    try {
      const fileContent = await fs.readFile(resultsPath, 'utf8');
      const results = JSON.parse(fileContent);
      const opportunities = results.opportunities.slice(0, topCount);

      console.log('\n🏆 TOP OPPORTUNITIES');
      console.log('═'.repeat(70));

      opportunities.forEach(opp => {
        const { homeTeam, awayTeam, league, opportunity } = opp;
        const { rank, compositeScore, recommendation } = opportunity;

        console.log(`\n#${rank}. ${homeTeam} vs ${awayTeam}`);
        console.log(`    League: ${league}`);
        console.log(`    Score: ${compositeScore}/100`);
        console.log(`    Action: ${recommendation.action} (${recommendation.confidence})`);
        console.log(`    Reason: ${recommendation.reason}`);
      });

      console.log('\n' + '═'.repeat(70) + '\n');
    } catch (error) {
      console.error('Error printing summary:', error.message);
    }
  }
}

module.exports = OpportunityAgent;
