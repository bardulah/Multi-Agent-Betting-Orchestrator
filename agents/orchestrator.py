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

from .internet_picks_agent import InternetPicksAgent
from .data_driven_agent import DataDrivenAgent
from .synthesis_agent import SynthesisAgent
from .notification_agent import NotificationAgent
from .utils.logging_config import setup_logging, get_logger


class BettingSystemOrchestrator:
    """
    Main orchestrator that coordinates all agents in the betting system
    """

    def __init__(self, config_path: str = 'config/config.yaml'):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv('config/.env')

        # Setup logging
        setup_logging(self.config)
        self.logger = get_logger(__name__)

        # Initialize agents
        self.logger.info("Initializing agents...")
        self.internet_picks_agent = InternetPicksAgent(self.config)
        self.data_driven_agent = DataDrivenAgent(self.config)
        self.synthesis_agent = SynthesisAgent(self.config)
        self.notification_agent = NotificationAgent(self.config)

        self.logger.info("All agents initialized successfully")

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

        # Extract results for synthesis
        internet_picks_results = [a['internet_picks'] for a in analyses]
        data_driven_results = [a['data_driven'] for a in analyses]

        # Run synthesis agent
        self.logger.info("Running synthesis agent...")
        recommendations = self.synthesis_agent.process_matches(
            matches,
            internet_picks_results,
            data_driven_results
        )

        return recommendations

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

    def run(self):
        """
        Main execution method
        """
        self.logger.info("=" * 60)
        self.logger.info("Starting Multi-Agent Betting System")
        self.logger.info("=" * 60)

        try:
            # Step 1: Scrape matches
            self.logger.info("\n[STEP 1] Scraping matches from Flashscore...")
            matches = self.run_scraper()

            if not matches:
                self.logger.warning("No matches found. Exiting.")
                return

            self.logger.info(f"Found {len(matches)} matches to analyze")

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

    orchestrator.run()


if __name__ == '__main__':
    main()
