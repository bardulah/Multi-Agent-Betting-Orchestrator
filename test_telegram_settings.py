#!/usr/bin/env python3
"""
Test script for Telegram bot settings functionality
"""

import sys
import os
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from bot_integration import UserSettings
from agents.utils.logging_config import get_logger

logger = get_logger(__name__)


def test_settings_initialization():
    """Test UserSettings initializes correctly"""
    print("\n" + "="*60)
    print("TEST 1: Settings Initialization")
    print("="*60)

    try:
        settings = UserSettings()
        print("✅ UserSettings initialized successfully")
        print(f"   Settings file: {settings.settings_file}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize UserSettings: {e}")
        return False


def test_default_settings():
    """Test default settings are applied to new users"""
    print("\n" + "="*60)
    print("TEST 2: Default Settings")
    print("="*60)

    settings = UserSettings()
    test_user = 99999999

    # Get defaults for new user
    user_settings = settings.get_user_settings(test_user)

    # Verify all defaults exist
    required_keys = ['confidence_threshold', 'sports', 'notifications_enabled', 'show_reasoning', 'min_odds_value']
    all_keys_exist = all(key in user_settings for key in required_keys)

    if all_keys_exist:
        print("✅ All default settings present")
        print(f"   Confidence threshold: {user_settings['confidence_threshold']:.0%}")
        print(f"   Sports: {', '.join(user_settings['sports'])}")
        print(f"   Notifications: {user_settings['notifications_enabled']}")
        return True
    else:
        print("❌ Missing default settings")
        return False


def test_update_single_setting():
    """Test updating a single setting"""
    print("\n" + "="*60)
    print("TEST 3: Update Single Setting")
    print("="*60)

    settings = UserSettings()
    test_user = 88888888

    # Update confidence threshold
    success = settings.update_user_setting(test_user, 'confidence_threshold', 0.8)

    if success:
        # Verify it was saved
        user_settings = settings.get_user_settings(test_user)
        if user_settings['confidence_threshold'] == 0.8:
            print("✅ Single setting updated successfully")
            print(f"   New confidence: {user_settings['confidence_threshold']:.0%}")
            return True
        else:
            print("❌ Setting was not saved correctly")
            return False
    else:
        print("❌ Failed to update setting")
        return False


def test_update_multiple_settings():
    """Test updating multiple settings at once"""
    print("\n" + "="*60)
    print("TEST 4: Update Multiple Settings")
    print("="*60)

    settings = UserSettings()
    test_user = 77777777

    # Update multiple settings
    new_settings = {
        'confidence_threshold': 0.75,
        'notifications_enabled': False,
        'sports': ['football', 'basketball']
    }

    success = settings.update_user_settings(test_user, new_settings)

    if success:
        # Verify they were saved
        user_settings = settings.get_user_settings(test_user)
        if (user_settings['confidence_threshold'] == 0.75 and
            user_settings['notifications_enabled'] == False and
            user_settings['sports'] == ['football', 'basketball']):
            print("✅ Multiple settings updated successfully")
            print(f"   Confidence: {user_settings['confidence_threshold']:.0%}")
            print(f"   Notifications: {user_settings['notifications_enabled']}")
            print(f"   Sports: {', '.join(user_settings['sports'])}")
            return True
        else:
            print("❌ Not all settings were saved correctly")
            return False
    else:
        print("❌ Failed to update settings")
        return False


