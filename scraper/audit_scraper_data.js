const fs = require('fs');
const path = require('path');

const dataFile = path.join(__dirname, '../data/matches.json');
const data = JSON.parse(fs.readFileSync(dataFile, 'utf-8'));

const matches = data.matches;
const sports = {};

// Group by sport
matches.forEach(match => {
  if (!sports[match.sport]) {
    sports[match.sport] = {
      total: 0,
      withLeague: 0,
      withOdds: 0,
      withTime: 0,
      samples: []
    };
  }

  sports[match.sport].total++;
  if (match.league && match.league !== 'Unknown League') sports[match.sport].withLeague++;
  if (match.odds && Object.keys(match.odds).length > 0) sports[match.sport].withOdds++;
  if (match.time && match.time !== 'TBD') sports[match.sport].withTime++;

  if (sports[match.sport].samples.length < 3) {
    sports[match.sport].samples.push({
      matchup: match.homeTeam + ' vs ' + match.awayTeam,
      league: match.league,
      time: match.time,
      odds: match.odds,
      hasOdds: match._hasOdds
    });
  }
});

console.log('\n' + '='.repeat(80));
console.log('SCRAPER DATA AUDIT - CURRENT STATE');
console.log('='.repeat(80));

Object.entries(sports).forEach(entry => {
  const sport = entry[0];
  const info = entry[1];

  console.log('\n\n' + sport.toUpperCase());
  console.log('-'.repeat(80));

  const oddsRate = ((info.withOdds / info.total) * 100).toFixed(1);
  const leagueRate = ((info.withLeague / info.total) * 100).toFixed(1);
  const timeRate = ((info.withTime / info.total) * 100).toFixed(1);

  console.log('Total matches: ' + info.total);
  console.log('With league info: ' + info.withLeague + '/' + info.total + ' (' + leagueRate + '%)');
  console.log('With odds: ' + info.withOdds + '/' + info.total + ' (' + oddsRate + '%)');
  console.log('With time: ' + info.withTime + '/' + info.total + ' (' + timeRate + '%)');

  console.log('\nSample matches:');
  info.samples.forEach((sample, idx) => {
    console.log('\n  ' + (idx + 1) + '. ' + sample.matchup);
    console.log('     League: ' + sample.league);
    console.log('     Time: ' + sample.time);
    if (sample.hasOdds) {
      const odds = sample.odds.Flashscore;
      if (odds.draw) {
        console.log('     Odds: ' + odds.home + ' / ' + odds.draw + ' / ' + odds.away);
      } else {
        console.log('     Odds: ' + odds.home + ' / ' + odds.away);
      }
    } else {
      console.log('     Odds: NONE');
    }
  });
});

console.log('\n\n' + '='.repeat(80));
console.log('MISSING DATA SUMMARY');
console.log('='.repeat(80));

Object.entries(sports).forEach(entry => {
  const sport = entry[0];
  const info = entry[1];

  console.log('\n' + sport.toUpperCase() + ':');

  const missingLeague = info.total - info.withLeague;
  const missingOdds = info.total - info.withOdds;
  const missingTime = info.total - info.withTime;

  if (missingLeague > 0) {
    const pct = ((missingLeague / info.total) * 100).toFixed(1);
    console.log('  Missing league: ' + missingLeague + ' matches (' + pct + '%)');
  }
  if (missingOdds > 0) {
    const pct = ((missingOdds / info.total) * 100).toFixed(1);
    console.log('  Missing odds: ' + missingOdds + ' matches (' + pct + '%)');
  }
  if (missingTime > 0) {
    const pct = ((missingTime / info.total) * 100).toFixed(1);
    console.log('  Missing time: ' + missingTime + ' matches (' + pct + '%)');
  }

  if (missingLeague === 0 && missingOdds === 0 && missingTime === 0) {
    console.log('  ALL DATA COMPLETE');
  }
});

console.log('\n');
