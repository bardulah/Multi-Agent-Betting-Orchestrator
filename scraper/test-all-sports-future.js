const FlashscoreScraper = require('./src/flashscore-scraper-future.js');
const yaml = require('yaml');
const fs = require('fs');
const path = require('path');

(async () => {
  const configPath = path.join(__dirname, '../config/config.yaml');
  const configContent = await fs.promises.readFile(configPath, 'utf8');
  const config = yaml.parse(configContent);

  console.log('\n╔════════════════════════════════════════════╗');
  console.log('║ TESTING ALL SPORTS WITH NEXT DAY BUTTON    ║');
  console.log('║ (Tomorrow\'s Matches)                       ║');
  console.log('╚════════════════════════════════════════════╝\n');

  const scraper = new FlashscoreScraper(config);

  try {
    await scraper.initialize();
    scraper.setScrapeDateToTomorrow();  // Set date to tomorrow BEFORE scraping
    await scraper.scrapeAll();
    await scraper.saveResults();

    console.log('\n✓ Test complete!\n');
    console.log(`Total matches: ${scraper.matches.length}`);
    console.log(`Matches with odds: ${scraper.matches.filter(m => m._hasOdds).length}\n`);

    // Show breakdown by sport
    const sports = {};
    scraper.matches.forEach(m => {
      sports[m.sport] = (sports[m.sport] || 0) + 1;
    });

    console.log('Matches by sport:');
    Object.entries(sports).forEach(([sport, count]) => {
      console.log(`  ${sport}: ${count}`);
    });

  } catch (error) {
    console.error('Error:', error);
  }
})();
