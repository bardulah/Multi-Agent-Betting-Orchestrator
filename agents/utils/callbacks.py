"""
ADK Callback Utilities
Implements callback factories for monitoring tool execution, agent lifecycle, and result modification.
Reference: llms-full.txt lines 515-644
"""

from typing import Dict, Any, Optional, Callable
from copy import deepcopy
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from .logging_config import get_logger

logger = get_logger(__name__)


def create_after_tool_callback(agent_name: str) -> Callable:
    """
    Factory for after-tool callbacks with logging and result modification.
    
    Monitors tool execution:
    - Logs what tools are being used
    - Tracks tool arguments and responses
    - Can modify tool responses (e.g., truncate search results)
    
    Args:
        agent_name: Name of agent using this callback for logging
    
    Returns:
        Callback function ready to be assigned to LlmAgent
    
    Example:
        agent = LlmAgent(
            name="my_agent",
            ...,
            after_tool_callback=create_after_tool_callback("MyAgent")
        )
    """
    
    def after_tool_callback(
        tool: BaseTool,
        args: Dict[str, Any],
        tool_context: ToolContext,
        tool_response: Dict
    ) -> Optional[Dict]:
        """
        Monitor and optionally modify tool execution result.
        
        Args:
            tool: The tool that was executed
            args: Arguments passed to the tool
            tool_context: Execution context with agent info
            tool_response: The tool's response dictionary
        
        Returns:
            Modified response (or None to use original)
        """
        
        func_call_id = getattr(tool_context, 'function_call_id', 'unknown')
        
        # Log tool execution
        logger.info(
            f"[{agent_name}] Tool '{tool.name}' executed. "
            f"Args keys: {list(args.keys())}, "
            f"Response keys: {list(tool_response.keys() if tool_response else [])}"
        )
        
        # Validate response
        if not tool_response:
            logger.warning(f"[{agent_name}] Tool '{tool.name}' returned empty response")
            return None
        
        # Modify response for specific tools
        modified_response = deepcopy(tool_response)
        
        if tool.name == "google_search":
            # Limit search results to avoid token bloat
            if "results" in modified_response and isinstance(modified_response["results"], list):
                original_count = len(modified_response["results"])
                if original_count > 10:
                    logger.info(
                        f"[{agent_name}] Truncating google_search results "
                        f"from {original_count} to 10"
                    )
                    modified_response["results"] = modified_response["results"][:10]
            return modified_response
        
        # Return None to use original response for other tools
        return None
    
    return after_tool_callback


def create_before_agent_callback(agent_name: str) -> Callable:
    """
    Factory for before-agent callbacks.
    
    Logs when an agent starts execution.
    
    Args:
        agent_name: Name of agent for logging
    
    Returns:
        Callback function ready to be assigned to LlmAgent
    
    Example:
        agent = LlmAgent(
            name="my_agent",
            ...,
            before_agent_callback=create_before_agent_callback("MyAgent")
        )
    """
    
    def before_agent_callback(callback_context) -> Optional[Dict]:
        """
        Log when agent starts.
        
        Args:
            callback_context: Execution context
        
        Returns:
            None (don't modify behavior)
        """
        invocation_id = getattr(callback_context, 'invocation_id', 'unknown')
        logger.info(f"[{agent_name}] Starting execution (invocation: {invocation_id})")
        return None
    
    return before_agent_callback


def create_after_agent_callback(agent_name: str) -> Callable:
    """
    Factory for after-agent callbacks.
    
    Logs when an agent completes execution.
    
    Args:
        agent_name: Name of agent for logging
    
    Returns:
        Callback function ready to be assigned to LlmAgent
    
    Example:
        agent = LlmAgent(
            name="my_agent",
            ...,
            after_agent_callback=create_after_agent_callback("MyAgent")
        )
    """
    
    def after_agent_callback(callback_context, response=None) -> Optional[Dict]:
        """
        Log when agent completes.

        Args:
            callback_context: Execution context
            response: Agent response (optional, for compatibility)

        Returns:
            None (don't modify response)
        """
        response_text = str(response) if response else ""
        response_len = len(response_text)

        # Enhanced logging with debug info
        logger.info(
            f"[{agent_name}] Completed execution. "
            f"Response length: {response_len} characters"
        )

        # FIX #1: Add detailed debug info when response is empty
        if response_len == 0:
            logger.warning(
                f"[{agent_name}] WARNING: Empty response from agent! "
                f"Response object type: {type(response).__name__} | "
                f"Response value: {repr(response)}"
            )
        else:
            logger.debug(f"[{agent_name}] Response preview: {response_text[:100]}...")

        return None
    
    return after_agent_callback


def create_error_handler_callback(agent_name: str) -> Callable:
    """
    Factory for error handling callback.
    
    Logs and can modify behavior on agent errors.
    
    Args:
        agent_name: Name of agent for logging
    
    Returns:
        Callback function
    """
    
    def error_callback(error: Exception) -> Optional[str]:
        """
        Handle agent execution errors.
        
        Args:
            error: The exception that occurred
        
        Returns:
            None to propagate error, or string to override error
        """
        logger.error(f"[{agent_name}] Error during execution: {error}")
        return None  # Let error propagate
    
    return error_callback
