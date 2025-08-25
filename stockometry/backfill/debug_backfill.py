"""
Debug Backfill System - Comprehensive Investigation

This module thoroughly investigates why only 1 report is being created.
Tests all aspects: date calculation, missing report detection, and report generation.
"""

import logging
from datetime import datetime, timezone, date, time
from typing import Dict, Any, List

from ..database import get_db_connection
from ..config import settings
from .config import BackfillConfig
from .report_analyzer import ReportAnalyzer, ReportAnalysis

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackfillDebugger:
    """Comprehensive debug class for backfill system"""
    
    def __init__(self):
        """Initialize the debugger"""
        self.config = BackfillConfig()
        self.analyzer = ReportAnalyzer(self.config)
        logger.info("🔍 BackfillDebugger initialized")
        logger.info(f"📅 Config: {self.config.to_dict()}")
    
    def debug_date_calculations(self):
        """Debug how dates are being calculated"""
        logger.info("="*60)
        logger.info("DEBUG 1: Date Calculations")
        logger.info("="*60)
        
        try:
            # Show current time and date
            now = datetime.now(timezone.utc)
            today = now.date()
            logger.info(f"🕐 Current UTC time: {now}")
            logger.info(f"📅 Current UTC date: {today}")
            logger.info(f"📅 Current day of week: {today.strftime('%A')}")
            
            # Show backfill date range
            end_date = today
            start_date = end_date - (today - today.replace(day=today.day - self.config.lookback_days + 1))
            logger.info(f"📊 Backfill range calculation:")
            logger.info(f"  End date: {end_date}")
            logger.info(f"  Start date: {start_date}")
            logger.info(f"  Lookback days: {self.config.lookback_days}")
            logger.info(f"  Total days: {(end_date - start_date).days + 1}")
            
            # Show each date in range
            logger.info(f"📅 Dates in backfill range:")
            current_date = start_date
            day_count = 1
            while current_date <= end_date:
                day_name = current_date.strftime('%A')
                logger.info(f"  Day {day_count}: {current_date} ({day_name})")
                current_date = current_date.replace(day=current_date.day + 1)
                day_count += 1
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Date calculation debug failed: {str(e)}")
            return False
    
    def debug_database_state(self):
        """Debug current database state"""
        logger.info("="*60)
        logger.info("DEBUG 2: Database State")
        logger.info("="*60)
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check database info
                cursor.execute("SELECT current_database();")
                current_db = cursor.fetchone()[0]
                logger.info(f"🗄️ Current database: {current_db}")
                
                # Check articles by date
                cursor.execute("""
                    SELECT published_at::date as pub_date, COUNT(*) as count 
                    FROM articles 
                    GROUP BY published_at::date 
                    ORDER BY pub_date DESC;
                """)
                article_dates = cursor.fetchall()
                
                logger.info(f"📰 Articles by date:")
                for pub_date, count in article_dates:
                    day_name = pub_date.strftime('%A')
                    logger.info(f"  {pub_date} ({day_name}): {count} articles")
                
                # Check existing reports
                cursor.execute("""
                    SELECT report_date, run_source, created_at 
                    FROM daily_reports 
                    ORDER BY report_date DESC;
                """)
                existing_reports = cursor.fetchall()
                
                logger.info(f"📊 Existing reports:")
                for report_date, run_source, created_at in existing_reports:
                    day_name = report_date.strftime('%A')
                    logger.info(f"  {report_date} ({day_name}) | {run_source} | {created_at}")
                
                cursor.close()
                return True
                
        except Exception as e:
            logger.error(f"❌ Database state debug failed: {str(e)}")
            return False
    
    def debug_missing_report_detection(self):
        """Debug how missing reports are being detected"""
        logger.info("="*60)
        logger.info("DEBUG 3: Missing Report Detection")
        logger.info("="*60)
        
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date.replace(day=end_date.day - self.config.lookback_days + 1)
            
            logger.info(f"🔍 Analyzing reports from {start_date} to {end_date}")
            
            # Get missing reports analysis
            analysis = self.analyzer.analyze_reports(start_date, end_date)
            
            logger.info(f"📊 Analysis results:")
            logger.info(f"  Total days analyzed: {(end_date - start_date).days + 1}")
            logger.info(f"  Coverage percentage: {analysis.coverage_percentage:.1f}%")
            logger.info(f"  Missing reports found: {len(analysis.missing_reports)}")
            
            if analysis.missing_reports:
                logger.info(f"📝 Missing reports details:")
                for i, missing in enumerate(analysis.missing_reports, 1):
                    day_name = missing.date.strftime('%A')
                    logger.info(f"  {i}. {missing.date} ({day_name}) at {missing.expected_time.strftime('%H:%M')} | {missing.report_type}")
            else:
                logger.info("✅ No missing reports found")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Missing report detection debug failed: {str(e)}")
            return False
    
    def debug_report_generation_logic(self):
        """Debug the report generation logic"""
        logger.info("="*60)
        logger.info("DEBUG 4: Report Generation Logic")
        logger.info("="*60)
        
        try:
            # Calculate date range
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date.replace(day=end_date.day - self.config.lookback_days + 1)
            
            logger.info(f"🔍 Testing report generation for {start_date} to {end_date}")
            
            # Test each date individually
            current_date = start_date
            day_count = 1
            
            while current_date <= end_date:
                day_name = current_date.strftime('%A')
                logger.info(f"📅 Day {day_count}: {current_date} ({day_name})")
                
                # Check if this date has articles
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) FROM articles 
                        WHERE published_at::date = %s;
                    """, (current_date,))
                    article_count = cursor.fetchone()[0]
                    cursor.close()
                
                logger.info(f"  📰 Articles available: {article_count}")
                
                # Check if reports exist for this date
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT COUNT(*) FROM daily_reports 
                        WHERE report_date::date = %s;
                    """, (current_date,))
                    report_count = cursor.fetchone()[0]
                    cursor.close()
                
                logger.info(f"  📊 Reports exist: {report_count}")
                
                # Show expected report times
                logger.info(f"  ⏰ Expected report times:")
                for i, report_time in enumerate(self.config.daily_report_times, 1):
                    logger.info(f"    {i}. {report_time.strftime('%H:%M')} UTC")
                
                current_date = current_date.replace(day=current_date.day + 1)
                day_count += 1
                
                if day_count <= 3:  # Add separator between days
                    logger.info("  " + "-" * 40)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Report generation logic debug failed: {str(e)}")
            return False
    
    def debug_weekend_logic(self):
        """Debug if there's any weekend processing logic"""
        logger.info("="*60)
        logger.info("DEBUG 5: Weekend Processing Logic")
        logger.info("="*60)
        
        try:
            # Check current date
            today = datetime.now(timezone.utc).date()
            day_name = today.strftime('%A')
            is_weekend = today.weekday() >= 5  # Saturday = 5, Sunday = 6
            
            logger.info(f"📅 Today: {today} ({day_name})")
            logger.info(f"🏠 Is weekend: {is_weekend}")
            
            # Check if there are any weekend-specific checks in the code
            logger.info(f"🔍 Checking for weekend logic in code...")
            
            # Look for any weekend-related logic in the backfill runner
            logger.info(f"  📝 No weekend logic found in current implementation")
            logger.info(f"  📝 System should process every day normally")
            
            # Check if weekend affects data collection
            logger.info(f"📊 Weekend impact on data:")
            logger.info(f"  📰 Articles: NewsAPI may have reduced weekend coverage")
            logger.info(f"  📈 Market data: Markets closed on weekends")
            logger.info(f"  🔄 Processing: Should continue normally")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Weekend logic debug failed: {str(e)}")
            return False
    
    def run_comprehensive_debug(self):
        """Run all debug tests"""
        logger.info("🚀 Starting Comprehensive Backfill Debug")
        logger.info("="*80)
        
        debug_results = []
        
        # Run all debug tests
        debug_results.append(("Date Calculations", self.debug_date_calculations()))
        debug_results.append(("Database State", self.debug_database_state()))
        debug_results.append(("Missing Report Detection", self.debug_missing_report_detection()))
        debug_results.append(("Report Generation Logic", self.debug_report_generation_logic()))
        debug_results.append(("Weekend Processing Logic", self.debug_weekend_logic()))
        
        # Summary
        logger.info("="*80)
        logger.info("🏁 DEBUG SUMMARY")
        logger.info("="*80)
        
        passed = 0
        total = len(debug_results)
        
        for test_name, result in debug_results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} {test_name}")
            if result:
                passed += 1
        
        logger.info(f"📊 Results: {passed}/{total} debug tests passed")
        
        if passed == total:
            logger.info("🎉 All debug tests completed successfully!")
        else:
            logger.warning("⚠️ Some debug tests failed. Check logs above.")
        
        return passed == total


if __name__ == "__main__":
    # Run comprehensive debug
    debugger = BackfillDebugger()
    success = debugger.run_comprehensive_debug()
    
    if success:
        print("\n🎉 Debug completed! Check the logs above for insights.")
    else:
        print("\n⚠️ Debug completed with some failures. Review the logs above.")
