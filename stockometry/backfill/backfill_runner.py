"""
Backfill Runner - Main Orchestration

This module handles the complete backfill process for missing daily reports.
"""

import logging
from datetime import datetime, timezone, timedelta, time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from ..database import get_db_connection
from ..config import settings
from .config import BackfillConfig
from .report_analyzer import ReportAnalyzer, ReportAnalysis, MissingReport

logger = logging.getLogger(__name__)

@dataclass
class BackfillProgress:
    """Simple progress tracking"""
    day_date: datetime.date
    status: str  # 'pending', 'collecting', 'processing', 'complete', 'failed'
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class BackfillRunner:
    """Orchestrates the complete backfill process"""
    
    def __init__(self, config: BackfillConfig = None):
        """Initialize the backfill runner"""
        self.config = config or BackfillConfig()
        self.analyzer = ReportAnalyzer(self.config)
        self.progress: List[BackfillProgress] = []
        
        logger.info(f"BackfillRunner initialized with config: {self.config.to_dict()}")
        logger.info(f"Database Environment: {settings.environment}")
        logger.info(f"Active Database: {settings.db_name_active}")
    
    def _validate_database_environment(self):
        """Validate that we're working with the correct database environment"""
        logger.info(f"Validating database environment...")
        
        try:
            # Get current database connection info
            db_name = settings.db_name_active
            environment = settings.environment
            host = settings.db_host
            port = settings.db_port
            
            logger.info(f"  Environment: {environment}")
            logger.info(f"  Active Database: {db_name}")
            logger.info(f"  Host: {host}:{port}")
            
            # Test database connection using context manager
            with get_db_connection() as conn:
                if conn:
                    # Get database name from connection
                    cursor = conn.cursor()
                    cursor.execute("SELECT current_database();")
                    current_db = cursor.fetchone()[0]
                    cursor.close()
                    
                    logger.info(f"  Connected to database: {current_db}")
                    
                    if current_db != db_name:
                        logger.warning(f"  ⚠️  Warning: Connected to {current_db} but expected {db_name}")
                    else:
                        logger.info(f"  ✅ Database connection validated successfully")
                        
                else:
                    logger.error(f"  ❌ Failed to establish database connection")
                    raise Exception("Database connection failed")
                
        except Exception as e:
            logger.error(f"Database validation failed: {str(e)}")
            raise Exception(f"Database environment validation failed: {str(e)}")
    
    def run_backfill(self, start_date: Optional[datetime.date] = None, 
                     end_date: Optional[datetime.date] = None,
                     dry_run: bool = False) -> Dict[str, Any]:
        """
        Run the complete backfill process
        
        Args:
            start_date: Start date for backfill (defaults to lookback_days ago)
            end_date: End date for backfill (defaults to today)
            dry_run: If True, only show what would be processed
            
        Returns:
            Dictionary with backfill results and status
        """
        try:
            logger.info("="*60)
            logger.info("BACKFILL PROCESS STARTING")
            logger.info("="*60)
            
            # Validate database environment first
            self._validate_database_environment()
            
            # Determine date range
            if end_date is None:
                end_date = datetime.now(timezone.utc).date()
            
            if start_date is None:
                start_date = end_date - timedelta(days=self.config.lookback_days - 1)
            
            logger.info(f"Backfill range: {start_date} to {end_date}")
            logger.info(f"Total Days: {(end_date - start_date).days + 1}")
            
            if dry_run:
                return self._dry_run_backfill(start_date, end_date)
            
            # Initialize progress tracking
            self._initialize_progress(start_date, end_date)
            
            # Phase 1: Data Collection
            logger.info("-"*50)
            logger.info("PHASE 1: DATA COLLECTION")
            logger.info("-"*50)
            self._collect_data_for_all_days()
            
            # Phase 2: Report Generation
            logger.info("-"*50)
            logger.info("PHASE 2: REPORT GENERATION")
            logger.info("-"*50)
            self._generate_reports_for_all_days()
            
            # Final status
            logger.info("="*60)
            logger.info("BACKFILL PROCESS COMPLETED")
            logger.info("="*60)
            return self._get_final_status()
            
        except Exception as e:
            logger.error("="*60)
            logger.error("BACKFILL PROCESS FAILED")
            logger.error("="*60)
            logger.error(f"Backfill process failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "progress": [p.__dict__ for p in self.progress]
            }
    
    def _dry_run_backfill(self, start_date: datetime.date, end_date: datetime.date) -> Dict[str, Any]:
        """Show what would be processed without actually doing it"""
        logger.info("Running dry-run backfill")
        
        # Get missing reports
        analysis = self.analyzer.analyze_reports(start_date, end_date)
        
        if not analysis.missing_reports:
            return {
                "status": "dry_run",
                "message": "No missing reports found - nothing to backfill",
                "coverage": f"{analysis.coverage_percentage:.1f}%"
            }
        
        # Group by date
        reports_by_date = {}
        for missing in analysis.missing_reports:
            date_str = missing.date.isoformat()
            if date_str not in reports_by_date:
                reports_by_date[date_str] = []
            reports_by_date[date_str].append({
                "time": missing.expected_time.strftime("%H:%M"),
                "type": missing.report_type
            })
        
        return {
            "status": "dry_run",
            "message": f"Would process {len(analysis.missing_reports)} missing reports",
            "coverage": f"{analysis.coverage_percentage:.1f}%",
            "days_to_process": len(reports_by_date),
            "reports_by_date": reports_by_date,
            "total_missing": len(analysis.missing_reports)
        }
    
    def _initialize_progress(self, start_date: datetime.date, end_date: datetime.date):
        """Initialize simple progress tracking for all days"""
        self.progress = []
        current_date = start_date
        
        while current_date <= end_date:
            progress = BackfillProgress(
                day_date=current_date,
                status='pending'
            )
            self.progress.append(progress)
            current_date += timedelta(days=1)
        
        logger.info(f"Initialized progress tracking for {len(self.progress)} days")
    
    def _collect_data_for_all_days(self):
        """Collect data for all days sequentially"""
        total_days = len(self.progress)
        
        for day_index, progress in enumerate(self.progress):
            try:
                logger.info(f"Processing Day {day_index + 1}/{total_days}: {progress.day_date}")
                
                progress.status = 'collecting'
                progress.started_at = datetime.now(timezone.utc)
                
                # Collect data for this day
                self._collect_data_for_day(progress.day_date, day_index, total_days)
                
                progress.status = 'complete'
                progress.completed_at = datetime.now(timezone.utc)
                
                logger.info(f"Data collection complete for {progress.day_date}")
                
            except Exception as e:
                progress.status = 'failed'
                progress.error_message = str(e)
                logger.error(f"Data collection failed for {progress.day_date}: {str(e)}")
                # Continue with next day instead of failing completely
    
    def _generate_reports_for_all_days(self):
        """Generate reports for all days sequentially"""
        total_days = len(self.progress)
        
        for day_index, progress in enumerate(self.progress):
            if progress.status == 'failed':
                logger.warning(f"Skipping report generation for {progress.day_date} due to data collection failure")
                continue
                
            try:
                logger.info(f"Processing Day {day_index + 1}/{total_days}: {progress.day_date}")
                
                progress.status = 'processing'
                progress.started_at = datetime.now(timezone.utc)
                
                # Generate reports for this day
                self._generate_reports_for_day(progress.day_date, day_index, total_days)
                
                progress.status = 'complete'
                progress.completed_at = datetime.now(timezone.utc)
                
                logger.info(f"Report generation complete for {progress.day_date}")
                
            except Exception as e:
                progress.status = 'failed'
                progress.error_message = str(e)
                logger.error(f"Report generation failed for {progress.day_date}: {str(e)}")
                # Continue with next day instead of failing completely
    
    def _collect_data_for_day(self, date: datetime.date, day_index: int, total_days: int):
        """Collect data for a specific day using existing Stockometry collectors"""
        logger.info(f"Collecting data for {date}")
        
        try:
            # Convert date to datetime for the specific report times
            # We'll collect data up to each report time to respect time-aware filtering
            report_times = self.config.daily_report_times
            
            for report_time in report_times:
                # Create datetime for this specific report time on the target date
                report_datetime = datetime.combine(date, report_time, tzinfo=timezone.utc)
                
                logger.info(f"  Collecting data for {date} at {report_time}")
                
                # Step 1: Fetch and store news articles (up to report time)
                self._collect_news_for_report_time(date, report_datetime)
                
                # Step 2: Fetch and store market data (up to report time)
                self._collect_market_data_for_report_time(date, report_datetime)
                
                # Step 3: Process articles and store features (up to report time)
                self._process_articles_for_report_time(date, report_datetime)
                
                logger.info(f"  Data collection complete for {date} at {report_time}")
                
        except Exception as e:
            logger.error(f"Data collection failed for {date}: {str(e)}")
            raise
    
    def _collect_news_for_report_time(self, date: datetime.date, report_datetime: datetime):
        """Collect news articles up to the specific report time"""
        try:
            from ..core.collectors.news_collector import fetch_and_store_news
            
            logger.info(f"    Fetching news articles up to {report_datetime}")
            
            # Call the existing news collector
            fetch_and_store_news()
            
            logger.info(f"    News collection complete for {report_datetime}")
            
        except Exception as e:
            logger.error(f"News collection failed for {report_datetime}: {str(e)}")
            logger.warning(f"Continuing with other data sources despite news collection failure")
    
    def _collect_market_data_for_report_time(self, date: datetime.date, report_datetime: datetime):
        """Collect market data up to the specific report time"""
        try:
            from ..core.collectors.market_data_collector import fetch_and_store_market_data
            
            logger.info(f"    Fetching market data up to {report_datetime}")
            
            # Call the existing market data collector
            fetch_and_store_market_data()
            
            logger.info(f"    Market data collection complete for {report_datetime}")
            
        except Exception as e:
            logger.error(f"Market data collection failed for {report_datetime}: {str(e)}")
            logger.warning(f"Continuing with other data sources despite market data collection failure")
    
    def _process_articles_for_report_time(self, date: datetime.date, report_datetime: datetime):
        """Process articles and store features up to the specific report time"""
        try:
            from ..core.nlp.processor import process_articles_and_store_features
            
            logger.info(f"    Processing articles and storing features up to {report_datetime}")
            
            # Call the existing article processor
            process_articles_and_store_features()
            
            logger.info(f"    Article processing complete for {report_datetime}")
            
        except Exception as e:
            logger.error(f"Article processing failed for {report_datetime}: {str(e)}")
            logger.warning(f"Continuing with other processing despite article processing failure")
    
    def _generate_reports_for_day(self, date: datetime.date, day_index: int, total_days: int):
        """Generate reports for a specific day using existing Stockometry analysis pipeline"""
        logger.info(f"Generating reports for {date}")
        
        try:
            # Generate reports for each report time on this date
            report_times = self.config.daily_report_times
            
            for report_time in report_times:
                # Create datetime for this specific report time on the target date
                report_datetime = datetime.combine(date, report_time, tzinfo=timezone.utc)
                
                logger.info(f"  Generating report for {date} at {report_time}")
                
                # Generate and save the report (this includes synthesis)
                self._generate_and_save_report(date, report_datetime)
                
                logger.info(f"  Report generation complete for {date} at {report_time}")
                
        except Exception as e:
            logger.error(f"Report generation failed for {date}: {str(e)}")
            raise
    
    def _run_synthesis_for_report_time(self, date: datetime.date, report_datetime: datetime):
        """Run synthesis and analysis for the specific report time"""
        try:
            from ..core.analysis.historical_analyzer import analyze_historical_trends
            from ..core.analysis.today_analyzer import analyze_impact_for_date
            
            logger.info(f"    Running synthesis and analysis for {report_datetime}")
            
            # For backfill, we need to analyze data for the target date, not today
            # Use the new backfill-specific function that respects the target date
            
            # 1. Historical trends (this should work for any date)
            historical_result = analyze_historical_trends()
            
            # 2. Impact analysis for the target date (not today)
            impact_result = analyze_impact_for_date(date)
            
            # Combine signals
            all_signals = historical_result['signals'] + impact_result['signals']
            
            # Create executive summary
            summary_points = historical_result['summary_points'] + impact_result['summary_points']
            executive_summary = " ".join(summary_points)
            
            # Create final report object
            synthesis_result = {
                "executive_summary": executive_summary,
                "signals": {
                    "historical": historical_result['signals'],
                    "impact": impact_result['signals'],
                    "confidence": []  # Simplified for backfill
                }
            }
            
            logger.info(f"    Synthesis complete for {report_datetime}")
            return synthesis_result
            
        except Exception as e:
            logger.error(f"Synthesis failed for {report_datetime}: {str(e)}")
            logger.warning(f"Continuing with other processing despite synthesis failure")
            return None
    
    def _generate_and_save_report(self, date: datetime.date, report_datetime: datetime):
        """Generate and save the final report to database"""
        try:
            from ..core.output.processor import OutputProcessor
            
            logger.info(f"    Generating and saving report for {report_datetime}")
            
            # First, run synthesis to get the report object
            synthesis_result = self._run_synthesis_for_report_time(date, report_datetime)
            
            if synthesis_result is None:
                logger.warning(f"    No synthesis result available for {report_datetime}")
                return
            
            # Create output processor instance with the report object
            # Use BACKFILL as run_source to distinguish from scheduled/ondemand reports
            output_processor = OutputProcessor(report_object=synthesis_result, run_source="BACKFILL")
            
            # Save the report to the daily_reports table
            saved_report = output_processor.process_and_save()
            
            if saved_report:
                logger.info(f"    Report saved to daily_reports table for {report_datetime}")
                logger.info(f"    Report ID: {saved_report}")
                logger.info(f"    Run Source: BACKFILL")
            else:
                logger.warning(f"    Report save returned no result for {report_datetime}")
            
        except Exception as e:
            logger.error(f"Report saving failed for {report_datetime}: {str(e)}")
            logger.warning(f"Continuing with other processing despite report saving failure")
    
    def _get_final_status(self) -> Dict[str, Any]:
        """Get final status of backfill process"""
        total_days = len(self.progress)
        completed_days = len([p for p in self.progress if p.status == 'complete'])
        failed_days = len([p for p in self.progress if p.status == 'failed'])
        pending_days = len([p for p in self.progress if p.status == 'pending'])
        
        success_rate = (completed_days / total_days * 100) if total_days > 0 else 0
        
        logger.info(f"Backfill Summary:")
        logger.info(f"  Total Days: {total_days}")
        logger.info(f"  Completed: {completed_days}")
        logger.info(f"  Failed: {failed_days}")
        logger.info(f"  Success Rate: {success_rate:.1f}%")
        
        return {
            "status": "complete" if failed_days == 0 else "partial_success",
            "total_days": total_days,
            "completed_days": completed_days,
            "failed_days": failed_days,
            "pending_days": pending_days,
            "success_rate": f"{success_rate:.1f}%",
            "progress": [p.__dict__ for p in self.progress]
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current backfill status"""
        return {
            "status": "ready",
            "config": self.config.to_dict(),
            "database": {
                "environment": settings.environment,
                "active_database": settings.db_name_active,
                "host": settings.db_host,
                "port": settings.db_port
            },
            "capabilities": {
                "daily_report_count": self.config.daily_report_count,
                "lookback_days": self.config.lookback_days
            }
        }