def test_sports_list_manipulation():
    """Test toggling sports on/off"""
    print("\n" + "="*60)
    print("TEST 5: Sports List Manipulation")
    print("="*60)

    settings = UserSettings()
    test_user = 66666666

    # Start with all sports
    all_sports = ['football', 'basketball', 'tennis', 'hockey']
    settings.update_user_setting(test_user, 'sports', all_sports.copy())

    # Remove one sport
    current_sports = settings.get_user_settings(test_user)['sports']
    if 'tennis' in current_sports:
        current_sports.remove('tennis')
    settings.update_user_setting(test_user, 'sports', current_sports)

    # Verify
    user_settings = settings.get_user_settings(test_user)
    if 'tennis' not in user_settings['sports'] and len(user_settings['sports']) == 3:
        print("✅ Sport removal works")
        print(f"   Remaining sports: {', '.join(user_settings['sports'])}")

        # Add it back
        user_settings['sports'].append('tennis')
        settings.update_user_setting(test_user, 'sports', user_settings['sports'])

        # Verify
        final_settings = settings.get_user_settings(test_user)
        if 'tennis' in final_settings['sports'] and len(final_settings['sports']) == 4:
            print("✅ Sport addition works")
            print(f"   Final sports: {', '.join(final_settings['sports'])}")
            return True
        else:
            print("❌ Sport addition failed")
            return False
    else:
        print("❌ Sport removal failed")
        return False


def test_reset_settings():
    """Test resetting user settings to defaults"""
    print("\n" + "="*60)
    print("TEST 6: Reset Settings")
    print("="*60)

    settings = UserSettings()
    test_user = 55555555

    # Modify settings
    settings.update_user_setting(test_user, 'confidence_threshold', 0.5)
    settings.update_user_setting(test_user, 'notifications_enabled', False)

    # Verify changes were made
    modified = settings.get_user_settings(test_user)
    if modified['confidence_threshold'] != 0.7 or modified['notifications_enabled'] != True:
        print("✅ Settings were modified")

        # Reset
        success = settings.reset_user_settings(test_user)
        if success:
            # Verify reset worked
            reset_settings = settings.get_user_settings(test_user)
            if reset_settings['confidence_threshold'] == 0.7 and reset_settings['notifications_enabled'] == True:
                print("✅ Settings reset to defaults successfully")
                return True
            else:
                print("❌ Settings were not fully reset")
                return False
        else:
            print("❌ Reset failed")
            return False
    else:
        print("❌ Failed to modify settings for testing")
        return False


def test_persistence():
    """Test that settings persist across multiple calls"""
    print("\n" + "="*60)
    print("TEST 7: Settings Persistence")
    print("="*60)

    settings1 = UserSettings()
    test_user = 44444444

    # Set a value
    settings1.update_user_setting(test_user, 'confidence_threshold', 0.85)

    # Create a new instance and verify
    settings2 = UserSettings()
    retrieved = settings2.get_user_settings(test_user)

    if retrieved['confidence_threshold'] == 0.85:
        print("✅ Settings persist across instances")
        print(f"   Value: {retrieved['confidence_threshold']:.0%}")
        return True
    else:
        print("❌ Settings did not persist")
        return False


def test_concurrent_users():
    """Test that different users have isolated settings"""
    print("\n" + "="*60)
    print("TEST 8: User Isolation")
    print("="*60)

    settings = UserSettings()

    # Set different values for different users
    settings.update_user_setting(33333333, 'confidence_threshold', 0.6)
    settings.update_user_setting(22222222, 'confidence_threshold', 0.9)

    # Verify isolation
    user1_settings = settings.get_user_settings(33333333)
    user2_settings = settings.get_user_settings(22222222)

    if (user1_settings['confidence_threshold'] == 0.6 and
        user2_settings['confidence_threshold'] == 0.9):
        print("✅ User settings are properly isolated")
        print(f"   User 1 confidence: {user1_settings['confidence_threshold']:.0%}")
        print(f"   User 2 confidence: {user2_settings['confidence_threshold']:.0%}")
        return True
    else:
        print("❌ User settings are not isolated")
        return False


def main():
    """Run all tests"""
    print("\n🤖 TELEGRAM BOT SETTINGS TEST SUITE")
    print("=" * 60)

    results = {
        'Initialization': test_settings_initialization(),
        'Default Settings': test_default_settings(),
        'Update Single Setting': test_update_single_setting(),
        'Update Multiple Settings': test_update_multiple_settings(),
        'Sports Manipulation': test_sports_list_manipulation(),
        'Reset Settings': test_reset_settings(),
        'Persistence': test_persistence(),
        'User Isolation': test_concurrent_users(),
    }

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All settings tests passed! Settings system is ready.")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
