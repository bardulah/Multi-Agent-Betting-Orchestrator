"""
Internet Picks Agent - ADK Implementation
Searches for betting tips and predictions from online sources using ADK's built-in google_search
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


def create_internet_picks_agent(config: Dict) -> LlmAgent:
    """
    Create an ADK LlmAgent that searches for internet betting picks

    Args:
        config: System configuration dictionary

    Returns:
        Configured LlmAgent instance
    """

    instruction = """You are a betting intelligence analyst specializing in aggregating public opinion and expert picks.

Your task: For each match provided, search the internet to find betting tips, predictions, and expert opinions.

Process:
1. Use Google Search to find recent betting tips for the specific match
2. Search for multiple sources: betting forums, tipster sites, expert predictions
3. Identify the consensus pick (if any exists)
4. Note any contrarian or minority opinions
5. Assess the confidence based on source agreement

Search queries to use:
- "[home_team] vs [away_team] betting tips prediction"
- "[home_team] [away_team] picks today"
- "[home_team] vs [away_team] expert prediction [sport]"

Output Format (JSON):
{
    "picks": ["home_win", "away_win", "draw", "over", "under", "btts"],
    "confidence": 0.0-1.0,
    "consensus": "description of majority opinion",
    "sources_count": number,
    "summary": "brief summary of findings"
}

Important Rules:
- ONLY report what you find from searches, don't add your own betting opinion
- If sources disagree significantly, lower the confidence score
- Rate confidence based on: source quality, agreement level, recency
- If you find no relevant tips, return confidence: 0.0 and picks: []
- Always use google_search tool before responding
"""

    agent = LlmAgent(
        name="internet_picks_agent",
        model="gemini-1.5-flash",
        instruction=instruction,
        tools=[google_search],
        description="Searches internet for betting tips and expert predictions",
    )

    return agent


class InternetPicksAgent:
    """
    Wrapper for ADK Internet Picks Agent with sync interface
    """

    def __init__(self, config: Dict):
        self.config = config
        self.agent = create_internet_picks_agent(config)
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            app_name='betting_system',
            agent=self.agent,
            session_service=self.session_service
        )
        self.user_id = 'betting_user'
        self.session_id = 'internet_picks_session'
        logger.info("Internet Picks Agent (ADK) initialized")

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
        logger.info(f"Internet Picks: Analyzing {match['homeTeam']} vs {match['awayTeam']}")

        prompt = f"""Analyze this match and find betting picks from the internet:

Match: {match['homeTeam']} vs {match['awayTeam']}
Sport: {match['sport']}
League: {match.get('league', 'Unknown')}
Date: {match.get('date', 'Today')}
Time: {match.get('time', 'TBD')}

Search for betting tips and predictions for this specific match. Provide your analysis in JSON format.
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
                'sources_count': analysis.get('sources_count', 0),
                'summary': analysis.get('summary', result_text[:500]),
                'consensus': analysis.get('consensus', 'No clear consensus')
            }

        except Exception as e:
            logger.error(f"Error in Internet Picks Agent: {e}")
            return {
                'match_id': match['id'],
                'homeTeam': match['homeTeam'],
                'awayTeam': match['awayTeam'],
                'sport': match['sport'],
                'picks': [],
                'confidence': 0.0,
                'sources_count': 0,
                'summary': f'Error: {str(e)}',
                'consensus': 'Error'
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
            'sources_count': self._extract_source_count(text),
            'summary': text[:500],
            'consensus': self._extract_consensus(text)
        }

    def _extract_picks(self, text: str) -> list:
        """Extract picks from text"""
        picks = []
        text_lower = text.lower()

        if 'home' in text_lower and ('win' in text_lower or 'victory' in text_lower):
            picks.append('home_win')
        if 'away' in text_lower and ('win' in text_lower or 'victory' in text_lower):
            picks.append('away_win')
        if 'draw' in text_lower:
            picks.append('draw')
        if 'over' in text_lower:
            picks.append('over')
        if 'under' in text_lower:
            picks.append('under')
        if 'btts' in text_lower or 'both teams to score' in text_lower:
            picks.append('btts')

        return picks if picks else ['no_clear_pick']

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence from text"""
        import re
        text_lower = text.lower()

        # Look for explicit confidence value
        conf_match = re.search(r'confidence[:\s]+([0-9.]+)', text_lower)
        if conf_match:
            try:
                val = float(conf_match.group(1))
                return min(max(val, 0.0), 1.0)  # Clamp to 0-1
            except:
                pass

        # Qualitative
        if 'high confidence' in text_lower:
            return 0.8
        elif 'moderate' in text_lower or 'medium' in text_lower:
            return 0.6
        elif 'low confidence' in text_lower:
            return 0.3

        return 0.5

    def _extract_source_count(self, text: str) -> int:
        """Extract source count from text"""
        import re
        match = re.search(r'sources?[:\s]+(\d+)', text.lower())
        if match:
            return int(match.group(1))
        return 0

    def _extract_consensus(self, text: str) -> str:
        """Extract consensus from text"""
        for line in text.split('\n'):
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
