const fs = require('fs');
const path = require('path');

const dataFile = path.join(__dirname, '../data/matches.json');
const data = JSON.parse(fs.readFileSync(dataFile, 'utf-8'));

const footballMatches = data.matches.filter(m => m.sport === 'football');
const missingLeague = footballMatches.filter(m => m.league === 'Unknown League');

console.log('\n📊 ANALYZING ' + missingLeague.length + ' FOOTBALL MATCHES WITH MISSING LEAGUES\n');
console.log('='.repeat(80));

for (let idx = 0; idx < Math.min(20, missingLeague.length); idx++) {
  const match = missingLeague[idx];
  console.log('\n' + (idx + 1) + '. ' + match.homeTeam + ' vs ' + match.awayTeam);
  console.log('   Time: ' + match.time);
  console.log('   Odds: ' + (match._hasOdds ? 'YES' : 'NO'));
}

console.log('\n\n📈 SUMMARY:');
console.log('Total football matches: ' + footballMatches.length);
console.log('Missing league: ' + missingLeague.length + ' (' + ((missingLeague.length / footballMatches.length) * 100).toFixed(1) + '%)');
console.log('With league: ' + (footballMatches.length - missingLeague.length) + ' (' + (((footballMatches.length - missingLeague.length) / footballMatches.length) * 100).toFixed(1) + '%)');

// Check if they're all from same time or pattern
const timePattern = {};
missingLeague.forEach(m => {
  const time = m.time || 'TBD';
  if (!timePattern[time]) timePattern[time] = 0;
  timePattern[time]++;
});

console.log('\n⏰ Time distribution of missing-league matches:');
Object.entries(timePattern).forEach(entry => {
  console.log('   ' + entry[0] + ': ' + entry[1] + ' matches');
});
