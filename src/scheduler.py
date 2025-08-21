# src/scheduler.py
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from src.database import init_db
from src.collectors.news_collector import fetch_and_store_news
from src.collectors.market_data_collector import fetch_and_store_market_data
from src.nlp.processor import process_articles_and_store_features
# Import the new analyzer function
from src.analysis.historical_analyzer import analyze_historical_trends

def main():
    """Initializes the DB and starts the scheduled jobs."""
    init_db()

    scheduler = BlockingScheduler(timezone="UTC")

    # --- Data Collection Jobs ---
    scheduler.add_job(fetch_and_store_news, 'interval', hours=1, id='news_fetcher')
    scheduler.add_job(fetch_and_store_market_data, 'cron', hour=1, minute=0, id='market_data_fetcher')
    
    # --- Processing Job ---
    scheduler.add_job(process_articles_and_store_features, 'interval', minutes=15, id='nlp_processor')

    # --- NEW JOB FOR MILESTONE 3 ---
    # Schedule historical analysis to run once a day (e.g., at 2:00 AM UTC)
    scheduler.add_job(analyze_historical_trends, 'cron', hour=2, minute=0, id='historical_analyzer')

    print("Scheduler starting...")

    try:
        # Run all jobs immediately on startup
        print("Running initial data collection, processing, and analysis jobs...")
        fetch_and_store_news()
        fetch_and_store_market_data()
        process_articles_and_store_features()
        analyze_historical_trends() # Run analysis on startup too
        print("Initial jobs complete. Scheduler is now running. Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")

if __name__ == '__main__':
    main()
