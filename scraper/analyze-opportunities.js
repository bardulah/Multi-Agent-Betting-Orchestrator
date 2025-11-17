#!/usr/bin/env node

/**
 * CLI tool to run the Opportunity Agent
 *
 * Usage:
 *   npm run analyze-opportunities
 *   npm run analyze-opportunities -- --top-n 50
 *   npm run analyze-opportunities -- --min-score 70
 *   npm run analyze-opportunities -- --top-n 100 --min-score 60
 */

const path = require('path');
const OpportunityAgent = require('./src/opportunityAgent');

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    topN: 100,
    minScore: 0,
    inputFile: '../data/matches.json',
    outputFile: '../data/opportunities-ranked.json',
    showHelp: false,
    showSummary: true,
    summaryCount: 10
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--top-n':
        options.topN = parseInt(args[++i], 10);
        break;
      case '--min-score':
        options.minScore = parseInt(args[++i], 10);
        break;
      case '--input':
        options.inputFile = args[++i];
        break;
      case '--output':
        options.outputFile = args[++i];
        break;
      case '--no-summary':
        options.showSummary = false;
        break;
      case '--summary-count':
        options.summaryCount = parseInt(args[++i], 10);
        break;
      case '--help':
      case '-h':
        options.showHelp = true;
        break;
    }
  }

  return options;
}

function printHelp() {
  console.log(`
╔════════════════════════════════════════════════════════════════════════════╗
║                   OPPORTUNITY AGENT - PHASE 2 CLI                          ║
║                     Sports Betting Opportunity Detection                   ║
╚════════════════════════════════════════════════════════════════════════════╝

USAGE:
  npm run analyze-opportunities [options]

OPTIONS:
  --top-n <number>          Number of top opportunities to find (default: 100)
  --min-score <number>      Minimum opportunity score 0-100 (default: 0)
  --input <path>            Input JSON file path (default: data/matches.json)
  --output <path>           Output JSON file path (default: data/opportunities-ranked.json)
  --no-summary              Skip printing summary after analysis
  --summary-count <number>  Number of top opportunities to show (default: 10)
  --help, -h                Show this help message

EXAMPLES:

  # Find top 100 opportunities (default)
  npm run analyze-opportunities

  # Find top 50 opportunities with score >= 70
  npm run analyze-opportunities -- --top-n 50 --min-score 70

  # Find top 30 with score >= 60, show top 20 summary
  npm run analyze-opportunities -- --top-n 30 --min-score 60 --summary-count 20

  # Analyze with custom input/output files
  npm run analyze-opportunities -- --input mymatches.json --output myopportunities.json

SCORING EXPLAINED:

  Score Range        Action        Confidence    Reason
  ───────────────────────────────────────────────────────────────────────────
  80-100            STRONG BUY     High          High EV + good odds + inefficiency
  60-80             BUY            Medium        Decent opportunity + market signals
  40-60             HOLD           Low           Marginal - explore other options
  0-40              SKIP           Very Low      Insufficient edge

The score is calculated using 3 layers:
  1. Market Efficiency (30%): Identifies where edges exist
  2. Odds Quality (30%):       Measures value in available odds
  3. Expected Value (40%):     Detects profit potential

OUTPUT:

  data/opportunities-ranked.json will contain:
  - All opportunities ranked by composite score
  - Detailed scoring breakdown for each match
  - Betting recommendations with confidence levels

For more information, see:
  - PHASE2_OPPORTUNITY_AGENT_PLAN.md (technical details)
  - PHASE2_QUICK_SUMMARY.md (quick reference)

`);
}

async function main() {
  const options = parseArgs();

  if (options.showHelp) {
    printHelp();
    process.exit(0);
  }

  try {
    // Create agent
    const agent = new OpportunityAgent({
      topN: options.topN,
      minScore: options.minScore,
      verbose: true
    });

    // Resolve paths
    const inputPath = path.resolve(__dirname, options.inputFile);
    const outputPath = path.resolve(__dirname, options.outputFile);

    // Run analysis
    await agent.analyze(inputPath, outputPath);

    // Show summary if requested
    if (options.showSummary) {
      await agent.printSummary(outputPath, options.summaryCount);
    }

  } catch (error) {
    console.error('❌ Fatal error:', error.message);
    process.exit(1);
  }
}

main();
