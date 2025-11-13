#!/usr/bin/env python3
"""
Test Data-Driven Agent independently
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

print('=== Data-Driven Agent Test ===\n')

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create test match
test_match = {
    'id': 'test_002',
    'homeTeam': 'Manchester City',
    'awayTeam': 'Liverpool',
    'sport': 'football',
    'league': 'Premier League',
    'date': '2025-11-12',
    'time': '15:00'
}

print(f"Test Match: {test_match['homeTeam']} vs {test_match['awayTeam']}")
print(f"Sport: {test_match['sport']}")
print(f"League: {test_match['league']}\n")

try:
    from agents.data_driven_agent import DataDrivenAgent
    print('✓ DataDrivenAgent imported\n')
    
    # Initialize agent
    print('Initializing agent...')
    agent = DataDrivenAgent(config)
    print('✓ Agent initialized\n')
    
    # Test analyze_match
    print('Analyzing match (this will use Google Search for statistics)...')
    print('This may take 10-30 seconds...\n')
    
    result = agent.analyze_match(test_match)
    
    print('✓ Analysis completed!\n')
    print('=== Results ===')
    print(f"Match: {result.get('homeTeam')} vs {result.get('awayTeam')}")
    print(f"Picks: {result.get('picks', [])}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print(f"Key Factors: {result.get('key_factors', [])}")
    print(f"\nAnalysis: {result.get('analysis', 'N/A')[:300]}...")
    
    if result.get('statistics'):
        print(f"\nStatistics Found: {list(result['statistics'].keys())}")
    
    # Save result
    Path('data').mkdir(exist_ok=True)
    with open('data/test_data_driven_result.json', 'w') as f:
        json.dump(result, f, indent=2)
    print('\n✓ Result saved to data/test_data_driven_result.json')
    
    print('\n✅ Data-Driven Agent test PASSED')
    
except Exception as e:
    print(f'\n✗ Test FAILED: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
