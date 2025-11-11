"""
Data-Driven Analysis Agent - ADK Implementation
Analyzes matches based on statistics, form, and objective data using ADK's built-in google_search
"""

import json
import asyncio
from typing import Dict, List
from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
from .utils.logging_config import get_logger

logger = get_logger(__name__)


def create_data_driven_agent(config: Dict) -> LlmAgent:
    """
    Create an ADK LlmAgent that analyzes matches using statistical data

    Args:
        config: System configuration dictionary

    Returns:
        Configured LlmAgent instance
    """

    instruction = """You are a sports data analyst specializing in objective statistical analysis.

Your task: For each match provided, search for and analyze statistical data to make data-driven predictions.

Process:
1. Use Google Search to find relevant statistics for this matchup
2. Search for: head-to-head records, recent form, home/away performance, injuries, lineups
3. Analyze trends and patterns from the data
4. Make predictions based ONLY on objective data
5. Do NOT reference betting odds, tips, or expert opinions

Search queries to use:
- "[home_team] vs [away_team] head to head statistics"
- "[home_team] recent form results [sport]"
- "[away_team] recent form results [sport]"
- "[home_team] vs [away_team] injuries news lineup"

Output Format (JSON):
{
    "picks": ["home_win", "away_win", "draw", "over", "under", "btts"],
    "confidence": 0.0-1.0,
    "key_factors": ["list of important factors"],
    "analysis": "detailed analysis based on data",
    "statistics": {
        "head_to_head": "summary",
        "home_form": "summary",
        "away_form": "summary"
    }
}

Important Rules:
- Base analysis ONLY on objective data and statistics
- DO NOT use betting tips, odds, or subjective opinions
- Focus on: recent results, form, injuries, head-to-head, home/away records
- If data is insufficient, return lower confidence
- Always use google_search tool before responding
- Be factual and data-driven
"""

    agent = LlmAgent(
        name="data_driven_agent",
        model="gemini-2.5-flash",
        instruction=instruction,
        tools=[google_search],
        description="Analyzes matches using statistical and objective data",
    )

    return agent


class DataDrivenAgent:
    """
    Wrapper for ADK Data-Driven Agent with sync interface
    """

    def __init__(self, config: Dict):
        self.config = config
        self.agent = create_data_driven_agent(config)
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            app_name='betting_system',
            agent=self.agent,
            session_service=self.session_service
        )
        self.user_id = 'betting_user'
        self.session_id = 'data_driven_session'
        logger.info("Data-Driven Agent (ADK) initialized")

    def analyze_match(self, match: Dict) -> Dict:
        """
        Analyze a match using the ADK agent (sync wrapper)

        Args:
            match: Match data dictionary

        Returns:
            Analysis result dictionary
        """
        # Run async method in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.analyze_match_async(match))

    async def analyze_match_async(self, match: Dict) -> Dict:
        """
        Analyze a match using the ADK agent (async)

        Args:
            match: Match data dictionary

        Returns:
            Analysis result dictionary
        """
        logger.info(f"Data-Driven: Analyzing {match['homeTeam']} vs {match['awayTeam']}")

        prompt = f"""Analyze this match using statistical and objective data:

Match: {match['homeTeam']} vs {match['awayTeam']}
Sport: {match['sport']}
League: {match.get('league', 'Unknown')}
Date: {match.get('date', 'Today')}
Time: {match.get('time', 'TBD')}

Search for relevant statistics and provide a data-driven analysis in JSON format.
Do NOT reference betting tips or opinions - only use objective data.
"""

        try:
            # Create or get session
            session = await self.session_service.create_session(
                app_name='betting_system',
                user_id=self.user_id,
                session_id=self.session_id
            )

            # Create proper ADK message
            message = types.Content(
                parts=[types.Part(text=prompt)],
                role='user'
            )

            # Run the ADK agent via Runner
            result_text = ""
            async for event in self.runner.run_async(
                user_id=self.user_id,
                session_id=self.session_id,
                new_message=message
            ):
                # Extract text from event content
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                result_text += part.text
                    else:
                        result_text += str(event.content)

            if not result_text:
                result_text = "No response from agent"

            # Parse response
            analysis = self._parse_response(result_text)

            return {
                'match_id': match['id'],
                'homeTeam': match['homeTeam'],
                'awayTeam': match['awayTeam'],
                'sport': match['sport'],
                'picks': analysis.get('picks', []),
                'confidence': analysis.get('confidence', 0.0),
                'data_sources': [],  # ADK search tool handles this internally
                'analysis': analysis.get('analysis', result_text[:800]),
                'key_factors': analysis.get('key_factors', []),
                'statistics': analysis.get('statistics', {})
            }

        except Exception as e:
            logger.error(f"Error in Data-Driven Agent: {e}")
            return {
                'match_id': match['id'],
                'homeTeam': match['homeTeam'],
                'awayTeam': match['awayTeam'],
                'sport': match['sport'],
                'picks': [],
                'confidence': 0.0,
                'data_sources': [],
                'analysis': f'Error: {str(e)}',
                'key_factors': [],
                'statistics': {}
            }

    def _extract_text(self, response) -> str:
        """Extract text from ADK response"""
        if hasattr(response, 'content'):
            return response.content
        elif hasattr(response, 'text'):
            return response.text
        else:
            return str(response)

    def _parse_response(self, text: str) -> Dict:
        """Parse JSON from agent response"""
        try:
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception as e:
            logger.debug(f"Could not parse JSON: {e}")

        # Fallback: extract information manually
        return {
            'picks': self._extract_picks(text),
            'confidence': self._extract_confidence(text),
            'key_factors': self._extract_key_factors(text),
            'analysis': text[:800],
            'statistics': self._extract_statistics(text)
        }

    def _extract_picks(self, text: str) -> List[str]:
        """Extract prediction picks from analysis text"""
        picks = []
        text_lower = text.lower()

        # Look for explicit predictions
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

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level from analysis"""
        import re
        text_lower = text.lower()

        # Try to find numerical confidence
        confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', text_lower)
        if confidence_match:
            try:
                val = float(confidence_match.group(1))
                return min(max(val, 0.0), 1.0)
            except:
                pass

        # Qualitative confidence
        if 'high confidence' in text_lower or 'very confident' in text_lower:
            return 0.8
        elif 'moderate confidence' in text_lower or 'reasonably confident' in text_lower:
            return 0.6
        elif 'low confidence' in text_lower or 'uncertain' in text_lower:
            return 0.3

        return 0.5  # Default

    def _extract_key_factors(self, text: str) -> List[str]:
        """Extract key factors from analysis"""
        factors = []
        lines = text.split('\n')

        for line in lines:
            line_lower = line.lower()
            if 'key factor' in line_lower or 'important' in line_lower:
                factor = line.strip('- ').strip()
                if factor and len(factor) > 10:
                    factors.append(factor[:200])

        # Default factors if none found
        if not factors:
            if 'home advantage' in text.lower():
                factors.append('Home advantage')
            if 'injury' in text.lower() or 'injuries' in text.lower():
                factors.append('Injury concerns')
            if 'form' in text.lower():
                factors.append('Recent form')

        return factors[:5]

    def _extract_statistics(self, text: str) -> Dict:
        """Extract statistics from analysis"""
        stats = {}

        # Look for common statistics
        if 'head to head' in text.lower() or 'h2h' in text.lower():
            stats['head_to_head'] = 'Mentioned in analysis'

        if 'recent form' in text.lower():
            stats['recent_form'] = 'Analyzed'

        if 'goals' in text.lower():
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
