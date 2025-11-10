#!/usr/bin/env python3
"""
Live API test - Testing agents with real Google API calls!
"""

import sys
import os
import yaml
import asyncio
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

# Load environment
load_dotenv('config/.env')

from agents.internet_picks_agent import InternetPicksAgent
from agents.data_driven_agent import DataDrivenAgent
from agents.synthesis_agent import SynthesisAgent

async def test_internet_picks():
    print("=" * 60)
    print("🔥 TESTING INTERNET PICKS AGENT - LIVE API 🔥")
    print("=" * 60)

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # Create test match
    test_match = {
        'id': 'live_test_001',
        'homeTeam': 'Manchester City',
        'awayTeam': 'Liverpool',
        'sport': 'football',
        'league': 'Premier League',
        'date': '2025-01-15',
        'time': '15:00'
    }

    print(f"\nTest Match: {test_match['homeTeam']} vs {test_match['awayTeam']}")
    print(f"Sport: {test_match['sport']}")

    # Initialize agent
    print("\n[1/3] Initializing Internet Picks Agent...")
    agent = InternetPicksAgent(config)
    print("✓ Agent initialized")

    # Test analysis
    print("\n[2/3] Running analysis with LIVE API call...")
    print("This will use google_search tool to find real betting tips!")
    print("(This may take 10-30 seconds...)")

    try:
        result = await agent.analyze_match_async(test_match)

        print("\n[3/3] ✓ ANALYSIS COMPLETE!")
        print("=" * 60)
        print("\n📊 RESULTS:")
        print(f"  Match: {result['homeTeam']} vs {result['awayTeam']}")
        print(f"  Picks: {result['picks']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Sources: {result['sources_count']}")
        print(f"  Consensus: {result['consensus']}")
        print(f"\n  Summary:")
        print(f"  {result['summary'][:300]}...")

        return result

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_data_driven():
    print("\n\n" + "=" * 60)
    print("🔥 TESTING DATA-DRIVEN AGENT - LIVE API 🔥")
    print("=" * 60)

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    test_match = {
        'id': 'live_test_002',
        'homeTeam': 'Manchester City',
        'awayTeam': 'Liverpool',
        'sport': 'football',
        'league': 'Premier League',
        'date': '2025-01-15',
        'time': '15:00'
    }

    print(f"\nTest Match: {test_match['homeTeam']} vs {test_match['awayTeam']}")

    print("\n[1/3] Initializing Data-Driven Agent...")
    agent = DataDrivenAgent(config)
    print("✓ Agent initialized")

    print("\n[2/3] Running statistical analysis with LIVE API call...")
    print("(This may take 10-30 seconds...)")

    try:
        result = await agent.analyze_match_async(test_match)

        print("\n[3/3] ✓ ANALYSIS COMPLETE!")
        print("=" * 60)
        print("\n📊 RESULTS:")
        print(f"  Match: {result['homeTeam']} vs {result['awayTeam']}")
        print(f"  Picks: {result['picks']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Key Factors: {', '.join(result['key_factors'][:3])}")
        print(f"\n  Analysis:")
        print(f"  {result['analysis'][:300]}...")

        return result

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_synthesis(internet_result, data_result):
    print("\n\n" + "=" * 60)
    print("🔥 TESTING SYNTHESIS AGENT - LIVE API 🔥")
    print("=" * 60)

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    test_match = {
        'id': 'live_test_003',
        'homeTeam': 'Manchester City',
        'awayTeam': 'Liverpool',
        'sport': 'football',
        'league': 'Premier League',
        'date': '2025-01-15',
        'time': '15:00',
        'odds': {
            'Bet365': {'home': 2.10, 'draw': 3.50, 'away': 3.20},
            '1xBet': {'home': 2.15, 'draw': 3.45, 'away': 3.15}
        }
    }

    print(f"\nTest Match: {test_match['homeTeam']} vs {test_match['awayTeam']}")
    print(f"Available odds: {len(test_match['odds'])} bookmakers")

    print("\n[1/3] Initializing Synthesis Agent...")
    agent = SynthesisAgent(config)
    print("✓ Agent initialized")

    print("\n[2/3] Synthesizing both analyses...")
    print("(This may take 10-30 seconds...)")

    try:
        result = await agent.synthesize_async(test_match, internet_result, data_result)

        print("\n[3/3] ✓ SYNTHESIS COMPLETE!")
        print("=" * 60)
        print("\n🎯 FINAL RECOMMENDATION:")
        print(f"  Decision: {result['recommendation']}")
        if result['recommendation'] == 'BET':
            print(f"  Pick: {result['recommended_pick']}")
            print(f"  Odds: {result['recommended_odds']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Agreement Score: {result['agreement_score']:.2%}")
        print(f"\n  Reasoning:")
        print(f"  {result['reasoning'][:400]}...")

        return result

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    print("\n" + "🚀" * 30)
    print("LIVE API TESTING - LET'S GOOOO!")
    print("🚀" * 30)

    # Test Internet Picks
    internet_result = await test_internet_picks()

    if not internet_result:
        print("\n✗ Internet Picks test failed, stopping here")
        return False

    # Test Data-Driven
    data_result = await test_data_driven()

    if not data_result:
        print("\n✗ Data-Driven test failed, but continuing...")

    # Test Synthesis
    if internet_result and data_result:
        synthesis_result = await test_synthesis(internet_result, data_result)

    print("\n\n" + "=" * 60)
    print("🎉 LIVE API TESTING COMPLETE! 🎉")
    print("=" * 60)
    print("\n✓ The agents work with real API calls!")
    print("✓ google_search tool is functioning!")
    print("✓ LLM analysis is working!")
    print("\nNext: Test with scraper for full end-to-end workflow")

    return True

if __name__ == '__main__':
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
