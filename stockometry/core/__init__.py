"""
Stockometry Core - Shared business logic
Contains the main analysis pipeline that can be used by both CLI and FastAPI.
"""

import time
import logging
from .collectors.news_collector import fetch_and_store_news
from .collectors.market_data_collector import fetch_and_store_market_data
from .nlp.processor import process_articles_and_store_features
from .analysis.synthesizer import synthesize_analyses
from .output.processor import OutputProcessor
from ..database.connection import init_db

logger = logging.getLogger(__name__)

def run_stockometry_analysis(run_source: str = "ONDEMAND"):
    """
    Main analysis function - runs the complete Stockometry pipeline.
    This is the core function used by both CLI and FastAPI.
    
    Args:
        run_source: Source of the run - "ONDEMAND" or "SCHEDULED"
    
    Returns:
        bool: True if successful, False otherwise
    """
    from ..config import settings
    logger.info(f"Starting Stockometry Analysis (Source: {run_source}, Environment: {settings.environment})")
    logger.info(f"Using database: {settings.db_name_active}")
    start_time = time.time()
    
    try:
        # Step 1: Initialize database
        logger.info("[STEP 1/5] Initializing database...")
        init_db()  # Will automatically use the correct database based on environment
        logger.info(f"Database '{settings.db_name_active}' initialized successfully")
        
        # Step 2: Fetch fresh news from NewsAPI
        logger.info("[STEP 2/5] Fetching fresh news from NewsAPI...")
        fetch_and_store_news()
        logger.info("News collection completed")
        
        # Step 3: Fetch fresh market data from yfinance
        logger.info("[STEP 3/5] Fetching fresh market data from yfinance...")
        fetch_and_store_market_data()
        logger.info("Market data collection completed")
        
        # Step 4: Process articles with NLP
        logger.info("[STEP 4/5] Processing articles with NLP...")
        process_articles_and_store_features()
        logger.info("NLP processing completed")
        
        # Step 5: Run analysis and save to database
        logger.info("[STEP 5/5] Running analysis and saving to database...")
        report_object = synthesize_analyses()
        
        if report_object:
            logger.info("Report generated successfully, processing and saving...")
            processor = OutputProcessor(report_object, run_source=run_source)
            report_id = processor.process_and_save()
            
            if report_id:
                logger.info(f"Report saved to database (Source: {run_source})")
                
                # Optional: Export to JSON if needed
                logger.info("Exporting report to JSON format...")
                json_data = processor.export_to_json(report_id=report_id)
                if json_data:
                    logger.info("JSON export successful")
                    processor.save_json_to_file(json_data, "exports")
                else:
                    logger.warning("JSON export failed")
                
                # Calculate total runtime
                end_time = time.time()
                runtime = end_time - start_time
                
                logger.info(f"Analysis completed successfully in {runtime:.2f} seconds")
                return True
            else:
                logger.error("Failed to save report to database")
                return False
        else:
            logger.error("Synthesizer did not return a report")
            return False
            
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        logger.error("Analysis failed - check logs for details")
        raise
    
    return False

# Export core functions for easy access
__all__ = [
    "run_stockometry_analysis",
    "fetch_and_store_news",
    "fetch_and_store_market_data", 
    "process_articles_and_store_features",
    "synthesize_analyses"
]
