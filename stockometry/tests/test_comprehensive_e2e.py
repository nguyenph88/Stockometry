#!/usr/bin/env python3
"""
Comprehensive End-to-End Test for Stockometry
Tests the complete workflow from data collection to API endpoints
Validates database state at each step for easy debugging
"""

import json
import time
import requests
from datetime import datetime, timedelta
from unittest.mock import patch
from stockometry.database import init_db, get_db_connection_string
from stockometry.core.collectors.news_collector import fetch_and_store_news
from stockometry.core.collectors.market_data_collector import fetch_and_store_market_data
from stockometry.core.nlp.processor import process_articles_and_store_features
from stockometry.core.analysis.synthesizer import synthesize_analyses
from stockometry.core.output.processor import OutputProcessor
from stockometry.config import settings
import psycopg2

class ComprehensiveE2ETest:
    """Comprehensive end-to-end test for Stockometry workflow"""
    
    def __init__(self):
        self.test_name = "Comprehensive E2E Test"
        self.start_time = datetime.now()
        self.report_id = None
        self.api_base_url = "http://localhost:8000/stockometry"
        
    def log_step(self, step_name, message=""):
        """Log a test step with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{timestamp}] 🔍 STEP: {step_name}")
        if message:
            print(f"   {message}")
        print("-" * 60)
    
    def log_success(self, message):
        """Log a successful step"""
        print(f"✅ {message}")
    
    def log_error(self, message):
        """Log an error"""
        print(f"❌ {message}")
        raise Exception(message)
    
    def log_info(self, message):
        """Log informational message"""
        print(f"ℹ️  {message}")
    
    def drop_all_tables(self):
        """Step 0: Drop all existing tables to start fresh"""
        self.log_step("Drop All Existing Tables")
        
        try:
            conn_string = get_db_connection_string('stockometry_staging')
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    # Disable foreign key checks temporarily
                    cursor.execute("SET session_replication_role = replica;")
                    
                    # Drop all tables in dependency order
                    tables_to_drop = [
                        'predicted_stocks',
                        'signal_sources', 
                        'report_signals',
                        'daily_reports',
                        'articles',
                        'stock_data'
                    ]
                    
                    for table in tables_to_drop:
                        cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
                        self.log_info(f"Dropped table: {table}")
                    
                    # Re-enable foreign key checks
                    cursor.execute("SET session_replication_role = DEFAULT;")
                    
                    conn.commit()
                    self.log_success("All tables dropped successfully")
                    
        except Exception as e:
            self.log_error(f"Failed to drop tables: {e}")
    
    def check_database_connection(self):
        """Step 1: Verify database connection and initialize schema"""
        self.log_step("Database Connection & Schema Initialization")
        
        try:
            # Initialize database schema (this will create all tables)
            init_db('stockometry_staging')
            self.log_success("Database schema initialized successfully")
            
            # Verify connection
            conn_string = get_db_connection_string('stockometry_staging')
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    # Check if all required tables exist
                    cursor.execute("""
                        SELECT table_name FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name IN ('articles', 'stock_data', 'daily_reports', 'report_signals', 'signal_sources', 'predicted_stocks')
                        ORDER BY table_name;
                    """)
                    tables = [row[0] for row in cursor.fetchall()]
                    
                    expected_tables = ['articles', 'stock_data', 'daily_reports', 'report_signals', 'signal_sources', 'predicted_stocks']
                    missing_tables = set(expected_tables) - set(tables)
                    
                    if missing_tables:
                        self.log_error(f"Missing tables: {missing_tables}")
                    
                    self.log_success(f"All required tables exist: {tables}")
                    
                    # Check articles table structure
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'articles' 
                        ORDER BY column_name;
                    """)
                    columns = [row[0] for row in cursor.fetchall()]
                    
                    required_columns = ['id', 'title', 'url', 'published_at', 'nlp_features']
                    missing_columns = set(required_columns) - set(columns)
                    
                    if missing_columns:
                        self.log_error(f"Missing columns in articles table: {missing_columns}")
                    
                    self.log_success(f"Articles table has all required columns: {len(columns)} columns")
                    
        except Exception as e:
            self.log_error(f"Database connection failed: {e}")
    
    def test_news_collection(self):
        """Step 2: Test news collection and verify database storage"""
        self.log_step("News Collection & Storage")
        
        try:
            # Clear existing articles for clean test
            conn_string = get_db_connection_string('stockometry_staging')
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM articles;")
                    cursor.execute("DELETE FROM report_signals;")
                    cursor.execute("DELETE FROM daily_reports;")
                    conn.commit()
                    self.log_info("Cleared existing test data")
            
            # Collect news
            self.log_info("Fetching news from NewsAPI...")
            fetch_and_store_news()
            
            # Verify articles were stored
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM articles;")
                    article_count = cursor.fetchone()[0]
                    
                    if article_count == 0:
                        self.log_error("No articles were collected")
                    
                    self.log_success(f"Collected {article_count} articles")
                    
                    # Check article structure
                    cursor.execute("""
                        SELECT id, title, url, published_at, nlp_features 
                        FROM articles 
                        LIMIT 3;
                    """)
                    sample_articles = cursor.fetchall()
                    
                    for article in sample_articles:
                        if not article[1] or not article[2]:  # title or url
                            self.log_error(f"Article missing title or URL: {article}")
                    
                    self.log_success("Article structure validation passed")
                    
                    # Check if articles have recent dates
                    cursor.execute("""
                        SELECT COUNT(*) FROM articles 
                        WHERE published_at >= NOW() - INTERVAL '7 days';
                    """)
                    recent_count = cursor.fetchone()[0]
                    
                    if recent_count == 0:
                        self.log_error("No recent articles found")
                    
                    self.log_success(f"Found {recent_count} recent articles (last 7 days)")
                    
        except Exception as e:
            self.log_error(f"News collection test failed: {e}")
    
    def test_market_data_collection(self):
        """Step 3: Test market data collection and verify database storage"""
        self.log_step("Market Data Collection & Storage")
        
        try:
            # Collect market data
            self.log_info("Fetching market data from yfinance...")
            fetch_and_store_market_data()
            
            # Verify market data was stored
            conn_string = get_db_connection_string('stockometry_staging')
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM stock_data;")
                    data_count = cursor.fetchone()[0]
                    
                    if data_count == 0:
                        self.log_error("No market data was collected")
                    
                    self.log_success(f"Collected {data_count} market data records")
                    
                    # Check data structure
                    cursor.execute("""
                        SELECT ticker, date, open, high, low, close, volume 
                        FROM stock_data 
                        LIMIT 3;
                    """)
                    sample_data = cursor.fetchall()
                    
                    for data in sample_data:
                        if not data[0] or not data[1]:  # ticker or date
                            self.log_error(f"Market data missing ticker or date: {data}")
                    
                    self.log_success("Market data structure validation passed")
                    
        except Exception as e:
            self.log_error(f"Market data collection test failed: {e}")
    
    def test_nlp_processing(self):
        """Step 4: Test NLP processing and verify database storage"""
        self.log_step("NLP Processing & Storage")
        
        try:
            # Process articles with NLP
            self.log_info("Processing articles with NLP...")
            process_articles_and_store_features()
            
            # Verify NLP features were stored
            conn_string = get_db_connection_string('stockometry_staging')
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM articles WHERE nlp_features IS NOT NULL;")
                    processed_count = cursor.fetchone()[0]
                    
                    if processed_count == 0:
                        self.log_error("No articles were processed with NLP")
                    
                    self.log_success(f"Processed {processed_count} articles with NLP")
                    
                    # Check NLP features structure
                    cursor.execute("""
                        SELECT id, nlp_features 
                        FROM articles 
                        WHERE nlp_features IS NOT NULL 
                        LIMIT 3;
                    """)
                    sample_features = cursor.fetchall()
                    
                    for article_id, features in sample_features:
                        if not features:
                            self.log_error(f"Article {article_id} has empty NLP features")
                        
                        # Check if features contain expected keys
                        if isinstance(features, dict):
                            if 'sentiment' not in features:
                                self.log_error(f"Article {article_id} missing sentiment in NLP features")
                            if 'entities' not in features:
                                self.log_error(f"Article {article_id} missing entities in NLP features")
                    
                    self.log_success("NLP features structure validation passed")
                    
        except Exception as e:
            self.log_error(f"NLP processing test failed: {e}")
    
    def test_analysis_generation(self):
        """Step 5: Test analysis generation and verify output"""
        self.log_step("Analysis Generation")
        
        try:
            # Generate analysis
            self.log_info("Generating analysis...")
            report_object = synthesize_analyses()
            
            if not report_object:
                self.log_error("Analysis failed to generate report object")
            
            # Verify report structure
            required_keys = ['executive_summary', 'signals']
            missing_keys = set(required_keys) - set(report_object.keys())
            
            if missing_keys:
                self.log_error(f"Report missing required keys: {missing_keys}")
            
            self.log_success("Analysis report generated successfully")
            
            # Check signals structure
            signals = report_object.get('signals', {})
            signal_types = ['historical', 'impact', 'confidence']
            
            for signal_type in signal_types:
                if signal_type not in signals:
                    self.log_info(f"No {signal_type} signals generated (this is normal)")
                else:
                    signal_count = len(signals[signal_type])
                    self.log_info(f"Generated {signal_count} {signal_type} signals")
            
            # Store report object for later use
            self.report_object = report_object
            
        except Exception as e:
            self.log_error(f"Analysis generation test failed: {e}")
    
    def test_report_saving(self):
        """Step 6: Test report saving and verify database storage"""
        self.log_step("Report Saving & Database Storage")
        
        try:
            if not hasattr(self, 'report_object'):
                self.log_error("No report object available for saving")
            
            # Save report to database
            self.log_info("Saving report to database...")
            processor = OutputProcessor(self.report_object, run_source="COMPREHENSIVE_TEST")
            report_id = processor.process_and_save()
            
            if not report_id:
                self.log_error("Failed to save report to database")
            
            self.report_id = report_id
            self.log_success(f"Report saved with ID: {report_id}")
            
            # Verify report was stored in database
            conn_string = get_db_connection_string('stockometry_staging')
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    # Check daily_reports table
                    cursor.execute("SELECT id, report_date, executive_summary, run_source FROM daily_reports WHERE id = %s;", (report_id,))
                    report_row = cursor.fetchone()
                    
                    if not report_row:
                        self.log_error("Report not found in daily_reports table")
                    
                    report_id, report_date, summary, run_source = report_row
                    self.log_success(f"Report found in database: Date={report_date}, Source={run_source}")
                    
                    # Check report_signals table
                    cursor.execute("SELECT COUNT(*) FROM report_signals WHERE report_id = %s;", (report_id,))
                    signal_count = cursor.fetchone()[0]
                    
                    self.log_success(f"Found {signal_count} signals for report {report_id}")
                    
                    if signal_count > 0:
                        # Check signal structure
                        cursor.execute("""
                            SELECT signal_type, sector, direction, details 
                            FROM report_signals 
                            WHERE report_id = %s 
                            LIMIT 3;
                        """, (report_id,))
                        sample_signals = cursor.fetchall()
                        
                        for signal in sample_signals:
                            if not signal[0] or not signal[1]:  # signal_type or sector
                                self.log_error(f"Signal missing required fields: {signal}")
                        
                        self.log_success("Signal structure validation passed")
                    
        except Exception as e:
            self.log_error(f"Report saving test failed: {e}")
    
    def test_json_export(self):
        """Step 7: Test JSON export functionality"""
        self.log_step("JSON Export Functionality")
        
        try:
            if not self.report_id:
                self.log_error("No report ID available for export")
            
            # Test export to JSON
            self.log_info("Testing JSON export...")
            processor = OutputProcessor({}, run_source="COMPREHENSIVE_TEST")
            json_data = processor.export_to_json(report_id=self.report_id)
            
            if not json_data:
                self.log_error("JSON export failed")
            
            # Verify JSON structure
            required_keys = ['report_id', 'report_date', 'executive_summary', 'signals']
            missing_keys = set(required_keys) - set(json_data.keys())
            
            if missing_keys:
                self.log_error(f"JSON export missing required keys: {missing_keys}")
            
            self.log_success("JSON export structure validation passed")
            
            # Test file export
            self.log_info("Testing file export...")
            file_path = processor.save_json_to_file(json_data, "exports")
            
            if not file_path:
                self.log_error("File export failed")
            
            self.log_success(f"Report exported to file: {file_path}")
            
        except Exception as e:
            self.log_error(f"JSON export test failed: {e}")
    
    def test_api_endpoints(self):
        """Step 8: Test API endpoints (if FastAPI server is running)"""
        self.log_step("API Endpoints Testing")
        
        try:
            # Test if API server is accessible
            try:
                response = requests.get(f"{self.api_base_url}/health", timeout=5)
                if response.status_code != 200:
                    self.log_info("API server not accessible, skipping endpoint tests")
                    return
            except requests.exceptions.RequestException:
                self.log_info("API server not running, skipping endpoint tests")
                return
            
            self.log_info("API server accessible, testing endpoints...")
            
            # Test health endpoint
            response = requests.get(f"{self.api_base_url}/health")
            if response.status_code != 200:
                self.log_error(f"Health endpoint failed: {response.status_code}")
            self.log_success("Health endpoint working")
            
            # Test latest report endpoint
            response = requests.get(f"{self.api_base_url}/reports/latest")
            if response.status_code != 200:
                self.log_error(f"Latest report endpoint failed: {response.status_code}")
            
            latest_data = response.json()
            if 'executive_summary' not in latest_data:
                self.log_error("Latest report endpoint missing executive_summary")
            self.log_success("Latest report endpoint working")
            
            # Test specific report endpoint
            if self.report_id:
                response = requests.get(f"{self.api_base_url}/reports/{self.report_id}")
                if response.status_code != 200:
                    self.log_error(f"Specific report endpoint failed: {response.status_code}")
                
                report_data = response.json()
                if report_data.get('report_id') != self.report_id:
                    self.log_error("Specific report endpoint returned wrong report")
                self.log_success("Specific report endpoint working")
            
            # Test export endpoint
            if self.report_id:
                response = requests.get(f"{self.api_base_url}/export/{self.report_id}/json")
                if response.status_code != 200:
                    self.log_error(f"Export endpoint failed: {response.status_code}")
                
                export_data = response.json()
                if 'report_id' not in export_data:
                    self.log_error("Export endpoint missing report_id")
                self.log_success("Export endpoint working")
            
        except Exception as e:
            self.log_error(f"API endpoints test failed: {e}")
    
    def cleanup_test_data(self):
        """Step 9: Clean up test data"""
        self.log_step("Test Data Cleanup")
        
        try:
            conn_string = get_db_connection_string('stockometry_staging')
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    # Get counts before cleanup for reporting
                    cursor.execute("SELECT COUNT(*) FROM daily_reports;")
                    reports_before = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM report_signals;")
                    signals_before = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM articles;")
                    articles_before = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM stock_data;")
                    stock_data_before = cursor.fetchone()[0]
                    
                    self.log_info(f"Before cleanup: {reports_before} reports, {signals_before} signals, {articles_before} articles, {stock_data_before} stock records")
                    
                    # Clean up in reverse dependency order to avoid foreign key constraint violations
                    if self.report_id:
                        # Clean up specific test report data
                        cursor.execute("DELETE FROM predicted_stocks WHERE signal_id IN (SELECT id FROM report_signals WHERE report_id = %s);", (self.report_id,))
                        cursor.execute("DELETE FROM signal_sources WHERE signal_id IN (SELECT id FROM report_signals WHERE report_id = %s);", (self.report_id,))
                        cursor.execute("DELETE FROM report_signals WHERE report_id = %s;", (self.report_id,))
                        cursor.execute("DELETE FROM daily_reports WHERE id = %s;", (self.report_id,))
                        self.log_success(f"Test report {self.report_id} data cleaned up")
                    
                    # Clean up all test-related data
                    # Note: report_signals doesn't have run_source column, so we clean up by report_id
                    if self.report_id:
                        cursor.execute("DELETE FROM predicted_stocks WHERE signal_id IN (SELECT id FROM report_signals WHERE report_id = %s);", (self.report_id,))
                        cursor.execute("DELETE FROM signal_sources WHERE signal_id IN (SELECT id FROM report_signals WHERE report_id = %s);", (self.report_id,))
                        cursor.execute("DELETE FROM report_signals WHERE report_id = %s;", (self.report_id,))
                        cursor.execute("DELETE FROM daily_reports WHERE id = %s;", (self.report_id,))
                    else:
                        # If no specific report_id, clean up all data
                        cursor.execute("DELETE FROM predicted_stocks;")
                        cursor.execute("DELETE FROM signal_sources;")
                        cursor.execute("DELETE FROM report_signals;")
                        cursor.execute("DELETE FROM daily_reports;")
                    
                    # Clean up test articles (identified by test URLs or recent test data)
                    cursor.execute("DELETE FROM articles WHERE url LIKE '%test%' OR url LIKE '%e2e%';")
                    
                    # Clean up any orphaned data
                    cursor.execute("DELETE FROM predicted_stocks WHERE signal_id NOT IN (SELECT id FROM report_signals);")
                    cursor.execute("DELETE FROM signal_sources WHERE signal_id NOT IN (SELECT id FROM report_signals);")
                    
                    conn.commit()
                    
                    # Get counts after cleanup
                    cursor.execute("SELECT COUNT(*) FROM daily_reports;")
                    reports_after = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM report_signals;")
                    signals_after = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM articles;")
                    articles_after = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM stock_data;")
                    stock_data_after = cursor.fetchone()[0]
                    
                    self.log_success(f"After cleanup: {reports_after} reports, {signals_after} signals, {articles_after} articles, {stock_data_after} stock records")
                    
                    # Report cleanup summary
                    reports_cleaned = reports_before - reports_after
                    signals_cleaned = signals_before - signals_after
                    articles_cleaned = articles_before - articles_after
                    
                    if reports_cleaned > 0 or signals_cleaned > 0 or articles_cleaned > 0:
                        self.log_success(f"Cleanup summary: {reports_cleaned} reports, {signals_cleaned} signals, {articles_cleaned} articles removed")
                    else:
                        self.log_success("No test data found to clean up")
                    
        except Exception as e:
            self.log_error(f"Cleanup failed: {e}")
    
    def cleanup_staging_database(self):
        """Step 10: Complete staging database cleanup"""
        self.log_step("Complete Staging Database Cleanup")
        
        try:
            conn_string = get_db_connection_string('stockometry_staging')
            with psycopg2.connect(conn_string) as conn:
                with conn.cursor() as cursor:
                    # Get database size before cleanup
                    cursor.execute("""
                        SELECT pg_size_pretty(pg_database_size('stockometry_staging')) as db_size;
                    """)
                    db_size_before = cursor.fetchone()[0]
                    self.log_info(f"Database size before cleanup: {db_size_before}")
                    
                    # Clean up all test-related data completely
                    cursor.execute("DELETE FROM predicted_stocks;")
                    cursor.execute("DELETE FROM signal_sources;")
                    cursor.execute("DELETE FROM report_signals;")
                    cursor.execute("DELETE FROM daily_reports;")
                    cursor.execute("DELETE FROM articles;")
                    cursor.execute("DELETE FROM stock_data;")
                    
                    # Reset auto-increment counters
                    cursor.execute("ALTER SEQUENCE daily_reports_id_seq RESTART WITH 1;")
                    cursor.execute("ALTER SEQUENCE report_signals_id_seq RESTART WITH 1;")
                    cursor.execute("ALTER SEQUENCE articles_id_seq RESTART WITH 1;")
                    cursor.execute("ALTER SEQUENCE stock_data_id_seq RESTART WITH 1;")
                    cursor.execute("ALTER SEQUENCE predicted_stocks_id_seq RESTART WITH 1;")
                    cursor.execute("ALTER SEQUENCE signal_sources_id_seq RESTART WITH 1;")
                    
                    conn.commit()
                    
                    # Get database size after cleanup
                    cursor.execute("""
                        SELECT pg_size_pretty(pg_database_size('stockometry_staging')) as db_size;
                    """)
                    db_size_after = cursor.fetchone()[0]
                    
                    # Verify all tables are empty
                    cursor.execute("SELECT COUNT(*) FROM daily_reports;")
                    reports_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM report_signals;")
                    signals_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM articles;")
                    articles_count = cursor.fetchone()[0]
                    cursor.execute("SELECT COUNT(*) FROM stock_data;")
                    stock_count = cursor.fetchone()[0]
                    
                    if reports_count == 0 and signals_count == 0 and articles_count == 0 and stock_count == 0:
                        self.log_success("All tables successfully emptied")
                    else:
                        self.log_error(f"Tables not empty: reports={reports_count}, signals={signals_count}, articles={articles_count}, stock={stock_count}")
                    
                    self.log_success(f"Database size after cleanup: {db_size_after}")
                    self.log_success("Complete staging database cleanup finished")
                    
        except Exception as e:
            self.log_error(f"Complete database cleanup failed: {e}")
    
    def run_comprehensive_test(self):
        """Run the complete comprehensive end-to-end test"""
        print(f"\n🚀 STARTING {self.test_name}")
        print(f"📅 Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌍 Environment: {settings.environment}")
        print(f"🗄️  Database: {settings.db_name_active}")
        print("=" * 80)
        
        try:
            # Run all test steps
            self.drop_all_tables()
            self.check_database_connection()
            self.test_news_collection()
            self.test_market_data_collection()
            self.test_nlp_processing()
            self.test_analysis_generation()
            self.test_report_saving()
            self.test_json_export()
            self.test_api_endpoints()
            self.cleanup_test_data()
            self.cleanup_staging_database()
            
            # Test completed successfully
            end_time = datetime.now()
            duration = end_time - self.start_time
            
            print("\n" + "=" * 80)
            print(f"🎉 {self.test_name} COMPLETED SUCCESSFULLY!")
            print(f"⏱️  Total duration: {duration}")
            print(f"📊 All workflow stages validated")
            print(f"🗄️  Database state verified at each step")
            print(f"🔌 API endpoints tested")
            print("=" * 80)
            
            return True
            
        except Exception as e:
            end_time = datetime.now()
            duration = end_time - self.start_time
            
            print("\n" + "=" * 80)
            print(f"💥 {self.test_name} FAILED!")
            print(f"❌ Error: {e}")
            print(f"⏱️  Duration before failure: {duration}")
            print(f"🔍 Check the step above for details")
            print("=" * 80)
            
            # Clean up on failure
            try:
                self.cleanup_test_data()
            except:
                pass
            
            return False

def run_comprehensive_e2e_test():
    """Main function to run the comprehensive E2E test"""
    test = ComprehensiveE2ETest()
    return test.run_comprehensive_test()

if __name__ == "__main__":
    run_comprehensive_e2e_test()
