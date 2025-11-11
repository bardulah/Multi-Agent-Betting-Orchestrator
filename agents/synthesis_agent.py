"""
Synthesis & Decision Agent - ADK Implementation
Combines inputs from Internet Picks and Data-Driven agents to make final betting recommendations
"""

import json
import asyncio
from typing import Dict, List, Optional
from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from .utils.logging_config import get_logger

logger = get_logger(__name__)


def create_synthesis_agent(config: Dict) -> LlmAgent:
    """
    Create an ADK LlmAgent that synthesizes analyses and makes betting decisions

    Args:
        config: System configuration dictionary

    Returns:
        Configured LlmAgent instance
    """

    min_value = config.get('agents', {}).get('synthesis', {}).get('min_value_threshold', 1.05)
    confidence_threshold = config.get('agents', {}).get('synthesis', {}).get('confidence_threshold', 0.7)

    instruction = f"""You are a betting decision expert. Your job is to synthesize two independent analyses and make final betting recommendations.

You will receive:
1. Internet Picks Analysis: Consensus from betting tips and predictions found online
2. Data-Driven Analysis: Statistical analysis based on objective data
3. Available Odds: Bookmaker odds for the match

Your task:
1. Compare and contrast both analyses
2. Identify areas of agreement and disagreement
3. Assess which analysis has stronger supporting evidence
4. Evaluate if any available odds represent good value
5. Make a final recommendation: BET or NO_BET

Decision Criteria:
- Minimum odds value: {min_value} (only recommend if odds >= this)
- Minimum confidence: {confidence_threshold} (0.0 to 1.0 scale)
- Both analyses agree + good odds value = STRONG BET
- Both analyses agree + poor odds value = NO_BET
- Analyses disagree + weak evidence = NO_BET
- Analyses disagree + one has very strong evidence = CONSIDER BET (but carefully)
- Insufficient data = NO_BET

Output Format (JSON):
{{
    "recommendation": "BET" or "NO_BET",
    "pick": "home_win|away_win|draw|over|under|btts",
    "target_odds": number or null,
    "confidence": 0.0-1.0,
    "agreement_score": 0.0-1.0,
    "reasoning": "detailed explanation of decision",
    "value_assessment": "whether odds represent good value"
}}

Important Rules:
- Be CONSERVATIVE - only recommend bets with strong evidence and value
- If analyses conflict, explain why and default to NO_BET unless one has overwhelming evidence
- Consider the confidence levels from both agents
- Always assess odds value - don't recommend overpriced bets
- Provide clear reasoning for every decision
"""

    agent = LlmAgent(
        name="synthesis_agent",
        model="gemini-2.5-flash",
        instruction=instruction,
        description="Synthesizes multiple analyses and makes final betting decisions",
    )

    return agent


