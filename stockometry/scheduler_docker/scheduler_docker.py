"""
Scheduler Docker for Stockometry

A simplified scheduler designed specifically for Docker containers.
This scheduler reuses all existing core functionality without modification.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from stockometry.database import init_db
from stockometry.core.collectors.news_collector import fetch_and_store_news
from stockometry.core.collectors.market_data_collector import fetch_and_store_market_data
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
        print("Scheduler Docker: Initialized")
        
    def _ensure_db_initialized(self):
        """Initialize database if not already done - respects environment from settings.yml"""
        if not self._initialized:
            try:
                print("Scheduler Docker: Initializing database...")
                logger.info("Initializing database for Scheduler Docker...")
                # This will automatically use the correct database based on environment in settings.yml
                # - If environment=staging: uses stockometry_staging
                # - If environment=production: uses stockometry
                init_db()
                self._initialized = True
                print("Scheduler Docker: Database initialization complete")
                logger.info("Database initialization complete")
            except Exception as e:
                print(f"Scheduler Docker: Database initialization failed - {str(e)}")
                logger.error(f"Database initialization failed: {str(e)}")
                raise
    
    def start(self):
        """Start the Docker scheduler"""
        if self._running:
            print("Scheduler Docker: Already running")
            return {
                "status": "already_running",
                "message": "Scheduler Docker is already running"
            }
        
        try:
            print("Scheduler Docker: Starting...")
            # Ensure database is initialized (respects environment from settings.yml)
            self._ensure_db_initialized()
            
            # Create scheduler with simple single-threaded settings
            self._scheduler = BackgroundScheduler(
                timezone="UTC",
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
            
            print("Scheduler Docker: Started successfully")
            print(f"Scheduler Docker: Active jobs: {len(self._scheduler.get_jobs())}")
            logger.info("Scheduler Docker started successfully")
            logger.info(f"Active jobs: {len(self._scheduler.get_jobs())}")
            
            return {
                "status": "started",
                "message": "Scheduler Docker started successfully",
                "jobs_count": len(self._scheduler.get_jobs())
            }
            
        except Exception as e:
            print(f"Scheduler Docker: Failed to start - {str(e)}")
            logger.error(f"Failed to start Scheduler Docker: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to start Scheduler Docker: {str(e)}"
            }
    
    def _add_scheduled_jobs(self):
        """Add all scheduled jobs to the scheduler"""
        try:
            print("Scheduler Docker: Adding scheduled jobs...")
            
            # Data Collection Jobs
            self._scheduler.add_job(
                fetch_and_store_news,
                'interval',
                hours=1,
                id='scheduler_docker_news_fetcher',
                name='News Collection'
            )
            print("Scheduler Docker: Added News Collection job (every hour)")
            
            self._scheduler.add_job(
                fetch_and_store_market_data,
                'cron',
                hour=1,
                minute=0,
                id='scheduler_docker_market_data_fetcher',
                name='Market Data Collection'
            )
            print("Scheduler Docker: Added Market Data Collection job (daily at 1:00 AM)")
            
            # NLP Processing - Changed to run every hour, 5 minutes after news
            self._scheduler.add_job(
                process_articles_and_store_features,
                'cron',
                minute=5,  # 5 minutes past every hour
                id='scheduler_docker_nlp_processor',
                name='NLP Processing'
            )
            print("Scheduler Docker: Added NLP Processing job (every hour at 5 minutes past)")
            
            # Schedule daily reports at market-aligned times
            # 06:00 UTC = US pre-market, European morning
            # 14:00 UTC = US morning trading, European midday  
            # 22:00 UTC = US market close, complete daily coverage
            self._scheduler.add_job(
                func=self._run_synthesis_and_save,
                trigger='cron',
                hour=6,
                minute=0,
                id='daily_report_morning',
                name='Daily Report - Morning (Pre-market)',
                replace_existing=True
            )
            
            self._scheduler.add_job(
                func=self._run_synthesis_and_save,
                trigger='cron',
                hour=14,
                minute=0,
                id='daily_report_midday',
                name='Daily Report - Midday (Trading)',
                replace_existing=True
            )
            
            self._scheduler.add_job(
                func=self._run_synthesis_and_save,
                trigger='cron',
                hour=22,
                minute=0,
                id='daily_report_evening',
                name='Daily Report - Evening (Market Close)',
                replace_existing=True
            )
            
            print("Scheduler Docker: All scheduled jobs added successfully")
            logger.info("All scheduled jobs added successfully")
            
        except Exception as e:
            print(f"Scheduler Docker: Failed to add scheduled jobs - {str(e)}")
            logger.error(f"Failed to add scheduled jobs: {str(e)}")
            raise
    
    def _run_synthesis_and_save(self):
        """Run the synthesis and save job"""
        try:
            print("Scheduler Docker: Starting scheduled synthesis and save job...")
            logger.info("Starting scheduled synthesis and save job...")
            
            # Generate the report object
            report_object = synthesize_analyses()
            
            # Process and save if report was generated
            if report_object:
                processor = OutputProcessor(report_object, run_source="SCHEDULER_DOCKER")
                report_id = processor.process_and_save()
                
                if report_id:
                    print(f"Scheduler Docker: Scheduled report saved successfully. Report ID: {report_id}")
                    logger.info(f"Scheduler Docker scheduled report saved successfully. Report ID: {report_id}")
                else:
                    print("Scheduler Docker: Failed to save scheduled report to database")
                    logger.error("Failed to save Scheduler Docker scheduled report to database")
            else:
                print("Scheduler Docker: No report generated, skipping output processing")
                logger.warning("Synthesizer did not return a report. Skipping output processing.")
                
        except Exception as e:
            print(f"Scheduler Docker: Error in scheduled synthesis job - {str(e)}")
            logger.error(f"Error in Scheduler Docker scheduled synthesis job: {str(e)}")
            raise
    
    def stop(self):
        """Stop the Docker scheduler"""
        if not self._running or not self._scheduler:
            print("Scheduler Docker: Not running")
            return {
                "status": "not_running",
                "message": "Scheduler Docker is not running"
            }
        
        try:
            print("Scheduler Docker: Stopping...")
            logger.info("Stopping Scheduler Docker...")
            self._scheduler.shutdown(wait=False)
            self._scheduler = None
            self._running = False
            
            print("Scheduler Docker: Stopped successfully")
            logger.info("Scheduler Docker stopped successfully")
            return {
                "status": "stopped",
                "message": "Scheduler Docker stopped successfully"
            }
            
        except Exception as e:
            print(f"Scheduler Docker: Failed to stop - {str(e)}")
            logger.error(f"Failed to stop Scheduler Docker: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to stop Scheduler Docker: {str(e)}"
            }
    
    def restart(self):
        """Restart the Docker scheduler"""
        try:
            print("Scheduler Docker: Restarting...")
            logger.info("Restarting Scheduler Docker...")
            stop_result = self.stop()
            if stop_result["status"] in ["stopped", "not_running"]:
                return self.start()
            else:
                return {
                    "status": "error",
                    "message": f"Failed to stop scheduler before restart: {stop_result['message']}"
                }
        except Exception as e:
            print(f"Scheduler Docker: Failed to restart - {str(e)}")
            logger.error(f"Failed to restart Scheduler Docker: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to restart Scheduler Docker: {str(e)}"
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
                print("Scheduler Docker: Marked as running but not actually running")
                logger.warning("Scheduler Docker marked as running but not actually running")
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
            print(f"Scheduler Docker: Error getting status - {str(e)}")
            logger.error(f"Error getting Scheduler Docker status: {str(e)}")
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
