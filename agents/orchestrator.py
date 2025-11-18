"""
Orchestrator
Main coordinator for the multi-agent betting system
"""

import os
import json
import yaml
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from google.adk.sessions import InMemorySessionService

from .internet_picks_agent import InternetPicksAgent
from .data_driven_agent import DataDrivenAgent
from .synthesis_agent import SynthesisAgent
from .notification_agent import NotificationAgent
from .betting_orchestrator_agent import BettingOrchestratorAgent
from .utils.logging_config import setup_logging, get_logger


class BettingSystemOrchestrator:
    """
    Main orchestrator that coordinates all agents in the betting system
    """

    def __init__(self, config_path: str = 'config/config.yaml'):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Setup logging first
        setup_logging(self.config)
        self.logger = get_logger(__name__)

        # Load environment variables
        from dotenv import load_dotenv
        env_loaded = load_dotenv('config/.env')
        self.logger.info(f"Environment variables loaded: {env_loaded}")
        
        # Verify critical environment variables
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if google_api_key:
            self.logger.info(f"✓ GOOGLE_API_KEY loaded ({len(google_api_key)} chars)")
        else:
            self.logger.error("✗ GOOGLE_API_KEY not found after loading .env")

        # Validate API key (already verified above)
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key:
            self.logger.error("GOOGLE_API_KEY not found in environment variables!")
            self.logger.error("Please set GOOGLE_API_KEY in config/.env file")
            raise ValueError("Missing GOOGLE_API_KEY - required for ADK agents")

        # Create necessary directories
        Path('data').mkdir(exist_ok=True)
        Path('logs').mkdir(exist_ok=True)

        # Initialize agents
        self.logger.info("Initializing agents...")
        self.internet_picks_agent = InternetPicksAgent(self.config)
        self.data_driven_agent = DataDrivenAgent(self.config)
        self.synthesis_agent = SynthesisAgent(self.config)
        self.notification_agent = NotificationAgent(self.config)
        self.orchestrator_agent = BettingOrchestratorAgent(self.config)

        self.logger.info("All agents initialized successfully")

    def load_matches_from_file(self) -> List[Dict]:
        """
        Load matches from the pre-scraped JSON file (without re-scraping)

        Returns:
            List of match dictionaries, or empty list if file not found
        """
        try:
            matches_file = Path(self.config['storage']['matches_file'])
            if matches_file.exists():
                with open(matches_file, 'r') as f:
                    data = json.load(f)
                    matches = data.get('matches', [])
                self.logger.info(f"Loaded {len(matches)} matches from existing file (no scraping)")
                return matches
            else:
                self.logger.warning(f"Matches file not found: {matches_file}")
                return []
        except Exception as e:
            self.logger.error(f"Error loading matches from file: {e}")
            return []

    def run_scraper(self) -> List[Dict]:
        """
        Run the Node.js scraper to get match data

        Returns:
            List of match dictionaries
        """
        self.logger.info("Running Flashscore scraper...")

        try:
            # Check if node_modules exists
            scraper_dir = Path(__file__).parent.parent / 'scraper'
            node_modules = scraper_dir / 'node_modules'

            if not node_modules.exists():
                self.logger.info("Installing scraper dependencies...")
                subprocess.run(
                    ['npm', 'install'],
                    cwd=scraper_dir,
                    check=True,
                    capture_output=True
                )

            # Run the scraper
            result = subprocess.run(
                ['npm', 'run', 'scrape'],
                cwd=scraper_dir,
                check=True,
                capture_output=True,
                text=True
            )

            self.logger.info("Scraper completed successfully")
            self.logger.debug(f"Scraper output: {result.stdout}")

            # Load scraped data
            matches_file = Path(self.config['storage']['matches_file'])
            if matches_file.exists():
                with open(matches_file, 'r') as f:
                    data = json.load(f)
                    matches = data.get('matches', [])
                    self.logger.info(f"Loaded {len(matches)} matches from scraper")
                    return matches
            else:
                self.logger.error("Matches file not found after scraping")
                return []

        except subprocess.CalledProcessError as e:
            self.logger.error(f"Scraper failed: {e}")
            self.logger.error(f"Output: {e.output}")
            return []
        except Exception as e:
            self.logger.error(f"Error running scraper: {e}")
            return []

    def analyze_match_parallel(self, match: Dict) -> Dict:
        """
        Analyze a single match with both agents in parallel

        Args:
            match: Match data dictionary

        Returns:
            Dictionary with both analyses
        """
        self.logger.info(f"Analyzing match: {match['homeTeam']} vs {match['awayTeam']}")

        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both agent tasks
            internet_future = executor.submit(
                self.internet_picks_agent.analyze_match,
                match
            )
            data_driven_future = executor.submit(
                self.data_driven_agent.analyze_match,
                match
            )

            # Wait for both to complete
            internet_result = internet_future.result()
            data_driven_result = data_driven_future.result()

        return {
            'match': match,
            'internet_picks': internet_result,
            'data_driven': data_driven_result
        }

    async def process_all_matches_with_adk_orchestrator(self, matches: List[Dict]) -> List[Dict]:
        """
        Alternative orchestration using BettingOrchestratorAgent
        
        This is an async wrapper that demonstrates using the custom ADK orchestrator agent.
        Currently uses the same underlying ThreadPoolExecutor implementation but with ADK patterns.
        
        Future: This can be upgraded to use full ADK orchestration with event tracing
        by properly initializing the BettingOrchestratorAgent through the Runner.

        Args:
            matches: List of match dictionaries

        Returns:
            List of recommendations
        """
        self.logger.info(f"Processing {len(matches)} matches with ADK-compatible orchestration...")
        
        # For now, use the existing ThreadPoolExecutor approach
        # The BettingOrchestratorAgent is ready in self.orchestrator_agent for future use
        return self.process_all_matches(matches)

    def process_all_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Process all matches with parallel analysis

        Args:
            matches: List of match dictionaries

        Returns:
            List of recommendations
        """
        self.logger.info(f"Processing {len(matches)} matches...")

        # Analyze all matches in parallel (2 agents per match)
        analyses = []
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(self.analyze_match_parallel, match)
                for match in matches
            ]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    analyses.append(result)
                except Exception as e:
                    self.logger.error(f"Error analyzing match: {e}")

        self.logger.info(f"Completed analysis of {len(analyses)} matches")

        # Extract results for synthesis and add match_id to each result
        internet_picks_results = []
        data_driven_results = []

        for analysis in analyses:
            match_id = analysis['match']['id']

            # Add match_id to internet picks result
            internet_picks = analysis['internet_picks']
            internet_picks['match_id'] = match_id
            internet_picks_results.append(internet_picks)

            # Add match_id to data-driven result
            data_driven = analysis['data_driven']
            data_driven['match_id'] = match_id
            data_driven_results.append(data_driven)

        # Run synthesis agent (3-layer: Internet Picks + Data-Driven → Synthesis)
        self.logger.info("Running synthesis agent (3-layer analysis)...")
        synthesis_recommendations = self.synthesis_agent.process_matches(
            matches,
            internet_picks_results,
            data_driven_results
        )

        # Enhance recommendations with individual agent results (all 3 layers)
        recommendations = self._enhance_recommendations_with_all_layers(
            synthesis_recommendations,
            internet_picks_results,
            data_driven_results
        )

        return recommendations

    def _enhance_recommendations_with_all_layers(self, synthesis_recs: List[Dict],
                                                  internet_picks: List[Dict],
                                                  data_driven: List[Dict]) -> List[Dict]:
        """
        Enhance recommendations by including all 3 layers of agent analysis.

        Args:
            synthesis_recs: Final synthesis recommendations
            internet_picks: Internet Picks agent results
            data_driven: Data-Driven agent results

        Returns:
            Enhanced recommendations with all layers
        """
        # Create lookup maps for quick access
        internet_map = {r.get('match_id'): r for r in internet_picks}
        data_driven_map = {r.get('match_id'): r for r in data_driven}

        # Enhance each synthesis recommendation with individual layer results
        for rec in synthesis_recs:
            match_id = rec.get('match_id')

            # Add Internet Picks layer
            if match_id in internet_map:
                internet_data = internet_map[match_id]
                rec['internet_picks'] = {
                    'picks': internet_data.get('picks', []),
                    'confidence': internet_data.get('confidence', 0.0),
                    'analysis': internet_data.get('analysis', '')
                }

            # Add Data-Driven layer
            if match_id in data_driven_map:
                data_driven_data = data_driven_map[match_id]
                rec['data_driven'] = {
                    'picks': data_driven_data.get('picks', []),
                    'confidence': data_driven_data.get('confidence', 0.0),
                    'analysis': data_driven_data.get('analysis', '')
                }

        return synthesis_recs

    def save_results(self, recommendations: List[Dict]):
        """
        Save recommendations to file

        Args:
            recommendations: List of recommendation dictionaries
        """
        results_file = Path(self.config['storage']['results_file'])
        results_file.parent.mkdir(parents=True, exist_ok=True)

        output = {
            'timestamp': datetime.now().isoformat(),
            'total_matches': len(recommendations),
            'bets_recommended': len([r for r in recommendations if r.get('recommendation') == 'BET']),
            'recommendations': recommendations
        }

        with open(results_file, 'w') as f:
            json.dump(output, f, indent=2)

        self.logger.info(f"Results saved to {results_file}")

        # Also append to history
        history_file = Path(self.config['storage']['history_file'])
        history = []

        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)

        history.append(output)

        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)

        self.logger.info(f"History updated: {history_file}")

    def load_filter_config(self, filter_path: str = None) -> Dict:
        """
        Load filter configuration from file

        Args:
            filter_path: Path to filter YAML file

        Returns:
            Filter configuration dictionary
        """
        if not filter_path:
            # Default: analyze all matches
            return {
                'enabled': False,
                'sports': [],
                'leagues': [],
                'limits': {},
                'analysis': {
                    'run_internet_picks': True,
                    'run_data_driven': True,
                    'run_synthesis': True
                }
            }

        try:
            with open(filter_path, 'r') as f:
                config = yaml.safe_load(f)
                filter_config = config.get('filter', {})
                self.logger.info(f"Loaded filter: {filter_config.get('name', 'Custom')}")
                return filter_config
        except Exception as e:
            self.logger.error(f"Failed to load filter config: {e}")
            return {'enabled': False, 'sports': [], 'leagues': [], 'limits': {}}

    def apply_filters(self, matches: List[Dict], filter_config: Dict) -> List[Dict]:
        """
        Apply filter configuration to matches

        Args:
            matches: All scraped matches
            filter_config: Filter configuration

        Returns:
            Filtered list of matches
        """
        if not filter_config.get('enabled', False):
            self.logger.info(f"No filter applied. Analyzing all {len(matches)} matches.")
            return matches

        filtered = matches.copy()

        # Filter by sport
        sports = filter_config.get('sports', [])
        if sports:
            before = len(filtered)
            filtered = [m for m in filtered if m.get('sport') in sports]
            self.logger.info(f"✓ Sport filter: {before} → {len(filtered)} matches")

        # Filter by league
        leagues = filter_config.get('leagues', [])
        if leagues:
            league_set = set(l.lower() for l in leagues)
            before = len(filtered)
            filtered = [m for m in filtered if m.get('league', '').lower() in league_set]
            self.logger.info(f"✓ League filter: {before} → {len(filtered)} matches")

        # Apply per-sport limits
        limits = filter_config.get('limits', {})
        if limits:
            from collections import defaultdict
            limited = []
            sport_counts = defaultdict(int)

            for match in filtered:
                sport = match.get('sport')
                limit = limits.get(sport, float('inf'))

                if sport_counts[sport] < limit:
                    limited.append(match)
                    sport_counts[sport] += 1

            before = len(filtered)
            filtered = limited
            self.logger.info(f"✓ Applied limits: {before} → {len(filtered)} matches")

        return filtered

    def run(self, filter_path: str = None):
        """
        Main execution method

        Args:
            filter_path: Optional path to filter configuration file
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Multi-Agent Betting System")
        self.logger.info("=" * 60)

        # Load filter configuration
        filter_config = self.load_filter_config(filter_path)

        try:
            # Step 1: Load or scrape matches
            self.logger.info("\n[STEP 1] Loading match data...")

            # Try to load from existing file first (avoids unnecessary scraping)
            all_matches = self.load_matches_from_file()

            # If no pre-scraped data exists, run the scraper
            if not all_matches:
                self.logger.info("No pre-scraped matches found, running scraper...")
                all_matches = self.run_scraper()

            if not all_matches:
                self.logger.warning("No matches found. Exiting.")
                return

            self.logger.info(f"Found {len(all_matches)} matches total")

            # Step 1b: Apply filters
            self.logger.info("\n[STEP 1b] Applying match filters...")
            matches = self.apply_filters(all_matches, filter_config)
            self.logger.info(f"Selected {len(matches)} matches for analysis")

            # Step 2: Analyze matches with parallel agents
            self.logger.info("\n[STEP 2] Analyzing matches with Internet Picks and Data-Driven agents...")
            recommendations = self.process_all_matches(matches)

            # Step 3: Save results
            self.logger.info("\n[STEP 3] Saving results...")
            self.save_results(recommendations)

            # Step 4: Send notifications
            bets = [r for r in recommendations if r.get('recommendation') == 'BET']
            self.logger.info(f"\n[STEP 4] Sending notifications for {len(bets)} betting recommendations...")
            self.notification_agent.send_notifications(recommendations)

            # Summary
            self.logger.info("\n" + "=" * 60)
            self.logger.info("EXECUTION SUMMARY")
            self.logger.info("=" * 60)
            self.logger.info(f"Total matches analyzed: {len(matches)}")
            self.logger.info(f"Betting recommendations: {len(bets)}")
            self.logger.info(f"Pass recommendations: {len(recommendations) - len(bets)}")

            if bets:
                self.logger.info("\nRecommended Bets:")
                for i, bet in enumerate(bets, 1):
                    self.logger.info(
                        f"  {i}. {bet['homeTeam']} vs {bet['awayTeam']} - "
                        f"Pick: {bet.get('recommended_pick')} @ {bet.get('recommended_odds')} "
                        f"(Confidence: {bet.get('confidence', 0):.0%})"
                    )

            self.logger.info("\n" + "=" * 60)
            self.logger.info("Execution completed successfully!")
            self.logger.info("=" * 60)

        except Exception as e:
            self.logger.error(f"Fatal error in orchestrator: {e}", exc_info=True)
            raise


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Multi-Agent Betting System')
    parser.add_argument(
        '--config',
        default='config/config.yaml',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--filter',
        default=None,
        help='Path to match filter configuration file (e.g., config/filters/balanced.yaml)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Launch interactive match selection mode'
    )
    parser.add_argument(
        '--test-notification',
        action='store_true',
        help='Send a test notification and exit'
    )

    args = parser.parse_args()

    orchestrator = BettingSystemOrchestrator(args.config)

    if args.test_notification:
        print("Sending test notification...")
        success = orchestrator.notification_agent.send_test_notification()
        if success:
            print("✓ Test notification sent successfully")
        else:
            print("✗ Failed to send test notification")
        return

    # Determine filter configuration
    filter_config = None
    filter_path = args.filter

    # Launch interactive mode only if explicitly requested
    if args.interactive:
        from utils.interactive_selector import InteractiveSelector
        selector = InteractiveSelector()
        filter_config = selector.run_interactive_session()

        if filter_config:
            # Save the interactive config to a temporary filter file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False, dir='config/filters') as f:
                import yaml
                yaml.dump({'filter': filter_config}, f)
                filter_path = f.name
                print(f"\n✓ Configuration saved to: {filter_path}\n")
        else:
            print("❌ No configuration selected. Exiting.")
            return

    orchestrator.run(filter_path=filter_path)


if __name__ == '__main__':
    main()
