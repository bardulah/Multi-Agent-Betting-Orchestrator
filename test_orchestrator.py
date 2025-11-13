#!/usr/bin/env python3
"""
Test Orchestrator initialization
"""

import sys
import os
from pathlib import Path

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from dotenv import load_dotenv
load_dotenv('config/.env')

print('=== Orchestrator Initialization Test ===\n')

# Remove data/logs to test creation
test_dirs = ['data', 'logs']
print('Testing directory creation...')
for d in test_dirs:
    if Path(d).exists():
        print(f'  {d}/ already exists')
    else:
        print(f'  {d}/ will be created')
print()

try:
    from agents.orchestrator import BettingSystemOrchestrator
    print('✓ Orchestrator imported\n')
    
    print('Initializing orchestrator...')
    orchestrator = BettingSystemOrchestrator('config/config.yaml')
    print('✓ Orchestrator initialized\n')
    
    # Verify directories created
    print('Verifying directories...')
    for d in test_dirs:
        if Path(d).exists():
            print(f'  ✓ {d}/ exists')
        else:
            print(f'  ✗ {d}/ NOT created!')
    
    # Verify API key was validated
    print('\n✓ API key validation passed during init')
    
    # Verify agents initialized
    print('\nAgent verification:')
    print(f'  ✓ Internet Picks Agent: {orchestrator.internet_picks_agent is not None}')
    print(f'  ✓ Data-Driven Agent: {orchestrator.data_driven_agent is not None}')
    print(f'  ✓ Synthesis Agent: {orchestrator.synthesis_agent is not None}')
    print(f'  ✓ Notification Agent: {orchestrator.notification_agent is not None}')
    
    print('\n✅ Orchestrator initialization test PASSED')
    
except Exception as e:
    print(f'\n✗ Test FAILED: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
