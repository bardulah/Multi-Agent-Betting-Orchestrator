#!/usr/bin/env python3
"""
Main entry point for the Multi-Agent Betting System
"""

import sys
import os

# Add current directory to path (for agents, utils, and other modules)
sys.path.insert(0, os.path.dirname(__file__))

from agents.orchestrator import main

if __name__ == '__main__':
    main()
