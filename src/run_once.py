# run_once.py
# Production script to run the complete Stockometry pipeline once
# Fetches real data from APIs, processes with NLP, analyzes, and saves to production database
# COMPLETELY INDEPENDENT - No scheduler dependencies

from src.database import init_db
from src.collectors.news_collector import fetch_and_store_news
from src.collectors.market_data_collector import fetch_and_store_market_data
from src.nlp.processor import process_articles_and_store_features
from src.analysis.synthesizer import synthesize_analyses
from src.output.processor import OutputProcessor
import time
import logging
import sys

# Configure logging with proper encoding for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rune_once.log', encoding='utf-8'),  # Fix: Add UTF-8 encoding
        logging.StreamHandler(sys.stdout)  # Fix: Use stdout instead of default stderr
    ]
)
logger = logging.getLogger(__name__)

def run_analysis_and_save():
    """
    Independent function to run analysis and save output.
    Extracted from scheduler to ensure complete independence.
    """
    logger.info("Running market analysis...")
    
    # Step 1: Generate the report object
    report_object = synthesize_analyses()
    
    # Step 2: If a report was successfully generated, process and save it
    if report_object:
        logger.info("Report generated successfully, processing and saving...")
        # Mark this as an ONDEMAND run
        processor = OutputProcessor(report_object, run_source="ONDEMAND")
        report_id = processor.process_and_save()
        
        if report_id:
            logger.info("Report saved to database (ONDEMAND)")
            
            # Optional: Export to JSON if needed
            logger.info("Exporting report to JSON format...")
            json_data = processor.export_to_json(report_id=report_id)
            if json_data:
                logger.info("JSON export successful")
                # Optionally save to file for backup
                processor.save_json_to_file(json_data, "exports")
            else:
                logger.warning("JSON export failed")
            
            return True
        else:
            logger.error("Failed to save report to database")
            return False
    else:
        logger.error("Synthesizer did not return a report")
        return False

def run_job_now():
    """
    Runs the complete Stockometry pipeline once:
    1. Initialize production database
    2. Fetch fresh news from NewsAPI
    3. Fetch fresh market data from yfinance
    4. Process articles with NLP
    5. Run analysis and save to production database
    
    COMPLETELY INDEPENDENT - No external dependencies on scheduler
    """
    logger.info("Starting Stockometry Production Run (Independent Mode)")
    start_time = time.time()
    
    try:
        # Step 1: Initialize production database
        logger.info("[STEP 1/5] Initializing production database...")
        init_db()
        logger.info("Database initialized successfully")
        
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
        
        # Step 5: Run analysis and save to production database (INDEPENDENT)
        logger.info("[STEP 5/5] Running analysis and saving to production database...")
        success = run_analysis_and_save()
        
        if not success:
            logger.error("Analysis and save step failed")
            return False
        
        # Calculate total runtime
        end_time = time.time()
        runtime = end_time - start_time
        
        logger.info(f"Production run completed successfully in {runtime:.2f} seconds")
        logger.info("Data has been saved to the production database")
        logger.info("JSON export available on demand using export_reports.py")
        logger.info("Run completed independently - no scheduler needed")
        
    except Exception as e:
        logger.error(f"Error during production run: {e}")
        logger.error("Production run failed - check logs for details")
        raise
    
    return True

if __name__ == '__main__':
    try:
        print("STOCKOMETRY INDEPENDENT PRODUCTION RUN")
        print("="*60)
        print("This script runs completely independently")
        print("No scheduler or external dependencies required")
        print("Fetches real data from APIs and saves to production DB")
        print("="*60)
        
        success = run_job_now()
        
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
        print("Check 'rune_once.log' for detailed error information")
