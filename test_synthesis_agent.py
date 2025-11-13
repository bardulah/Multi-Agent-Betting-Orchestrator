#!/usr/bin/env python3
"""
Test Synthesis Agent independently
"""

import sys
import os
import yaml
import json
from pathlib import Path

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from dotenv import load_dotenv
load_dotenv('config/.env')

print('=== Synthesis Agent Test ===\n')

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Load previous test results
print('Loading previous agent test results...')
with open('data/test_internet_picks_result.json', 'r') as f:
    internet_picks = json.load(f)
print('✓ Internet Picks result loaded')

with open('data/test_data_driven_result.json', 'r') as f:
    data_driven = json.load(f)
print('✓ Data-Driven result loaded\n')

# Create test match with odds
test_match = {
    'id': 'test_003',
    'homeTeam': 'Manchester City',
    'awayTeam': 'Liverpool',
    'sport': 'football',
    'league': 'Premier League',
    'date': '2025-11-12',
    'time': '15:00',
    'odds': {
        'Bet365': {
            'home': 1.72,
            'draw': 3.75,
            'away': 4.50
        },
        'Unibet': {
            'home': 1.75,
            'draw': 3.80,
            'away': 4.40
        }
    }
}

print(f"Test Match: {test_match['homeTeam']} vs {test_match['awayTeam']}")
print(f"Odds (Bet365): Home {test_match['odds']['Bet365']['home']} | Draw {test_match['odds']['Bet365']['draw']} | Away {test_match['odds']['Bet365']['away']}\n")

try:
    from agents.synthesis_agent import SynthesisAgent
    print('✓ SynthesisAgent imported\n')
    
    # Initialize agent
    print('Initializing agent...')
    agent = SynthesisAgent(config)
    print('✓ Agent initialized\n')
    
    # Test synthesize
    print('Synthesizing analyses...')
    print('This may take 15-30 seconds...\n')
    
    result = agent.synthesize(test_match, internet_picks, data_driven)
    
    print('✓ Synthesis completed!\n')
    print('=== FINAL RECOMMENDATION ===')
    print(f"Match: {result.get('homeTeam')} vs {result.get('awayTeam')}")
    print(f"Recommendation: {result.get('recommendation')}")
    print(f"Recommended Pick: {result.get('recommended_pick')}")
    print(f"Recommended Odds: {result.get('recommended_odds')}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print(f"Agreement Score: {result.get('agreement_score', 0):.2f}")
    print(f"\nValue Assessment: {result.get('value_assessment', 'N/A')}")
    print(f"\nReasoning: {result.get('reasoning', 'N/A')[:400]}...")
    
    # Save result
    with open('data/test_synthesis_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print('\n✓ Result saved to data/test_synthesis_result.json')
    
    print('\n✅ Synthesis Agent test PASSED')
    
except Exception as e:
    print(f'\n✗ Test FAILED: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
