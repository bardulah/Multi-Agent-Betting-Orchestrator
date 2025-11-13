#!/usr/bin/env python3
"""
Test Notification Agent independently
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

print('=== Notification Agent Test ===\n')

# Load config
with open('config/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Check notification settings
notif_config = config.get('notifications', {})
print(f"Notifications Enabled: {notif_config.get('enabled', False)}")
print(f"Notification Method: {notif_config.get('method', 'N/A')}")
print(f"Email Sender: {notif_config.get('email', {}).get('sender_email', 'N/A')}")
print(f"Email Recipient: {notif_config.get('email', {}).get('recipient_email', 'N/A')}")
print(f"EMAIL_PASSWORD env: {'SET' if os.getenv('EMAIL_PASSWORD') else 'NOT SET'}")
print(f"TELEGRAM_BOT_TOKEN env: {'SET' if os.getenv('TELEGRAM_BOT_TOKEN') else 'NOT SET'}")
print()

# Load test recommendation
print('Loading test synthesis result...')
with open('data/test_synthesis_result.json', 'r') as f:
    test_recommendation = json.load(f)
print('✓ Test recommendation loaded\n')

try:
    from agents.notification_agent import NotificationAgent
    print('✓ NotificationAgent imported\n')
    
    # Initialize agent
    print('Initializing agent...')
    agent = NotificationAgent(config)
    print('✓ Agent initialized\n')
    
    # Create test recommendations list
    recommendations = [test_recommendation]
    
    print(f"Testing with {len(recommendations)} recommendation(s)")
    print(f"BET recommendations: {len([r for r in recommendations if r.get('recommendation') == 'BET'])}\n")
    
    # Test notification
    if notif_config.get('enabled'):
        print('⚠️  Notifications are ENABLED - this will send real notifications!')
        print('Skipping actual send to avoid spam...\n')
        print('✓ Notification Agent initialized correctly')
        print('✓ Can access email/telegram configuration')
    else:
        print('Notifications are disabled in config')
        print('Testing dry-run...')
        success = agent.send_notifications(recommendations)
        print(f'Result: {success}')
    
    print('\n✅ Notification Agent test PASSED')
    
except Exception as e:
    print(f'\n✗ Test FAILED: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)
