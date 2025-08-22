from apscheduler.schedulers.blocking import BlockingScheduler
from stockometry.database import init_db
from stockometry.core.collectors.news_collector import fetch_and_store_news
from stockometry.core.collectors.market_data_collector import fetch_and_store_market_data
from stockometry.core.nlp.processor import process_articles_and_store_features
from stockometry.core.analysis.synthesizer import synthesize_analyses
# Import the new OutputProcessor
from stockometry.core.output.processor import OutputProcessor

# Global scheduler instance for API control
_scheduler = None
_scheduler_running = False

def start_scheduler():
    """Start the Stockometry scheduler"""
    global _scheduler, _scheduler_running
    
    if _scheduler_running:
        return {"status": "already_running", "message": "Scheduler is already running"}
    
    try:
        init_db()
        _scheduler = BlockingScheduler(timezone="UTC")
        
        # --- Data Collection & Processing Jobs ---
        _scheduler.add_job(fetch_and_store_news, 'interval', hours=1, id='news_fetcher')
        _scheduler.add_job(fetch_and_store_market_data, 'cron', hour=1, minute=0, id='market_data_fetcher')
        _scheduler.add_job(process_articles_and_store_features, 'interval', minutes=15, id='nlp_processor')
        
        # --- Final Synthesis & Output Job ---
        _scheduler.add_job(run_synthesis_and_save, 'cron', hour=2, minute=30, id='final_report_job')
        
        # Start the scheduler in a separate thread
        import threading
        scheduler_thread = threading.Thread(target=_scheduler.start, daemon=True)
        scheduler_thread.start()
        
        _scheduler_running = True
        
        return {"status": "started", "message": "Scheduler started successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to start scheduler: {str(e)}"}

def stop_scheduler():
    """Stop the Stockometry scheduler"""
    global _scheduler, _scheduler_running
    
    if not _scheduler_running or not _scheduler:
        return {"status": "not_running", "message": "Scheduler is not running"}
    
    try:
        _scheduler.shutdown()
        _scheduler = None
        _scheduler_running = False
        
        return {"status": "stopped", "message": "Scheduler stopped successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to stop scheduler: {str(e)}"}

def get_scheduler_status():
    """Get current scheduler status"""
    global _scheduler, _scheduler_running
    
    if not _scheduler_running:
        return {"status": "stopped", "running": False}
    
    try:
        jobs = _scheduler.get_jobs()
        job_info = []
        for job in jobs:
            job_info.append({
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "status": "running",
            "running": True,
            "jobs": job_info,
            "total_jobs": len(jobs)
        }
    except Exception as e:
        return {
            "status": "error",
            "running": False,
            "error": str(e)
        }

def run_synthesis_and_save():
    """
    A wrapper function that runs the full analysis pipeline and then
    processes the output for saving. This is the main job for the scheduler.
    """
    # Step 1: Generate the report object. The synthesizer will print it to the console.
    report_object = synthesize_analyses()
    
    # Step 2: If a report was successfully generated, process and save it.
    if report_object:
        # Mark this as a SCHEDULED run
        processor = OutputProcessor(run_source="SCHEDULED")
        report_id = processor.process_and_save()
        
        if report_id:
            print("Scheduled report saved to database successfully")
            print("Report ID:", report_id)
            
            # Optional: Export to JSON if needed
            json_data = processor.export_to_json(report_id=report_id)
            if json_data:
                print("JSON export available on demand")
            else:
                print("JSON export failed")
        else:
            print("Failed to save scheduled report to database")
    else:
        print("Synthesizer did not return a report. Skipping output processing.")

def main():
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
    main()
