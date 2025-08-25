"""
Report Analyzer for Backfill System

This module analyzes the daily_reports table to identify missing reports
based on the configured daily report schedule. It excludes ONDEMAND reports.
"""

from datetime import datetime, timezone, timedelta, time
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

from ..database import get_db_connection
from .config import BackfillConfig

logger = logging.getLogger(__name__)

@dataclass
class MissingReport:
    """Represents a missing report that needs to be generated"""
    date: datetime.date
    expected_time: time
    report_type: str

@dataclass
class ReportAnalysis:
    """Results of analyzing reports for missing data"""
    start_date: datetime.date
    end_date: datetime.date
    total_reports_expected: int
    total_reports_found: int
    missing_reports: List[MissingReport]
    coverage_percentage: float

class ReportAnalyzer:
    """Analyzes daily reports to identify missing data"""
    
    def __init__(self, config: BackfillConfig = None):
        """Initialize the report analyzer"""
        self.config = config or BackfillConfig()
        logger.info(f"ReportAnalyzer initialized with {self.config.daily_report_count} daily reports")
    
    def analyze_reports(self, start_date: datetime.date = None, end_date: datetime.date = None) -> ReportAnalysis:
        """
        Analyze reports for the specified date range
        
        Args:
            start_date: Start date for analysis (defaults to lookback_days ago)
            end_date: End date for analysis (defaults to today)
            
        Returns:
            ReportAnalysis object with complete analysis results
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc).date()
        
        if start_date is None:
            start_date = end_date - timedelta(days=self.config.lookback_days - 1)
        
        logger.info(f"Analyzing reports from {start_date} to {end_date}")
        
        # Get existing reports for the date range
        existing_reports = self._get_existing_reports(start_date, end_date)
        
        # Find missing reports
        missing_reports = []
        total_expected = 0
        total_found = 0
        
        current_date = start_date
        while current_date <= end_date:
            for report_time in self.config.daily_report_times:
                total_expected += 1
                
                # Check if this report exists
                report_found = any(
                    report.date == current_date and 
                    report.expected_time == report_time
                    for report in existing_reports
                )
                
                if report_found:
                    total_found += 1
                else:
                    # Create missing report entry
                    missing_report = MissingReport(
                        date=current_date,
                        expected_time=report_time,
                        report_type=self._get_report_type(report_time)
                    )
                    missing_reports.append(missing_report)
            
            current_date += timedelta(days=1)
        
        # Calculate coverage percentage
        coverage_percentage = (total_found / total_expected * 100) if total_expected > 0 else 0
        
        return ReportAnalysis(
            start_date=start_date,
            end_date=end_date,
            total_reports_expected=total_expected,
            total_reports_found=total_found,
            missing_reports=missing_reports,
            coverage_percentage=coverage_percentage
        )
    
    def _get_existing_reports(self, start_date: datetime.date, end_date: datetime.date) -> List[Dict[str, Any]]:
        """Get existing reports from database for the date range"""
        try:
            with get_db_connection() as conn:
                if not conn:
                    logger.error("Failed to get database connection")
                    return []
                
                cursor = conn.cursor()
                
                # Query for existing reports, excluding ONDEMAND and BACKFILL reports
                # We only want to count scheduled reports (SCHEDULED, SCHEDULER_DOCKER)
                query = """
                    SELECT 
                        DATE(report_date) as report_date,
                        EXTRACT(HOUR FROM report_date) as hour,
                        EXTRACT(MINUTE FROM report_date) as minute,
                        run_source
                    FROM daily_reports 
                    WHERE DATE(report_date) BETWEEN %s AND %s
                    AND run_source NOT IN ('ONDEMAND', 'BACKFILL')
                    ORDER BY report_date
                """
                
                cursor.execute(query, (start_date, end_date))
                rows = cursor.fetchall()
                cursor.close()
                
                # Convert to our internal format
                reports = []
                for row in rows:
                    report_date, hour, minute, run_source = row
                    if hour is not None and minute is not None:
                        expected_time = time(int(hour), int(minute))
                        reports.append({
                            'date': report_date,
                            'expected_time': expected_time,
                            'run_source': run_source
                        })
                
                logger.info(f"Found {len(reports)} existing scheduled reports")
                return reports
                
        except Exception as e:
            logger.error(f"Error getting existing reports: {str(e)}")
            return []
    
    def _analyze_day(self, date: datetime.date, day_reports: List[Dict]) -> List[MissingReport]:
        """Analyze a single day to find missing reports"""
        missing = []
        
        # Check each expected report time
        for expected_time in self.config.daily_report_times:
            # Find if we have a report for this time
            report_found = False
            
            for report in day_reports:
                report_time = report['generated_at'].time()
                # Allow 2-hour window for each report time
                if self._is_time_in_window(report_time, expected_time, hours=2):
                    report_found = True
                    break
            
            if not report_found:
                # Determine report type based on time
                report_type = self._get_report_type(expected_time)
                
                missing_report = MissingReport(
                    date=date,
                    expected_time=expected_time,
                    report_type=report_type
                )
                missing.append(missing_report)
        
        return missing
    
    def _is_time_in_window(self, actual_time: time, expected_time: time, hours: int = 2) -> bool:
        """Check if actual time is within the expected window"""
        # Convert times to minutes for easier comparison
        actual_minutes = actual_time.hour * 60 + actual_time.minute
        expected_minutes = expected_time.hour * 60 + expected_time.minute
        
        # Handle midnight crossing
        if abs(actual_minutes - expected_minutes) > 12 * 60:  # More than 12 hours difference
            if actual_minutes < expected_minutes:
                actual_minutes += 24 * 60
            else:
                expected_minutes += 24 * 60
        
        # Check if within window
        return abs(actual_minutes - expected_minutes) <= hours * 60
    
    def _get_report_type(self, report_time: time) -> str:
        """Get descriptive name for report type based on time"""
        hour = report_time.hour
        if hour < 6:
            return "Early Morning"
        elif hour < 12:
            return "Morning"
        elif hour < 18:
            return "Afternoon"
        else:
            return "Evening"
    
    def get_missing_reports_summary(self, analysis: ReportAnalysis) -> Dict[str, Any]:
        """Get a summary of missing reports for display"""
        if not analysis.missing_reports:
            return {
                "status": "complete",
                "message": "All reports are present",
                "coverage": f"{analysis.coverage_percentage:.1f}%"
            }
        
        # Group missing reports by date
        missing_by_date = {}
        for missing in analysis.missing_reports:
            date_str = missing.date.isoformat()
            if date_str not in missing_by_date:
                missing_by_date[date_str] = []
            missing_by_date[date_str].append({
                "time": missing.expected_time.strftime("%H:%M"),
                "type": missing.report_type
            })
        
        return {
            "status": "incomplete",
            "message": f"Found {len(analysis.missing_reports)} missing reports",
            "coverage": f"{analysis.coverage_percentage:.1f}%",
            "missing_by_date": missing_by_date,
            "total_missing": len(analysis.missing_reports)
        }
