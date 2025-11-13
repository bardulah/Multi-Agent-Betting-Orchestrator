"""
Custom Orchestration Agent for ADK
Replaces ThreadPoolExecutor with proper ADK custom agent pattern
Enables full event tracing and distributed execution
"""

import uuid
from typing import Dict, List, Any, Optional
from pydantic import Field
from google.adk.agents import BaseAgent, LlmAgent, InvocationContext
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .internet_picks_agent import create_internet_picks_agent
from .data_driven_agent import create_data_driven_agent
from .synthesis_agent import create_synthesis_agent
from .utils.logging_config import get_logger

logger = get_logger(__name__)


class BettingOrchestratorAgent(BaseAgent):
    """
    Custom ADK Agent that orchestrates the betting system.
    
    Replaces ThreadPoolExecutor with native ADK orchestration:
    - Proper event tracing through all sub-agents
    - State management between agents
    - Error isolation per match
    - Ready for distributed execution (Agent2Agent protocol)
    
    Workflow:
    1. Initialize session with current match data
    2. Run InternetPicksAgent (saves to session.state["internet_picks_analysis"])
    3. Run DataDrivenAgent (saves to session.state["data_driven_analysis"])
    4. Run SynthesisAgent (reads from state, saves to session.state["final_recommendation"])
    5. Yield progress events
    6. Return aggregated results
    """
    
    def __init__(self, config: Dict):
        """
        Initialize the orchestrator agent
        
        Args:
            config: System configuration dictionary
        """
        super().__init__(
            name="betting_orchestrator_agent",
            description="Orchestrates internet picks, data-driven, and synthesis agents"
        )
        
        # Use object.__setattr__ to bypass Pydantic validation
        object.__setattr__(self, '_config', config)
        object.__setattr__(self, 'internet_picks_agent', create_internet_picks_agent(config))
        object.__setattr__(self, 'data_driven_agent', create_data_driven_agent(config))
        object.__setattr__(self, 'synthesis_agent', create_synthesis_agent(config))
        
        logger.info("BettingOrchestratorAgent initialized with 3 sub-agents")
    
    @property
    def config(self) -> Dict:
        """Get config via property"""
        return object.__getattribute__(self, '_config')
    
    async def _run_async_impl(self, ctx: InvocationContext) -> None:
        """
        Main orchestration logic executed by ADK framework
        
        Args:
            ctx: ADK InvocationContext with session state and runner
        """
        
        # Extract matches from context
        # In actual integration, these would come from context input
        matches = ctx.session.state.get("matches", [])
        
        if not matches:
            logger.warning("No matches in context.session.state['matches']")
            yield  # Signal to ADK that work is done
            return
        
        logger.info(f"Orchestrator: Processing {len(matches)} matches")
        
        # Create runner with current session service
        runner = Runner(
            app_name=self._config.get('app_name', 'betting_system'),
            agent=self.internet_picks_agent,  # Will be swapped per sub-agent
            session_service=ctx.session_service
        )
        
        # Results collector
        all_recommendations = []
        
        # Process each match
        for match_idx, match in enumerate(matches, 1):
            match_id = match.get('id', f'match_{match_idx}')
            
            logger.info(f"[Match {match_idx}/{len(matches)}] {match['homeTeam']} vs {match['awayTeam']}")
            
            # Create fresh session per match (important for isolation)
            match_session_id = f"match_{match_id}_{uuid.uuid4()}"
            
            try:
                # ========== STEP 1: Internet Picks Analysis ==========
                logger.debug(f"  Step 1: Internet Picks Agent")
                
                # Create new runner with internet picks agent
                runner = Runner(
                    app_name=self._config.get('app_name', 'betting_system'),
                    agent=self.internet_picks_agent,
                    session_service=ctx.session_service
                )
                
                # Prompt for internet picks
                internet_prompt = f"""Analyze this match and find betting picks from the internet:

Match: {match['homeTeam']} vs {match['awayTeam']}
Sport: {match['sport']}
League: {match.get('league', 'Unknown')}
Date: {match.get('date', 'Today')}
Time: {match.get('time', 'TBD')}

Search for betting tips and predictions for this specific match. Provide your analysis in JSON format.
"""
                
                # Run internet picks agent
                internet_text = await self._run_sub_agent(
                    runner=runner,
                    session_id=match_session_id,
                    prompt=internet_prompt,
                    agent_name="InternetPicks"
                )
                
                logger.debug(f"  ✓ Internet picks received ({len(internet_text)} chars)")
                
                # ========== STEP 2: Data-Driven Analysis ==========
                logger.debug(f"  Step 2: Data-Driven Agent")
                
                # Create new runner with data-driven agent
                runner = Runner(
                    app_name=self._config.get('app_name', 'betting_system'),
                    agent=self.data_driven_agent,
                    session_service=ctx.session_service
                )
                
                # Prompt for data-driven analysis
                data_driven_prompt = f"""Analyze this match using statistical and objective data:

Match: {match['homeTeam']} vs {match['awayTeam']}
Sport: {match['sport']}
League: {match.get('league', 'Unknown')}
Date: {match.get('date', 'Today')}
Time: {match.get('time', 'TBD')}

Search for relevant statistics and provide a data-driven analysis in JSON format.
Do NOT reference betting tips or opinions - only use objective data.
"""
                
                # Run data-driven agent
                data_driven_text = await self._run_sub_agent(
                    runner=runner,
                    session_id=match_session_id,
                    prompt=data_driven_prompt,
                    agent_name="DataDriven"
                )
                
                logger.debug(f"  ✓ Data-driven analysis received ({len(data_driven_text)} chars)")
                
                # ========== STEP 3: Synthesis & Final Decision ==========
                logger.debug(f"  Step 3: Synthesis Agent")
                
                # Create new runner with synthesis agent
                runner = Runner(
                    app_name=self._config.get('app_name', 'betting_system'),
                    agent=self.synthesis_agent,
                    session_service=ctx.session_service
                )
                
                # Format odds for display
                odds_text = self._format_odds(match.get('odds', {}))
                
                # Prompt for synthesis
                synthesis_prompt = f"""Make a final betting decision for this match:

Match: {match['homeTeam']} vs {match['awayTeam']}
Sport: {match['sport']}
League: {match.get('league', 'Unknown')}
Time: {match.get('time', 'TBD')}

Available Odds:
{odds_text}

The following analyses have been completed:
- Internet Picks Analysis: {internet_text[:500]}
- Data-Driven Analysis: {data_driven_text[:500]}

Synthesize these analyses and make your final betting recommendation.
Provide your decision in JSON format.
"""
                
                # Run synthesis agent
                synthesis_text = await self._run_sub_agent(
                    runner=runner,
                    session_id=match_session_id,
                    prompt=synthesis_prompt,
                    agent_name="Synthesis"
                )
                
                logger.debug(f"  ✓ Synthesis complete ({len(synthesis_text)} chars)")
                
                # ========== Parse Synthesis Result ==========
                recommendation = self._parse_synthesis_result(synthesis_text, match)
                all_recommendations.append(recommendation)
                
                logger.info(f"  ✓ Decision: {recommendation.get('recommendation', 'NO_BET')}")
                
            except Exception as e:
                logger.error(f"Error processing match {match_id}: {e}", exc_info=True)
                
                # Add error result
                all_recommendations.append({
                    'match_id': match_id,
                    'homeTeam': match['homeTeam'],
                    'awayTeam': match['awayTeam'],
                    'sport': match['sport'],
                    'recommendation': 'NO_BET',
                    'error': str(e),
                    'confidence': 0.0
                })
            
            # Signal progress to ADK (allows for streaming updates)
            yield
        
        # Store final results in session state for retrieval
        ctx.session.state["all_recommendations"] = all_recommendations
        
        logger.info(f"Orchestrator: Completed {len(all_recommendations)} recommendations")
        logger.info(f"  - BET recommendations: {len([r for r in all_recommendations if r.get('recommendation') == 'BET'])}")
        logger.info(f"  - NO_BET recommendations: {len([r for r in all_recommendations if r.get('recommendation') == 'NO_BET'])}")
    
    async def _run_sub_agent(
        self,
        runner: Runner,
        session_id: str,
        prompt: str,
        agent_name: str
    ) -> str:
        """
        Run a sub-agent and collect its text response
        
        Args:
            runner: ADK Runner with the sub-agent configured
            session_id: Unique session ID for this execution
            prompt: Prompt to send to the agent
            agent_name: Name for logging
        
        Returns:
            Text response from the agent
        """
        
        try:
            # Create the message
            message = types.Content(
                parts=[types.Part(text=prompt)],
                role='user'
            )
            
            # Run the agent and collect output
            result_text = ""
            
            async for event in runner.run_async(
                user_id='betting_user',
                session_id=session_id,
                new_message=message
            ):
                # Extract text from events
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts'):
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                result_text += part.text
                    else:
                        result_text += str(event.content)
            
            if not result_text:
                logger.warning(f"[{agent_name}] No response received")
                result_text = "No response from agent"
            
            return result_text
            
        except Exception as e:
            logger.error(f"[{agent_name}] Error: {e}")
            raise
    
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
    
    def _parse_synthesis_result(self, text: str, match: Dict) -> Dict:
        """Parse synthesis agent output into recommendation"""
        
        import json
        import re
        
        # Try JSON parsing first
        try:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                # Map to standard result format
                return {
                    'match_id': match['id'],
                    'homeTeam': match['homeTeam'],
                    'awayTeam': match['awayTeam'],
                    'sport': match['sport'],
                    'league': match.get('league', 'Unknown'),
                    'recommendation': parsed.get('recommendation', 'NO_BET'),
                    'recommended_pick': parsed.get('pick'),
                    'target_odds': parsed.get('target_odds'),
                    'confidence': parsed.get('confidence', 0.0),
                    'reasoning': parsed.get('reasoning', ''),
                    'agreement_score': parsed.get('agreement_score', 0.0),
                }
        except Exception as e:
            logger.debug(f"Could not parse JSON from synthesis: {e}")
        
        # Fallback: extract from text
        return {
            'match_id': match['id'],
            'homeTeam': match['homeTeam'],
            'awayTeam': match['awayTeam'],
            'sport': match['sport'],
            'league': match.get('league', 'Unknown'),
            'recommendation': 'NO_BET' if 'no_bet' in text.lower() else 'BET' if 'bet' in text.lower() else 'NO_BET',
            'recommended_pick': None,
            'target_odds': None,
            'confidence': 0.5,
            'reasoning': text[:600],
            'agreement_score': 0.5,
        }
