"""
Backfill Manager - Main Interface

This module provides the main interface for checking missing daily reports.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import logging

from ..database import get_db_connection
from ..config import settings
from .config import BackfillConfig, DEFAULT_BACKFILL_CONFIG
from .report_analyzer import ReportAnalyzer, ReportAnalysis
from .backfill_runner import BackfillRunner

logger = logging.getLogger(__name__)

class BackfillManager:
    """Main interface for checking missing daily reports"""
    
    def __init__(self, config: BackfillConfig = None):
        """Initialize the backfill manager"""
        self.config = config or DEFAULT_BACKFILL_CONFIG
        self.analyzer = ReportAnalyzer(self.config)
        self.runner = BackfillRunner(self.config)
        
        # Log database environment information
        logger.info(f"BackfillManager initialized with config: {self.config.to_dict()}")
        logger.info(f"Database Environment: {settings.environment}")
        logger.info(f"Active Database: {settings.db_name_active}")
        logger.info(f"Database Host: {settings.db_host}:{settings.db_port}")
    
    def check_missing_reports(self, 
                              start_date: Optional[datetime.date] = None,
                              end_date: Optional[datetime.date] = None) -> ReportAnalysis:
        """
        Check for missing reports in the specified date range
        
        Args:
            start_date: Start date for analysis (defaults to lookback_days ago)
            end_date: End date for analysis (defaults to today)
            
        Returns:
            ReportAnalysis object with complete analysis
        """
        logger.info("Starting missing reports check")
        logger.info(f"Using database: {settings.db_name_active}")
        
        analysis = self.analyzer.analyze_reports(start_date, end_date)
        
        # Log summary
        if analysis.missing_reports:
            logger.info(f"Found {len(analysis.missing_reports)} missing reports")
            for missing in analysis.missing_reports[:5]:  # Log first 5
                logger.info(f"  - {missing.date} at {missing.expected_time}: {missing.report_type}")
            if len(analysis.missing_reports) > 5:
                logger.info(f"  ... and {len(analysis.missing_reports) - 5} more")
        else:
            logger.info("No missing reports found - all data is complete!")
        
        return analysis
    
    def run_backfill(self, 
                     start_date: Optional[datetime.date] = None,
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
        logger.info("Starting backfill process")
        if dry_run:
            logger.info("Running in dry-run mode - no actual processing")
        
        try:
            result = self.runner.run_backfill(start_date, end_date, dry_run)
            logger.info(f"Backfill process completed with status: {result.get('status', 'unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Backfill process failed: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "message": "Backfill process encountered an error"
            }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status"""
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
                "lookback_days": self.config.lookback_days,
                "backfill_runner": "available"
            }
        }
    
    def update_config(self, new_config: BackfillConfig) -> Dict[str, Any]:
        """Update the configuration"""
        logger.info("Updating configuration")
        
        old_config = self.config
        self.config = new_config
        
        # Reinitialize analyzer and runner with new config
        self.analyzer = ReportAnalyzer(self.config)
        self.runner = BackfillRunner(self.config)
        
        logger.info(f"Configuration updated: {self.config.to_dict()}")
        
        return {
            "status": "updated",
            "old_config": old_config.to_dict(),
            "new_config": self.config.to_dict(),
            "message": "Configuration updated successfully"
        }
    
    def get_missing_reports_summary(self, 
                                  start_date: Optional[datetime.date] = None,
                                  end_date: Optional[datetime.date] = None) -> Dict[str, Any]:
        """Get a quick summary of missing reports"""
        logger.info("Getting missing reports summary")
        
        analysis = self.check_missing_reports(start_date, end_date)
        summary = self.analyzer.get_missing_reports_summary(analysis)
        
        return {
            "summary": summary,
            "analysis": {
                "total_days_checked": analysis.total_days_checked,
                "total_reports_expected": analysis.total_reports_expected,
                "total_reports_found": analysis.total_reports_found,
                "coverage_percentage": analysis.coverage_percentage
            }
        }
