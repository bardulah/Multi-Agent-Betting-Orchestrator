"""
Google Search utility functions
"""

import os
import requests
import time
from typing import List, Dict


class GoogleSearchHelper:
    """Helper class for Google Custom Search API"""

    def __init__(self, api_key=None, search_engine_id=None):
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        self.search_engine_id = search_engine_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID')
        self.base_url = "https://www.googleapis.com/customsearch/v1"

    def search(self, query: str, num_results: int = 10) -> List[Dict]:
        """
        Perform a Google search and return results

        Args:
            query: Search query string
            num_results: Number of results to return (max 10 per request)

        Returns:
            List of search result dictionaries
        """
        if not self.api_key or not self.search_engine_id:
            return [{
                'title': 'API Configuration Missing',
                'snippet': 'Please set GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID',
                'link': ''
            }]

        try:
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(num_results, 10)
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = []

            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', '')
                })

            return results

        except requests.exceptions.RequestException as e:
            print(f"Search error: {e}")
            return []

    def search_betting_tips(self, home_team: str, away_team: str, sport: str) -> List[Dict]:
        """
        Search for betting tips for a specific match

        Args:
            home_team: Home team name
            away_team: Away team name
            sport: Sport type

        Returns:
            List of search results
        """
        queries = [
            f"{home_team} vs {away_team} betting tips prediction",
            f"{home_team} {away_team} {sport} picks today",
            f"{home_team} vs {away_team} expert prediction"
        ]

        all_results = []
        for query in queries:
            results = self.search(query, num_results=5)
            all_results.extend(results)
            time.sleep(1)  # Rate limiting

        return all_results

    def search_match_stats(self, home_team: str, away_team: str, sport: str) -> List[Dict]:
        """
        Search for match statistics and data

        Args:
            home_team: Home team name
            away_team: Away team name
            sport: Sport type

        Returns:
            List of search results
        """
        queries = [
            f"{home_team} vs {away_team} head to head statistics",
            f"{home_team} recent form results {sport}",
            f"{away_team} recent form results {sport}",
            f"{home_team} vs {away_team} injuries news lineup"
        ]

        all_results = []
        for query in queries:
            results = self.search(query, num_results=5)
            all_results.extend(results)
            time.sleep(1)  # Rate limiting

        return all_results
