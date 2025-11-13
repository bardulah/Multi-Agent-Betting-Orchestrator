// Quick test of scraper functionality without full execution
const fs = require('fs');
const path = require('path');

console.log('=== Scraper Dependencies Test ===');

try {
    // Test required modules
    const puppeteer = require('puppeteer-extra');
    console.log('✓ puppeteer-extra loaded');
    
    const StealthPlugin = require('puppeteer-extra-plugin-stealth');
    console.log('✓ stealth plugin loaded');
    
    const yaml = require('yaml');
    console.log('✓ yaml loaded');
    
    // Test config file exists
    const configPath = path.join(__dirname, 'config', 'config.yaml');
    if (fs.existsSync(configPath)) {
        console.log('✓ config.yaml found');
        const configContent = fs.readFileSync(configPath, 'utf8');
        const config = yaml.parse(configContent);
        console.log('✓ config.yaml parsed successfully');
        console.log(`  - Sports to scrape: ${config.sports.join(', ')}`);
        console.log(`  - Headless mode: ${config.scraper.headless}`);
        console.log(`  - Rate limit: ${config.scraper.rate_limit_delay}ms`);
    } else {
        console.log('✗ config.yaml not found');
    }
    
    // Test data directory
    const dataDir = path.join(__dirname, 'data');
    if (!fs.existsSync(dataDir)) {
        fs.mkdirSync(dataDir, { recursive: true });
        console.log('✓ data directory created');
    } else {
        console.log('✓ data directory exists');
    }
    
    console.log('\n✓ All scraper dependencies OK');
    process.exit(0);
    
} catch (error) {
    console.error('✗ Scraper test failed:', error.message);
    process.exit(1);
}
