#!/usr/bin/env python3
"""
Main entry point for the Multi-Agent Betting System
"""

import sys
import os

# Add agents directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from agents.orchestrator import main

if __name__ == '__main__':
    main()
