const fs = require('fs');
const data = JSON.parse(fs.readFileSync('data/matches.json', 'utf-8'));
const leagues = {};

data.matches.forEach(m => {
  const league = m.league;
  if (!leagues[league]) leagues[league] = 0;
  leagues[league]++;
});

console.log('Unique leagues in current data:\n');
Object.entries(leagues)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 20)
  .forEach(([league, count]) => {
    console.log(count.toString().padStart(3) + ' matches: ' + league);
  });
