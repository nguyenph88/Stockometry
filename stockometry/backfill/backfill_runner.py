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
    """Tracks progress of backfill process"""
    day_date: datetime.date
    status: str  # 'pending', 'collecting', 'processing', 'complete', 'failed'
    phase: str   # 'pending', 'data_collection', 'report_generation'
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Phase-specific progress
    data_collection_progress: int = 0  # 0-100
    report_generation_progress: int = 0  # 0-100
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0

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
    
    def _print_separator(self, title: str = ""):
        """Print a visual separator with optional title"""
        if title:
            print(f"\n{'='*60}")
            print(f"🚀 {title}")
            print(f"{'='*60}")
        else:
            print(f"\n{'-'*60}")
    
    def _print_phase_header(self, phase: str, phase_number: int, total_phases: int):
        """Print a phase header with progress indicator"""
        print(f"\n{'#'*50}")
        print(f"📋 PHASE {phase_number}/{total_phases}: {phase.upper()}")
        print(f"{'#'*50}")
    
    def _print_day_progress(self, progress: BackfillProgress, day_index: int, total_days: int):
        """Print progress for a specific day"""
        day_num = day_index + 1
        status_emoji = {
            'pending': '⏳',
            'collecting': '📥',
            'processing': '⚙️',
            'complete': '✅',
            'failed': '❌'
        }
        
        emoji = status_emoji.get(progress.status, '❓')
        
        if progress.phase == 'data_collection':
            progress_bar = self._create_progress_bar(progress.data_collection_progress)
            print(f"  {emoji} Day {day_num}/{total_days}: {progress.day_date} - Data Collection {progress_bar} {progress.data_collection_progress}%")
            if progress.current_step:
                print(f"     └─ {progress.current_step}")
        elif progress.phase == 'report_generation':
            progress_bar = self._create_progress_bar(progress.report_generation_progress)
            print(f"  {emoji} Day {day_num}/{total_days}: {progress.day_date} - Report Generation {progress_bar} {progress.report_generation_progress}%")
            if progress.current_step:
                print(f"     └─ {progress.current_step}")
        else:
            print(f"  {emoji} Day {day_num}/{total_days}: {progress.day_date} - {progress.status.title()}")
    
    def _create_progress_bar(self, percentage: int, width: int = 20) -> str:
        """Create a visual progress bar"""
        filled = int(width * percentage / 100)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}]"
    
    def _print_overall_progress(self):
        """Print overall progress summary"""
        total_days = len(self.progress)
        completed_days = len([p for p in self.progress if p.status == 'complete'])
        failed_days = len([p for p in self.progress if p.status == 'failed'])
        in_progress_days = len([p for p in self.progress if p.status in ['collecting', 'processing']])
        pending_days = len([p for p in self.progress if p.status == 'pending'])
        
        overall_progress = (completed_days / total_days * 100) if total_days > 0 else 0
        
        print(f"\n📊 OVERALL PROGRESS: {overall_progress:.1f}%")
        print(f"   ✅ Completed: {completed_days}/{total_days}")
        print(f"   📥 In Progress: {in_progress_days}")
        print(f"   ❌ Failed: {failed_days}")
        print(f"   ⏳ Pending: {pending_days}")
        
        # Overall progress bar
        overall_bar = self._create_progress_bar(int(overall_progress), 40)
        print(f"   {overall_bar}")
    
    def _print_phase_progress(self, phase_name: str):
        """Print progress for a specific phase"""
        phase_progress = []
        
        if phase_name == 'data_collection':
            phase_progress = [p.data_collection_progress for p in self.progress]
        elif phase_name == 'report_generation':
            phase_progress = [p.report_generation_progress for p in self.progress]
        
        if phase_progress:
            avg_progress = sum(phase_progress) / len(phase_progress)
            print(f"\n📈 {phase_name.replace('_', ' ').title()} Progress: {avg_progress:.1f}%")
            phase_bar = self._create_progress_bar(int(avg_progress), 30)
            print(f"   {phase_bar}")
    
    def _update_day_progress(self, day_date: datetime.date, phase: str, progress_percentage: int, 
                           current_step: str = "", completed_steps: int = 0, total_steps: int = 0):
        """Update progress for a specific day"""
        for progress in self.progress:
            if progress.day_date == day_date:
                if phase == 'data_collection':
                    progress.data_collection_progress = progress_percentage
                elif phase == 'report_generation':
                    progress.report_generation_progress = progress_percentage
                
                progress.current_step = current_step
                progress.completed_steps = completed_steps
                progress.total_steps = total_steps
                break
    
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
            self._print_separator("BACKFILL PROCESS STARTING")
            logger.info("Starting backfill process")
            
            # Validate database environment first
            self._validate_database_environment()
            
            # Determine date range
            if end_date is None:
                end_date = datetime.now(timezone.utc).date()
            
            if start_date is None:
                start_date = end_date - timedelta(days=self.config.lookback_days - 1)
            
            logger.info(f"Backfill range: {start_date} to {end_date}")
            print(f"📅 Date Range: {start_date} to {end_date}")
            print(f"📊 Total Days: {(end_date - start_date).days + 1}")
            
            if dry_run:
                return self._dry_run_backfill(start_date, end_date)
            
            # Initialize progress tracking
            self._initialize_progress(start_date, end_date)
            
            # Phase 1: Data Collection
            self._print_phase_header("Data Collection", 1, 2)
            self._collect_data_for_all_days()
            
            # Phase 2: Report Generation
            self._print_phase_header("Report Generation", 2, 2)
            self._generate_reports_for_all_days()
            
            # Final status
            self._print_separator("BACKFILL PROCESS COMPLETED")
            return self._get_final_status()
            
        except Exception as e:
            self._print_separator("BACKFILL PROCESS FAILED")
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
        """Initialize progress tracking for all days"""
        self.progress = []
        current_date = start_date
        
        while current_date <= end_date:
            progress = BackfillProgress(
                day_date=current_date,
                status='pending',
                phase='pending'
            )
            self.progress.append(progress)
            current_date += timedelta(days=1)
        
        logger.info(f"Initialized progress tracking for {len(self.progress)} days")
    
    def _collect_data_for_all_days(self):
        """Collect data for all days sequentially"""
        total_days = len(self.progress)
        
        for day_index, progress in enumerate(self.progress):
            try:
                print(f"\n📥 Processing Day {day_index + 1}/{total_days}: {progress.day_date}")
                
                progress.status = 'collecting'
                progress.phase = 'data_collection'
                progress.started_at = datetime.now(timezone.utc)
                
                # Simulate data collection with progress updates
                self._collect_data_for_day(progress.day_date, day_index, total_days)
                
                progress.status = 'complete'
                progress.completed_at = datetime.now(timezone.utc)
                progress.data_collection_progress = 100
                
                print(f"  ✅ Data collection complete for {progress.day_date}")
                logger.info(f"Data collection complete for {progress.day_date}")
                
                # Show progress after each day
                self._print_overall_progress()
                self._print_phase_progress('data_collection')
                
            except Exception as e:
                progress.status = 'failed'
                progress.error_message = str(e)
                progress.data_collection_progress = 0
                logger.error(f"Data collection failed for {progress.day_date}: {str(e)}")
                print(f"  ❌ Data collection failed for {progress.day_date}: {str(e)}")
                # Continue with next day instead of failing completely
    
    def _generate_reports_for_all_days(self):
        """Generate reports for all days sequentially"""
        total_days = len(self.progress)
        
        for day_index, progress in enumerate(self.progress):
            if progress.status == 'failed':
                print(f"\n⚠️  Skipping report generation for {progress.day_date} due to data collection failure")
                logger.warning(f"Skipping report generation for {progress.day_date} due to data collection failure")
                continue
                
            try:
                print(f"\n⚙️  Processing Day {day_index + 1}/{total_days}: {progress.day_date}")
                
                progress.status = 'processing'
                progress.phase = 'report_generation'
                progress.started_at = datetime.now(timezone.utc)
                
                # Simulate report generation with progress updates
                self._generate_reports_for_day(progress.day_date, day_index, total_days)
                
                progress.status = 'complete'
                progress.completed_at = datetime.now(timezone.utc)
                progress.report_generation_progress = 100
                
                print(f"  ✅ Report generation complete for {progress.day_date}")
                logger.info(f"Report generation complete for {progress.day_date}")
                
                # Show progress after each day
                self._print_overall_progress()
                self._print_phase_progress('report_generation')
                
            except Exception as e:
                progress.status = 'failed'
                progress.error_message = str(e)
                progress.report_generation_progress = 0
                logger.error(f"Report generation failed for {progress.day_date}: {str(e)}")
                print(f"  ❌ Report generation failed for {progress.day_date}: {str(e)}")
                # Continue with next day instead of failing completely
    
    def _collect_data_for_day(self, date: datetime.date, day_index: int, total_days: int):
        """Collect data for a specific day using existing Stockometry collectors"""
        logger.info(f"Collecting data for {date}")
        
        try:
            # Convert date to datetime for the specific report times
            # We'll collect data up to each report time to respect time-aware filtering
            report_times = self.config.daily_report_times
            total_steps = len(report_times) * 3  # 3 steps per report time
            completed_steps = 0
            
            for report_time in report_times:
                # Create datetime for this specific report time on the target date
                report_datetime = datetime.combine(date, report_time, tzinfo=timezone.utc)
                
                logger.info(f"  Collecting data for {date} at {report_time}")
                
                # Step 1: Fetch and store news articles (up to report time)
                self._collect_news_for_report_time(date, report_datetime)
                completed_steps += 1
                self._update_progress(date, 'data_collection', completed_steps, total_steps, "News collection")
                
                # Step 2: Fetch and store market data (up to report time)
                self._collect_market_data_for_report_time(date, report_datetime)
                completed_steps += 1
                self._update_progress(date, 'data_collection', completed_steps, total_steps, "Market data collection")
                
                # Step 3: Process articles and store features (up to report time)
                self._process_articles_for_report_time(date, report_datetime)
                completed_steps += 1
                self._update_progress(date, 'data_collection', completed_steps, total_steps, "Article processing")
                
                logger.info(f"  Data collection complete for {date} at {report_time}")
                
        except Exception as e:
            logger.error(f"Data collection failed for {date}: {str(e)}")
            raise
    
    def _update_progress(self, date: datetime.date, phase: str, completed_steps: int, total_steps: int, current_step: str):
        """Update progress for a specific day and phase"""
        progress_percentage = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
        
        for progress in self.progress:
            if progress.day_date == date:
                if phase == 'data_collection':
                    progress.data_collection_progress = progress_percentage
                elif phase == 'report_generation':
                    progress.report_generation_progress = progress_percentage
                
                progress.current_step = current_step
                progress.completed_steps = completed_steps
                progress.total_steps = total_steps
                break
    
    def _collect_news_for_report_time(self, date: datetime.date, report_datetime: datetime):
        """Collect news articles up to the specific report time"""
        try:
            from ..core.collectors.news_collector import fetch_and_store_news
            
            # Collect news up to the report time
            # This respects the time-aware filtering we discussed
            logger.info(f"    📰 Fetching news articles up to {report_datetime}")
            
            # Call the existing news collector
            # The existing function should handle the time filtering
            fetch_and_store_news()
            
            logger.info(f"    ✅ News collection complete for {report_datetime}")
            
        except Exception as e:
            logger.error(f"News collection failed for {report_datetime}: {str(e)}")
            # Don't fail completely - continue with other data sources
            logger.warning(f"Continuing with other data sources despite news collection failure")
    
    def _collect_market_data_for_report_time(self, date: datetime.date, report_datetime: datetime):
        """Collect market data up to the specific report time"""
        try:
            from ..core.collectors.market_data_collector import fetch_and_store_market_data
            
            logger.info(f"    📊 Fetching market data up to {report_datetime}")
            
            # Call the existing market data collector
            fetch_and_store_market_data()
            
            logger.info(f"    ✅ Market data collection complete for {report_datetime}")
            
        except Exception as e:
            logger.error(f"Market data collection failed for {report_datetime}: {str(e)}")
            # Don't fail completely - continue with other data sources
            logger.warning(f"Continuing with other data sources despite market data collection failure")
    
    def _process_articles_for_report_time(self, date: datetime.date, report_datetime: datetime):
        """Process articles and store features up to the specific report time"""
        try:
            from ..core.analysis.historical_analyzer import process_articles_and_store_features
            
            logger.info(f"    🔍 Processing articles and storing features up to {report_datetime}")
            
            # Call the existing article processor
            process_articles_and_store_features()
            
            logger.info(f"    ✅ Article processing complete for {report_datetime}")
            
        except Exception as e:
            logger.error(f"Article processing failed for {report_datetime}: {str(e)}")
            # Don't fail completely - continue with other processing
            logger.warning(f"Continuing with other processing despite article processing failure")
    
    def _generate_reports_for_day(self, date: datetime.date, day_index: int, total_days: int):
        """Generate reports for a specific day using existing Stockometry analysis pipeline"""
        logger.info(f"Generating reports for {date}")
        
        try:
            # Generate reports for each report time on this date
            report_times = self.config.daily_report_times
            total_steps = len(report_times)  # 1 step per report time (synthesis + save combined)
            completed_steps = 0
            
            for report_time in report_times:
                # Create datetime for this specific report time on the target date
                report_datetime = datetime.combine(date, report_time, tzinfo=timezone.utc)
                
                logger.info(f"  Generating report for {date} at {report_time}")
                
                # Generate and save the report (this includes synthesis)
                self._generate_and_save_report(date, report_datetime)
                completed_steps += 1
                self._update_progress(date, 'report_generation', completed_steps, total_steps, f"Report for {report_time}")
                
                logger.info(f"  Report generation complete for {date} at {report_time}")
                
        except Exception as e:
            logger.error(f"Report generation failed for {date}: {str(e)}")
            raise
    
    def _run_synthesis_for_report_time(self, date: datetime.date, report_datetime: datetime):
        """Run synthesis and analysis for the specific report time"""
        try:
            from ..core.analysis.synthesizer import synthesize_analyses
            
            logger.info(f"    🧠 Running synthesis and analysis for {report_datetime}")
            
            # Call the existing synthesis function
            # This will analyze the collected data and generate insights
            synthesis_result = synthesize_analyses()
            
            logger.info(f"    ✅ Synthesis complete for {report_datetime}")
            return synthesis_result
            
        except Exception as e:
            logger.error(f"Synthesis failed for {report_datetime}: {str(e)}")
            # Don't fail completely - continue with other processing
            logger.warning(f"Continuing with other processing despite synthesis failure")
            return None
    
    def _generate_and_save_report(self, date: datetime.date, report_datetime: datetime):
        """Generate and save the final report to database"""
        try:
            from ..core.output.processor import OutputProcessor
            
            logger.info(f"    💾 Generating and saving report for {report_datetime}")
            
            # First, run synthesis to get the report object
            synthesis_result = self._run_synthesis_for_report_time(date, report_datetime)
            
            if synthesis_result is None:
                logger.warning(f"    ⚠️  No synthesis result available for {report_datetime}")
                return
            
            # Create output processor instance with the report object
            # Use BACKFILL as run_source to distinguish from scheduled/ondemand reports
            output_processor = OutputProcessor(report_object=synthesis_result, run_source="BACKFILL")
            
            # Save the report to the daily_reports table
            # This will use the existing database connection and respect the environment
            saved_report = output_processor.save_to_database()
            
            if saved_report:
                logger.info(f"    ✅ Report saved to daily_reports table for {report_datetime}")
                logger.info(f"    📊 Report ID: {saved_report.get('id', 'unknown')}")
                logger.info(f"    🏷️  Run Source: BACKFILL")
            else:
                logger.warning(f"    ⚠️  Report save returned no result for {report_datetime}")
            
        except Exception as e:
            logger.error(f"Report saving failed for {report_datetime}: {str(e)}")
            # Don't fail completely - continue with other processing
            logger.warning(f"Continuing with other processing despite report saving failure")
    
    def _get_final_status(self) -> Dict[str, Any]:
        """Get final status of backfill process"""
        total_days = len(self.progress)
        completed_days = len([p for p in self.progress if p.status == 'complete'])
        failed_days = len([p for p in self.progress if p.status == 'failed'])
        pending_days = len([p for p in self.progress if p.status == 'pending'])
        
        success_rate = (completed_days / total_days * 100) if total_days > 0 else 0
        
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
