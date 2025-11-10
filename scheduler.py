#!/usr/bin/env python3
"""
Scheduler for daily automated execution of the betting system
"""

import schedule
import time
import yaml
import logging
from datetime import datetime
from pathlib import Path
import sys

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent / 'agents'))

from agents.orchestrator import BettingSystemOrchestrator
from agents.utils.logging_config import setup_logging, get_logger


def run_betting_system():
    """Execute the betting system"""
    logger = get_logger(__name__)
    logger.info(f"\n{'='*60}")
    logger.info(f"SCHEDULED EXECUTION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"{'='*60}\n")

    try:
        orchestrator = BettingSystemOrchestrator('config/config.yaml')
        orchestrator.run()
    except Exception as e:
        logger.error(f"Scheduled execution failed: {e}", exc_info=True)


def main():
    """Main scheduler function"""
    # Load configuration
    config_path = Path('config/config.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Setup logging
    setup_logging(config)
    logger = get_logger(__name__)

    # Get schedule settings
    schedule_config = config.get('schedule', {})
    enabled = schedule_config.get('enabled', True)
    run_time = schedule_config.get('time', '09:00')

    if not enabled:
        logger.info("Scheduling is disabled in configuration")
        return

    logger.info(f"Multi-Agent Betting System Scheduler started")
    logger.info(f"Scheduled to run daily at {run_time}")
    logger.info("Press Ctrl+C to stop")

    # Schedule daily execution
    schedule.every().day.at(run_time).do(run_betting_system)

    # Also run immediately on startup
    logger.info("\nRunning initial execution...")
    run_betting_system()

    # Keep the scheduler running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("\nScheduler stopped by user")


if __name__ == '__main__':
    main()
