# src/scheduler.py
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from src.database import init_db
from src.collectors.news_collector import fetch_and_store_news
from src.collectors.market_data_collector import fetch_and_store_market_data
from src.nlp.processor import process_articles_and_store_features
from src.analysis.historical_analyzer import analyze_historical_trends
# Import the new analyzer function
from src.analysis.today_analyzer import analyze_todays_impact

def main():
    """Initializes the DB and starts the scheduled jobs."""
    init_db()

    scheduler = BlockingScheduler(timezone="UTC")

    # --- Data Collection & Processing Jobs ---
    scheduler.add_job(fetch_and_store_news, 'interval', hours=1, id='news_fetcher')
    scheduler.add_job(fetch_and_store_market_data, 'cron', hour=1, minute=0, id='market_data_fetcher')
    scheduler.add_job(process_articles_and_store_features, 'interval', minutes=15, id='nlp_processor')

    # --- Analysis Jobs ---
    scheduler.add_job(analyze_historical_trends, 'cron', hour=2, minute=0, id='historical_analyzer')
    
    # --- NEW JOB FOR MILESTONE 4 ---
    # Schedule today's impact analysis to run shortly after the historical one
    scheduler.add_job(analyze_todays_impact, 'cron', hour=2, minute=15, id='today_analyzer')

    print("Scheduler starting...")

    try:
        # Run all jobs immediately on startup
        print("Running initial data collection, processing, and analysis jobs...")
        fetch_and_store_news()
        fetch_and_store_market_data()
        process_articles_and_store_features()
        analyze_historical_trends()
        analyze_todays_impact() # Run today's analysis on startup too
        print("Initial jobs complete. Scheduler is now running. Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")

if __name__ == '__main__':
    main()
