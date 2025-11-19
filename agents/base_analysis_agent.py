"""
Base Analysis Agent
Shared base class for all ADK analysis agents to eliminate duplication.
Implements common patterns: async/sync bridge, session management, JSON parsing, extraction utilities.
"""

import json
import re
import asyncio
import uuid
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from google.adk.agents import LlmAgent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types, Client
from dotenv import load_dotenv
from .utils.logging_config import get_logger

logger = get_logger(__name__)


class BaseAnalysisAgent(ABC):
    """
    Abstract base class for ADK-based analysis agents.
    
    Subclasses must implement:
    - create_agent(): Define the LlmAgent with instruction and tools
    - build_prompt(match): Build the prompt for the match
    - format_result(match, analysis): Format the analysis result
    - error_result(match, error): Format error result
    - _fallback_parse(text): Define fallback parsing logic
    
    Inherited functionality:
    - Async/sync bridge with event loop management
    - Per-match session creation (fixes accumulation issue)
    - Shared JSON parsing with fallbacks
    - Shared extraction utilities (picks, confidence, etc.)
    """
    
    def __init__(self, config: Dict):
        """
        Initialize base agent.
        
        Args:
            config: System configuration dictionary
        """
        self.config = config
        self.agent = self.create_agent()
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info(f"{self.__class__.__name__} initialized (session-per-match mode)")
    
    @abstractmethod
    def create_agent(self) -> LlmAgent:
        """
        Create and return the LlmAgent.
        Must be implemented by subclass.
        
        Returns:
            Configured LlmAgent instance
        """
        pass
    
    @abstractmethod
    def build_prompt(self, match: Dict) -> str:
        """
        Build the prompt for analyzing a match.
        Must be implemented by subclass.
        
        Args:
            match: Match data dictionary
        
        Returns:
            Prompt string for the LLM
        """
        pass
    
    @abstractmethod
    def format_result(self, match: Dict, analysis: Dict) -> Dict:
        """
        Format the analysis result.
        Must be implemented by subclass.
        
        Args:
            match: Original match data
            analysis: Parsed analysis from agent
        
        Returns:
            Formatted result dictionary
        """
        pass
    
    @abstractmethod
    def error_result(self, match: Dict, error: str) -> Dict:
        """
        Format error result.
        Must be implemented by subclass.
        
        Args:
            match: Original match data
            error: Error message
        
        Returns:
            Error result dictionary
        """
        pass
    
    @abstractmethod
    def _fallback_parse(self, text: str) -> Dict:
        """
        Define fallback parsing when JSON extraction fails.
        Must be implemented by subclass.
        
        Args:
            text: Raw text response from agent
        
        Returns:
            Parsed dictionary with fallback extraction
        """
        pass
    
    # ========== SYNC/ASYNC BRIDGE ==========
    
    def analyze_match(self, match: Dict) -> Dict:
        """
        Synchronous wrapper for analyze_match_async.
        Safe to use in ThreadPoolExecutor contexts.
        
        Args:
            match: Match data dictionary
        
        Returns:
            Analysis result dictionary
        """
        # Create fresh event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.analyze_match_async(match))
        finally:
            loop.close()  # Critical: prevent event loop leaks
    
    async def analyze_match_async(self, match: Dict) -> Dict:
        """
        Asynchronous match analysis using ADK agent.
        Creates fresh session per match (prevents accumulation).
        
        Args:
            match: Match data dictionary
        
        Returns:
            Analysis result dictionary
        """
        self.logger.info(f"Analyzing {match.get('homeTeam', 'Unknown')} vs {match.get('awayTeam', 'Unknown')}")
        
        # Build prompt (subclass-specific)
        prompt = self.build_prompt(match)
        
        try:
            # FIX: Create fresh session per match instead of reusing
            # Load API key and set as environment variable for Google ADK
            load_dotenv('config/.env')
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment variables")
            
            # Set API key as environment variable for Google ADK
            os.environ['GOOGLE_API_KEY'] = api_key
            
            session_service = InMemorySessionService()
            runner = Runner(
                app_name='betting_system',
                agent=self.agent,
                session_service=session_service
            )
            
            # Unique session ID per match (includes UUID to prevent collisions)
            user_id = 'betting_user'
            session_id = f"match_{match.get('id', 'unknown')}_{uuid.uuid4().hex[:8]}"
            
            self.logger.debug(f"Created session: {session_id}")
            
            # Create session
            session = await session_service.create_session(
                app_name='betting_system',
                user_id=user_id,
                session_id=session_id
            )
            
            # Create proper ADK message
            message = types.Content(
                parts=[types.Part(text=prompt)],
                role='user'
            )
            
            # Run the ADK agent via Runner
            # FIX #1: Enhanced response extraction with debug logging
            result_text = ""
            event_count = 0

            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=message
            ):
                event_count += 1
                self.logger.debug(f"[DEBUG] Event #{event_count}: type={type(event).__name__}")

                # Try multiple extraction strategies
                extracted = False

                # Strategy 1: Try event.content.parts (original approach)
                if hasattr(event, 'content') and event.content:
                    self.logger.debug(f"[DEBUG] Event has content: {type(event.content).__name__}")

                    if hasattr(event.content, 'parts'):
                        self.logger.debug(f"[DEBUG] Event.content has parts: {len(event.content.parts)}")
                        for i, part in enumerate(event.content.parts):
                            self.logger.debug(f"[DEBUG] Part {i}: type={type(part).__name__}")
                            if hasattr(part, 'text') and part.text:
                                self.logger.debug(f"[DEBUG] Extracted text from part {i}: {len(part.text)} chars")
                                result_text += part.text
                                extracted = True
                    else:
                        # Strategy 2: Try direct string conversion
                        content_str = str(event.content)
                        if content_str and content_str != "":
                            self.logger.debug(f"[DEBUG] Using str(event.content): {len(content_str)} chars")
                            result_text += content_str
                            extracted = True

                # Strategy 3: Check for response/result/output attributes
                if not extracted:
                    for attr in ['response', 'result', 'output', 'text', 'data']:
                        if hasattr(event, attr):
                            val = getattr(event, attr)
                            if val and isinstance(val, str) and len(val) > 0:
                                self.logger.debug(f"[DEBUG] Found {attr}: {len(val)} chars")
                                result_text += val
                                extracted = True
                                break

                if not extracted:
                    self.logger.debug(f"[DEBUG] Event #{event_count} yielded no text")

            self.logger.debug(f"[DEBUG] Processing complete: {event_count} events, {len(result_text)} chars extracted")

            if not result_text:
                result_text = "No response from agent"
                self.logger.warning(f"Agent returned empty response for {match.get('id')} after {event_count} events")
            else:
                self.logger.debug(f"[DEBUG] Final result: {result_text[:200]}...")
            
            # Parse response (shared logic)
            analysis = self._parse_response(result_text)
            
            # Format result (subclass-specific)
            return self.format_result(match, analysis)
        
        except Exception as e:
            self.logger.error(f"Error analyzing match {match.get('id')}: {e}")
            return self.error_result(match, str(e))
    
    # ========== SHARED PARSING LOGIC ==========
    
    def _parse_response(self, text: str) -> Dict:
        """
        Parse JSON from agent response with fallback.

        Args:
            text: Raw text response from agent

        Returns:
            Parsed dictionary
        """
        try:
            # Strategy 1: Try to find JSON in markdown code blocks first
            # Look for ```json ... ``` blocks
            code_block_match = re.search(r'```json\s*\n(.*?)\n```', text, re.DOTALL)
            if code_block_match:
                try:
                    parsed = json.loads(code_block_match.group(1))
                    self.logger.debug(f"Successfully parsed JSON from markdown code block")
                    return parsed
                except json.JSONDecodeError:
                    self.logger.debug(f"Invalid JSON in code block, trying alternative patterns")

            # Strategy 2: Try to find bare JSON object (non-greedy to avoid spanning multiple objects)
            # Use non-greedy matching and try to find valid JSON
            for json_match in re.finditer(r'\{[^{}]*\}', text):
                try:
                    parsed = json.loads(json_match.group())
                    self.logger.debug(f"Successfully parsed JSON from response")
                    return parsed
                except json.JSONDecodeError:
                    continue

            # Strategy 3: Try greedy matching as last resort
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                self.logger.debug(f"Successfully parsed JSON from response (greedy)")
                return parsed

        except Exception as e:
            self.logger.debug(f"Could not parse JSON: {e}")

        # Fallback: use subclass-specific extraction
        self.logger.debug(f"Using fallback parsing for {self.__class__.__name__}")
        return self._fallback_parse(text)
    
    # ========== SHARED EXTRACTION UTILITIES ==========
    
    def _extract_confidence(self, text: str) -> float:
        """
        Extract confidence level from text (shared implementation).
        Handles both numeric (0.85) and qualitative (high, medium, low) formats.
        
        Args:
            text: Text to extract confidence from
        
        Returns:
            Confidence value 0.0-1.0
        """
        text_lower = text.lower()
        
        # Look for explicit numeric confidence
        conf_match = re.search(r'confidence[:\s]+([0-9.]+)', text_lower)
        if conf_match:
            try:
                val = float(conf_match.group(1))
                return min(max(val, 0.0), 1.0)  # Clamp to 0-1
            except Exception:
                pass
        
        # Qualitative (check most specific first)
        if 'very high' in text_lower or 'extremely high' in text_lower:
            return 0.9
        elif 'high' in text_lower and 'confidence' in text_lower:
            return 0.8
        elif 'moderate' in text_lower or 'medium' in text_lower:
            return 0.6
        elif 'low' in text_lower and 'confidence' in text_lower:
            return 0.3
        
        return 0.5  # Default
    
    def _extract_picks(self, text: str) -> list:
        """
        Extract betting picks from text (shared implementation).
        
        Args:
            text: Text to extract picks from
        
        Returns:
            List of pick strings (home_win, away_win, draw, over, under, btts)
        """
        picks = []
        text_lower = text.lower()
        
        # Check for various pick types
        if ('home' in text_lower or 'host' in text_lower) and ('win' in text_lower or 'victory' in text_lower or '1' in text_lower):
            picks.append('home_win')
        if ('away' in text_lower or 'visitor' in text_lower) and ('win' in text_lower or 'victory' in text_lower or '2' in text_lower):
            picks.append('away_win')
        if 'draw' in text_lower or 'tie' in text_lower or 'x' in text_lower:
            picks.append('draw')
        if 'over' in text_lower and ('goal' in text_lower or 'goal' in text_lower or 'total' in text_lower):
            picks.append('over')
        if 'under' in text_lower and ('goal' in text_lower or 'total' in text_lower):
            picks.append('under')
        if 'btts' in text_lower or 'both teams to score' in text_lower or 'both score' in text_lower:
            picks.append('btts')
        
        return picks if picks else ['no_clear_pick']
    
    def process_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Process multiple matches sequentially.
        
        Args:
            matches: List of match dictionaries
        
        Returns:
            List of analysis results
        """
        results = []
        total = len(matches)
        
        for idx, match in enumerate(matches, 1):
            try:
                self.logger.info(f"Processing match {idx}/{total}: {match.get('homeTeam')} vs {match.get('awayTeam')}")
                result = self.analyze_match(match)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error processing match {match.get('id')}: {e}")
                results.append(self.error_result(match, str(e)))
        
        self.logger.info(f"Completed processing {len(results)}/{total} matches")
        return results
