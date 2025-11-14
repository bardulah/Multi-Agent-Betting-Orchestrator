#!/usr/bin/env node

/**
 * Telegram Bot for Betting Opportunities
 * Phase 3: User Interface for displaying betting opportunities
 *
 * Features:
 * - Display top opportunities
 * - Filter by score/recommendation
 * - Export results
 * - Show statistics
 */

const fs = require('fs');
const path = require('path');

class TelegramBotSimulator {
  constructor(opportunitiesFile = null) {
    // Default to most recent opportunities file
    if (!opportunitiesFile) {
      // Try multiple locations in order of preference
      const possiblePaths = [
        path.join(__dirname, '../../data/opportunities-ranked.json'),
        path.join(__dirname, '../../data/opportunities-football-50.json'),
        path.join(__dirname, '../../data/opportunities-100.json')
      ];

      for (const p of possiblePaths) {
        if (fs.existsSync(p)) {
          opportunitiesFile = p;
          break;
        }
      }
    }

    this.opportunitiesFile = opportunitiesFile;
    this.opportunities = [];
    this.loadOpportunities();
  }

  loadOpportunities() {
    try {
      if (!this.opportunitiesFile) {
        throw new Error('No opportunities file found');
      }
      const data = fs.readFileSync(this.opportunitiesFile, 'utf-8');
      const parsed = JSON.parse(data);
      this.opportunities = parsed.opportunities || [];
      console.log(`✓ Loaded ${this.opportunities.length} opportunities from ${path.basename(this.opportunitiesFile)}`);
    } catch (error) {
      console.error(`✗ Failed to load opportunities: ${error.message}`);
      this.opportunities = [];
    }
  }

  /**
   * /show - Display top opportunities
   */
  show(limit = 10) {
    console.log('\n' + '═'.repeat(60));
    console.log('📊 TOP BETTING OPPORTUNITIES');
    console.log('═'.repeat(60));

    const topOps = this.opportunities.slice(0, limit);

    topOps.forEach((opp, idx) => {
      const score = opp.opportunity.compositeScore;
      const action = opp.opportunity.recommendation.action;
      const confidence = opp.opportunity.recommendation.confidence;

      const scoreBar = this.createScoreBar(score);

      console.log(`\n#${idx + 1}. ${opp.homeTeam} vs ${opp.awayTeam}`);
      console.log(`   League: ${opp.league}`);
      console.log(`   Time: ${opp.time} (${opp.date})`);
      console.log(`   Score: ${scoreBar} ${score}/100`);
      console.log(`   Action: ${action} | Confidence: ${confidence}`);
      console.log(`   Reason: ${opp.opportunity.recommendation.reason}`);

      if (opp.odds && opp.odds.Flashscore) {
        const odds = opp.odds.Flashscore;
        console.log(`   Odds: Home ${odds.home}, Draw ${odds.draw}, Away ${odds.away}`);
      }
    });

    console.log('\n' + '═'.repeat(60));
    console.log(`Showing ${topOps.length} of ${this.opportunities.length} total opportunities`);
    console.log('═'.repeat(60) + '\n');
  }

  /**
   * /filter - Filter opportunities by minimum score
   */
  filter(minScore = 70, limit = 10) {
    console.log('\n' + '═'.repeat(60));
    console.log(`🎯 FILTERING BY SCORE >= ${minScore}`);
    console.log('═'.repeat(60));

    const filtered = this.opportunities.filter(opp =>
      opp.opportunity.compositeScore >= minScore
    );

    console.log(`Found ${filtered.length} opportunities with score >= ${minScore}\n`);

    const topFiltered = filtered.slice(0, limit);

    topFiltered.forEach((opp, idx) => {
      const score = opp.opportunity.compositeScore;
      const action = opp.opportunity.recommendation.action;

      console.log(`#${idx + 1}. ${opp.homeTeam} vs ${opp.awayTeam}`);
      console.log(`   Score: ${score}/100 | Action: ${action}`);
      console.log(`   League: ${opp.league}`);
    });

    console.log('\n' + '═'.repeat(60) + '\n');
  }

