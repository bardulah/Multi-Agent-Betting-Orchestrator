#!/usr/bin/env node
/**
 * Advanced league extraction - test different parsing strategies
 *
 * Identifies the best approach to extract league names from Flashscore
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs').promises;

puppeteer.use(StealthPlugin());

async function advancedLeagueInspection() {
    console.log('\n🔬 ADVANCED LEAGUE EXTRACTION TEST\n');
    console.log('═'.repeat(70));

    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    try {
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');

        console.log('\n📍 Loading Flashscore...');
        await page.goto('https://www.flashscore.com/football/', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        await page.waitForTimeout(3000);

        console.log('🔬 Testing extraction strategies...\n');

        // Test different league extraction approaches
        const results = await page.evaluate(() => {
            const outcomes = {
                strategy1: [],  // Parent .leagues--live text parsing
                strategy2: [],  // Look for section headers
                strategy3: [],  // Parse from sidebar
                strategy4: []   // Extract from match hierarchy
            };

            const matchElements = document.querySelectorAll('[id^="g_1"]');
            const samplesToTest = Math.min(10, matchElements.length);

            console.log(`Testing ${samplesToTest} matches...\n`);

            for (let i = 0; i < samplesToTest; i++) {
                const el = matchElements[i];

                // STRATEGY 1: Find parent with "leagues--live" class and extract text
                // The parent contains: "EUROPE: World Cup - QualificationStandings17:00Finland..."
                // We need to extract just the league name
                const leaguesLiveParent = el.closest('.leagues--live');
                let strategy1_league = 'Unknown';

                if (leaguesLiveParent) {
                    // Look for text node or first text element
                    // The structure seems to be: REGION: League Name - Type
                    const allText = leaguesLiveParent.textContent;

                    // Try to extract: look for first line until we hit a match element
                    const lines = allText.split('\n').filter(l => l.trim().length > 0);

                    // Usually format: "REGION: League Name" or "REGION: League Name - Type"
                    for (const line of lines) {
                        // Skip lines that look like team names or times
                        if (!/^\d{2}:\d{2}/.test(line.trim()) &&
                            line.length < 100 &&
                            line.includes(':')) {
                            strategy1_league = line.trim();
                            break;
                        }
                    }

                    // Alternative: look for the first strong/bold/heading element
                    const heading = leaguesLiveParent.querySelector('div, span, h1, h2, h3, strong, em');
                    if (heading && heading.textContent.length < 100) {
                        const headingText = heading.textContent.trim();
                        if (headingText.includes(':') || headingText.includes('Cup') || headingText.includes('League')) {
                            strategy1_league = headingText;
                        }
                    }
                }

                outcomes.strategy1.push(strategy1_league);

                // STRATEGY 2: Look for section header above the match
                // Flashscore often has headers like "World Cup - Qualification" above groups of matches
                let strategy2_league = 'Unknown';
                let prev = el.previousElementSibling;
                for (let j = 0; j < 5; j++) {
                    if (!prev) break;
                    const text = prev.textContent.trim();
                    if (text.length > 0 && text.length < 100 &&
                        (text.includes('Cup') || text.includes('League') || text.includes('Championship'))) {
                        strategy2_league = text;
                        break;
                    }
                    prev = prev.previousElementSibling;
                }
                outcomes.strategy2.push(strategy2_league);

                // STRATEGY 3: Check if there's a tournament/category element
                let strategy3_league = 'Unknown';
                const categoryEl = el.querySelector('[class*="tournament"], [class*="category"], [class*="league"]');
                if (categoryEl) {
                    strategy3_league = categoryEl.textContent.trim().substring(0, 100);
                }
                outcomes.strategy3.push(strategy3_league);

                // STRATEGY 4: Look at match element's data attributes or id structure
                let strategy4_league = 'Unknown';
                if (el.id) {
                    // IDs like "g_1_abc123" - might be parseable
                    // But more likely, check all data attributes
                    for (const attr of el.attributes) {
                        if (attr.value.includes('Cup') || attr.value.includes('League')) {
                            strategy4_league = attr.value.substring(0, 50);
                            break;
                        }
                    }
                }
                outcomes.strategy4.push(strategy4_league);
            }

            return {
                matchCount: matchElements.length,
                samplesCount: samplesToTest,
                results: outcomes
            };
        });

        // Analyze results
        console.log('\n📊 RESULTS\n');
        console.log('═'.repeat(70));

        const strategies = [
            { name: 'Strategy 1: Parent .leagues--live parsing', data: results.results.strategy1 },
            { name: 'Strategy 2: Section header lookback', data: results.results.strategy2 },
            { name: 'Strategy 3: Category/tournament element', data: results.results.strategy3 },
            { name: 'Strategy 4: Data attributes', data: results.results.strategy4 }
        ];

        for (const strategy of strategies) {
            const successCount = strategy.data.filter(d => d !== 'Unknown').length;
            const successRate = ((successCount / strategy.data.length) * 100).toFixed(1);

            console.log(`\n${strategy.name}`);
            console.log(`   Success rate: ${successRate}% (${successCount}/${strategy.data.length})`);

            // Show sample results
            const samples = strategy.data.filter(d => d !== 'Unknown').slice(0, 3);
            if (samples.length > 0) {
                console.log('   Sample results:');
                for (const sample of samples) {
                    console.log(`      → "${sample.substring(0, 60)}..."`);
                }
            }
        }

        // Recommendation
        console.log('\n\n🎯 RECOMMENDATION\n');
        console.log('═'.repeat(70));

        const bestStrategy = strategies.reduce((best, current) => {
            const currentSuccess = current.data.filter(d => d !== 'Unknown').length;
            const bestSuccess = best.data.filter(d => d !== 'Unknown').length;
            return currentSuccess > bestSuccess ? current : best;
        });

        const bestRate = (bestStrategy.data.filter(d => d !== 'Unknown').length / bestStrategy.data.length) * 100;
        console.log(`\n✅ BEST APPROACH: ${bestStrategy.name}`);
        console.log(`   Success rate: ${bestRate.toFixed(1)}%`);
        console.log(`\nIMPLEMENTATION:`);
        console.log('   Use this extraction method in flashscore-scraper.js');
        console.log('   as the primary league extraction strategy.\n');

        console.log('═'.repeat(70) + '\n');

    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        await browser.close();
    }
}

advancedLeagueInspection().catch(console.error);
