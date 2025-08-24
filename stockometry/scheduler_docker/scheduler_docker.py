"""
Scheduler Docker for Stockometry

A simplified scheduler designed specifically for Docker containers.
This scheduler reuses all existing core functionality without modification.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from stockometry.database import init_db
from stockometry.core.collectors.news_collector import fetch_and_store_news
from stockometry.core.core.collectors.market_data_collector import fetch_and_store_market_data
from stockometry.core.nlp.processor import process_articles_and_store_features
from stockometry.core.analysis.synthesizer import synthesize_analyses
from stockometry.core.output.processor import OutputProcessor
import logging
import os

# Configure logging for Docker scheduler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SchedulerDocker:
    """
    Docker-optimized scheduler for Stockometry.
    
    This scheduler is designed to run inside Docker containers and provides
    all the same functionality as the main scheduler but with Docker-specific
    optimizations and simplified management.
    """
    
    def __init__(self):
        """Initialize the Docker scheduler"""
        self._scheduler = None
        self._running = False
        self._initialized = False
        
    def _ensure_db_initialized(self):
        """Initialize database if not already done"""
        if not self._initialized:
            try:
                logger.info("Initializing database for Docker scheduler...")
                init_db()
                self._initialized = True
                logger.info("Database initialization complete")
            except Exception as e:
                logger.error(f"Database initialization failed: {str(e)}")
                raise
    
    def start(self):
        """Start the Docker scheduler"""
        if self._running:
            return {
                "status": "already_running",
                "message": "Docker scheduler is already running"
            }
        
        try:
            # Ensure database is initialized
            self._ensure_db_initialized()
            
            # Configure thread pool for Docker environment
            executors = {
                'default': ThreadPoolExecutor(
                    max_workers=4, 
                    thread_name_prefix="scheduler_docker"
                )
            }
            
            # Create scheduler with Docker-optimized settings
            self._scheduler = BackgroundScheduler(
                timezone="UTC",
                executors=executors,
                job_defaults={
                    'coalesce': False,
                    'max_instances': 1,
                    'misfire_grace_time': 300  # 5 minutes grace time
                },
                daemon=False  # Important for Docker containers
            )
            
            # Add all the scheduled jobs
            self._add_scheduled_jobs()
            
            # Start the scheduler
            self._scheduler.start()
            self._running = True
            
            logger.info("Docker scheduler started successfully")
            logger.info(f"Active jobs: {len(self._scheduler.get_jobs())}")
            
            return {
                "status": "started",
                "message": "Docker scheduler started successfully",
                "jobs_count": len(self._scheduler.get_jobs())
            }
            
        except Exception as e:
            logger.error(f"Failed to start Docker scheduler: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to start Docker scheduler: {str(e)}"
            }
    
    def _add_scheduled_jobs(self):
        """Add all scheduled jobs to the scheduler"""
        try:
            # Data Collection Jobs
            self._scheduler.add_job(
                fetch_and_store_news,
                'interval',
                hours=1,
                id='scheduler_docker_news_fetcher',
                name='News Collection'
            )
            
            self._scheduler.add_job(
                fetch_and_store_market_data,
                'cron',
                hour=1,
                minute=0,
                id='scheduler_docker_market_data_fetcher',
                name='Market Data Collection'
            )
            
            self._scheduler.add_job(
                process_articles_and_store_features,
                'interval',
                minutes=15,
                id='scheduler_docker_nlp_processor',
                name='NLP Processing'
            )
            
            # Final Synthesis Job
            self._scheduler.add_job(
                self._run_synthesis_and_save,
                'cron',
                hour=2,
                minute=30,
                id='scheduler_docker_final_report_job',
                name='Final Report Generation'
            )
            
            # Heartbeat job to keep scheduler alive in Docker
            self._scheduler.add_job(
                self._heartbeat,
                'interval',
                minutes=5,
                id='scheduler_docker_heartbeat',
                name='Scheduler Heartbeat'
            )
            
            logger.info("All scheduled jobs added successfully")
            
        except Exception as e:
            logger.error(f"Failed to add scheduled jobs: {str(e)}")
            raise
    
    def _run_synthesis_and_save(self):
        """Run the synthesis and save job"""
        try:
            logger.info("Starting scheduled synthesis and save job...")
            
            # Generate the report object
            report_object = synthesize_analyses()
            
            # Process and save if report was generated
            if report_object:
                processor = OutputProcessor(report_object, run_source="SCHEDULER_DOCKER")
                report_id = processor.process_and_save()
                
                if report_id:
                    logger.info(f"Scheduler Docker scheduled report saved successfully. Report ID: {report_id}")
                else:
                    logger.error("Failed to save Scheduler Docker scheduled report to database")
            else:
                logger.warning("Synthesizer did not return a report. Skipping output processing.")
                
        except Exception as e:
            logger.error(f"Error in Scheduler Docker scheduled synthesis job: {str(e)}")
            raise
    
    def _heartbeat(self):
        """Heartbeat function to keep scheduler alive in Docker"""
        logger.info("Scheduler Docker heartbeat - keeping alive")
    
    def stop(self):
        """Stop the Docker scheduler"""
        if not self._running or not self._scheduler:
            return {
                "status": "not_running",
                "message": "Docker scheduler is not running"
            }
        
        try:
            logger.info("Stopping Docker scheduler...")
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            self._running = False
            
            logger.info("Docker scheduler stopped successfully")
            return {
                "status": "stopped",
                "message": "Docker scheduler stopped successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to stop Docker scheduler: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to stop Docker scheduler: {str(e)}"
            }
    
    def restart(self):
        """Restart the Docker scheduler"""
        try:
            logger.info("Restarting Docker scheduler...")
            stop_result = self.stop()
            if stop_result["status"] in ["stopped", "not_running"]:
                return self.start()
            else:
                return {
                    "status": "error",
                    "message": f"Failed to stop scheduler before restart: {stop_result['message']}"
                }
        except Exception as e:
            logger.error(f"Failed to restart Docker scheduler: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to restart Docker scheduler: {str(e)}"
            }
    
    def get_status(self):
        """Get current Docker scheduler status"""
        if not self._running or not self._scheduler:
            return {
                "status": "stopped",
                "running": False,
                "scheduler_type": "scheduler_docker"
            }
        
        try:
            # Verify scheduler is actually running
            if not self._scheduler.running:
                logger.warning("Docker scheduler marked as running but not actually running")
                self._running = False
                return {
                    "status": "stopped",
                    "running": False,
                    "error": "Scheduler thread died",
                    "scheduler_type": "scheduler_docker"
                }
            
            jobs = self._scheduler.get_jobs()
            job_info = []
            for job in jobs:
                job_info.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger)
                })
            
            return {
                "status": "running",
                "running": True,
                "scheduler_type": "scheduler_docker",
                "jobs": job_info,
                "total_jobs": len(jobs)
            }
            
        except Exception as e:
            logger.error(f"Error getting Docker scheduler status: {str(e)}")
            self._running = False
            self._scheduler = None
            return {
                "status": "error",
                "running": False,
                "error": str(e),
                "scheduler_type": "scheduler_docker"
            }
    
    def is_running(self):
        """Check if scheduler is running"""
        return self._running and self._scheduler and self._scheduler.running
