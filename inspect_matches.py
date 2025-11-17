#!/usr/bin/env python3
"""
Match Data Inspector
View what matches are available and filter them
"""

import json
from pathlib import Path
from collections import defaultdict
from tabulate import tabulate

def load_matches(filepath='data/matches.json'):
    """Load scraped matches from file"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data.get('matches', [])

def analyze_matches(matches):
    """Analyze and summarize match data"""

    # Group by sport
    by_sport = defaultdict(list)
    by_league = defaultdict(list)

    for match in matches:
        sport = match.get('sport', 'Unknown')
        league = match.get('league', 'Unknown League')

        by_sport[sport].append(match)
        by_league[league].append(match)

    return by_sport, by_league

def print_summary(matches, by_sport, by_league):
    """Print summary of available matches"""

    print("\n" + "="*80)
    print("MATCH DATA SUMMARY")
    print("="*80)

    print(f"\nTotal Matches Scraped: {len(matches)}")

    # Sports breakdown
    print("\n📊 MATCHES BY SPORT:")
    print("-" * 80)
    sport_data = []
    for sport, sport_matches in sorted(by_sport.items()):
        with_odds = len([m for m in sport_matches if m.get('odds')])
        sport_data.append([
            sport.upper(),
            len(sport_matches),
            with_odds,
            f"{with_odds/len(sport_matches)*100:.1f}%" if sport_matches else "0%"
        ])
    print(tabulate(sport_data, headers=["Sport", "Matches", "With Odds", "Odds %"]))

    # League breakdown
    print("\n🏆 AVAILABLE LEAGUES/COMPETITIONS:")
    print("-" * 80)

    league_data = []
    for league, league_matches in sorted(by_league.items(), key=lambda x: -len(x[1])):
        sports_in_league = set(m.get('sport', 'Unknown') for m in league_matches)
        with_odds = len([m for m in league_matches if m.get('odds')])

        league_data.append([
            league,
            len(league_matches),
            with_odds,
            ", ".join(sorted(sports_in_league))
        ])

    print(tabulate(league_data, headers=["League/Competition", "Matches", "With Odds", "Sports"]))

    print("\n" + "="*80)

def print_filter_examples(by_sport, by_league):
    """Print example filter configurations"""

    print("\n📋 FILTER CONFIGURATION EXAMPLES:")
    print("-" * 80)

    # Get sample leagues
    sample_leagues = list(by_league.keys())[:5]

    print("\n# Example 1: Single sport with limit")
    print("filter:")
    print("  sports: ['football']")
    print("  limits:")
    print("    football: 50")

    print("\n# Example 2: Multiple sports with different limits")
    print("filter:")
    print("  sports: ['football', 'tennis']")
    print("  limits:")
    print("    football: 50")
    print("    tennis: 30")

    print("\n# Example 3: Specific leagues only")
    print("filter:")
    print("  sports: ['football']")
    print(f"  leagues: ['{sample_leagues[0]}', '{sample_leagues[1]}']")

    print("\n# Example 4: All sports except one")
    print("filter:")
    print("  sports: ['football', 'tennis', 'basketball']")
    print("  limits:")
    print("    football: 50")
    print("    tennis: 40")
    print("    basketball: 20")

    print("\n# Example 5: Combine sport, league, and limit")
    print("filter:")
    print("  sports: ['football']")
    print(f"  leagues: ['{sample_leagues[0]}']")
    print("  limits:")
    print("    football: 30")

    print("\n" + "="*80)

def apply_filters(matches, sports=None, leagues=None, limits=None):
    """Apply filters to matches"""

    filtered = matches.copy()

    # Filter by sport
    if sports:
        filtered = [m for m in filtered if m.get('sport') in sports]
        print(f"✓ Filtered by sports {sports}: {len(filtered)} matches")

    # Filter by league
    if leagues:
        filtered = [m for m in filtered if m.get('league') in leagues]
        print(f"✓ Filtered by leagues: {len(filtered)} matches")

    # Apply per-sport limits
    if limits:
        limited = []
        sport_counts = defaultdict(int)

        for match in filtered:
            sport = match.get('sport')
            limit = limits.get(sport, float('inf'))

            if sport_counts[sport] < limit:
                limited.append(match)
                sport_counts[sport] += 1

        filtered = limited
        print(f"✓ Applied per-sport limits: {len(filtered)} matches")

    return filtered

def main():
    import sys
    import argparse

    parser = argparse.ArgumentParser(description='Inspect scraped match data')
    parser.add_argument('--summary', action='store_true', default=True,
                        help='Show summary of matches')
    parser.add_argument('--sports', type=str,
                        help='Filter by sports (comma-separated)')
    parser.add_argument('--leagues', type=str,
                        help='Filter by leagues (comma-separated)')
    parser.add_argument('--limit', type=str,
                        help='Per-sport limits (e.g., football:50,tennis:30)')
    parser.add_argument('--show-matches', action='store_true',
                        help='Show detailed match list')

    args = parser.parse_args()

    # Load matches
    matches_file = Path('data/matches.json')
    if not matches_file.exists():
        print(f"❌ No matches file found at {matches_file}")
        print("   Run the scraper first: npm run scrape")
        return

    matches = load_matches(str(matches_file))
    if not matches:
        print("❌ No matches loaded")
        return

    # Analyze
    by_sport, by_league = analyze_matches(matches)

    # Show summary
    if args.summary:
        print_summary(matches, by_sport, by_league)
        print_filter_examples(by_sport, by_league)

    # Apply filters if specified
    if args.sports or args.leagues or args.limit:
        print("\n📌 APPLYING FILTERS:")
        print("-" * 80)

        sports = args.sports.split(',') if args.sports else None
        leagues = args.leagues.split(',') if args.leagues else None

        limits = {}
        if args.limit:
            for item in args.limit.split(','):
                sport, limit = item.split(':')
                limits[sport.strip()] = int(limit.strip())

        filtered = apply_filters(matches, sports=sports, leagues=leagues, limits=limits)

        print(f"\n✅ Filtered result: {len(filtered)} matches ready for analysis")

        # Show breakdown by sport
        if filtered:
            sport_breakdown = defaultdict(int)
            for m in filtered:
                sport_breakdown[m.get('sport')] += 1

            print("\nBreakdown by sport:")
            for sport, count in sorted(sport_breakdown.items()):
                print(f"  • {sport}: {count} matches")

    # Show detailed matches if requested
    if args.show_matches:
        print("\n📋 DETAILED MATCHES:")
        print("-" * 80)

        for i, match in enumerate(matches[:10], 1):
            print(f"\n{i}. {match.get('homeTeam')} vs {match.get('awayTeam')}")
            print(f"   Sport: {match.get('sport')}")
            print(f"   League: {match.get('league')}")
            print(f"   Odds: {match.get('odds', 'N/A')}")
            print(f"   ID: {match.get('id')}")

        if len(matches) > 10:
            print(f"\n... and {len(matches) - 10} more matches")

if __name__ == '__main__':
    main()
