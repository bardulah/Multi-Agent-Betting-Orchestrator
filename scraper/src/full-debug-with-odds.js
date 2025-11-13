// Full debug to understand page structure with odds visible
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs').promises;

puppeteer.use(StealthPlugin());

async function debug() {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    
    console.log('Navigating to Flashscore football...');
    await page.goto('https://www.flashscore.com/football/', {
        waitUntil: 'domcontentloaded'
    });

    await page.waitForTimeout(3000);
    
    // Click odds tab
    console.log('Clicking odds tab...');
    const clicked = await page.evaluate(() => {
        const allTabs = document.querySelectorAll('.filters__tab');
        const oddsTab = Array.from(allTabs).find(tab => {
          const text = tab.textContent.trim().toLowerCase();
          return text === 'odds' || text.includes('odds');
        });
        
        if (oddsTab) {
          oddsTab.click();
          return true;
        }
        return false;
    });
    
    if (clicked) {
        console.log('✓ Clicked odds tab');
        await page.waitForTimeout(6000); // Wait for odds to load
    }
    
    // Get detailed structure of first match
    const matchStructure = await page.evaluate(() => {
        // Find first match
        const firstMatch = document.querySelector('[id^="g_1"]');
        if (!firstMatch) return { error: 'No match found' };
        
        const result = {
            matchId: firstMatch.id,
            matchClasses: firstMatch.className,
            matchHTML: firstMatch.outerHTML.substring(0, 1500),
            
            // Look for odds in match element
            oddsInMatch: {
                byClass: firstMatch.querySelectorAll('.odds__odd').length,
                bySpan: firstMatch.querySelectorAll('span.up, span.down').length,
                anyOdds: firstMatch.querySelectorAll('[class*="odds"]').length
            },
            
            // Look for odds in parent/siblings
            parent: {
                tag: firstMatch.parentElement?.tagName,
                classes: firstMatch.parentElement?.className,
                oddsCount: firstMatch.parentElement?.querySelectorAll('.odds__odd').length || 0
            },
            
            // Look for odds globally on page
            pageOdds: {
                totalOddsOdd: document.querySelectorAll('.odds__odd').length,
                totalUpDown: document.querySelectorAll('span.up, span.down').length,
                firstOddsOddHTML: document.querySelector('.odds__odd')?.outerHTML.substring(0, 500)
            }
        };
        
        // Try to find relationship between match and odds
        const parentRow = firstMatch.closest('div[class*="event"]');
        if (parentRow) {
            result.parentRow = {
                classes: parentRow.className,
                oddsCount: parentRow.querySelectorAll('.odds__odd').length,
                html: parentRow.outerHTML.substring(0, 2000)
            };
        }
        
        return result;
    });
    
    console.log('\n=== MATCH STRUCTURE ===');
    console.log(JSON.stringify(matchStructure, null, 2));
    
    // Save full page HTML
    const html = await page.content();
    await fs.writeFile('../data/flashscore_with_odds.html', html);
    console.log('\n✓ Full HTML saved to data/flashscore_with_odds.html');
    
    await browser.close();
}

debug().catch(console.error);
