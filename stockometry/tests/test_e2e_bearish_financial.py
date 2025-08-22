# test_e2e_bearish_financial.py
# Tests bearish financial sector scenarios with various signal combinations
import os
import json
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from stockometry.database import get_db_connection, init_db
from stockometry.core.analysis.synthesizer import synthesize_analyses
from stockometry.core.output.processor import OutputProcessor

# --- Test Scenario: Bearish Financial Sector ---
TODAY = datetime.now(timezone.utc)
DUMMY_ARTICLES = [
    # 1. HISTORICAL BEARISH TREND for Financial (6 days of negative sentiment)
    {"url": f"https://e2e.test/hist_fin_bear_{i}", "published_at": TODAY - timedelta(days=i), 
     "title": f"Financial Sector Faces Challenges Day {i}", 
     "description": f"Banks and financial institutions report declining performance on day {i}",
     "nlp_features": {"sentiment": {"label": "negative", "score": 0.95}, 
                      "entities": [{"text": "JPMorgan", "label": "ORG"}]}}
    for i in range(1, 7)
] + [
    # 2. TODAY'S HIGH-IMPACT BEARISH EVENTS for Financial
    {"url": "https://e2e.test/today_fin_regulation", "published_at": TODAY, 
     "title": "Federal Reserve Announces Stricter Banking Regulations", 
     "description": "New capital requirements could reduce bank profitability by 15%",
     "nlp_features": {"sentiment": {"label": "negative", "score": 0.95}, 
                      "entities": [{"text": "JPMorgan", "label": "ORG"}]}},
    
    {"url": "https://e2e.test/today_fin_scandal", "published_at": TODAY, 
     "title": "Major Bank Faces Regulatory Investigation", 
     "description": "SEC launches probe into alleged accounting irregularities",
     "nlp_features": {"sentiment": {"label": "negative", "score": 0.98}, 
                      "entities": [{"text": "Goldman Sachs", "label": "ORG"}, {"text": "GS", "label": "ORG"}]}},
    
    # 3. HISTORICAL NOISE ARTICLES (mixed sectors, should not interfere)
    {"url": "https://e2e.test/hist_tech_1", "published_at": TODAY - timedelta(days=2), 
     "title": "Technology Sector Shows Innovation", 
     "description": "Tech companies continue to innovate",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.8}, 
                      "entities": [{"text": "Apple", "label": "ORG"}, {"text": "Technology", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_health_1", "published_at": TODAY - timedelta(days=3), 
     "title": "Healthcare Breakthrough Announced", 
     "description": "New drug shows promising results",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.9}, 
                      "entities": [{"text": "Pfizer", "label": "ORG"}, {"text": "Healthcare", "label": "SECTOR"}]}},
    
    # 4. TODAY'S NOISE ARTICLES (should be filtered out)
    {"url": "https://e2e.test/noise_energy_1", "published_at": TODAY, 
     "title": "Oil Prices Rise Slightly", 
     "description": "Energy markets show minimal gains",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.6}, 
                      "entities": [{"text": "Exxon", "label": "ORG"}, {"text": "Energy", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/noise_consumer_1", "published_at": TODAY, 
     "title": "Consumer Confidence Stable", 
     "description": "Retail sentiment remains unchanged",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.5}, 
                      "entities": [{"text": "Walmart", "label": "ORG"}, {"text": "Consumer", "label": "SECTOR"}]}}
]

