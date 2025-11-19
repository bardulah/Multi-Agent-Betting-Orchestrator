#!/usr/bin/env python3
"""
Test the /show command and result formatting
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(__file__))

from bot_integration import ResultsLoader, ResultFormatter, BetPaginator
from agents.utils.logging_config import get_logger

logger = get_logger(__name__)


def test_results_loader():
    """Test loading results from file"""
    print("\n" + "="*60)
    print("TEST 1: Results Loader")
    print("="*60)

    loader = ResultsLoader()

    # Try to load today's results
    results = loader.load_results("today")

    if results:
        print(f"✅ Loaded results from data/results.json")
        print(f"   Total matches: {results.get('total_matches', 0)}")
        print(f"   Total bets: {results.get('bets_recommended', 0)}")
        print(f"   Recommendations: {len(results.get('recommendations', []))}")
        return True
    else:
        print("⚠️  No results file found (this is expected if not run yet)")
        return False


def test_result_formatter():
    """Test formatting results for display"""
    print("\n" + "="*60)
    print("TEST 2: Result Formatter")
    print("="*60)

    loader = ResultsLoader()
    results = loader.load_results("today")

    if not results:
        print("⚠️  Skipping formatter test (no results file)")
        return True

    # Test summary formatting
    summary = ResultFormatter.format_recommendation_summary(results)
    if summary and "BET" in summary:
        print("✅ Summary formatter works")
        print(f"   Sample: {summary[:100]}...")
    else:
        print("❌ Summary formatter failed")
        return False

    # Test bet formatting
    recommendations = results.get('recommendations', [])
    bet_recommendations = [r for r in recommendations if r.get('recommendation') == 'BET']

    if bet_recommendations:
        bet = bet_recommendations[0]
        formatted = ResultFormatter.format_bet(bet, number=1)
        if formatted and "Match:" in formatted:
            print("✅ Bet formatter works")
            print(f"   Sample: {formatted[:150]}...")
        else:
            print("❌ Bet formatter failed")
            return False
    else:
        print("⚠️  No BET recommendations to format")

    return True


def test_pagination():
    """Test pagination functionality"""
    print("\n" + "="*60)
    print("TEST 3: Pagination")
    print("="*60)

    # Create test bets
    test_bets = [
        {'homeTeam': f'Team {i}', 'awayTeam': f'Team {i+1}'} for i in range(5)
    ]

    paginator = BetPaginator(test_bets)

    # Test initial state
    if paginator.current_index != 0:
        print("❌ Initial index wrong")
        return False
    print("✅ Initial state correct")

    # Test navigation
    if not paginator.has_prev():
        print("✅ Correctly no previous at start")
    else:
        print("❌ Should not have previous at start")
        return False

    if paginator.has_next():
        print("✅ Has next button available")
    else:
        print("❌ Should have next button")
        return False

    # Test moving next
    paginator.next()
    if paginator.current_index == 1:
        print("✅ Navigation next works")
    else:
        print("❌ Navigation next failed")
        return False

    # Test status string
    status = paginator.get_status()
    if status == "2/5":
        print(f"✅ Status string correct: {status}")
    else:
        print(f"❌ Status string wrong: {status} (expected 2/5)")
        return False

    return True


def test_end_to_end():
    """Test end-to-end: load, format, paginate"""
    print("\n" + "="*60)
    print("TEST 4: End-to-End Integration")
    print("="*60)

    loader = ResultsLoader()
    results = loader.load_results("today")

    if not results:
        print("⚠️  Skipping E2E test (no results file)")
        return True

    recommendations = results.get('recommendations', [])
    bet_recommendations = [r for r in recommendations if r.get('recommendation') == 'BET']

    if not bet_recommendations:
        print("⚠️  No BET recommendations to test pagination")
        return True

    # Create paginator
    paginator = BetPaginator(bet_recommendations)

    # Simulate navigation
    steps = 0
    max_steps = len(bet_recommendations) + 2  # Go through all + 2 extra

    while steps < max_steps:
        current = paginator.get_current()
        if not current:
            print(f"❌ Failed to get current bet at step {steps}")
            return False

        status = paginator.get_status()
        if not status:
            print(f"❌ Failed to get status at step {steps}")
            return False

        if paginator.has_next():
            paginator.next()
        elif paginator.has_prev():
            paginator.prev()
        else:
            break

        steps += 1

    print(f"✅ End-to-end navigation works ({steps} steps)")
    return True


def main():
    """Run all tests"""
    print("\n🤖 TELEGRAM BOT /SHOW COMMAND TEST SUITE")
    print("=" * 60)

    results = {
        'Results Loader': test_results_loader(),
        'Result Formatter': test_result_formatter(),
        'Pagination': test_pagination(),
        'End-to-End': test_end_to_end(),
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
        print("✅ All /show command tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