  /**
   * /stats - Show statistics about opportunities
   */
  stats() {
    console.log('\n' + '═'.repeat(60));
    console.log('📈 BETTING OPPORTUNITIES STATISTICS');
    console.log('═'.repeat(60));

    // Count by recommendation
    const byAction = {};
    const byLeague = {};
    let totalScore = 0;

    this.opportunities.forEach(opp => {
      const action = opp.opportunity.recommendation.action;
      const league = opp.league || 'Unknown';
      const score = opp.opportunity.compositeScore;

      byAction[action] = (byAction[action] || 0) + 1;
      byLeague[league] = (byLeague[league] || 0) + 1;
      totalScore += score;
    });

    // Display stats
    console.log('\n📋 By Recommendation:');
    Object.entries(byAction).sort((a, b) => b[1] - a[1]).forEach(([action, count]) => {
      const pct = ((count / this.opportunities.length) * 100).toFixed(1);
      const bar = '█'.repeat(Math.round(pct / 5));
      console.log(`   ${action.padEnd(12)} ${bar} ${count} (${pct}%)`);
    });

    console.log('\n🏆 Top 5 Leagues:');
    Object.entries(byLeague)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .forEach(([league, count]) => {
        console.log(`   ${league}: ${count} matches`);
      });

    console.log('\n📊 Score Distribution:');
    const avgScore = (totalScore / this.opportunities.length).toFixed(2);
    console.log(`   Average Score: ${avgScore}/100`);
    console.log(`   Total Opportunities: ${this.opportunities.length}`);
    console.log(`   STRONG BUY (80-100): ${this.opportunities.filter(o => o.opportunity.compositeScore >= 80).length}`);
    console.log(`   BUY (60-80): ${this.opportunities.filter(o => o.opportunity.compositeScore >= 60 && o.opportunity.compositeScore < 80).length}`);
    console.log(`   HOLD (40-60): ${this.opportunities.filter(o => o.opportunity.compositeScore >= 40 && o.opportunity.compositeScore < 60).length}`);
    console.log(`   SKIP (0-40): ${this.opportunities.filter(o => o.opportunity.compositeScore < 40).length}`);

    console.log('\n' + '═'.repeat(60) + '\n');
  }

  /**
   * /export - Export opportunities to CSV
   */
  export(format = 'csv', limit = null) {
    const toExport = limit ? this.opportunities.slice(0, limit) : this.opportunities;
    const timestamp = new Date().toISOString().split('T')[0];
    let filename;

    if (format === 'csv') {
      filename = `opportunities_${timestamp}.csv`;
      const csv = this.toCSV(toExport);
      fs.writeFileSync(filename, csv);
      console.log(`✓ Exported ${toExport.length} opportunities to ${filename}`);
    } else if (format === 'json') {
      filename = `opportunities_${timestamp}.json`;
      fs.writeFileSync(filename, JSON.stringify({ opportunities: toExport }, null, 2));
      console.log(`✓ Exported ${toExport.length} opportunities to ${filename}`);
    }

    console.log(`📁 File location: ${path.resolve(filename)}\n`);
  }

  /**
   * Convert opportunities to CSV format
   */
  toCSV(opportunities) {
    const headers = [
      'Rank',
      'Home Team',
      'Away Team',
      'League',
      'Score',
      'Action',
      'Confidence',
      'Risk Level',
      'Market Efficiency',
      'Odds Quality',
      'EV Score',
      'Home Odds',
      'Draw Odds',
      'Away Odds'
    ].join(',');

    const rows = opportunities.map((opp, idx) => {
      const odds = opp.odds?.Flashscore || {};
      return [
        idx + 1,
        `"${opp.homeTeam}"`,
        `"${opp.awayTeam}"`,
        `"${opp.league}"`,
        opp.opportunity.compositeScore,
        opp.opportunity.recommendation.action,
        opp.opportunity.recommendation.confidence,
        opp.opportunity.recommendation.riskLevel,
        (opp.opportunity.marketEfficiencyScore * 100).toFixed(1),
        (opp.opportunity.oddsQualityScore * 100).toFixed(1),
        (opp.opportunity.evScore * 100).toFixed(1),
        odds.home || 'N/A',
        odds.draw || 'N/A',
        odds.away || 'N/A'
      ].join(',');
    });

    return headers + '\n' + rows.join('\n');
  }

