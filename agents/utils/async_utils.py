"""
Async Utilities for Timeout and Retry Logic
Implements timeout protection and exponential backoff retry for robust agent execution.
"""

import asyncio
from typing import Coroutine, TypeVar, Callable, Optional, Any
from .logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


async def run_with_timeout(
    coro: Coroutine[Any, Any, T],
    timeout_seconds: int = 300,
    agent_name: str = "unknown"
) -> Optional[T]:
    """
    Run async operation with timeout protection.
    
    Prevents agents from hanging indefinitely. Useful for network calls,
    LLM generation, or any potentially slow async operation.
    
    Args:
        coro: Coroutine to execute
        timeout_seconds: Maximum execution time (default 5 minutes)
        agent_name: Name for logging purposes
    
    Returns:
        Result from coroutine, or None if timeout occurs
    
    Example:
        result = await run_with_timeout(
            agent.analyze_match_async(match),
            timeout_seconds=300,
            agent_name="InternetPicks"
        )
        if result is None:
            logger.error("Agent timed out")
    """
    try:
        logger.info(f"[{agent_name}] Starting with {timeout_seconds}s timeout")
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    
    except asyncio.TimeoutError:
        logger.error(
            f"[{agent_name}] Timed out after {timeout_seconds} seconds. "
            f"Operation took too long."
        )
        return None
    
    except Exception as e:
        logger.error(f"[{agent_name}] Error during timeout-protected execution: {e}")
        raise


async def run_with_retry(
    coro_factory: Callable[[], Coroutine[Any, Any, T]],
    max_retries: int = 3,
    backoff_seconds: int = 2,
    agent_name: str = "unknown"
) -> Optional[T]:
    """
    Run async operation with exponential backoff retry.
    
    Automatically retries transient failures (e.g., network timeouts, API errors).
    Uses exponential backoff: 2s, 4s, 8s between retries.
    
    Args:
        coro_factory: Callable that creates fresh coroutine for each attempt
        max_retries: Number of total attempts (default 3)
        backoff_seconds: Initial backoff duration - doubles each retry
        agent_name: Name for logging purposes
    
    Returns:
        Result from coroutine, or None if all retries exhausted
    
    Example:
        async def do_analysis():
            return await agent.analyze_match_async(match)
        
        result = await run_with_retry(
            do_analysis,
            max_retries=3,
            backoff_seconds=2,
            agent_name="InternetPicks-Match1"
        )
    """
    
    for attempt in range(max_retries):
        try:
            logger.info(f"[{agent_name}] Attempt {attempt + 1}/{max_retries}")
            return await coro_factory()
        
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed
                logger.error(
                    f"[{agent_name}] Failed after {max_retries} attempts. "
                    f"Final error: {e}"
                )
                return None
            
            # Calculate backoff
            wait_time = backoff_seconds * (2 ** attempt)
            logger.warning(
                f"[{agent_name}] Attempt {attempt + 1} failed: {e}. "
                f"Retrying in {wait_time}s... (attempt {attempt + 2}/{max_retries})"
            )
            
            # Wait before retry
            await asyncio.sleep(wait_time)
    
    return None


async def run_with_timeout_and_retry(
    coro_factory: Callable[[], Coroutine[Any, Any, T]],
    timeout_seconds: int = 300,
    max_retries: int = 3,
    backoff_seconds: int = 2,
    agent_name: str = "unknown"
) -> Optional[T]:
    """
    Run async operation with both timeout and retry protection.
    
    Combines timeout (per attempt) and retry (with backoff) for robust execution.
    Each attempt gets its own timeout window.
    
    Args:
        coro_factory: Callable that creates fresh coroutine
        timeout_seconds: Timeout per attempt
        max_retries: Number of total attempts
        backoff_seconds: Initial backoff between retries
        agent_name: Name for logging
    
    Returns:
        Result from coroutine, or None if all attempts fail/timeout
    
    Example:
        result = await run_with_timeout_and_retry(
            lambda: agent.analyze_match_async(match),
            timeout_seconds=300,
            max_retries=3,
            backoff_seconds=2,
            agent_name="InternetPicks-Match1"
        )
    """
    
    for attempt in range(max_retries):
        try:
            logger.info(
                f"[{agent_name}] Attempt {attempt + 1}/{max_retries} "
                f"(timeout: {timeout_seconds}s)"
            )
            
            return await run_with_timeout(
                coro_factory(),
                timeout_seconds=timeout_seconds,
                agent_name=f"{agent_name}-Attempt{attempt + 1}"
            )
        
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(
                    f"[{agent_name}] All {max_retries} attempts failed. "
                    f"Final error: {e}"
                )
                return None
            
            wait_time = backoff_seconds * (2 ** attempt)
            logger.warning(
                f"[{agent_name}] Attempt {attempt + 1} failed: {e}. "
                f"Retrying in {wait_time}s..."
            )
            await asyncio.sleep(wait_time)
    
    return None


# Context manager for timing operations
class AsyncTimer:
    """
    Context manager for timing async operations.
    
    Example:
        async with AsyncTimer("agent_execution") as timer:
            result = await agent.analyze()
        logger.info(f"Operation took {timer.elapsed_seconds:.2f}s")
    """
    
    def __init__(self, operation_name: str):
        """
        Initialize timer.
        
        Args:
            operation_name: Name of operation being timed
        """
        self.operation_name = operation_name
        self.start_time = None
        self.end_time = None
    
    async def __aenter__(self):
        """Start timing"""
        import time
        self.start_time = time.time()
        logger.debug(f"[Timer] Starting: {self.operation_name}")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End timing"""
        import time
        self.end_time = time.time()
        elapsed = self.elapsed_seconds
        
        if exc_type:
            logger.warning(
                f"[Timer] {self.operation_name} failed after {elapsed:.2f}s: {exc_val}"
            )
        else:
            logger.info(f"[Timer] {self.operation_name} completed in {elapsed:.2f}s")
    
    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds"""
        import time
        end = self.end_time or time.time()
        return end - (self.start_time or end)
