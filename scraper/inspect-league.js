#!/usr/bin/env node
/**
 * Inspect Flashscore DOM for league/tournament extraction
 *
 * This script analyzes the actual DOM structure to find where league
 * information is exposed on Flashscore.
 *
 * Run: node scraper/inspect-league.js
 */

const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs').promises;

puppeteer.use(StealthPlugin());

async function inspectLeagueData() {
    console.log('\n🔍 FLASHSCORE LEAGUE EXTRACTION INSPECTION\n');
    console.log('═'.repeat(70));

    const browser = await puppeteer.launch({
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
        ]
    });

    try {
        const page = await browser.newPage();
        await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36');

        console.log('\n📍 Loading Flashscore Football...');
        await page.goto('https://www.flashscore.com/football/', {
            waitUntil: 'networkidle2',
            timeout: 30000
        });

        await page.waitForTimeout(3000);

        console.log('📊 Analyzing page structure...\n');

        // Inspect the DOM for league information
        const leagueInfo = await page.evaluate(() => {
            const results = {
                totalMatches: 0,
                leagueSourcesFound: [],
                matchExamples: []
            };

            // Get all match elements
            const matchElements = document.querySelectorAll('[id^="g_1"]');
            results.totalMatches = matchElements.length;

            console.log(`Found ${matchElements.length} match elements`);

            // Inspect first 5 matches for league information
            const samplesToInspect = Math.min(5, matchElements.length);

            for (let i = 0; i < samplesToInspect; i++) {
                const el = matchElements[i];
                const example = {
                    matchId: el.id,
                    homeTeam: '',
                    awayTeam: '',
                    leagueCandidates: []
                };

                // Extract team names
                const homeEl = el.querySelector('.event__participant--home');
                const awayEl = el.querySelector('.event__participant--away');

                if (homeEl) example.homeTeam = homeEl.textContent.trim();
                if (awayEl) example.awayTeam = awayEl.textContent.trim();

                // === STRATEGY 1: Look for breadcrumb/path ===
                const breadcrumb = el.closest('[class*="breadcrumb"], [class*="path"], .event__round');
                if (breadcrumb) {
                    example.leagueCandidates.push({
                        strategy: 'breadcrumb parent',
                        value: breadcrumb.textContent.trim().substring(0, 100),
                        selector: 'breadcrumb parent (closest)'
                    });
                }

                // === STRATEGY 2: Look for league/tournament label in same row ===
                const leagueLabel = el.querySelector(
                    '[class*="tournament"], ' +
                    '[class*="league"], ' +
                    '[class*="category"], ' +
                    '.event__round, ' +
                    '[class*="badge"]'
                );
                if (leagueLabel) {
                    example.leagueCandidates.push({
                        strategy: 'league label',
                        value: leagueLabel.textContent.trim().substring(0, 100),
                        selector: leagueLabel.className,
                        tagName: leagueLabel.tagName
                    });
                }

                // === STRATEGY 3: Look in parent containers ===
                let parent = el.parentElement;
                for (let j = 0; j < 5; j++) {
                    if (!parent) break;

                    const leagueText = parent.querySelector('[class*="league"], [class*="tournament"]');
                    if (leagueText && leagueText.textContent.trim().length > 0) {
                        example.leagueCandidates.push({
                            strategy: `parent (level ${j})`,
                            value: leagueText.textContent.trim().substring(0, 100),
                            selector: leagueText.className,
                            parentLevel: j
                        });
                        break;
                    }

                    parent = parent.parentElement;
                }

                // === STRATEGY 4: Look for text nodes with league patterns ===
                const allText = el.textContent;
                const leaguePatterns = [
                    /([A-Z][a-zA-Z\s]+\s(?:Cup|League|Championship|Playoff|Qualifier|Final))/g,
                    /([A-Z][a-zA-Z\s]+\s(?:Premier|Division|Serie|Ligue))/g,
                    /(?:Group\s+[A-Z]|Round\s+\d+|Knockout)/g
                ];

                let patternMatches = [];
                for (const pattern of leaguePatterns) {
                    const matches = allText.match(pattern);
                    if (matches) {
                        patternMatches.push(...matches);
                    }
                }

                if (patternMatches.length > 0) {
                    example.leagueCandidates.push({
                        strategy: 'regex pattern match',
                        values: [...new Set(patternMatches)].slice(0, 3)  // unique top 3
                    });
                }

                // === STRATEGY 5: Check title attribute ===
                if (el.title && el.title.length > 0) {
                    example.leagueCandidates.push({
                        strategy: 'title attribute',
                        value: el.title.substring(0, 100)
                    });
                }

                // === STRATEGY 6: Look for data attributes ===
                const dataAttrs = {};
                for (const attr of el.attributes) {
                    if (attr.name.includes('league') || attr.name.includes('tournament') || attr.name.includes('category')) {
                        dataAttrs[attr.name] = attr.value;
                    }
                }
                if (Object.keys(dataAttrs).length > 0) {
                    example.leagueCandidates.push({
                        strategy: 'data attributes',
                        attributes: dataAttrs
                    });
                }

                results.matchExamples.push(example);
            }

            return results;
        });

        // Save inspection results
        const report = {
            timestamp: new Date().toISOString(),
            url: 'https://www.flashscore.com/football/',
            totalMatches: leagueInfo.totalMatches,
            samplesInspected: leagueInfo.matchExamples.length,
            matches: leagueInfo.matchExamples
        };

        console.log('\n📋 INSPECTION RESULTS\n');
        console.log('═'.repeat(70));

        for (const match of leagueInfo.matchExamples) {
            console.log(`\n🎯 ${match.homeTeam} vs ${match.awayTeam}`);
            console.log(`   ID: ${match.matchId}`);

            if (match.leagueCandidates.length === 0) {
                console.log('   ❌ No league information found');
            } else {
                console.log('   ✅ League candidates:');
                for (const candidate of match.leagueCandidates) {
                    console.log(`      • [${candidate.strategy}]`);
                    if (candidate.value) {
                        console.log(`        Value: "${candidate.value}"`);
                    }
                    if (candidate.values) {
                        console.log(`        Values: ${candidate.values.map(v => `"${v}"`).join(', ')}`);
                    }
                    if (candidate.attributes) {
                        console.log(`        Attributes: ${JSON.stringify(candidate.attributes)}`);
                    }
                }
            }
        }

        console.log('\n═'.repeat(70));
        console.log(`\n📊 SUMMARY`);
        console.log(`   Total matches on page: ${leagueInfo.totalMatches}`);
        console.log(`   Samples inspected: ${leagueInfo.matchExamples.length}`);
        console.log(`   Matches with league data: ${
            leagueInfo.matchExamples.filter(m => m.leagueCandidates.length > 0).length
        }`);

        // Save detailed report
        await fs.writeFile(
            'data/league-inspection-report.json',
            JSON.stringify(report, null, 2)
        );
        console.log(`\n💾 Detailed report saved to: data/league-inspection-report.json`);

        // Analysis and recommendations
        console.log('\n🔍 ANALYSIS\n');

        const successRate = leagueInfo.matchExamples.filter(m => m.leagueCandidates.length > 0).length /
                           leagueInfo.matchExamples.length;

        if (successRate === 1.0) {
            console.log('✅ All matches have league information available in DOM');
            console.log('   → Proceed with implementation using found strategies');
        } else if (successRate > 0.7) {
            console.log('⚠️  Most matches have league information (~' + (successRate * 100).toFixed(0) + '%)');
            console.log('   → Use primary strategies, fallback to "Unknown" for missing');
        } else if (successRate > 0.3) {
            console.log('⚠️  Some matches have league information (~' + (successRate * 100).toFixed(0) + '%)');
            console.log('   → May need supplementary data source or URL pattern analysis');
        } else {
            console.log('❌ League information not easily available in DOM');
            console.log('   → May need to use URL structure or external API');
        }

        console.log('\n═'.repeat(70) + '\n');

    } catch (error) {
        console.error('Error during inspection:', error.message);
    } finally {
        await browser.close();
    }
}

// Run inspection
inspectLeagueData().catch(console.error);
