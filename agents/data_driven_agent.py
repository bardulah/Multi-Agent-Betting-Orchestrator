"""
Data-Driven Analysis Agent - ADK Implementation with Base Class
Analyzes matches based on statistics, form, and objective data.
Inherits common functionality from BaseAnalysisAgent.
"""

import re
from typing import Dict, List
from google.adk.agents import LlmAgent
from google.adk.tools import google_search
from .base_analysis_agent import BaseAnalysisAgent
from .utils.callbacks import (
    create_after_tool_callback,
    create_before_agent_callback,
    create_after_agent_callback
)


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
        # ADK State Management: Auto-save output to session state
        output_key="data_driven_analysis",
        # Add callbacks for monitoring and observability
        before_agent_callback=create_before_agent_callback("DataDriven"),
        after_agent_callback=create_after_agent_callback("DataDriven"),
        after_tool_callback=create_after_tool_callback("DataDriven"),
    )
    
    return agent


class DataDrivenAgent(BaseAnalysisAgent):
    """
    Data-Driven Analysis Agent
    Inherits session management, async/sync bridge, and shared parsing from BaseAnalysisAgent.
    Implements data-driven-specific: build_prompt, format_result, and extraction methods.
    """
    
    def create_agent(self) -> LlmAgent:
        """Create the data-driven analysis agent"""
        return create_data_driven_agent(self.config)
    
    def build_prompt(self, match: Dict) -> str:
        """Build the prompt for analyzing data-driven statistics"""
        return f"""Analyze this match using statistical and objective data:

Match: {match['homeTeam']} vs {match['awayTeam']}
Sport: {match['sport']}
League: {match.get('league', 'Unknown')}
Date: {match.get('date', 'Today')}
Time: {match.get('time', 'TBD')}

Search for relevant statistics and provide a data-driven analysis in JSON format.
Do NOT reference betting tips or opinions - only use objective data.
"""
    
    def format_result(self, match: Dict, analysis: Dict) -> Dict:
        """Format the analysis result for data-driven analysis"""
        return {
            'match_id': match['id'],
            'homeTeam': match['homeTeam'],
            'awayTeam': match['awayTeam'],
            'sport': match['sport'],
            'picks': analysis.get('picks', []),
            'confidence': analysis.get('confidence', 0.0),
            'data_sources': [],  # ADK search tool handles this internally
            'analysis': analysis.get('analysis', ''),
            'key_factors': analysis.get('key_factors', []),
            'statistics': analysis.get('statistics', {})
        }
    
    def error_result(self, match: Dict, error: str) -> Dict:
        """Format error result for data-driven analysis"""
        return {
            'match_id': match['id'],
            'homeTeam': match['homeTeam'],
            'awayTeam': match['awayTeam'],
            'sport': match['sport'],
            'picks': [],
            'confidence': 0.0,
            'data_sources': [],
            'analysis': f'Error: {error}',
            'key_factors': [],
            'statistics': {}
        }
    
    def _fallback_parse(self, text: str) -> Dict:
        """
        Fallback parsing when JSON extraction fails.
        Uses data-driven-specific extraction methods.
        """
        return {
            'picks': self._extract_picks(text),
            'confidence': self._extract_confidence(text),
            'key_factors': self._extract_key_factors(text),
            'analysis': text[:800],
            'statistics': self._extract_statistics(text)
        }
    
    # ========== DATA-DRIVEN-SPECIFIC EXTRACTION ==========
    
    def _extract_key_factors(self, text: str) -> List[str]:
        """
        Extract key factors from analysis.
        Looks for lines containing 'key factor', 'important', etc.
        """
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
        """
        Extract statistics summaries from analysis.
        Looks for mentions of head-to-head, recent form, goals data, etc.
        """
        stats = {}
        
        # Look for common statistics
        if 'head to head' in text.lower() or 'h2h' in text.lower():
            stats['head_to_head'] = 'Mentioned in analysis'
        
        if 'recent form' in text.lower():
            stats['recent_form'] = 'Analyzed'
        
        if 'goals' in text.lower():
            stats['goals_data'] = 'Available'
        
        if 'injury' in text.lower():
            stats['injuries'] = 'Noted'
        
        if 'home' in text.lower() and 'away' in text.lower():
            stats['home_away_performance'] = 'Analyzed'
        
        return stats
