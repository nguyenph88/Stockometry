# src/scheduler.py
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from src.database import init_db
from src.collectors.news_collector import fetch_and_store_news
from src.collectors.market_data_collector import fetch_and_store_market_data
from src.nlp.processor import process_articles_and_store_features
from src.analysis.historical_analyzer import analyze_historical_trends
from src.analysis.today_analyzer import analyze_todays_impact
# Import the new synthesizer function
from src.analysis.synthesizer import synthesize_analyses

def main():
    """Initializes the DB and starts the scheduled jobs."""
    init_db()

    scheduler = BlockingScheduler(timezone="UTC")

    # --- Data Collection & Processing Jobs ---
    scheduler.add_job(fetch_and_store_news, 'interval', hours=1, id='news_fetcher')
    scheduler.add_job(fetch_and_store_market_data, 'cron', hour=1, minute=0, id='market_data_fetcher')
    scheduler.add_job(process_articles_and_store_features, 'interval', minutes=15, id='nlp_processor')

    # --- Analysis Jobs ---
    # We will remove the individual analyzers from the schedule
    # as the synthesizer will call them directly.
    
    # --- NEW JOB FOR MILESTONE 5 ---
    # Schedule the final synthesis to run once a day, producing the complete report
    scheduler.add_job(synthesize_analyses, 'cron', hour=2, minute=30, id='synthesizer')

    print("Scheduler starting...")

    try:
        # Run the final synthesizer on startup
        print("Running initial end-to-end analysis...")
        synthesize_analyses()
        print("Initial analysis complete. Scheduler is now running. Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")

if __name__ == '__main__':
    main()
