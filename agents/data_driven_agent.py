"""
Data-Driven Analysis Agent
Analyzes matches based on statistics, form, and objective data
"""

import os
from typing import Dict, List
from google import genai
from google.genai import types
from .utils.search import GoogleSearchHelper
from .utils.logging_config import get_logger

logger = get_logger(__name__)


class DataDrivenAgent:
    """
    Agent that analyzes matches using statistical and objective data
    Does NOT use external betting tips or opinions
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
        Analyze a match using statistical and objective data

        Args:
            match: Match data dictionary

        Returns:
            Analysis result with data-driven picks and reasoning
        """
        logger.info(f"Data-Driven: Analyzing {match['homeTeam']} vs {match['awayTeam']}")

        # Search for statistical data
        search_results = self.search_helper.search_match_stats(
            match['homeTeam'],
            match['awayTeam'],
            match['sport']
        )

        if not search_results:
            logger.warning(f"No statistical data found for match {match['id']}")
            return {
                'match_id': match['id'],
                'picks': [],
                'confidence': 0.0,
                'data_sources': [],
                'analysis': 'Insufficient data for analysis'
            }

        # Use ADK agent to analyze data and generate picks
        analysis = self._analyze_with_adk(match, search_results)

        return {
            'match_id': match['id'],
            'homeTeam': match['homeTeam'],
            'awayTeam': match['awayTeam'],
            'sport': match['sport'],
            'picks': analysis.get('picks', []),
            'confidence': analysis.get('confidence', 0.0),
            'data_sources': [r['link'] for r in search_results[:5]],
            'analysis': analysis.get('analysis', ''),
            'key_factors': analysis.get('key_factors', []),
            'statistics': analysis.get('statistics', {})
        }

    def _analyze_with_adk(self, match: Dict, search_results: List[Dict]) -> Dict:
        """
        Use Google ADK to analyze statistical data

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
                'confidence': 0.5,
                'analysis': 'Mock analysis - API key not configured',
                'key_factors': ['Home advantage', 'Recent form'],
                'statistics': {}
            }

        # Prepare data summary
        data_text = "\n\n".join([
            f"Source {i+1}: {r['title']}\n{r['snippet']}\nURL: {r['link']}"
            for i, r in enumerate(search_results[:15])
        ])

        prompt = f"""You are a sports data analyst. Analyze the following match using ONLY objective data and statistics.

Match: {match['homeTeam']} vs {match['awayTeam']}
Sport: {match['sport']}
League: {match.get('league', 'Unknown')}

Statistical Data Sources:
{data_text}

Your task:
1. Extract relevant statistics (head-to-head, recent form, home/away records)
2. Identify key factors that could influence the outcome
3. Note any injuries, suspensions, or lineup changes
4. Analyze historical trends and patterns
5. Make data-driven predictions

IMPORTANT RULES:
- Base your analysis ONLY on objective data and statistics
- DO NOT reference betting tips, odds, or expert opinions
- DO NOT use subjective assessments
- Focus on: form, results, statistics, injuries, head-to-head records

Provide your analysis in the following format:
1. Key Statistics Summary
2. Form Analysis (recent results for both teams)
3. Head-to-Head Record
4. Key Factors (injuries, home advantage, etc.)
5. Data-Driven Prediction with reasoning
6. Confidence Level (0.0 to 1.0)

Format your prediction as one of: home_win, away_win, draw, over, under, or btts (both teams to score)
"""

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,  # Lower temperature for more factual analysis
                    max_output_tokens=1500
                )
            )

            analysis_text = response.text

            # Parse the response to extract structured data
            picks = self._extract_picks(analysis_text)
            confidence = self._extract_confidence(analysis_text)
            key_factors = self._extract_key_factors(analysis_text)
            statistics = self._extract_statistics(analysis_text)

            return {
                'picks': picks,
                'confidence': confidence,
                'analysis': analysis_text[:800],
                'key_factors': key_factors,
                'statistics': statistics
            }

        except Exception as e:
            logger.error(f"Error in ADK analysis: {e}")
            return {
                'picks': ['error'],
                'confidence': 0.0,
                'analysis': f'Analysis error: {str(e)}',
                'key_factors': [],
                'statistics': {}
            }

    def _extract_picks(self, analysis_text: str) -> List[str]:
        """Extract prediction picks from analysis text"""
        picks = []
        text_lower = analysis_text.lower()

        # Look for explicit predictions
        if 'prediction' in text_lower or 'recommend' in text_lower:
            if 'home' in text_lower and ('win' in text_lower or 'victory' in text_lower):
                picks.append('home_win')
            if 'away' in text_lower and ('win' in text_lower or 'victory' in text_lower):
                picks.append('away_win')
            if 'draw' in text_lower:
                picks.append('draw')
            if 'over' in text_lower and 'goals' in text_lower:
                picks.append('over')
            if 'under' in text_lower and 'goals' in text_lower:
                picks.append('under')
            if 'both teams to score' in text_lower or 'btts' in text_lower:
                picks.append('btts')

        return picks if picks else ['no_clear_pick']

    def _extract_confidence(self, analysis_text: str) -> float:
        """Extract confidence level from analysis"""
        text_lower = analysis_text.lower()

        if 'high confidence' in text_lower or 'very confident' in text_lower:
            return 0.8
        elif 'moderate confidence' in text_lower or 'reasonably confident' in text_lower:
            return 0.6
        elif 'low confidence' in text_lower or 'uncertain' in text_lower:
            return 0.3
        else:
            # Try to find numerical confidence
            import re
            confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', text_lower)
            if confidence_match:
                try:
                    return float(confidence_match.group(1))
                except:
                    pass

        return 0.5  # Default

    def _extract_key_factors(self, analysis_text: str) -> List[str]:
        """Extract key factors from analysis"""
        factors = []
        lines = analysis_text.split('\n')

        for line in lines:
            line_lower = line.lower()
            if 'key factor' in line_lower or 'important' in line_lower:
                factor = line.strip('- ').strip()
                if factor and len(factor) > 10:
                    factors.append(factor[:200])

        # Default factors if none found
        if not factors:
            if 'home advantage' in analysis_text.lower():
                factors.append('Home advantage')
            if 'injury' in analysis_text.lower() or 'injuries' in analysis_text.lower():
                factors.append('Injury concerns')
            if 'form' in analysis_text.lower():
                factors.append('Recent form')

        return factors[:5]

    def _extract_statistics(self, analysis_text: str) -> Dict:
        """Extract statistics from analysis"""
        stats = {}

        # Look for common statistics
        if 'head to head' in analysis_text.lower() or 'h2h' in analysis_text.lower():
            stats['head_to_head'] = 'Mentioned in analysis'

        if 'recent form' in analysis_text.lower():
            stats['recent_form'] = 'Analyzed'

        if 'goals' in analysis_text.lower():
            stats['goals_data'] = 'Available'

        return stats

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
