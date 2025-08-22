# src/scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from src.database import init_db
from src.collectors.news_collector import fetch_and_store_news
from src.collectors.market_data_collector import fetch_and_store_market_data
from src.nlp.processor import process_articles_and_store_features
from src.analysis.synthesizer import synthesize_analyses
from src.output.processor import OutputProcessor

def run_synthesis_and_save():
    """
    Runs the full analysis pipeline and then processes the structured output object.
    """
    report_object = synthesize_analyses()
    if report_object:
        processor = OutputProcessor(report_object)
        processor.process_and_save()
    else:
        print("Synthesizer did not return a report. Skipping output processing.")

def main():
    init_db()
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(fetch_and_store_news, 'interval', hours=1, id='news_fetcher')
    scheduler.add_job(fetch_and_store_market_data, 'cron', hour=1, minute=0, id='market_data_fetcher')
    scheduler.add_job(process_articles_and_store_features, 'interval', minutes=15, id='nlp_processor')
    scheduler.add_job(run_synthesis_and_save, 'cron', hour=2, minute=30, id='final_report_job')
    print("Scheduler starting...")
    try:
        print("Running initial end-to-end analysis and output processing...")
        run_synthesis_and_save()
        print("Initial job complete. Scheduler is now running. Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler shut down.")

if __name__ == '__main__':
    main()
