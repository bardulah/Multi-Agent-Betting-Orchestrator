// Inspect Flashscore structure to find correct selectors
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs').promises;

puppeteer.use(StealthPlugin());

async function inspectFlashscore() {
    console.log('Launching browser...\n');
    const browser = await puppeteer.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
        ]
    });

    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');
    
    console.log('Navigating to Flashscore football...\n');
    await page.goto('https://www.flashscore.com/football/', {
        waitUntil: 'networkidle2',
        timeout: 30000
    });

    await page.waitForTimeout(3000);

    console.log('=== INSPECTING PAGE STRUCTURE ===\n');

    // Find match containers
    const matchInfo = await page.evaluate(() => {
        // Try different possible selectors for matches
        const possibleSelectors = [
            '.event__match',
            '[class*="event"]',
            '[id*="g_1"]',
            '.sportName',
            '[class*="match"]',
            'div[title]'
        ];

        let foundMatches = [];
        
        for (const selector of possibleSelectors) {
            const elements = document.querySelectorAll(selector);
            if (elements.length > 0) {
                console.log(`Selector "${selector}" found ${elements.length} elements`);
                
                // Get first few matches
                const samples = Array.from(elements).slice(0, 3).map(el => {
                    return {
                        selector: selector,
                        id: el.id || 'no-id',
                        classes: el.className,
                        innerHTML: el.innerHTML.substring(0, 300),
                        textContent: el.textContent.substring(0, 100)
                    };
                });
                
                foundMatches.push({
                    selector,
                    count: elements.length,
                    samples
                });
            }
        }

        // Try to find team names specifically
        const teamSelectors = [
            '.event__participant--home',
            '.event__participant--away',
            '[class*="participant"]',
            '[class*="team"]',
            '[class*="home"]',
            '[class*="away"]'
        ];

        let teamElements = [];
        for (const selector of teamSelectors) {
            const els = document.querySelectorAll(selector);
            if (els.length > 0) {
                teamElements.push({
                    selector,
                    count: els.length,
                    sample: els[0] ? els[0].textContent.trim() : 'empty'
                });
            }
        }

        return {
            matchElements: foundMatches,
            teamElements,
            pageTitle: document.title,
            bodyClasses: document.body.className
        };
    });

    console.log('Page Title:', matchInfo.pageTitle);
    console.log('\n=== MATCH ELEMENTS FOUND ===');
    console.log(JSON.stringify(matchInfo.matchElements, null, 2));
    
    console.log('\n=== TEAM ELEMENTS FOUND ===');
    console.log(JSON.stringify(matchInfo.teamElements, null, 2));

    // Save detailed HTML snapshot of first match
    console.log('\n=== GETTING FIRST MATCH HTML ===');
    const firstMatchHTML = await page.evaluate(() => {
        const match = document.querySelector('[id^="g_1"]') || 
                      document.querySelector('.event__match') ||
                      document.querySelector('[class*="event"]');
        
        if (match) {
            return {
                id: match.id,
                outerHTML: match.outerHTML.substring(0, 2000),
                classList: Array.from(match.classList)
            };
        }
        return null;
    });

    if (firstMatchHTML) {
        console.log('First Match ID:', firstMatchHTML.id);
        console.log('First Match Classes:', firstMatchHTML.classList);
        console.log('\nFirst Match HTML (truncated):');
        console.log(firstMatchHTML.outerHTML);
    }

    // Save to file
    await fs.writeFile(
        'data/flashscore_inspection.json',
        JSON.stringify({ matchInfo, firstMatchHTML }, null, 2)
    );
    
    console.log('\n✓ Inspection saved to data/flashscore_inspection.json');

    await browser.close();
}

inspectFlashscore().catch(console.error);
