"""
Synthesis & Decision Agent
Combines inputs from Internet Picks and Data-Driven agents to make final betting recommendations
"""

import os
from typing import Dict, List, Optional
from google import genai
from google.genai import types
from .utils.logging_config import get_logger

logger = get_logger(__name__)


class SynthesisAgent:
    """
    Agent that synthesizes multiple analyses and makes final betting decisions
    """

    def __init__(self, config: Dict):
        self.config = config
        self.min_value_threshold = config.get('agents', {}).get('synthesis', {}).get('min_value_threshold', 1.05)
        self.confidence_threshold = config.get('agents', {}).get('synthesis', {}).get('confidence_threshold', 0.7)

        # Initialize Google GenAI client
        api_key = os.getenv('GOOGLE_API_KEY')
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            logger.warning("GOOGLE_API_KEY not set, using mock responses")
            self.client = None

    def synthesize(
        self,
        match: Dict,
        internet_picks: Dict,
        data_driven: Dict
    ) -> Dict:
        """
        Synthesize analyses and make final betting decision

        Args:
            match: Original match data with odds
            internet_picks: Analysis from Internet Picks Agent
            data_driven: Analysis from Data-Driven Agent

        Returns:
            Final betting recommendation
        """
        logger.info(f"Synthesis: Analyzing {match['homeTeam']} vs {match['awayTeam']}")

        # Use ADK to synthesize and decide
        decision = self._make_decision_with_adk(match, internet_picks, data_driven)

        return {
            'match_id': match['id'],
            'homeTeam': match['homeTeam'],
            'awayTeam': match['awayTeam'],
            'sport': match['sport'],
            'league': match.get('league', 'Unknown'),
            'time': match.get('time', 'TBD'),
            'recommendation': decision.get('recommendation', 'NO_BET'),
            'recommended_pick': decision.get('pick'),
            'recommended_odds': decision.get('odds'),
            'confidence': decision.get('confidence', 0.0),
            'reasoning': decision.get('reasoning', ''),
            'value_assessment': decision.get('value_assessment', ''),
            'agreement_score': decision.get('agreement_score', 0.0),
            'internet_picks_summary': internet_picks.get('summary', ''),
            'data_driven_summary': data_driven.get('analysis', ''),
            'odds_available': len(match.get('odds', {})) > 0
        }

    def _make_decision_with_adk(
        self,
        match: Dict,
        internet_picks: Dict,
        data_driven: Dict
    ) -> Dict:
        """
        Use Google ADK to make final betting decision

        Args:
            match: Match data with odds
            internet_picks: Internet picks analysis
            data_driven: Data-driven analysis

        Returns:
            Decision dictionary
        """
        if not self.client:
            # Mock response when API key not available
            return {
                'recommendation': 'NO_BET',
                'pick': None,
                'odds': None,
                'confidence': 0.0,
                'reasoning': 'Mock decision - API key not configured',
                'value_assessment': 'Cannot assess without API',
                'agreement_score': 0.0
            }

        # Prepare odds information
        odds_text = "Odds not available"
        if match.get('odds'):
            odds_list = []
            for bookmaker, odds_data in list(match['odds'].items())[:5]:
                odds_list.append(
                    f"{bookmaker}: Home={odds_data.get('home')}, "
                    f"Draw={odds_data.get('draw')}, Away={odds_data.get('away')}"
                )
            odds_text = "\n".join(odds_list)

        prompt = f"""You are a betting decision expert. Your job is to synthesize two independent analyses and make a final betting recommendation.

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

Your task:
1. Compare and contrast both analyses
2. Identify areas of agreement and disagreement
3. Assess which analysis has stronger supporting evidence
4. Evaluate if any available odds represent good value
5. Make a final recommendation: BET or NO_BET

Betting Value Threshold: Only recommend a bet if odds >= {self.min_value_threshold}
Confidence Threshold: Only recommend a bet if combined confidence >= {self.confidence_threshold}

Decision Criteria:
- Both analyses agree + good odds value = STRONG BET
- Both analyses agree + poor odds value = NO_BET
- Analyses disagree + weak evidence = NO_BET
- Analyses disagree + one has very strong evidence = CONSIDER BET
- Insufficient data = NO_BET

Provide your decision in this format:
1. Agreement Score (0.0 to 1.0): How much the analyses align
2. Recommendation: BET or NO_BET
3. If BET, specify: Pick (e.g., home_win, away_win, over, etc.) and target odds
4. Confidence Level (0.0 to 1.0)
5. Reasoning: Detailed explanation of your decision
6. Value Assessment: Whether the odds represent good value

Be conservative. Only recommend bets when there is strong evidence and value.
"""

        try:
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,  # Very low temperature for consistent decisions
                    max_output_tokens=1000
                )
            )

            decision_text = response.text

            # Parse the response
            recommendation = self._extract_recommendation(decision_text)
            pick = self._extract_pick(decision_text)
            odds = self._extract_odds(decision_text, match.get('odds', {}), pick)
            confidence = self._extract_confidence(decision_text)
            agreement_score = self._extract_agreement_score(decision_text)

            return {
                'recommendation': recommendation,
                'pick': pick,
                'odds': odds,
                'confidence': confidence,
                'reasoning': decision_text[:600],
                'value_assessment': self._extract_value_assessment(decision_text),
                'agreement_score': agreement_score
            }

        except Exception as e:
            logger.error(f"Error in synthesis: {e}")
            return {
                'recommendation': 'NO_BET',
                'pick': None,
                'odds': None,
                'confidence': 0.0,
                'reasoning': f'Synthesis error: {str(e)}',
                'value_assessment': 'Error',
                'agreement_score': 0.0
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
            # Find the line with the pick
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

    def _extract_odds(self, text: str, odds_dict: Dict, pick: Optional[str]) -> Optional[float]:
        """Extract or find appropriate odds based on the pick"""
        if not pick or not odds_dict:
            return None

        # Try to find odds value in text
        import re
        odds_match = re.search(r'odds[:\s]+([0-9.]+)', text.lower())
        if odds_match:
            try:
                return float(odds_match.group(1))
            except:
                pass

        # Find best odds for the pick from available bookmakers
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

    def _extract_confidence(self, text: str) -> float:
        """Extract confidence level"""
        import re
        text_lower = text.lower()

        # Look for explicit confidence value
        confidence_match = re.search(r'confidence[:\s]+([0-9.]+)', text_lower)
        if confidence_match:
            try:
                conf = float(confidence_match.group(1))
                return min(max(conf, 0.0), 1.0)  # Clamp between 0 and 1
            except:
                pass

        # Look for qualitative confidence
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

        # Look for keywords
        if 'strong agreement' in text_lower or 'fully agree' in text_lower:
            return 0.9
        elif 'disagree' in text_lower or 'conflict' in text_lower:
            return 0.2
        elif 'partial agreement' in text_lower:
            return 0.6

        return 0.5

    def _extract_value_assessment(self, text: str) -> str:
        """Extract value assessment"""
        lines = text.split('\n')
        for line in lines:
            if 'value' in line.lower() and 'assessment' in line.lower():
                return line.strip()

        if 'good value' in text.lower():
            return 'Good value identified'
        elif 'poor value' in text.lower() or 'no value' in text.lower():
            return 'Poor value, not recommended'

        return 'Value assessment unclear'

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
