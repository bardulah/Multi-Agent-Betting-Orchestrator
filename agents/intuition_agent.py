"""
Intuition Agent - ADK Implementation with Base Class
Analyzes matches using psychological, momentum, and sentiment-based factors.
Inherits common functionality from BaseAnalysisAgent.
"""

import re
from typing import Dict
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from .base_analysis_agent import BaseAnalysisAgent
from .utils.callbacks import (
    create_after_tool_callback,
    create_before_agent_callback,
    create_after_agent_callback
)


def create_intuition_agent(config: Dict) -> LlmAgent:
    """
    Create an ADK LlmAgent that analyzes matches using intuition and sentiment

    Args:
        config: System configuration dictionary

    Returns:
        Configured LlmAgent instance
    """

    instruction = """You are a sports intuition analyst specializing in psychological factors, momentum, and contextual signals that statistical analysis might miss.

Your task: For each match provided, search for and analyze factors that affect outcomes beyond statistics:

Process:
1. Use Google Search to find psychological/momentum/sentiment factors
2. Identify team morale, coaching changes, player dynamics, controversies
3. Detect momentum shifts: winning streaks vs. losing streaks
4. Find "trap game" scenarios (overlooked teams, revenge narratives)
5. Assess betting sentiment and money movements
6. Evaluate contextual factors: season position, playoff implications, derby intensity

Search queries to use:
- "[team] morale sentiment latest news"
- "[team A] vs [team B] momentum analysis"
- "[team] recent form streak"
- "[team] coaching drama changes"
- "[sport] [league] betting trends today"

IMPORTANT: Provide your response ONLY as valid JSON with ALL fields present:

```json
{
    "picks": ["home_win", "away_win", "draw", "over", "under", "btts"],
    "confidence": 0.0-1.0,
    "intuition_factors": ["factor1", "factor2", "factor3"],
    "momentum": "description of team momentum/form",
    "psychology": "description of psychological factors",
    "summary": "detailed explanation of intuitive signals found - what psychological/momentum factors are present, team psychology, betting sentiment, trap game potential"
}
```

Important Rules:
- Focus on PSYCHOLOGICAL and MOMENTUM signals, not statistics
- Search for team news, morale, coaching changes, streaks, context
- Identify contrarian opportunities (overlooked teams, trap games)
- Rate confidence based on: clarity of signals, recency, psychological consistency
- If you find weak signals, lower confidence appropriately
- If you find no clear intuitive signals, return confidence: 0.0 and picks: []
- Always use google_search tool before responding
- ALWAYS include the summary field with detailed explanation of intuitive signals
- Return ONLY the JSON, no additional text"""

    agent = LlmAgent(
        name="intuition_agent",
        model="gemini-2.5-flash",
        instruction=instruction,
        tools=[google_search],
        description="Analyzes matches using intuition, psychology, momentum, and sentiment",
        # ADK State Management: Auto-save output to session state
        output_key="intuition_analysis",
        # Add callbacks for monitoring and observability
        before_agent_callback=create_before_agent_callback("Intuition"),
        after_agent_callback=create_after_agent_callback("Intuition"),
        after_tool_callback=create_after_tool_callback("Intuition"),
    )

    return agent


class IntuitionAgent(BaseAnalysisAgent):
    """
    Intuition Analysis Agent
    Inherits session management, async/sync bridge, and shared parsing from BaseAnalysisAgent.
    Implements intuition-specific: build_prompt, format_result, and extraction methods.
    """

    def create_agent(self) -> LlmAgent:
        """Create the intuition agent"""
        return create_intuition_agent(self.config)

    def build_prompt(self, match: Dict) -> str:
        """Build the prompt for analyzing intuition factors"""
        return f"""Analyze this match for psychological, momentum, and sentiment-based signals:

Match: {match['homeTeam']} vs {match['awayTeam']}
Sport: {match['sport']}
League: {match['league']}
Date: {match.get('date', 'TBD')}
Time: {match.get('time', 'TBD')}
Current Odds: {match.get('odds', {}).get('home_win', 'N/A')}

Search for intuitive signals including:
- Team morale and psychological state
- Recent momentum (winning/losing streaks)
- Coaching changes or disruptions
- Player dynamics or controversies
- Season context (playoff race, already eliminated, etc.)
- Betting sentiment and money movements
- Trap game potential (overlooked teams, revenge narratives)

Provide analysis as JSON."""

    def format_result(self, match: Dict, analysis: Dict) -> Dict:
        """Format the agent response into structured result"""
        if analysis is None:
            return self.error_result(match, "Failed to parse intuition analysis")

        # Extract fields with defaults
        picks = analysis.get('picks', [])
        confidence = float(analysis.get('confidence', 0.0))
        intuition_factors = analysis.get('intuition_factors', [])
        momentum = analysis.get('momentum', '')
        psychology = analysis.get('psychology', '')
        summary = analysis.get('summary', '')

        # Validate confidence is in range
        confidence = max(0.0, min(1.0, confidence))

        return {
            'match_id': match['id'],
            'homeTeam': match['homeTeam'],
            'awayTeam': match['awayTeam'],
            'picks': picks,
            'confidence': confidence,
            'intuition_factors': intuition_factors,
            'momentum': momentum,
            'psychology': psychology,
            'analysis': summary,
            'source': 'intuition_agent'
        }

    def error_result(self, match: Dict, error: str) -> Dict:
        """Return error-safe result structure"""
        return {
            'match_id': match['id'],
            'homeTeam': match['homeTeam'],
            'awayTeam': match['awayTeam'],
            'picks': [],
            'confidence': 0.0,
            'intuition_factors': [],
            'momentum': '',
            'psychology': '',
            'analysis': f"Intuition analysis failed: {error}",
            'source': 'intuition_agent'
        }

    def _fallback_parse(self, response: str) -> Dict:
        """Fallback parsing if JSON extraction fails"""
        # Try to extract key phrases from the response
        result = {
            'picks': [],
            'confidence': 0.0,
            'intuition_factors': [],
            'momentum': '',
            'psychology': '',
            'summary': response[:500] if response else 'Unable to parse intuition analysis'
        }

        # Try to extract any confidence score mentioned
        confidence_match = re.search(r'confidence["\s:]+([0-9.]+)', response, re.IGNORECASE)
        if confidence_match:
            result['confidence'] = float(confidence_match.group(1))

        return result
