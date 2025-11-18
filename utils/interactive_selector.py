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
        import questionary

        self._print_header("STEP 1: SELECT SPORTS")

        sports = sorted(self.sports_data.keys())

        # Create choices with league and match count info
        choices = []
        for sport in sports:
            leagues = self.sports_data[sport]
            league_count = len(leagues)
            match_count = sum(len(matches) for matches in leagues.values())
            choices.append(f"{sport.upper():15} ({league_count:2} leagues, {match_count:3} matches)")

        # Use checkbox for multi-select
        selected_choices = questionary.checkbox(
            "Select sports (Use arrow keys, Space to select, Enter to confirm):",
            choices=choices
        ).ask()

        if not selected_choices:
            print("❌ No sports selected")
            return self._show_sport_selection()

        # Extract sport names from selected choices
        selected = []
        for choice in selected_choices:
            # Extract sport name from choice string (e.g., "FOOTBALL        (30 matches)" → "football")
            sport_name = choice.split()[0].lower()
            selected.append(sport_name)

        print(f"\n✅ Selected: {', '.join([s.upper() for s in selected])}")
        return selected

    def _show_league_selection(self, selected_sports: List[str]) -> List[str]:
        """Show multi-select checklist for leagues (filtered by sport)"""
        import questionary

        self._print_header("STEP 2: SELECT LEAGUES (OR SKIP FOR ALL)")

        # Gather all leagues for selected sports, organized by sport
        league_choices = []
        league_map = {}  # Map display string to actual league name

        for sport in selected_sports:
            sport_leagues = sorted(self.sports_data[sport].keys())
            if sport_leagues:
                # Add sport header (disabled so it's just a label)
                sport_label = f"➤ {sport.upper()}"
                league_choices.append(sport_label)

                for league_name in sport_leagues:
                    count = len(self.sports_data[sport][league_name])
                    # Indent leagues under sport
                    display_str = f"  {league_name[:52]:52} ({count:2})"
                    league_choices.append(display_str)
                    league_map[display_str] = league_name

        if not league_choices:
            print("❌ No leagues found for selected sports")
            return []

        # Add special "All Leagues" option at the top
        all_option = "✓ INCLUDE ALL AVAILABLE LEAGUES"
        league_choices.insert(0, all_option)

        # Use checkbox for multi-select
        selected_choices = questionary.checkbox(
            "Select specific leagues (or leave empty for all):",
            choices=league_choices
        ).ask()

        # If user skipped or selected "All Leagues" option
        if selected_choices is None or not selected_choices or all_option in selected_choices:
            print(f"\n✅ Selected: All available leagues")
            return []  # Empty list means all leagues

        # Extract actual league names from selected choices
        selected_leagues = []
        for choice in selected_choices:
            if choice in league_map:
                selected_leagues.append(league_map[choice])

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
        import questionary

        self._print_header("STEP 4: SELECT ANALYSIS AGENTS")

        agent_choices = [
            "Internet Picks - Consensus tips from betting community",
            "Data-Driven - Statistical analysis of match history",
            "Synthesis - Combine both analyses for final decision"
        ]

        selected_agents = questionary.checkbox(
            "Which agents should run?",
            choices=agent_choices
        ).ask()

        if not selected_agents:
            print("❌ No agents selected")
            return self._show_agents_configuration()

        agents_config = {
            'run_internet_picks': any("Internet Picks" in a for a in selected_agents),
            'run_data_driven': any("Data-Driven" in a for a in selected_agents),
            'run_synthesis': any("Synthesis" in a for a in selected_agents)
        }

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
