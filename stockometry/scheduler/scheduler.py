from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from stockometry.database import init_db
from stockometry.core.collectors.news_collector import fetch_and_store_news
from stockometry.core.collectors.market_data_collector import fetch_and_store_market_data
from stockometry.core.nlp.processor import process_articles_and_store_features
from stockometry.core.analysis.synthesizer import synthesize_analyses
from stockometry.core.output.processor import OutputProcessor
import logging

# Configure logging for scheduler
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global scheduler instance for API control
_scheduler = None
_scheduler_running = False

def shutdown_scheduler():
    """Graceful shutdown for Docker environments"""
    global _scheduler, _scheduler_running
    
    if _scheduler and _scheduler_running:
        logger.info("Shutting down scheduler gracefully...")
        try:
            _scheduler.shutdown(wait=False)
            _scheduler = None
            _scheduler_running = False
            logger.info("Scheduler shutdown complete")
        except Exception as e:
            logger.error(f"Error during scheduler shutdown: {str(e)}")
    
    return {"status": "shutdown", "message": "Scheduler shutdown complete"}

def start_scheduler():
    """Start the Stockometry scheduler"""
    global _scheduler, _scheduler_running
    
    if _scheduler_running:
        return {"status": "already_running", "message": "Scheduler is already running"}
    
    try:
        init_db()
        
        # Configure thread pool for background execution
        executors = {
            'default': ThreadPoolExecutor(max_workers=4)
        }
        
        # Use BackgroundScheduler for Docker compatibility
        _scheduler = BackgroundScheduler(
            timezone="UTC",
            executors=executors,
            job_defaults={'coalesce': False, 'max_instances': 1}
        )
        
        # --- Data Collection & Processing Jobs ---
        _scheduler.add_job(fetch_and_store_news, 'interval', hours=1, id='news_fetcher')
        _scheduler.add_job(fetch_and_store_market_data, 'cron', hour=1, minute=0, id='market_data_fetcher')
        _scheduler.add_job(process_articles_and_store_features, 'interval', minutes=15, id='nlp_processor')
        
        # --- Final Synthesis & Output Job ---
        _scheduler.add_job(run_synthesis_and_save, 'cron', hour=2, minute=30, id='final_report_job')
        
        # Start the background scheduler (non-blocking)
        _scheduler.start()
        _scheduler_running = True
        
        logger.info("Scheduler started successfully in background mode")
        return {"status": "started", "message": "Scheduler started successfully in background mode"}
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}")
        return {"status": "error", "message": f"Failed to start scheduler: {str(e)}"}

def stop_scheduler():
    """Stop the Stockometry scheduler"""
    global _scheduler, _scheduler_running
    
    if not _scheduler_running or not _scheduler:
        return {"status": "not_running", "message": "Scheduler is not running"}
    
    try:
        _scheduler.shutdown(wait=False)  # Don't wait for jobs to complete
        _scheduler = None
        _scheduler_running = False
        
        logger.info("Scheduler stopped successfully")
        return {"status": "stopped", "message": "Scheduler stopped successfully"}
    except Exception as e:
        logger.error(f"Failed to stop scheduler: {str(e)}")
        return {"status": "error", "message": f"Failed to stop scheduler: {str(e)}"}

def get_scheduler_status():
    """Get current scheduler status"""
    global _scheduler, _scheduler_running
    
    if not _scheduler_running or not _scheduler:
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
        
        logger.info(f"Scheduler status: {len(jobs)} jobs running")
        return {
            "status": "running",
            "running": True,
            "jobs": job_info,
            "total_jobs": len(jobs)
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
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
    try:
        logger.info("Starting scheduled synthesis and save job...")
        
        # Step 1: Generate the report object
        report_object = synthesize_analyses()
        
        # Step 2: If a report was successfully generated, process and save it.
        if report_object:
            # Mark this as a SCHEDULED run
            processor = OutputProcessor(report_object, run_source="SCHEDULED")
            report_id = processor.process_and_save()
            
            if report_id:
                logger.info(f"Scheduled report saved to database successfully. Report ID: {report_id}")
            else:
                logger.error("Failed to save scheduled report to database")
        else:
            logger.warning("Synthesizer did not return a report. Skipping output processing.")
            
    except Exception as e:
        logger.error(f"Error in scheduled synthesis job: {str(e)}")
        raise

def main():
    """Standalone scheduler mode - for testing outside of FastAPI"""
    try:
        logger.info("Starting standalone scheduler...")
        init_db()
        
        # Use the same scheduler configuration as the API version
        start_result = start_scheduler()
        
        if start_result["status"] == "started":
            logger.info("Standalone scheduler started successfully")
            logger.info("Press Ctrl+C to stop the scheduler")
            
            # Keep the main thread alive
            try:
                while _scheduler_running:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received shutdown signal...")
                stop_scheduler()
                logger.info("Standalone scheduler stopped")
        else:
            logger.error(f"Failed to start standalone scheduler: {start_result}")
            
    except Exception as e:
        logger.error(f"Error in standalone scheduler: {str(e)}")
        raise

if __name__ == '__main__':
    main()
