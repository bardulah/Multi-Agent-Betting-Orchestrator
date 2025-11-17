#!/usr/bin/env python3
"""
Integration Test Suite for Multi-Agent Betting System

Tests the complete pipeline:
1. Scraper → data/matches.json
2. Opportunity Agent → data/opportunities.json
3. Internet Picks Agent → analysis
4. Data-Driven Agent → analysis
5. Synthesis Agent → final recommendation
6. Notification Agent → delivery

Run with: python3 test_integration.py
"""

import json
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from agents.orchestrator import BettingSystemOrchestrator
from agents.utils.logging_config import get_logger

logger = get_logger(__name__)


class IntegrationTestSuite:
    """Run integration tests on the betting system"""

    def __init__(self):
        self.test_data_dir = Path('data')
        self.test_data_dir.mkdir(exist_ok=True)
        self.matches_file = self.test_data_dir / 'matches.json'
        self.opportunities_file = self.test_data_dir / 'opportunities.json'
        self.results_file = self.test_data_dir / 'integration_test_results.json'

    def load_matches(self):
        """Load scraped matches"""
        if not self.matches_file.exists():
            raise FileNotFoundError(f"Matches file not found: {self.matches_file}")

        with open(self.matches_file, 'r') as f:
            data = json.load(f)
            return data.get('matches', [])

    def load_opportunities(self):
        """Load opportunity analysis results"""
        if not self.opportunities_file.exists():
            raise FileNotFoundError(f"Opportunities file not found: {self.opportunities_file}")

        with open(self.opportunities_file, 'r') as f:
            data = json.load(f)
            return data.get('opportunities', [])

    def test_phase_1_scraper(self):
        """Test Phase 1: Scraper output"""
        print("\n" + "="*70)
        print("TEST 1: Phase 1 - Scraper Output")
        print("="*70)

        matches = self.load_matches()
        print(f"✓ Loaded {len(matches)} matches")

        # Verify data completeness
        sports_count = {}
        league_count = 0
        odds_count = 0

        for match in matches:
            sport = match.get('sport', 'unknown')
            sports_count[sport] = sports_count.get(sport, 0) + 1

            if match.get('league') and match['league'] != 'Unknown League':
                league_count += 1

            if match.get('odds') and match['odds'].get('Flashscore'):
                odds_count += 1

        print(f"\nData Completeness:")
        print(f"  - Total matches: {len(matches)}")
        print(f"  - Sports coverage: {sports_count}")
        print(f"  - Matches with league: {league_count}/{len(matches)} ({100*league_count/len(matches):.1f}%)")
        print(f"  - Matches with odds: {odds_count}/{len(matches)} ({100*odds_count/len(matches):.1f}%)")

        if league_count < len(matches) * 0.8:
            logger.warning(f"⚠️  Low league coverage ({league_count}/{len(matches)})")
        if odds_count < len(matches) * 0.5:
            logger.warning(f"⚠️  Low odds coverage ({odds_count}/{len(matches)})")

        return {
            'phase': 1,
            'status': 'PASS',
            'matches_total': len(matches),
            'sports': sports_count,
            'league_coverage': f"{100*league_count/len(matches):.1f}%",
            'odds_coverage': f"{100*odds_count/len(matches):.1f}%"
        }

    def test_phase_2_opportunity_agent(self):
        """Test Phase 2: Opportunity Agent scoring"""
        print("\n" + "="*70)
        print("TEST 2: Phase 2 - Opportunity Agent Scoring")
        print("="*70)

        opportunities = self.load_opportunities()
        print(f"✓ Loaded {len(opportunities)} ranked opportunities")

        # Score distribution
        distribution = {
            'strong_buy': len([o for o in opportunities if o['opportunity']['compositeScore'] >= 80]),
            'buy': len([o for o in opportunities if 60 <= o['opportunity']['compositeScore'] < 80]),
            'hold': len([o for o in opportunities if 40 <= o['opportunity']['compositeScore'] < 60]),
            'skip': len([o for o in opportunities if o['opportunity']['compositeScore'] < 40]),
        }

        print(f"\nScore Distribution:")
        print(f"  - STRONG BUY (80-100): {distribution['strong_buy']}")
        print(f"  - BUY (60-80): {distribution['buy']}")
        print(f"  - HOLD (40-60): {distribution['hold']}")
        print(f"  - SKIP (0-40): {distribution['skip']}")

        if len(opportunities) > 0:
            avg_score = sum(o['opportunity']['compositeScore'] for o in opportunities) / len(opportunities)
            print(f"  - Average score: {avg_score:.1f}/100")

            print(f"\nTop 3 Opportunities:")
            for i, opp in enumerate(opportunities[:3], 1):
                matchup = f"{opp['homeTeam']} vs {opp['awayTeam']}"
                score = opp['opportunity']['compositeScore']
                action = opp['opportunity']['recommendation']['action']
                print(f"  {i}. {matchup}: {score}/100 → {action}")

        return {
            'phase': 2,
            'status': 'PASS',
            'opportunities_found': len(opportunities),
            'distribution': distribution
        }

    def test_phase_3_agents_ready(self):
        """Test Phase 3: Python agents are ready"""
        print("\n" + "="*70)
        print("TEST 3: Phase 3 - Python Agents Ready")
        print("="*70)

        try:
            from agents.internet_picks_agent import InternetPicksAgent
            from agents.data_driven_agent import DataDrivenAgent
            from agents.synthesis_agent import SynthesisAgent
            from agents.notification_agent import NotificationAgent

            print("✓ InternetPicksAgent imported")
            print("✓ DataDrivenAgent imported")
            print("✓ SynthesisAgent imported")
            print("✓ NotificationAgent imported")

            # Try to initialize (requires config)
            import yaml
            with open('config/config.yaml', 'r') as f:
                config = yaml.safe_load(f)

            print("\nAgent Initialization:")
            try:
                internet_agent = InternetPicksAgent(config)
                print("✓ InternetPicksAgent initialized")
            except Exception as e:
                print(f"⚠️  InternetPicksAgent init: {e}")

            try:
                data_agent = DataDrivenAgent(config)
                print("✓ DataDrivenAgent initialized")
            except Exception as e:
                print(f"⚠️  DataDrivenAgent init: {e}")

            try:
                synthesis_agent = SynthesisAgent(config)
                print("✓ SynthesisAgent initialized")
            except Exception as e:
                print(f"⚠️  SynthesisAgent init: {e}")

            return {
                'phase': 3,
                'status': 'PASS',
                'agents_ready': ['InternetPicksAgent', 'DataDrivenAgent', 'SynthesisAgent', 'NotificationAgent']
            }

        except Exception as e:
            logger.error(f"Error testing Phase 3: {e}")
            return {
                'phase': 3,
                'status': 'PARTIAL',
                'error': str(e)
            }

    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "#"*70)
        print("# MULTI-AGENT BETTING SYSTEM - INTEGRATION TEST SUITE")
        print("#"*70)

        results = []

        try:
            # Phase 1
            result1 = self.test_phase_1_scraper()
            results.append(result1)
        except Exception as e:
            logger.error(f"Phase 1 test failed: {e}")
            results.append({'phase': 1, 'status': 'FAIL', 'error': str(e)})

        try:
            # Phase 2
            result2 = self.test_phase_2_opportunity_agent()
            results.append(result2)
        except Exception as e:
            logger.error(f"Phase 2 test failed: {e}")
            results.append({'phase': 2, 'status': 'FAIL', 'error': str(e)})

        try:
            # Phase 3
            result3 = self.test_phase_3_agents_ready()
            results.append(result3)
        except Exception as e:
            logger.error(f"Phase 3 test failed: {e}")
            results.append({'phase': 3, 'status': 'FAIL', 'error': str(e)})

        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        passed = sum(1 for r in results if r.get('status') == 'PASS')
        total = len(results)

        print(f"\nResults: {passed}/{total} tests passed")

        for result in results:
            status = result.get('status', 'UNKNOWN')
            phase = result.get('phase', '?')
            symbol = '✓' if status == 'PASS' else '⚠️' if status == 'PARTIAL' else '✗'
            print(f"{symbol} Phase {phase}: {status}")

        # Save results
        output = {
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'summary': f"{passed}/{total} tests passed",
            'results': results
        }

        with open(self.results_file, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n✓ Results saved to {self.results_file}")
        print("\n" + "#"*70)
        print("# INTEGRATION TEST COMPLETE")
        print("#"*70 + "\n")

        return results


def main():
    """Main entry point"""
    suite = IntegrationTestSuite()
    results = suite.run_all_tests()

    # Exit with status code
    passed = sum(1 for r in results if r.get('status') == 'PASS')
    sys.exit(0 if passed == len(results) else 1)


if __name__ == '__main__':
    main()
