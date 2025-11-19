"""
Integration layer between Telegram bot and betting system
Handles data loading, formatting, and state management
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from agents.utils.logging_config import get_logger

logger = get_logger(__name__)


class ResultsLoader:
    """Load and cache betting results from files"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self._cache = {}
        logger.info(f"ResultsLoader initialized with data_dir: {data_dir}")

    def _get_results_file(self, date: str = "today") -> Path:
        """Get the results file path based on date"""
        if date.lower() == "tomorrow":
            return self.data_dir / "results-tomorrow.json"
        else:
            return self.data_dir / "results.json"

    def _get_matches_file(self, date: str = "today") -> Path:
        """Get the matches file path based on date"""
        if date.lower() == "tomorrow":
            return self.data_dir / "matches-tomorrow.json"
        else:
            return self.data_dir / "matches.json"

    def load_results(self, date: str = "today") -> Optional[Dict]:
        """
        Load results from file with caching

        Args:
            date: "today" or "tomorrow"

        Returns:
            Results dictionary or None if not found
        """
        results_file = self._get_results_file(date)

        if not results_file.exists():
            logger.warning(f"Results file not found: {results_file}")
            return None

        try:
            with open(results_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded results from {results_file}")
            return data
        except Exception as e:
            logger.error(f"Failed to load results: {e}")
            return None

    def load_matches(self, date: str = "today") -> Optional[Dict]:
        """Load match data from file"""
        matches_file = self._get_matches_file(date)

        if not matches_file.exists():
            logger.warning(f"Matches file not found: {matches_file}")
            return None

        try:
            with open(matches_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded matches from {matches_file}")
            return data
        except Exception as e:
            logger.error(f"Failed to load matches: {e}")
            return None


class ResultFormatter:
    """Format betting results for Telegram display"""

    @staticmethod
    def format_recommendation_summary(results: Dict) -> str:
        """
        Format results summary for display

        Args:
            results: Results dictionary from load_results()

        Returns:
            Formatted message string
        """
        if not results or not results.get('recommendations'):
            return "❌ No recommendations found"

        recommendations = results['recommendations']
        bet_recommendations = [r for r in recommendations if r.get('recommendation') == 'BET']

        timestamp = results.get('timestamp', 'Unknown')
        total_matches = results.get('total_matches', 0)
        total_bets = len(bet_recommendations)

        message = f"""📊 <b>Betting Recommendations</b>

📅 <i>{timestamp}</i>

<b>Summary:</b>
• Total matches analyzed: {total_matches}
• BET recommendations: {total_bets}

<b>Sports breakdown:</b>"""

        # Count by sport
        by_sport = {}
        for rec in bet_recommendations:
            sport = rec.get('sport', 'Unknown')
            by_sport[sport] = by_sport.get(sport, 0) + 1

        for sport in sorted(by_sport.keys()):
            message += f"\n  • {sport.upper()}: {by_sport[sport]} bets"

        message += f"\n\n<i>Select action below:</i>"

        return message

    @staticmethod
    def format_bet(bet: Dict, number: int = 1) -> str:
        """
        Format a single bet for display

        Args:
            bet: Bet recommendation dictionary
            number: Bet number for display

        Returns:
            Formatted bet string
        """
        home = bet.get('homeTeam', 'Unknown')
        away = bet.get('awayTeam', 'Unknown')
        sport = bet.get('sport', 'Unknown')
        league = bet.get('league', 'Unknown')
        time = bet.get('time', 'TBD')
        pick = bet.get('recommended_pick', 'N/A').upper()
        odds = bet.get('recommended_odds', 'N/A')
        confidence = bet.get('confidence', 0)

        message = f"""<b>🎯 BET #{number}</b>

<b>Match:</b> {home} vs {away}
<b>Sport:</b> {sport} | <b>League:</b> {league}
<b>Time:</b> {time}

<b>Recommendation:</b> <code>{pick}</code> @ {odds}
<b>Confidence:</b> {confidence:.1%}"""

        # Add layer analysis if available
        if bet.get('internet_picks'):
            internet = bet['internet_picks']
            internet_pick = internet.get('picks', [])[0] if internet.get('picks') else 'N/A'
            message += f"\n\n🌐 <b>Internet Picks:</b> {internet_pick.upper()}"

        if bet.get('data_driven'):
            data = bet['data_driven']
            data_pick = data.get('picks', [])[0] if data.get('picks') else 'N/A'
            message += f"\n📊 <b>Data-Driven:</b> {data_pick.upper()}"

        return message

    @staticmethod
    def format_full_bet(bet: Dict, number: int = 1) -> str:
        """
        Format a detailed bet with full analysis

        Args:
            bet: Bet recommendation dictionary
            number: Bet number for display

        Returns:
            Detailed formatted bet string
        """
        message = ResultFormatter.format_bet(bet, number)

        # Add detailed reasoning
        reasoning = bet.get('reasoning', 'No reasoning provided')
        if reasoning:
            # Truncate to reasonable length for Telegram
            max_length = 500
            if len(reasoning) > max_length:
                reasoning = reasoning[:max_length] + "..."

            message += f"\n\n<b>Reasoning:</b>\n{reasoning}"

        return message


class BetPaginator:
    """Handle pagination of bet results"""

    def __init__(self, bets: List[Dict]):
        self.bets = bets
        self.current_index = 0

    def get_current(self) -> Optional[Dict]:
        """Get current bet"""
        if 0 <= self.current_index < len(self.bets):
            return self.bets[self.current_index]
        return None

    def has_next(self) -> bool:
        """Check if there's a next bet"""
        return self.current_index < len(self.bets) - 1

    def has_prev(self) -> bool:
        """Check if there's a previous bet"""
        return self.current_index > 0

    def next(self) -> bool:
        """Move to next bet"""
        if self.has_next():
            self.current_index += 1
            return True
        return False

    def prev(self) -> bool:
        """Move to previous bet"""
        if self.has_prev():
            self.current_index -= 1
            return True
        return False

    def get_status(self) -> str:
        """Get pagination status string"""
        return f"{self.current_index + 1}/{len(self.bets)}"