def setup_test_environment():
    """Creates test environment using staging database."""
    print("--- [SETUP] Creating bearish financial test environment in staging database ---")
    
    # Initialize staging database with all tables
    from stockometry.database import init_db
    init_db(dbname='stockometry_staging')
    
    from stockometry.database import get_db_connection_string
    import psycopg2
    
    staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
    
    try:
        with psycopg2.connect(staging_conn_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                # Clear any existing test data
                cursor.execute("DELETE FROM articles WHERE url LIKE 'https://e2e.test/%';")
                cursor.execute("DELETE FROM daily_reports WHERE report_date = %s;", (TODAY.date(),))
                
                # Insert test data
                for article in DUMMY_ARTICLES:
                    cursor.execute(
                        "INSERT INTO articles (url, published_at, nlp_features, title, description) VALUES (%s, %s, %s, %s, %s);",
                        (article['url'], article['published_at'], json.dumps(article['nlp_features']), article['title'], article.get('description', ''))
                    )
                
        print(f"Bearish financial test environment created successfully with {len(DUMMY_ARTICLES)} articles.")
        
    except Exception as e:
        print(f"Error setting up staging database: {e}")
        raise

def cleanup_test_environment():
    """Cleans up test environment in staging database."""
    print("\n--- [CLEANUP] Cleaning up bearish financial test environment ---")
    
    from stockometry.database import get_db_connection_string
    import psycopg2
    
    staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
    
    try:
        with psycopg2.connect(staging_conn_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM articles WHERE url LIKE 'https://e2e.test/%';")
                cursor.execute("DELETE FROM daily_reports WHERE report_date = %s;", (TODAY.date(),))
                
        print("Staging database cleaned up.")
        
    except Exception as e:
        print(f"Error cleaning up staging database: {e}")
    
    # Remove test output file
    output_file = os.path.join("output", f"report_{TODAY.date()}.json")
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Removed test output file: {output_file}")
    
    # Clean up any test export files
    if os.path.exists("exports"):
        for file in os.listdir("exports"):
            if file.startswith(f"report_{TODAY.date()}_") and file.endswith("_scheduled.json"):
                os.remove(os.path.join("exports", file))
                print(f"Removed test export file: {file}")
    
    print("Bearish financial test environment cleaned up.")

def run_bearish_financial_test():
    """Runs the bearish financial sector test."""
    setup_test_environment()
    
    try:
        from stockometry.database import get_db_connection_string
        import psycopg2
        
        def get_staging_db_connection():
            staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
            return psycopg2.connect(staging_conn_string)
        
        # Patch database connections
        with patch('stockometry.core.analysis.historical_analyzer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('stockometry.core.analysis.today_analyzer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('stockometry.core.analysis.synthesizer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('stockometry.core.output.processor.get_db_connection', side_effect=get_staging_db_connection):
            
            print("\n--- [EXECUTION] Running bearish financial analysis pipeline ---")
            from stockometry.core.analysis.synthesizer import synthesize_analyses
            
            report_object = synthesize_analyses()
            
            if report_object:
                # Create OutputProcessor with staging database connection
                processor = OutputProcessor(report_object, run_source="SCHEDULED")
                
                # Patch the processor's database connection
                with patch('stockometry.core.output.processor.get_db_connection', side_effect=get_staging_db_connection):
                    report_id = processor.process_and_save()
                    
                    if report_id:
                        print("Bearish financial report saved to database successfully")
                        print("Report ID:", report_id)
                    else:
                        print("Failed to save bearish financial report to database")
            else:
                print("Synthesizer did not return a report. Skipping output processing.")

        # Verification
        print("\n--- [VERIFICATION] Checking bearish financial test results ---")
        
        # 1. Verify Database records in staging database
        staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
        with psycopg2.connect(staging_conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM daily_reports WHERE report_date = %s;", (TODAY.date(),))
                report_row = cursor.fetchone()
                assert report_row is not None, "Report was not saved to the database!"
                report_id = report_row[0]
                print("✅  Report saved to database successfully.")
                
                cursor.execute("SELECT COUNT(*) FROM report_signals WHERE report_id = %s;", (report_id,))
                signal_count = cursor.fetchone()[0]
                print(f"✅  {signal_count} signals saved to database.")
        
        # 2. Test JSON export functionality
        print("\n--- [EXPORT TEST] Testing JSON export functionality ---")
        
        # Create processor instance for export testing
        processor = OutputProcessor({})  # Empty object for export only
        
        # Patch the processor to use staging database
        with patch('stockometry.core.output.processor.get_db_connection', side_effect=get_staging_db_connection):
            # Export the report to JSON
            json_data = processor.export_to_json(report_id=report_id)
            
            assert json_data is not None, "JSON export failed!"
            print(f"✅  Executive Summary: {json_data.get('executive_summary', 'MISSING!')}")
            
            # Should have historical bearish signal for Financial Services
            assert len(json_data['signals']['historical']) >= 1, "No historical signals found!"
            fin_historical = [s for s in json_data['signals']['historical'] if s['sector'] == 'Financial Services']
            assert len(fin_historical) >= 1, "No Financial Services historical signal found!"
            assert fin_historical[0]['direction'] == 'Bearish', "Financial Services signal should be Bearish!"
            print("✅  Historical Financial Services bearish signal found.")
            
            # Should have impact signals for Financial Services
            if json_data['signals']['impact']:
                fin_impact = [s for s in json_data['signals']['impact'] if s['sector'] == 'Financial Services']
                if fin_impact:
                    print(f"✅  Financial Services impact signals found: {len(fin_impact)}")
                    for signal in fin_impact:
                        print(f"   - {signal['direction']}: {signal['details']}")
            
            # Should have confidence signals if both historical and impact align
            if json_data['signals']['confidence']:
                fin_confidence = [s for s in json_data['signals']['confidence'] if s['sector'] == 'Financial Services']
                if fin_confidence:
                    print(f"✅  Financial Services confidence signals found: {len(fin_confidence)}")
                    # Check for predicted stocks
                    for signal in fin_confidence:
                        if 'predicted_stocks' in signal:
                            print(f"✅  Predicted stocks: {[s['symbol'] for s in signal['predicted_stocks']]}")
            
            print("✅  JSON export content structure is correct.")
            
            # Test file export
            file_path = processor.save_json_to_file(json_data, "exports")
            assert file_path is not None, "File export failed!"
            assert os.path.exists(file_path), "Export file was not created!"
            print(f"✅  JSON file export working: {file_path}")
                
        print("✅  Bearish financial test completed successfully!")

    except Exception as e:
        print(f"\n❌  An error occurred during the bearish financial test: {e}")
        raise
    finally:
        cleanup_test_environment()

if __name__ == '__main__':
    run_bearish_financial_test()
