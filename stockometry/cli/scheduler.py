#!/usr/bin/env python3
"""
Stockometry CLI - Scheduler
Standalone script to run the Stockometry scheduler.
Equivalent to the original scheduler.py but using the new modular structure.
"""

from apscheduler.schedulers.blocking import BlockingScheduler
from ..database import init_db
from ..core.collectors.news_collector import fetch_and_store_news
from ..core.collectors.market_data_collector import fetch_and_store_market_data
from ..core.nlp.processor import process_articles_and_store_features
from ..core import run_stockometry_analysis

def run_synthesis_and_save():
    """
    A wrapper function that runs the full analysis pipeline and then
    processes the output for saving. This is the main job for the scheduler.
    """
    # Step 1: Generate the report object. The synthesizer will print it to the console.
    report_object = run_stockometry_analysis(run_source="SCHEDULED")
    
    if report_object:
        print("Scheduled report completed successfully")
    else:
        print("Scheduled report failed")

def start_scheduler():
    """Initializes the DB and starts the scheduled jobs."""
    init_db()

    scheduler = BlockingScheduler(timezone="UTC")

    # --- Data Collection & Processing Jobs ---
    scheduler.add_job(fetch_and_store_news, 'interval', hours=1, id='news_fetcher')
    scheduler.add_job(fetch_and_store_market_data, 'cron', hour=1, minute=0, id='market_data_fetcher')
    scheduler.add_job(process_articles_and_store_features, 'interval', minutes=15, id='nlp_processor')

    # --- Final Synthesis & Output Job ---
    # This single job now handles the entire final analysis and saving process.
    scheduler.add_job(run_synthesis_and_save, 'cron', hour=2, minute=30, id='final_report_job')

    print("Scheduler starting...")

    try:
        # Run the final end-to-end job on startup
        print("Running initial end-to-end analysis and output processing...")
        run_synthesis_and_save()
        print("Initial job complete. Scheduler is now running. Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")

if __name__ == '__main__':
    start_scheduler()
