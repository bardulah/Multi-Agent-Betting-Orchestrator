"""
Internet Picks Agent
Searches for betting tips and predictions from online sources
"""

import os
from typing import Dict, List
from google import genai
from google.genai import types
from .utils.search import GoogleSearchHelper
from .utils.logging_config import get_logger

logger = get_logger(__name__)


class InternetPicksAgent:
    """
    Agent that searches the internet for betting picks and tips
    """

    def __init__(self, config: Dict):
        self.config = config
        self.search_helper = GoogleSearchHelper()

        # Initialize Google GenAI client
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            logger.warning("GOOGLE_API_KEY not set, using mock responses")
            self.client = None

    def analyze_match(self, match: Dict) -> Dict:
        """
        Analyze a match by searching for internet betting picks

        Args:
            match: Match data dictionary

        Returns:
            Analysis result with picks and reasoning
        """
        logger.info(f"Internet Picks: Analyzing {match['homeTeam']} vs {match['awayTeam']}")

        # Search for betting tips
        search_results = self.search_helper.search_betting_tips(
            match['homeTeam'],
            match['awayTeam'],
            match['sport']
        )

        if not search_results:
            logger.warning(f"No search results found for match {match['id']}")
            return {
                'match_id': match['id'],
                'picks': [],
                'confidence': 0.0,
                'sources': [],
                'summary': 'No internet picks found'
            }

        # Use ADK agent to analyze and summarize picks
        analysis = self._analyze_with_adk(match, search_results)

        return {
            'match_id': match['id'],
            'homeTeam': match['homeTeam'],
            'awayTeam': match['awayTeam'],
            'sport': match['sport'],
            'picks': analysis.get('picks', []),
            'confidence': analysis.get('confidence', 0.0),
            'sources': [r['link'] for r in search_results[:5]],
            'summary': analysis.get('summary', ''),
            'consensus': analysis.get('consensus', '')
        }

    def _analyze_with_adk(self, match: Dict, search_results: List[Dict]) -> Dict:
        """
        Use Google ADK to analyze search results and extract picks

        Args:
            match: Match data
            search_results: List of search result dictionaries

        Returns:
            Structured analysis
        """
        if not self.client:
            # Mock response when API key not available
            return {
                'picks': ['home_win'],
                'confidence': 0.6,
                'summary': 'Mock analysis - API key not configured',
                'consensus': 'Majority of sources favor home team'
            }

        # Prepare search results summary
        sources_text = "\n\n".join([
            f"Source {i+1}: {r['title']}\n{r['snippet']}\nURL: {r['link']}"
            for i, r in enumerate(search_results[:10])
        ])

        prompt = f"""You are a betting analysis expert. Analyze the following internet sources for betting tips and predictions.

Match: {match['homeTeam']} vs {match['awayTeam']}
Sport: {match['sport']}
League: {match.get('league', 'Unknown')}

Internet Sources:
{sources_text}

Your task:
1. Extract all betting picks and predictions from these sources
2. Identify the consensus opinion (if any)
3. Note any disagreements or contrarian views
4. Assess the confidence level of the sources

Provide your analysis in the following format:
- List the main picks mentioned (e.g., "home_win", "away_win", "over_2.5", "draw", etc.)
- Summarize the consensus view
- Note the reasoning provided by sources
- Rate the overall confidence (0.0 to 1.0)

Be objective and don't add your own opinion. Only summarize what the sources say.
"""

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    max_output_tokens=1000
                )
            )

            analysis_text = response.text

            # Parse the response to extract structured data
            picks = []
            if 'home' in analysis_text.lower() and 'win' in analysis_text.lower():
                picks.append('home_win')
            if 'away' in analysis_text.lower() and 'win' in analysis_text.lower():
                picks.append('away_win')
            if 'draw' in analysis_text.lower():
                picks.append('draw')
            if 'over' in analysis_text.lower():
                picks.append('over')
            if 'under' in analysis_text.lower():
                picks.append('under')

            # Extract confidence (look for numbers between 0 and 1)
            confidence = 0.5  # Default
            if 'high confidence' in analysis_text.lower():
                confidence = 0.8
            elif 'low confidence' in analysis_text.lower():
                confidence = 0.3
            elif 'moderate' in analysis_text.lower():
                confidence = 0.6

            return {
                'picks': picks if picks else ['no_clear_pick'],
                'confidence': confidence,
                'summary': analysis_text[:500],
                'consensus': self._extract_consensus(analysis_text)
            }

        except Exception as e:
            logger.error(f"Error in ADK analysis: {e}")
            return {
                'picks': ['error'],
                'confidence': 0.0,
                'summary': f'Analysis error: {str(e)}',
                'consensus': 'Unable to determine'
            }

    def _extract_consensus(self, analysis_text: str) -> str:
        """Extract consensus view from analysis text"""
        lines = analysis_text.split('\n')
        for line in lines:
            if 'consensus' in line.lower():
                return line.strip()
        return 'No clear consensus'

    def process_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Process multiple matches

        Args:
            matches: List of match dictionaries

        Returns:
            List of analysis results
        """
        results = []
        for match in matches:
            try:
                result = self.analyze_match(match)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing match {match.get('id')}: {e}")
                results.append({
                    'match_id': match.get('id'),
                    'error': str(e)
                })

        return results