class SynthesisAgent:
    """
    Wrapper for ADK Synthesis Agent with sync interface
    """

    def __init__(self, config: Dict):
        self.config = config
        self.min_value_threshold = config.get('agents', {}).get('synthesis', {}).get('min_value_threshold', 1.05)
        self.confidence_threshold = config.get('agents', {}).get('synthesis', {}).get('confidence_threshold', 0.7)
        self.agent = create_synthesis_agent(config)
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            app_name='betting_system',
            agent=self.agent,
            session_service=self.session_service
        )
        self.user_id = 'betting_user'
        self.session_id = 'synthesis_session'
        logger.info("Synthesis Agent (ADK) initialized")

    def synthesize(
        self,
        match: Dict,
        internet_picks: Dict,
        data_driven: Dict
    ) -> Dict:
        """
        Synthesize analyses and make final betting decision (sync wrapper)

        Args:
            match: Original match data with odds
            internet_picks: Analysis from Internet Picks Agent
            data_driven: Analysis from Data-Driven Agent

        Returns:
            Final betting recommendation
        """
        # Run async method in event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(self.synthesize_async(match, internet_picks, data_driven))

    async def synthesize_async(
        self,
        match: Dict,
        internet_picks: Dict,
        data_driven: Dict
    ) -> Dict:
        """
        Synthesize analyses and make final betting decision (async)

        Args:
            match: Original match data with odds
            internet_picks: Analysis from Internet Picks Agent
            data_driven: Analysis from Data-Driven Agent

        Returns:
            Final betting recommendation
        """
        logger.info(f"Synthesis: Analyzing {match['homeTeam']} vs {match['awayTeam']}")

        # Prepare odds information
        odds_text = self._format_odds(match.get('odds', {}))

        prompt = f"""Make a final betting decision for this match:

Match: {match['homeTeam']} vs {match['awayTeam']}
Sport: {match['sport']}
League: {match.get('league', 'Unknown')}
Time: {match.get('time', 'TBD')}

Available Odds:
{odds_text}

INTERNET PICKS ANALYSIS:
Picks: {', '.join(internet_picks.get('picks', []))}
Confidence: {internet_picks.get('confidence', 0.0)}
Summary: {internet_picks.get('summary', 'No summary')[:500]}
Consensus: {internet_picks.get('consensus', 'No consensus')}

DATA-DRIVEN ANALYSIS:
Picks: {', '.join(data_driven.get('picks', []))}
Confidence: {data_driven.get('confidence', 0.0)}
Analysis: {data_driven.get('analysis', 'No analysis')[:500]}
Key Factors: {', '.join(data_driven.get('key_factors', []))}

Provide your final decision in JSON format.
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
            decision = self._parse_response(result_text)

            # Extract odds for the recommended pick
            recommended_odds = self._get_best_odds(
                match.get('odds', {}),
                decision.get('pick')
            )

            return {
                'match_id': match['id'],
                'homeTeam': match['homeTeam'],
                'awayTeam': match['awayTeam'],
                'sport': match['sport'],
                'league': match.get('league', 'Unknown'),
                'time': match.get('time', 'TBD'),
                'recommendation': decision.get('recommendation', 'NO_BET'),
                'recommended_pick': decision.get('pick'),
                'recommended_odds': recommended_odds or decision.get('target_odds'),
                'confidence': decision.get('confidence', 0.0),
                'reasoning': decision.get('reasoning', result_text[:600]),
                'value_assessment': decision.get('value_assessment', ''),
                'agreement_score': decision.get('agreement_score', 0.0),
                'internet_picks_summary': internet_picks.get('summary', ''),
                'data_driven_summary': data_driven.get('analysis', ''),
                'odds_available': len(match.get('odds', {})) > 0
            }

        except Exception as e:
            logger.error(f"Error in Synthesis Agent: {e}")
            return {
                'match_id': match['id'],
                'homeTeam': match['homeTeam'],
                'awayTeam': match['awayTeam'],
                'sport': match['sport'],
                'recommendation': 'NO_BET',
                'recommended_pick': None,
                'recommended_odds': None,
                'confidence': 0.0,
                'reasoning': f'Synthesis error: {str(e)}',
                'value_assessment': 'Error',
                'agreement_score': 0.0
            }

    def _extract_text(self, response) -> str:
        """Extract text from ADK response"""
        if hasattr(response, 'content'):
            return response.content
        elif hasattr(response, 'text'):
            return response.text
        else:
            return str(response)

    def _format_odds(self, odds_dict: Dict) -> str:
        """Format odds for display"""
        if not odds_dict:
            return "No odds available"

        odds_list = []
        for bookmaker, odds_data in list(odds_dict.items())[:5]:
            odds_list.append(
                f"{bookmaker}: Home={odds_data.get('home', 'N/A')}, "
                f"Draw={odds_data.get('draw', 'N/A')}, "
                f"Away={odds_data.get('away', 'N/A')}"
            )
        return "\n".join(odds_list) if odds_list else "No odds available"

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
            'recommendation': self._extract_recommendation(text),
            'pick': self._extract_pick(text),
            'target_odds': None,
            'confidence': self._extract_confidence(text),
            'agreement_score': self._extract_agreement_score(text),
            'reasoning': text[:600],
            'value_assessment': self._extract_value_assessment(text)
        }

    def _extract_recommendation(self, text: str) -> str:
        """Extract BET or NO_BET recommendation"""
        text_lower = text.lower()
        if 'recommendation: bet' in text_lower or 'recommend: bet' in text_lower:
            if 'no bet' not in text_lower and 'no_bet' not in text_lower:
                return 'BET'
        return 'NO_BET'

    def _extract_pick(self, text: str) -> Optional[str]:
        """Extract the specific pick from decision text"""
        text_lower = text.lower()

        if 'pick:' in text_lower:
            for line in text.split('\n'):
                if 'pick:' in line.lower():
                    if 'home' in line.lower() and 'win' in line.lower():
                        return 'home_win'
                    if 'away' in line.lower() and 'win' in line.lower():
                        return 'away_win'
                    if 'draw' in line.lower():
                        return 'draw'
                    if 'over' in line.lower():
                        return 'over'
                    if 'under' in line.lower():
                        return 'under'
                    if 'btts' in line.lower():
                        return 'btts'

        return None

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level"""
        import re
        text_lower = text.lower()

        confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', text_lower)
        if confidence_match:
            try:
                conf = float(confidence_match.group(1))
                return min(max(conf, 0.0), 1.0)
            except:
                pass

        if 'high confidence' in text_lower:
            return 0.8
        elif 'moderate confidence' in text_lower:
            return 0.6
        elif 'low confidence' in text_lower:
            return 0.3

        return 0.5

    def _extract_agreement_score(self, text: str) -> float:
        """Extract agreement score between analyses"""
        import re
        text_lower = text.lower()

        agreement_match = re.search(r'agreement[:\s]+([0-9.]+)', text_lower)
        if agreement_match:
            try:
                score = float(agreement_match.group(1))
                return min(max(score, 0.0), 1.0)
            except:
                pass

        if 'strong agreement' in text_lower or 'fully agree' in text_lower:
            return 0.9
        elif 'disagree' in text_lower or 'conflict' in text_lower:
            return 0.2
        elif 'partial agreement' in text_lower:
            return 0.6

        return 0.5

    def _extract_value_assessment(self, text: str) -> str:
        """Extract value assessment"""
        for line in text.split('\n'):
            if 'value' in line.lower() and 'assessment' in line.lower():
                return line.strip()

        if 'good value' in text.lower():
            return 'Good value identified'
        elif 'poor value' in text.lower() or 'no value' in text.lower():
            return 'Poor value, not recommended'

        return 'Value assessment unclear'

    def _get_best_odds(self, odds_dict: Dict, pick: Optional[str]) -> Optional[float]:
        """Find best available odds for the pick"""
        if not pick or not odds_dict:
            return None

        best_odds = None
        for bookmaker, odds_data in odds_dict.items():
            if pick == 'home_win' and odds_data.get('home'):
                if best_odds is None or odds_data['home'] > best_odds:
                    best_odds = odds_data['home']
            elif pick == 'away_win' and odds_data.get('away'):
                if best_odds is None or odds_data['away'] > best_odds:
                    best_odds = odds_data['away']
            elif pick == 'draw' and odds_data.get('draw'):
                if best_odds is None or odds_data['draw'] > best_odds:
                    best_odds = odds_data['draw']

        return best_odds

    def process_matches(
        self,
        matches: List[Dict],
        internet_picks_results: List[Dict],
        data_driven_results: List[Dict]
    ) -> List[Dict]:
        """
        Process multiple matches

        Args:
            matches: List of match dictionaries
            internet_picks_results: Results from Internet Picks Agent
            data_driven_results: Results from Data-Driven Agent

        Returns:
            List of final recommendations
        """
        recommendations = []

        # Create lookup dictionaries
        internet_picks_map = {r['match_id']: r for r in internet_picks_results}
        data_driven_map = {r['match_id']: r for r in data_driven_results}

        for match in matches:
            match_id = match['id']
            internet_picks = internet_picks_map.get(match_id, {})
            data_driven = data_driven_map.get(match_id, {})

            try:
                recommendation = self.synthesize(match, internet_picks, data_driven)
                recommendations.append(recommendation)
            except Exception as e:
                logger.error(f"Error synthesizing match {match_id}: {e}")
                recommendations.append({
                    'match_id': match_id,
                    'recommendation': 'NO_BET',
                    'error': str(e)
                })

        return recommendations
