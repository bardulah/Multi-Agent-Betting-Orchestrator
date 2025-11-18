const FlashscoreScraper = require('./src/flashscore-scraper-future.js');
const yaml = require('yaml');
const fs = require('fs');
const path = require('path');

(async () => {
  const configPath = path.join(__dirname, '../config/config.yaml');
  const configContent = await fs.promises.readFile(configPath, 'utf8');
  const config = yaml.parse(configContent);

  console.log('\n╔════════════════════════════════════════════╗');
  console.log('║ TESTING FOOTBALL WITH NEXT DAY BUTTON      ║');
  console.log('╚════════════════════════════════════════════╝\n');

  // Only scrape football
  config.sports = ['football'];

  const scraper = new FlashscoreScraper(config);

  try {
    await scraper.initialize();
    await scraper.scrapeAll();
    await scraper.saveResults();

    console.log('\n✓ Test complete!');
    console.log(`Total matches: ${scraper.matches.length}`);
    console.log(`Matches with odds: ${scraper.matches.filter(m => m._hasOdds).length}`);

    // Show first 3 matches
    console.log('\nFirst 3 matches:');
    scraper.matches.slice(0, 3).forEach((m, i) => {
      console.log(`${i+1}. ${m.homeTeam} vs ${m.awayTeam} (${m.date})`);
    });
  } catch (error) {
    console.error('Error:', error);
  }
})();
