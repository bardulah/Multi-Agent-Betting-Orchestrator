"""
Internet Picks Agent - ADK Implementation with Base Class
Searches for betting tips and predictions from online sources.
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

IMPORTANT: Provide your response ONLY as valid JSON with ALL fields present:

```json
{
    "picks": ["home_win", "away_win", "draw", "over", "under", "btts"],
    "confidence": 0.0-1.0,
    "consensus": "description of majority opinion",
    "sources_count": number,
    "summary": "detailed summary of all findings from searches - explain what sources say, consensus opinion, and any notable predictions"
}
```

Important Rules:
- ONLY report what you find from searches, don't add your own betting opinion
- If sources disagree significantly, lower the confidence score
- Rate confidence based on: source quality, agreement level, recency
- If you find no relevant tips, return confidence: 0.0 and picks: []
- Always use google_search tool before responding
- ALWAYS include the summary field with detailed explanation of findings
- Return ONLY the JSON, no additional text"""
    
    agent = LlmAgent(
        name="internet_picks_agent",
        model="gemini-2.5-flash",
        instruction=instruction,
        tools=[google_search],
        description="Searches internet for betting tips and expert predictions",
        # ADK State Management: Auto-save output to session state
        output_key="internet_picks_analysis",
        # Add callbacks for monitoring and observability
        before_agent_callback=create_before_agent_callback("InternetPicks"),
        after_agent_callback=create_after_agent_callback("InternetPicks"),
        after_tool_callback=create_after_tool_callback("InternetPicks"),
    )
    
    return agent


class InternetPicksAgent(BaseAnalysisAgent):
    """
    Internet Picks Analysis Agent
    Inherits session management, async/sync bridge, and shared parsing from BaseAnalysisAgent.
    Implements internet-specific: build_prompt, format_result, and extraction methods.
    """
    
    def create_agent(self) -> LlmAgent:
        """Create the internet picks agent"""
        return create_internet_picks_agent(self.config)
    
    def build_prompt(self, match: Dict) -> str:
        """Build the prompt for analyzing internet picks"""
        return f"""Analyze this match and find betting picks from the internet:

Match: {match['homeTeam']} vs {match['awayTeam']}
Sport: {match['sport']}
League: {match.get('league', 'Unknown')}
Date: {match.get('date', 'Today')}
Time: {match.get('time', 'TBD')}

Search for betting tips and predictions for this specific match. Provide your analysis in JSON format.
"""
    
    def format_result(self, match: Dict, analysis: Dict) -> Dict:
        """Format the analysis result for internet picks"""
        return {
            'match_id': match['id'],
            'homeTeam': match['homeTeam'],
            'awayTeam': match['awayTeam'],
            'sport': match['sport'],
            'picks': analysis.get('picks', []),
            'confidence': analysis.get('confidence', 0.0),
            'sources_count': analysis.get('sources_count', 0),
            'summary': analysis.get('summary', ''),
            'consensus': analysis.get('consensus', 'No clear consensus'),
            'analysis': analysis.get('summary', '')  # Analysis field for notifications
        }
    
    def error_result(self, match: Dict, error: str) -> Dict:
        """Format error result for internet picks"""
        error_message = f'Error: {error}'
        return {
            'match_id': match['id'],
            'homeTeam': match['homeTeam'],
            'awayTeam': match['awayTeam'],
            'sport': match['sport'],
            'picks': [],
            'confidence': 0.0,
            'sources_count': 0,
            'summary': error_message,
            'consensus': 'Error',
            'analysis': error_message  # Analysis field for notifications
        }
    
    def _fallback_parse(self, text: str) -> Dict:
        """
        Fallback parsing when JSON extraction fails.
        Uses internet-specific extraction methods.
        """
        return {
            'picks': self._extract_picks(text),
            'confidence': self._extract_confidence(text),
            'sources_count': self._extract_source_count(text),
            'summary': text[:500],
            'consensus': self._extract_consensus(text)
        }
    
    # ========== INTERNET-SPECIFIC EXTRACTION ==========
    
    def _extract_source_count(self, text: str) -> int:
        """
        Extract source count from text.
        Looks for patterns like "sources: 5" or "5 sources"
        """
        match = re.search(r'sources?[:\s]+(\d+)', text.lower())
        if match:
            return int(match.group(1))
        return 0
    
    def _extract_consensus(self, text: str) -> str:
        """
        Extract consensus opinion from text.
        Looks for a line containing 'consensus' or similar patterns.
        """
        for line in text.split('\n'):
            if 'consensus' in line.lower():
                return line.strip()
        
        # Fallback: look for summary lines
        lines = text.split('\n')
        for line in lines:
            if len(line) > 20 and ('majority' in line.lower() or 'most' in line.lower()):
                return line.strip()
        
        return 'No clear consensus'
