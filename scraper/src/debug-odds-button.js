// Debug script to find the odds button on Flashscore
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

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

    await page.waitForTimeout(5000);
    
    // Take screenshot before clicking
    await page.screenshot({ path: '../data/flashscore_before_odds.png', fullPage: false });
    console.log('Screenshot saved: data/flashscore_before_odds.png');
    
    // Find all buttons/links with text
    const buttons = await page.evaluate(() => {
        const all = Array.from(document.querySelectorAll('a, button, div, span'));
        return all
            .filter(el => el.textContent && el.offsetHeight > 0)
            .map(el => ({
                tag: el.tagName,
                text: el.textContent.trim().substring(0, 50),
                classList: el.className,
                href: el.href || ''
            }))
            .filter(b => b.text.length > 0 && b.text.length < 30);
    });
    
    console.log('\n=== All clickable elements with short text: ===');
    buttons.slice(0, 50).forEach((b, i) => {
        console.log(`${i}: [${b.tag}] "${b.text}" - ${b.classList}`);
    });
    
    // Try to find and click odds-related element
    console.log('\n\n=== Looking for "Odds" or similar text: ===');
    const oddsRelated = buttons.filter(b => 
        b.text.toLowerCase().includes('odd') || 
        b.text.toLowerCase().includes('kurz') || // Czech/Slovak for odds
        b.text.toLowerCase().includes('quota') // Another word for odds
    );
    
    oddsRelated.forEach(b => {
        console.log(`Found: [${b.tag}] "${b.text}" - ${b.classList}`);
    });
    
    if (oddsRelated.length > 0) {
        console.log(`\nTrying to click: "${oddsRelated[0].text}"`);
        
        const clicked = await page.evaluate((text) => {
            const all = Array.from(document.querySelectorAll('a, button, div, span'));
            const el = all.find(e => e.textContent.includes(text) && e.offsetHeight > 0);
            if (el) {
                el.click();
                return true;
            }
            return false;
        }, oddsRelated[0].text);
        
        if (clicked) {
            console.log('✓ Clicked!');
            await page.waitForTimeout(5000);
            
            await page.screenshot({ path: '../data/flashscore_after_odds.png', fullPage: false });
            console.log('Screenshot saved: data/flashscore_after_odds.png');
        }
    }
    
    // Save HTML for inspection
    const html = await page.content();
    const fs = require('fs').promises;
    await fs.writeFile('../data/flashscore_page.html', html);
    console.log('HTML saved: data/flashscore_page.html');
    
    await browser.close();
}

debug().catch(console.error);
