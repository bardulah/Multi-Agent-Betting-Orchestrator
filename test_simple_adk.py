#!/usr/bin/env python3
"""
Minimal ADK test to verify basic functionality
"""
import os
import asyncio
from dotenv import load_dotenv

# Load environment
load_dotenv('config/.env')

async def test_simple():
    """Test simplest possible ADK agent"""
    from google.adk.agents import LlmAgent

    print("Creating simple LlmAgent...")
    agent = LlmAgent(
        name="test_agent",
        model="gemini-1.5-flash",
        instruction="You are a helpful assistant. Answer briefly.",
    )

    print(f"Agent created: {agent.name}")
    print(f"Model: {agent.model}")

    # Try running without Runner - just agent directly
    print("\nAttempting direct agent call...")
    try:
        # Maybe the agent can be called more simply?
        from google.genai import types

        message = "What is 2+2? Answer with just the number."

        # Try calling the agent's run method if it exists
        if hasattr(agent, 'run'):
            print("Using agent.run()...")
            result = agent.run(message)
            print(f"Result: {result}")
        elif hasattr(agent, '__call__'):
            print("Agent is callable...")
            result = await agent(message)
            print(f"Result: {result}")
        else:
            print("Agent methods available:", [m for m in dir(agent) if not m.startswith('_')])

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_simple())
