#!/usr/bin/env python3
"""
Stockometry CLI - Run Once
Standalone script to run the complete Stockometry pipeline once.
"""

import sys
import logging
from ..core import run_stockometry_analysis

# Configure logging with console output only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_analysis_and_save():
    """
    Runs the complete Stockometry pipeline once and saves results.
    This is the main function for CLI usage.
    """
    from ..config import settings
    logger.info(f"Starting Stockometry Production Run (Environment: {settings.environment})")
    logger.info(f"Using database: {settings.db_name_active}")
    
    try:
        success = run_stockometry_analysis(run_source="ONDEMAND")
        
        if success:
            logger.info("Production run completed successfully")
            return True
        else:
            logger.error("Production run failed")
            return False
            
    except Exception as e:
        logger.error(f"Error during production run: {e}")
        logger.error("Production run failed - check logs for details")
        raise
    
    return False

def run_once():
    """
    Runs the complete Stockometry pipeline once.
    This is the standalone equivalent of the original run_once.py
    """
    return run_analysis_and_save()

if __name__ == '__main__':
    try:
        print("STOCKOMETRY INDEPENDENT PRODUCTION RUN")
        print("="*60)
        print("This script runs completely independently")
        print("No scheduler or external dependencies required")
        print("Fetches real data from APIs and saves to production DB")
        print("="*60)
        
        success = run_once()
        
        if success:
            print("\n" + "="*60)
            print("STOCKOMETRY PRODUCTION RUN COMPLETED SUCCESSFULLY!")
            print("="*60)
            print("Fresh data collected from APIs")
            print("Articles processed with NLP")
            print("Market analysis completed")
            print("Results saved to production database")
            print("JSON export available on demand using export_reports.py")
            print("Run completed independently - no scheduler needed")
            print("="*60)
        else:
            print("\nProduction run failed - check logs for details")
            
    except KeyboardInterrupt:
        print("\nProduction run interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        print("Check console output for detailed error information")
