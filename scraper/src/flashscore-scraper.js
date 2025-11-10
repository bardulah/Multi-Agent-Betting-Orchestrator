const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs').promises;
const path = require('path');
const yaml = require('yaml');

puppeteer.use(StealthPlugin());

class FlashscoreScraper {
  constructor(config) {
    this.config = config;
    this.browser = null;
    this.page = null;
    this.matches = [];
  }

  async initialize() {
    console.log('Initializing browser...');
    this.browser = await puppeteer.launch({
      headless: this.config.scraper.headless,
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-accelerated-2d-canvas',
        '--disable-gpu'
      ]
    });

    this.page = await this.browser.newPage();
    await this.page.setUserAgent(this.config.scraper.user_agent);
    await this.page.setViewport(this.config.scraper.viewport);

    // Set longer timeout
    this.page.setDefaultNavigationTimeout(this.config.scraper.timeout);
  }

  async delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  async scrapeFootball() {
    console.log('Scraping football matches...');
    const matches = [];

    try {
      await this.page.goto('https://www.flashscore.com/football/', {
        waitUntil: 'networkidle2'
      });

      await this.delay(this.config.scraper.rate_limit_delay);

      // Wait for matches to load
      await this.page.waitForSelector('.event__match', { timeout: 10000 }).catch(() => {
        console.log('No matches found or selector changed');
      });

      // Get today's matches
      const matchElements = await this.page.$$('.event__match');
      console.log(`Found ${matchElements.length} football matches`);

      for (let i = 0; i < Math.min(matchElements.length, 20); i++) {
        try {
          const match = await this.extractMatchData(matchElements[i], 'football');
          if (match) {
            matches.push(match);
          }
          await this.delay(this.config.scraper.rate_limit_delay);
        } catch (error) {
          console.error(`Error extracting match ${i}:`, error.message);
        }
      }
    } catch (error) {
      console.error('Error scraping football:', error.message);
    }

    return matches;
  }

  async scrapeBasketball() {
    console.log('Scraping basketball matches...');
    const matches = [];

    try {
      await this.page.goto('https://www.flashscore.com/basketball/', {
        waitUntil: 'networkidle2'
      });

      await this.delay(this.config.scraper.rate_limit_delay);

      await this.page.waitForSelector('.event__match', { timeout: 10000 }).catch(() => {
        console.log('No matches found or selector changed');
      });

      const matchElements = await this.page.$$('.event__match');
      console.log(`Found ${matchElements.length} basketball matches`);

      for (let i = 0; i < Math.min(matchElements.length, 20); i++) {
        try {
          const match = await this.extractMatchData(matchElements[i], 'basketball');
          if (match) {
            matches.push(match);
          }
          await this.delay(this.config.scraper.rate_limit_delay);
        } catch (error) {
          console.error(`Error extracting match ${i}:`, error.message);
        }
      }
    } catch (error) {
      console.error('Error scraping basketball:', error.message);
    }

    return matches;
  }

  async scrapeTennis() {
    console.log('Scraping tennis matches...');
    const matches = [];

    try {
      await this.page.goto('https://www.flashscore.com/tennis/', {
        waitUntil: 'networkidle2'
      });

      await this.delay(this.config.scraper.rate_limit_delay);

      await this.page.waitForSelector('.event__match', { timeout: 10000 }).catch(() => {
        console.log('No matches found or selector changed');
      });

      const matchElements = await this.page.$$('.event__match');
      console.log(`Found ${matchElements.length} tennis matches`);

      for (let i = 0; i < Math.min(matchElements.length, 20); i++) {
        try {
          const match = await this.extractMatchData(matchElements[i], 'tennis');
          if (match) {
            matches.push(match);
          }
          await this.delay(this.config.scraper.rate_limit_delay);
        } catch (error) {
          console.error(`Error extracting match ${i}:`, error.message);
        }
      }
    } catch (error) {
      console.error('Error scraping tennis:', error.message);
    }

    return matches;
  }

  async scrapeHockey() {
    console.log('Scraping hockey matches...');
    const matches = [];

    try {
      await this.page.goto('https://www.flashscore.com/hockey/', {
        waitUntil: 'networkidle2'
      });

      await this.delay(this.config.scraper.rate_limit_delay);

      await this.page.waitForSelector('.event__match', { timeout: 10000 }).catch(() => {
        console.log('No matches found or selector changed');
      });

      const matchElements = await this.page.$$('.event__match');
      console.log(`Found ${matchElements.length} hockey matches`);

      for (let i = 0; i < Math.min(matchElements.length, 20); i++) {
        try {
          const match = await this.extractMatchData(matchElements[i], 'hockey');
          if (match) {
            matches.push(match);
          }
          await this.delay(this.config.scraper.rate_limit_delay);
        } catch (error) {
          console.error(`Error extracting match ${i}:`, error.message);
        }
      }
    } catch (error) {
      console.error('Error scraping hockey:', error.message);
    }

    return matches;
  }

  async extractMatchData(matchElement, sport) {
    try {
      // Extract basic match information
      const homeTeam = await matchElement.$eval('.event__participant--home', el => el.textContent.trim()).catch(() => 'Unknown');
      const awayTeam = await matchElement.$eval('.event__participant--away', el => el.textContent.trim()).catch(() => 'Unknown');
      const time = await matchElement.$eval('.event__time', el => el.textContent.trim()).catch(() => 'TBD');

      // Try to get league/tournament
      const league = await this.page.$eval('.event__title--type', el => el.textContent.trim()).catch(() => 'Unknown League');

      // Get match ID for odds
      const matchId = await matchElement.evaluate(el => el.getAttribute('id'));

      const matchData = {
        id: matchId || `${homeTeam}_${awayTeam}_${Date.now()}`,
        sport: sport,
        homeTeam: homeTeam,
        awayTeam: awayTeam,
        league: league,
        time: time,
        date: new Date().toISOString().split('T')[0],
        odds: {}
      };

      // Try to get odds if available
      try {
        // Click on the match to see odds
        await matchElement.click();
        await this.delay(1000);

        // Try to click odds tab
        const oddsTab = await this.page.$('a[href*="odds"]').catch(() => null);
        if (oddsTab) {
          await oddsTab.click();
          await this.delay(1500);

          // Extract odds from bookmakers
          const oddsData = await this.page.evaluate(() => {
            const odds = {};
            const oddsRows = document.querySelectorAll('.ui-table__row');

            oddsRows.forEach(row => {
              const bookmaker = row.querySelector('.oddsCell__bookmaker')?.textContent.trim();
              const homeOdds = row.querySelector('.oddsValueInner:nth-child(1)')?.textContent.trim();
              const drawOdds = row.querySelector('.oddsValueInner:nth-child(2)')?.textContent.trim();
              const awayOdds = row.querySelector('.oddsValueInner:nth-child(3)')?.textContent.trim();

              if (bookmaker && homeOdds) {
                odds[bookmaker] = {
                  home: parseFloat(homeOdds) || null,
                  draw: parseFloat(drawOdds) || null,
                  away: parseFloat(awayOdds) || null
                };
              }
            });

            return odds;
          }).catch(() => ({}));

          matchData.odds = oddsData;
        }

        // Go back to matches list
        await this.page.goBack();
        await this.delay(1000);
      } catch (error) {
        console.log(`Could not extract odds for ${homeTeam} vs ${awayTeam}`);
      }

      console.log(`Extracted: ${homeTeam} vs ${awayTeam}`);
      return matchData;

    } catch (error) {
      console.error('Error in extractMatchData:', error.message);
      return null;
    }
  }

  async scrapeAll() {
    console.log('Starting scrape for all configured sports...');

    for (const sport of this.config.sports) {
      console.log(`\n=== Scraping ${sport.toUpperCase()} ===`);
      let sportMatches = [];

      switch(sport.toLowerCase()) {
        case 'football':
          sportMatches = await this.scrapeFootball();
          break;
        case 'basketball':
          sportMatches = await this.scrapeBasketball();
          break;
        case 'tennis':
          sportMatches = await scrapeTennis();
          break;
        case 'hockey':
          sportMatches = await this.scrapeHockey();
          break;
        default:
          console.log(`Sport ${sport} not supported yet`);
      }

      this.matches.push(...sportMatches);
      console.log(`Total matches scraped for ${sport}: ${sportMatches.length}`);
    }

    return this.matches;
  }

  async saveResults(outputPath) {
    const output = {
      scrapeDate: new Date().toISOString(),
      totalMatches: this.matches.length,
      matches: this.matches
    };

    await fs.writeFile(outputPath, JSON.stringify(output, null, 2));
    console.log(`\nResults saved to ${outputPath}`);
    console.log(`Total matches scraped: ${this.matches.length}`);
  }

  async close() {
    if (this.browser) {
      await this.browser.close();
      console.log('Browser closed');
    }
  }
}

async function main() {
  try {
    // Load configuration
    const configPath = path.join(__dirname, '../../config/config.yaml');
    const configFile = await fs.readFile(configPath, 'utf8');
    const config = yaml.parse(configFile);

    // Initialize scraper
    const scraper = new FlashscoreScraper(config);
    await scraper.initialize();

    // Scrape all sports
    await scraper.scrapeAll();

    // Save results
    const outputPath = path.join(__dirname, '../../data/matches.json');
    await scraper.saveResults(outputPath);

    // Close browser
    await scraper.close();

    process.exit(0);
  } catch (error) {
    console.error('Fatal error:', error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = FlashscoreScraper;
