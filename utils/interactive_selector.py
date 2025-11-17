"""
Interactive match and league selector with rich UI for user-friendly configuration
"""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple


class InteractiveSelector:
    """Interactive UI for selecting matches, leagues, and limits"""

    def __init__(self, matches_file: str = 'data/matches.json'):
        self.matches = self._load_matches(matches_file)
        self.sports_data = self._organize_by_sport()

    def _load_matches(self, matches_file: str) -> List[Dict]:
        """Load matches from JSON file"""
        path = Path(matches_file)
        if not path.exists():
            print(f"❌ Matches file not found: {matches_file}")
            print("   Run the scraper first: npm run scrape")
            return []

        try:
            with open(path, 'r') as f:
                data = json.load(f)
                return data.get('matches', [])
        except Exception as e:
            print(f"❌ Error loading matches: {e}")
            return []

    def _organize_by_sport(self) -> Dict[str, Dict]:
        """Organize matches by sport and league"""
        sports_data = defaultdict(lambda: defaultdict(list))

        for match in self.matches:
            sport = match.get('sport', 'Unknown')
            league = match.get('league', 'Unknown League')
            sports_data[sport][league].append(match)

        return dict(sports_data)

    def _print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")

    def _print_section(self, text: str):
        """Print section divider"""
        print(f"\n▶ {text}\n")

    def _show_sport_selection(self) -> List[str]:
        """Show multi-select checklist for sports"""
        self._print_header("STEP 1: SELECT SPORTS")

        sports = sorted(self.sports_data.keys())
        print("Available sports:")
        for i, sport in enumerate(sports, 1):
            count = len(self.sports_data[sport])
            print(f"  [{i}] {sport.upper():15} ({count} matches)")

        print("\nSelect sports (comma-separated numbers, or 'a' for all):")
        print("Example: 1,2 or a")
        user_input = input("Your selection: ").strip().lower()

        if user_input == 'a':
            selected = sports
            print(f"\n✅ Selected: {', '.join([s.upper() for s in selected])}")
        else:
            try:
                indices = [int(x.strip()) - 1 for x in user_input.split(',')]
                selected = [sports[i] for i in indices if 0 <= i < len(sports)]
                if not selected:
                    print("❌ Invalid selection")
                    return self._show_sport_selection()
                print(f"\n✅ Selected: {', '.join([s.upper() for s in selected])}")
            except (ValueError, IndexError):
                print("❌ Invalid input")
                return self._show_sport_selection()

        return selected

    def _show_league_selection(self, selected_sports: List[str]) -> List[str]:
        """Show multi-select checklist for leagues (filtered by sport)"""
        self._print_header("STEP 2: SELECT LEAGUES (OR SKIP FOR ALL)")

        # Gather all leagues for selected sports
        all_leagues = {}
        for sport in selected_sports:
            for league_name in self.sports_data[sport]:
                if league_name not in all_leagues:
                    all_leagues[league_name] = []
                all_leagues[league_name].append(sport)

        if not all_leagues:
            print("❌ No leagues found for selected sports")
            return []

        # Display leagues grouped by sport
        for sport in selected_sports:
            sport_leagues = list(self.sports_data[sport].keys())
            if sport_leagues:
                print(f"\n📍 {sport.upper()}:")
                for i, league in enumerate(sport_leagues, 1):
                    count = len(self.sports_data[sport][league])
                    print(f"  [{i}] {league[:55]:55} ({count:2})")

        print("\n\nSpecific leagues to analyze (or press Enter to select all):")
        print("Example: ENGLAND: Premier League, EUROPE: Champions League")
        print("(Enter 'skip' or leave blank to include all leagues)")

        user_input = input("Your selection: ").strip()

        if not user_input or user_input.lower() == 'skip':
            print(f"\n✅ Selected: All available leagues")
            return []  # Empty list means all leagues

        # Parse user input - support comma-separated league names
        selected_leagues = [l.strip() for l in user_input.split(',')]
        print(f"\n✅ Selected {len(selected_leagues)} specific league(s)")
        return selected_leagues

    def _show_limits_configuration(self, selected_sports: List[str]) -> Dict[str, int]:
        """Configure per-sport match limits"""
        self._print_header("STEP 3: SET MATCH LIMITS PER SPORT")

        limits = {}
        defaults = {
            'football': 50,
            'tennis': 40,
            'basketball': 15,
            'hockey': 20
        }

        print("Set maximum matches to analyze per sport:")
        print("(Press Enter to use default, or enter a number)\n")

        for sport in selected_sports:
            default = defaults.get(sport, 50)
            total = len(self.sports_data[sport])

            try:
                user_input = input(f"  {sport.upper():15} (default: {default}, available: {total}): ").strip()
                if user_input == '':
                    limits[sport] = default
                    print(f"    → Using default: {default}")
                else:
                    limit = int(user_input)
                    if limit <= 0:
                        print(f"    → Invalid (must be > 0), using default: {default}")
                        limits[sport] = default
                    else:
                        limits[sport] = limit
                        print(f"    → Set to: {limit}")
            except ValueError:
                print(f"    → Invalid input, using default: {default}")
                limits[sport] = default

        print(f"\n✅ Limits configured")
        return limits

    def _show_agents_configuration(self) -> Dict[str, bool]:
        """Configure which agents to run"""
        self._print_header("STEP 4: SELECT ANALYSIS AGENTS")

        print("Which agents should run?")
        print("  [1] Internet Picks (finds consensus picks from internet)")
        print("  [2] Data-Driven (analyzes statistics)")
        print("  [3] Synthesis (combines results for final decision)")
        print("\nTypically: all three (1,2,3) for best results\n")

        agents_config = {
            'run_internet_picks': True,
            'run_data_driven': True,
            'run_synthesis': True
        }

        user_input = input("Select agents to run (comma-separated, or 'a' for all): ").strip().lower()

        if user_input == 'a' or not user_input:
            print("\n✅ All agents enabled")
            return agents_config

        # Parse selections
        selected = set()
        try:
            for x in user_input.split(','):
                selected.add(int(x.strip()))
        except ValueError:
            print("❌ Invalid input, using all agents")
            return agents_config

        agents_config['run_internet_picks'] = 1 in selected
        agents_config['run_data_driven'] = 2 in selected
        agents_config['run_synthesis'] = 3 in selected

        agents_enabled = []
        if agents_config['run_internet_picks']:
            agents_enabled.append("Internet Picks")
        if agents_config['run_data_driven']:
            agents_enabled.append("Data-Driven")
        if agents_config['run_synthesis']:
            agents_enabled.append("Synthesis")

        print(f"\n✅ Agents: {', '.join(agents_enabled)}")
        return agents_config

    def _show_preview(self, selected_sports: List[str], selected_leagues: List[str],
                     limits: Dict[str, int]) -> int:
        """Show preview of what will be analyzed"""
        self._print_header("STEP 5: PREVIEW & CONFIRM")

        # Calculate actual matches that will be analyzed
        total_preview = 0
        for sport in selected_sports:
            sport_count = 0
            sport_leagues = self.sports_data[sport]

            for league_name, matches in sport_leagues.items():
                # Check if league is in selected_leagues (if filtering)
                if selected_leagues:
                    if league_name not in selected_leagues:
                        continue

                available = len(matches)
                limit = limits.get(sport, 50)
                will_analyze = min(available - sport_count, limit - sport_count)
                sport_count += will_analyze
                total_preview += will_analyze

            if sport_count > 0:
                limit = limits.get(sport, 50)
                print(f"  {sport.upper():15} {sport_count:3} matches (limit: {limit})")

        print(f"\n{'─'*40}")
        print(f"  Total matches to analyze: {total_preview}")
        time_estimate = max(1, total_preview * 4 / 60)  # ~4 seconds per match
        print(f"  Estimated time: {time_estimate:.0f} minutes")
        print(f"{'─'*40}\n")

        confirm = input("Proceed with analysis? (y/n): ").strip().lower()
        if confirm == 'y':
            print("✅ Starting analysis...\n")
            return total_preview
        else:
            print("❌ Analysis cancelled")
            return 0

    def run_interactive_session(self) -> Dict:
        """Run full interactive selection session"""
        if not self.matches:
            return None

        print("\n")
        print("╔" + "═"*58 + "╗")
        print("║" + " "*58 + "║")
        print("║" + "  🎯 MATCH SELECTION WIZARD".center(58) + "║")
        print("║" + "  Interactive Configuration for Match Analysis".center(58) + "║")
        print("║" + " "*58 + "║")
        print("╚" + "═"*58 + "╝")

        # Step 1: Sport selection
        selected_sports = self._show_sport_selection()
        if not selected_sports:
            return None

        # Step 2: League selection
        selected_leagues = self._show_league_selection(selected_sports)

        # Step 3: Limits configuration
        limits = self._show_limits_configuration(selected_sports)

        # Step 4: Agents configuration
        agents = self._show_agents_configuration()

        # Step 5: Preview
        total = self._show_preview(selected_sports, selected_leagues, limits)
        if total == 0:
            return None

        # Build filter configuration
        filter_config = {
            'enabled': True,
            'name': 'Interactive Selection',
            'description': 'User-selected configuration',
            'sports': selected_sports,
            'leagues': selected_leagues,
            'limits': limits,
            'analysis': agents
        }

        return filter_config
