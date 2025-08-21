# src/scheduler.py
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from src.database import init_db
from src.collectors.news_collector import fetch_and_store_news
from src.collectors.market_data_collector import fetch_and_store_market_data
# Import the new processor function
from src.nlp.processor import process_articles_and_store_features

def main():
    """Initializes the DB and starts the scheduled jobs."""
    # Initialize the database first
    init_db()

    scheduler = BlockingScheduler(timezone="UTC")

    # Schedule news fetching every hour
    scheduler.add_job(fetch_and_store_news, 'interval', hours=1, id='news_fetcher')

    # Schedule market data fetching once a day at 01:00 UTC
    scheduler.add_job(fetch_and_store_market_data, 'cron', hour=1, minute=0, id='market_data_fetcher')
    
    # --- NEW JOB FOR MILESTONE 2 ---
    # Schedule NLP processing to run every 15 minutes
    # It will process articles collected by the news_fetcher
    scheduler.add_job(process_articles_and_store_features, 'interval', minutes=15, id='nlp_processor')

    print("Scheduler starting...")

    try:
        # Run jobs immediately on startup before starting the schedule
        print("Running initial data collection and processing jobs...")
        fetch_and_store_news()
        fetch_and_store_market_data()
        process_articles_and_store_features() # Run NLP processor on startup too
        print("Initial jobs complete. Scheduler is now running. Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")

if __name__ == '__main__':
    main()
