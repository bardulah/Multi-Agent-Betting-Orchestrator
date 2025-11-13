#!/usr/bin/env python3
"""
Quick test to verify the fixes without running full system
Tests a single match to see if Session ID fix works
"""

import sys
import json
from pathlib import Path
from agents.synthesis_agent import SynthesisAgent
from dotenv import load_dotenv
import yaml

# Load config
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Load env
load_dotenv('config/.env')

# Create test match
test_match = {
    'id': 'test_match_001',
    'homeTeam': 'Test Team A',
    'awayTeam': 'Test Team B',
    'sport': 'football',
    'league': 'Test League',
    'time': '15:00',
    'odds': {
        'home_win': 1.5,
        'draw': 3.5,
        'away_win': 5.0
    }
}

# Test Synthesis Agent with unique session IDs
print("Testing Synthesis Agent with unique session IDs...")
print("=" * 60)

synthesis = SynthesisAgent(config)

# Create dummy analyses
internet_picks = {
    'picks': ['home_win'],
    'confidence': 0.75,
    'consensus': 'Test consensus',
    'summary': 'Test summary'
}

data_driven = {
    'picks': ['home_win'],
    'confidence': 0.80,
    'analysis': 'Test analysis',
    'key_factors': ['Factor 1', 'Factor 2']
}

# Test 3 matches to verify unique sessions
for i in range(3):
    test_match['id'] = f'test_match_{i:03d}'
    print(f"\n[Test {i+1}] Synthesizing {test_match['homeTeam']} vs {test_match['awayTeam']}")
    
    try:
        result = synthesis.synthesize(test_match, internet_picks, data_driven)
        print(f"✓ Success! Recommendation: {result.get('recommendation', 'ERROR')}")
        if result.get('recommendation') == 'BET':
            print(f"  Confidence: {result.get('confidence', 0)}")
            print(f"  Pick: {result.get('pick', 'Unknown')}")
    except Exception as e:
        print(f"✗ FAILED: {e}")

print("\n" + "=" * 60)
print("Test complete!")
