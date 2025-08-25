"""
Test Backfill System - Debug and Test Without API Calls

This module tests the backfill logic step by step using existing database data.
No API calls are made - we only test the analysis and synthesis logic.
"""

import logging
from datetime import datetime, timezone, date
from typing import Dict, Any

from ..database import get_db_connection
from ..core.analysis.historical_analyzer import analyze_historical_trends
from ..core.analysis.today_analyzer import analyze_impact_for_date
from ..core.output.processor import OutputProcessor

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackfillTester:
    """Test class to debug backfill logic without API calls"""
    
    def __init__(self):
        """Initialize the tester"""
        logger.info("🔧 BackfillTester initialized")
    
    def test_database_connection(self):
        """Test database connection and show current data"""
        logger.info("="*50)
        logger.info("TEST 1: Database Connection")
        logger.info("="*50)
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check current database
                cursor.execute("SELECT current_database();")
                current_db = cursor.fetchone()[0]
                logger.info(f"✅ Connected to database: {current_db}")
                
                # Check articles table
                cursor.execute("SELECT COUNT(*) FROM articles;")
                article_count = cursor.fetchone()[0]
                logger.info(f"📰 Total articles in database: {article_count}")
                
                # Check daily_reports table
                cursor.execute("SELECT COUNT(*) FROM daily_reports;")
                report_count = cursor.fetchone()[0]
                logger.info(f"📊 Total reports in database: {report_count}")
                
                # Show recent reports
                cursor.execute("""
                    SELECT report_date, run_source, created_at 
                    FROM daily_reports 
                    ORDER BY report_date DESC 
                    LIMIT 5;
                """)
                recent_reports = cursor.fetchall()
                
                logger.info("📅 Recent reports:")
                for report_date, run_source, created_at in recent_reports:
                    logger.info(f"  {report_date} | {run_source} | {created_at}")
                
                cursor.close()
                return True
                
        except Exception as e:
            logger.error(f"❌ Database test failed: {str(e)}")
            return False
    
    def test_article_dates(self, test_date: date):
        """Test what articles exist for a specific date"""
        logger.info("="*50)
        logger.info(f"TEST 2: Articles for {test_date}")
        logger.info("="*50)
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check articles for specific date
                cursor.execute("""
                    SELECT COUNT(*) FROM articles 
                    WHERE published_at::date = %s;
                """, (test_date,))
                date_articles = cursor.fetchone()[0]
                logger.info(f"📰 Articles for {test_date}: {date_articles}")
                
                # Check articles for previous day (fallback)
                prev_date = test_date.replace(day=test_date.day - 1)
                cursor.execute("""
                    SELECT COUNT(*) FROM articles 
                    WHERE published_at::date = %s;
                """, (prev_date,))
                prev_articles = cursor.fetchone()[0]
                logger.info(f"📰 Articles for {prev_date} (fallback): {prev_articles}")
                
                # Show sample articles
                cursor.execute("""
                    SELECT title, published_at, nlp_features IS NOT NULL as has_nlp
                    FROM articles 
                    WHERE published_at::date = %s
                    LIMIT 3;
                """, (test_date,))
                sample_articles = cursor.fetchall()
                
                logger.info(f"📝 Sample articles for {test_date}:")
                for title, pub_date, has_nlp in sample_articles:
                    logger.info(f"  '{title[:50]}...' | {pub_date} | NLP: {has_nlp}")
                
                cursor.close()
                return date_articles > 0 or prev_articles > 0
                
        except Exception as e:
            logger.error(f"❌ Article date test failed: {str(e)}")
            return False
    
    def test_impact_analysis(self, test_date: date):
        """Test the impact analysis function for a specific date"""
        logger.info("="*50)
        logger.info(f"TEST 3: Impact Analysis for {test_date}")
        logger.info("="*50)
        
        try:
            # Test the new function
            result = analyze_impact_for_date(test_date)
            
            logger.info(f"✅ Impact analysis completed for {test_date}")
            logger.info(f"📊 Signals found: {len(result['signals'])}")
            logger.info(f"📝 Summary points: {len(result['summary_points'])}")
            
            if result['signals']:
                logger.info("🎯 Sample signals:")
                for signal in result['signals'][:2]:  # Show first 2
                    logger.info(f"  {signal['type']} | {signal['sector']} | {signal['direction']}")
            
            if result['summary_points']:
                logger.info("📋 Summary points:")
                for point in result['summary_points'][:2]:  # Show first 2
                    logger.info(f"  {point}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Impact analysis test failed: {str(e)}")
            return False
    
    def test_synthesis(self, test_date: date):
        """Test the complete synthesis process for a specific date"""
        logger.info("="*50)
        logger.info(f"TEST 4: Complete Synthesis for {test_date}")
        logger.info("="*50)
        
        try:
            # Test historical trends
            logger.info("🔄 Testing historical trends...")
            historical_result = analyze_historical_trends()
            logger.info(f"✅ Historical trends: {len(historical_result['signals'])} signals")
            
            # Test impact analysis
            logger.info("🔄 Testing impact analysis...")
            impact_result = analyze_impact_for_date(test_date)
            logger.info(f"✅ Impact analysis: {len(impact_result['signals'])} signals")
            
            # Combine results
            all_signals = historical_result['signals'] + impact_result['signals']
            summary_points = historical_result['summary_points'] + impact_result['summary_points']
            executive_summary = " ".join(summary_points)
            
            logger.info(f"🎯 Combined signals: {len(all_signals)}")
            logger.info(f"📝 Combined summary points: {len(summary_points)}")
            logger.info(f"📄 Executive summary length: {len(executive_summary)} characters")
            
            # Create synthesis result
            synthesis_result = {
                "executive_summary": executive_summary,
                "signals": {
                    "historical": historical_result['signals'],
                    "impact": impact_result['signals'],
                    "confidence": []
                }
            }
            
            logger.info("✅ Synthesis test completed successfully")
            return synthesis_result
            
        except Exception as e:
            logger.error(f"❌ Synthesis test failed: {str(e)}")
            return None
    
    def test_report_saving(self, test_date: date, synthesis_result: Dict[str, Any]):
        """Test saving a report to the database"""
        logger.info("="*50)
        logger.info(f"TEST 5: Report Saving for {test_date}")
        logger.info("="*50)
        
        try:
            # Create output processor
            output_processor = OutputProcessor(
                report_object=synthesis_result, 
                run_source="TEST"
            )
            
            logger.info("🔄 Attempting to save report...")
            
            # Try to save
            saved_report = output_processor.process_and_save()
            
            if saved_report:
                logger.info(f"✅ Report saved successfully! ID: {saved_report}")
                return True
            else:
                logger.warning("⚠️ Report save returned no result")
                return False
                
        except Exception as e:
            logger.error(f"❌ Report saving test failed: {str(e)}")
            return False
    
    def run_all_tests(self, test_date: date = None):
        """Run all tests for a specific date"""
        if test_date is None:
            test_date = date(2025, 8, 20)  # Use a past date for testing
        
        logger.info("🚀 Starting Backfill System Tests")
        logger.info(f"📅 Test date: {test_date}")
        logger.info("="*60)
        
        # Run tests
        tests_passed = 0
        total_tests = 5
        
        # Test 1: Database connection
        if self.test_database_connection():
            tests_passed += 1
        
        # Test 2: Article dates
        if self.test_article_dates(test_date):
            tests_passed += 1
        
        # Test 3: Impact analysis
        if self.test_impact_analysis(test_date):
            tests_passed += 1
        
        # Test 4: Synthesis
        synthesis_result = self.test_synthesis(test_date)
        if synthesis_result:
            tests_passed += 1
            
            # Test 5: Report saving (only if synthesis worked)
            if self.test_report_saving(test_date, synthesis_result):
                tests_passed += 1
        
        # Final results
        logger.info("="*60)
        logger.info("🏁 TEST RESULTS")
        logger.info("="*60)
        logger.info(f"✅ Tests passed: {tests_passed}/{total_tests}")
        logger.info(f"❌ Tests failed: {total_tests - tests_passed}/{total_tests}")
        
        if tests_passed == total_tests:
            logger.info("🎉 All tests passed! Backfill system is working correctly.")
        else:
            logger.warning("⚠️ Some tests failed. Check the logs above for details.")
        
        return tests_passed == total_tests


if __name__ == "__main__":
    # Run tests
    tester = BackfillTester()
    
    # Test with a specific date
    test_date = date(2025, 8, 20)  # Adjust this date as needed
    success = tester.run_all_tests(test_date)
    
    if success:
        print("\n🎉 All tests passed! The backfill system is ready.")
    else:
        print("\n⚠️ Some tests failed. Review the logs above.")
