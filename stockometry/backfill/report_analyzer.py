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
    total_days_checked: int
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
        
        # Get all scheduled reports in the date range (exclude ONDEMAND)
        existing_reports = self._get_existing_reports(start_date, end_date)
        
        # Analyze each day
        missing_reports = []
        
        current_date = start_date
        while current_date <= end_date:
            day_reports = existing_reports.get(current_date, [])
            day_missing = self._analyze_day(current_date, day_reports)
            missing_reports.extend(day_missing)
            current_date += timedelta(days=1)
        
        total_days = (end_date - start_date).days + 1
        total_expected = total_days * self.config.daily_report_count
        total_found = total_expected - len(missing_reports)
        coverage = (total_found / total_expected * 100) if total_expected > 0 else 100.0
        
        analysis = ReportAnalysis(
            total_days_checked=total_days,
            total_reports_expected=total_expected,
            total_reports_found=total_found,
            missing_reports=missing_reports,
            coverage_percentage=coverage
        )
        
        logger.info(f"Analysis complete: {coverage:.1f}% coverage, {len(missing_reports)} missing reports")
        return analysis
    
    def _get_existing_reports(self, start_date: datetime.date, end_date: datetime.date) -> Dict[datetime.date, List[Dict]]:
        """Get all scheduled reports for the date range (exclude ONDEMAND)"""
        query = """
            SELECT report_date, generated_at_utc
            FROM daily_reports 
            WHERE report_date >= %s AND report_date <= %s 
            AND run_source != 'ONDEMAND'
            ORDER BY report_date, generated_at_utc
        """
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (start_date, end_date))
                rows = cursor.fetchall()
                
                # Group by date
                reports_by_date = {}
                for row in rows:
                    report_date = row[0]
                    generated_at = row[1]
                    
                    if report_date not in reports_by_date:
                        reports_by_date[report_date] = []
                    
                    reports_by_date[report_date].append({
                        'generated_at': generated_at
                    })
                
                return reports_by_date
                
        except Exception as e:
            logger.error(f"Error fetching existing reports: {str(e)}")
            return {}
    
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
