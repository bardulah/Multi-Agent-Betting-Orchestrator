#!/usr/bin/env python3
"""
Test script for ADK betting agents
"""

import sys
import os
import yaml

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from agents.internet_picks_agent import create_internet_picks_agent
from agents.data_driven_agent import create_data_driven_agent
from agents.synthesis_agent import create_synthesis_agent

def main():
    print("=" * 60)
    print("TESTING ADK BETTING AGENTS")
    print("=" * 60)

    # Load config
    with open('config/config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    print("\n[1/3] Testing Internet Picks Agent...")
    try:
        internet_agent = create_internet_picks_agent(config)
        print(f"✓ Internet Picks Agent created: {internet_agent.name}")
        print(f"  Model: {internet_agent.model}")
        print(f"  Tools: {len(internet_agent.tools)} tools")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

    print("\n[2/3] Testing Data-Driven Agent...")
    try:
        data_agent = create_data_driven_agent(config)
        print(f"✓ Data-Driven Agent created: {data_agent.name}")
        print(f"  Model: {data_agent.model}")
        print(f"  Tools: {len(data_agent.tools)} tools")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

    print("\n[3/3] Testing Synthesis Agent...")
    try:
        synthesis_agent = create_synthesis_agent(config)
        print(f"✓ Synthesis Agent created: {synthesis_agent.name}")
        print(f"  Model: {synthesis_agent.model}")
        print(f"  Tools: {len(synthesis_agent.tools)} tools")
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False

    print("\n" + "=" * 60)
    print("✓ ALL AGENTS CREATED SUCCESSFULLY!")
    print("=" * 60)

    # Test with a mock match (without API key)
    print("\n[BONUS] Testing agent wrapper initialization...")
    try:
        from agents.internet_picks_agent import InternetPicksAgent
        from agents.data_driven_agent import DataDrivenAgent
        from agents.synthesis_agent import SynthesisAgent

        internet_wrapper = InternetPicksAgent(config)
        print(f"✓ Internet Picks Wrapper initialized")

        data_wrapper = DataDrivenAgent(config)
        print(f"✓ Data-Driven Wrapper initialized")

        synthesis_wrapper = SynthesisAgent(config)
        print(f"✓ Synthesis Wrapper initialized")

        print("\n✓ ALL WRAPPERS INITIALIZED!")

    except Exception as e:
        print(f"✗ Wrapper test failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("TESTS COMPLETE!")
    print("=" * 60)
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
