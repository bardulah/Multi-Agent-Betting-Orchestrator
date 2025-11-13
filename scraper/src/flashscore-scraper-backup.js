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
        waitUntil: 'domcontentloaded'
      });

      await this.delay(5000); // Wait for dynamic content

      // Get all match elements with more robust selectors  
      const matchData = await this.page.evaluate(() => {
        const timeout = 25000; // 25 second timeout
        const startTime = Date.now();
        const matches = [];
        
        // Try multiple possible selectors
        const matchElements = document.querySelectorAll('[id^="g_1"]') || 
                             document.querySelectorAll('.event__match') ||
                             document.querySelectorAll('[class*="event"]');
        
        console.log(`Found ${matchElements.length} potential match elements`);
        
        for (let i = 0; i < Math.min(matchElements.length, 20); i++) {
          const el = matchElements[i];
          
          try {
            // Try multiple ways to get team names
            let homeTeam = 'Unknown';
            let awayTeam = 'Unknown';
            
            // Method 1: Standard classes
            const homeEl = el.querySelector('.event__participant--home');
            const awayEl = el.querySelector('.event__participant--away');
            
            if (homeEl) homeTeam = homeEl.textContent.trim();
            if (awayEl) awayTeam = awayEl.textContent.trim();
            
            // Method 2: Fallback - look for participant divs
            if (homeTeam === 'Unknown' || awayTeam === 'Unknown') {
              const participants = el.querySelectorAll('[class*="participant"]');
              if (participants.length >= 2) {
                homeTeam = participants[0].textContent.trim();
                awayTeam = participants[1].textContent.trim();
              }
            }
            
            // Method 3: Look in title attribute
            if ((homeTeam === 'Unknown' || awayTeam === 'Unknown') && el.title) {
              const titleParts = el.title.split(' - ');
              if (titleParts.length === 2) {
                homeTeam = titleParts[0].trim();
                awayTeam = titleParts[1].trim();
              }
            }
            
            // Get time
            let time = 'TBD';
            const timeEl = el.querySelector('.event__time') || 
                          el.querySelector('[class*="time"]');
            if (timeEl) time = timeEl.textContent.trim();
            
            // Get match ID
            const matchId = el.id || `match_${i}_${Date.now()}`;
            
            matches.push({
              id: matchId,
              sport: 'football',
              homeTeam: homeTeam,
              awayTeam: awayTeam,
              league: 'Unknown League', // Will try to get from context
              time: time,
              date: new Date().toISOString().split('T')[0],
              odds: {},
              _debug: {
                hasTitle: !!el.title,
                hasHomeClass: !!el.querySelector('.event__participant--home'),
                hasAwayClass: !!el.querySelector('.event__participant--away'),
                classList: el.className
              }
            });
            
          } catch (err) {
            console.error(`Error processing match ${i}:`, err.message);
          }
        }
        
        return matches;
      });

      console.log(`Extracted ${matchData.length} football matches`);
      
      // Filter out invalid matches
      const validMatches = matchData.filter(m => 
        m.homeTeam !== 'Unknown' && m.awayTeam !== 'Unknown'
      );
      
      console.log(`Valid matches: ${validMatches.length}`);
      matches.push(...validMatches);

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
        waitUntil: 'domcontentloaded',
        timeout: 45000
      });

      await this.delay(5000);

      const matchData = await this.page.evaluate(() => {
        const matches = [];
        const matchElements = document.querySelectorAll('[id^="g_2"]') || 
                             document.querySelectorAll('.event__match');
        
        for (let i = 0; i < Math.min(matchElements.length, 20); i++) {
          const el = matchElements[i];
          
          try {
            let homeTeam = 'Unknown';
            let awayTeam = 'Unknown';
            
            const homeEl = el.querySelector('.event__participant--home') ||
                          el.querySelector('[class*="participant"]:first-child');
            const awayEl = el.querySelector('.event__participant--away') ||
                          el.querySelector('[class*="participant"]:last-child');
            
            if (homeEl) homeTeam = homeEl.textContent.trim();
            if (awayEl) awayTeam = awayEl.textContent.trim();
            
            if (homeTeam === 'Unknown' && el.title) {
              const parts = el.title.split(' - ');
              if (parts.length >= 2) {
                homeTeam = parts[0].trim();
                awayTeam = parts[1].trim();
              }
            }
            
            let time = 'TBD';
            const timeEl = el.querySelector('.event__time') || 
                          el.querySelector('[class*="time"]');
            if (timeEl) time = timeEl.textContent.trim();
            
            const matchId = el.id || `basketball_${i}_${Date.now()}`;
            
            matches.push({
              id: matchId,
              sport: 'basketball',
              homeTeam: homeTeam,
              awayTeam: awayTeam,
              league: 'Unknown League',
              time: time,
              date: new Date().toISOString().split('T')[0],
              odds: {}
            });
            
          } catch (err) {
            console.error(`Error processing basketball match ${i}:`, err.message);
          }
        }
        
        return matches;
      });

      const validMatches = matchData.filter(m => 
        m.homeTeam !== 'Unknown' && m.awayTeam !== 'Unknown'
      );
      
      console.log(`Valid basketball matches: ${validMatches.length} / ${matchData.length}`);
      matches.push(...validMatches);

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
        waitUntil: 'domcontentloaded'
      });

      await this.delay(5000);

      const matchData = await this.page.evaluate(() => {
        const matches = [];
        const matchElements = document.querySelectorAll('[id^="g_2"]') || 
                             document.querySelectorAll('.event__match');
        
        for (let i = 0; i < Math.min(matchElements.length, 20); i++) {
          const el = matchElements[i];
          
          try {
            let homeTeam = 'Unknown';
            let awayTeam = 'Unknown';
            
            const homeEl = el.querySelector('.event__participant--home');
            const awayEl = el.querySelector('.event__participant--away');
            
            if (homeEl) homeTeam = homeEl.textContent.trim();
            if (awayEl) awayTeam = awayEl.textContent.trim();
            
            if (homeTeam === 'Unknown' && el.title) {
              const parts = el.title.split(' - ');
              if (parts.length >= 2) {
                homeTeam = parts[0].trim();
                awayTeam = parts[1].trim();
              }
            }
            
            let time = 'TBD';
            const timeEl = el.querySelector('.event__time');
            if (timeEl) time = timeEl.textContent.trim();
            
            const matchId = el.id || `tennis_${i}_${Date.now()}`;
            
            matches.push({
              id: matchId,
              sport: 'tennis',
              homeTeam: homeTeam,
              awayTeam: awayTeam,
              league: 'Unknown League',
              time: time,
              date: new Date().toISOString().split('T')[0],
              odds: {}
            });
            
          } catch (err) {
            console.error(`Error processing tennis match ${i}:`, err.message);
          }
        }
        
        return matches;
      });

      const validMatches = matchData.filter(m => 
        m.homeTeam !== 'Unknown' && m.awayTeam !== 'Unknown'
      );
      
      console.log(`Valid tennis matches: ${validMatches.length} / ${matchData.length}`);
      matches.push(...validMatches);

    } catch (error) {
      console.error('Error scraping tennis:', error.message);
    }

    return matches;
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
          sportMatches = await this.scrapeTennis();
          break;
        case 'hockey':
          console.log('Hockey scraping not implemented yet');
          break;
        default:
          console.log(`Unknown sport: ${sport}`);
      }

      this.matches.push(...sportMatches);
      console.log(`Total matches scraped for ${sport}: ${sportMatches.length}`);
    }

    return this.matches;
  }

  async saveResults() {
    const outputPath = path.join(__dirname, '../../data/matches.json');
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

// Main execution
async function main() {
  // Load configuration
  const configPath = path.join(__dirname, '../../config/config.yaml');
  const configContent = await fs.readFile(configPath, 'utf8');
  const config = yaml.parse(configContent);

  const scraper = new FlashscoreScraper(config);

  try {
    await scraper.initialize();
    await scraper.scrapeAll();
    await scraper.saveResults();
  } catch (error) {
    console.error('Fatal error:', error);
  } finally {
    await scraper.close();
  }
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = FlashscoreScraper;