  /**
   * Create a visual score bar
   */
  createScoreBar(score) {
    const filled = Math.round(score / 10);
    const empty = 10 - filled;
    const bar = '█'.repeat(filled) + '░'.repeat(empty);

    let icon;
    if (score >= 80) icon = '🟢';
    else if (score >= 60) icon = '🟡';
    else if (score >= 40) icon = '🟠';
    else icon = '🔴';

    return `${icon} [${bar}]`;
  }

  /**
   * /help - Show available commands
   */
  help() {
    console.log('\n' + '═'.repeat(60));
    console.log('🤖 TELEGRAM BOT COMMANDS');
    console.log('═'.repeat(60));
    console.log(`
/show [N]              - Display top N opportunities (default: 10)
/filter <score> [N]    - Filter by minimum score, show top N
/stats                 - Show statistics and distribution
/export [csv|json] [N] - Export top N opportunities to file
/help                  - Show this help message

Examples:
  /show 20               → Show top 20 opportunities
  /filter 75 10          → Show top 10 with score >= 75
  /stats                 → View opportunity statistics
  /export csv 50         → Export top 50 as CSV
    `);
    console.log('═'.repeat(60) + '\n');
  }
}

/**
 * CLI Interface
 */
function parseCommand(input) {
  const parts = input.trim().split(/\s+/);
  const command = parts[0].toLowerCase();
  const args = parts.slice(1);

  return { command, args };
}

async function main() {
  const bot = new TelegramBotSimulator();

  console.log('\n' + '╔' + '═'.repeat(58) + '╗');
  console.log('║ 🤖 TELEGRAM BOT - BETTING OPPORTUNITIES               ║');
  console.log('║ Type /help for available commands                    ║');
  console.log('╚' + '═'.repeat(58) + '╝\n');

  // Process command-line arguments
  const args = process.argv.slice(2);

  if (args.length === 0) {
    // Interactive mode
    const readline = require('readline');
    const rl = readline.createInterface({
      input: process.stdin,
      output: process.stdout
    });

    const askCommand = () => {
      rl.question('> ', (input) => {
        if (input.toLowerCase() === 'exit' || input.toLowerCase() === 'quit') {
          console.log('\nGoodbye! 👋\n');
          rl.close();
          return;
        }

        const { command, args: cmdArgs } = parseCommand(input);

        try {
          switch (command) {
            case '/show':
              bot.show(cmdArgs[0] ? parseInt(cmdArgs[0]) : 10);
              break;
            case '/filter':
              const minScore = cmdArgs[0] ? parseInt(cmdArgs[0]) : 70;
              const limit = cmdArgs[1] ? parseInt(cmdArgs[1]) : 10;
              bot.filter(minScore, limit);
              break;
            case '/stats':
              bot.stats();
              break;
            case '/export':
              const format = cmdArgs[0] || 'csv';
              const exportLimit = cmdArgs[1] ? parseInt(cmdArgs[1]) : null;
              bot.export(format, exportLimit);
              break;
            case '/help':
              bot.help();
              break;
            default:
              console.log('Unknown command. Type /help for available commands.\n');
          }
        } catch (error) {
          console.error(`Error: ${error.message}\n`);
        }

        askCommand();
      });
    };

    askCommand();
  } else {
    // CLI mode - execute single command
    const input = process.argv.slice(2).join(' ');
    const { command, args: cmdArgs } = parseCommand(input);

    try {
      switch (command) {
        case '/show':
          bot.show(cmdArgs[0] ? parseInt(cmdArgs[0]) : 10);
          break;
        case '/filter':
          const minScore = cmdArgs[0] ? parseInt(cmdArgs[0]) : 70;
          const limit = cmdArgs[1] ? parseInt(cmdArgs[1]) : 10;
          bot.filter(minScore, limit);
          break;
        case '/stats':
          bot.stats();
          break;
        case '/export':
          const format = cmdArgs[0] || 'csv';
          const exportLimit = cmdArgs[1] ? parseInt(cmdArgs[1]) : null;
          bot.export(format, exportLimit);
          break;
        case '/help':
          bot.help();
          break;
        default:
          console.error(`Unknown command: ${command}\nType /help for available commands.`);
          process.exit(1);
      }
    } catch (error) {
      console.error(`Error: ${error.message}`);
      process.exit(1);
    }
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = TelegramBotSimulator;
