# test_e2e_bullish_tech.py
# Tests bullish technology sector scenarios with various signal combinations
import os
import json
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from stockometry.database import get_db_connection, init_db
from stockometry.core.analysis.synthesizer import synthesize_analyses
from stockometry.core.output.processor import OutputProcessor

# --- Test Scenario: Strong Bullish Technology Sector ---
TODAY = datetime.now(timezone.utc)
DUMMY_ARTICLES = [
    # 1. HISTORICAL BULLISH TREND for Technology (6 days of positive sentiment)
    {"url": f"https://e2e.test/hist_tech_bull_{i}", "published_at": TODAY - timedelta(days=i), 
     "title": f"Tech Sector Shows Strong Growth Day {i}", 
     "description": f"Technology companies report positive earnings and innovation on day {i}",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.85 + (i * 0.02)}, 
                      "entities": [{"text": "Apple", "label": "ORG"}, {"text": "Technology", "label": "SECTOR"}]}}
    for i in range(1, 7)
] + [
    # 2. TODAY'S HIGH-IMPACT BULLISH EVENTS for Technology
    {"url": "https://e2e.test/today_tech_breakthrough", "published_at": TODAY, 
     "title": "Apple Announces Revolutionary AI Chip Breakthrough", 
     "description": "Apple unveils next-generation AI processor that outperforms competitors by 3x",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.98}, 
                      "entities": [{"text": "Apple", "label": "ORG"}, {"text": "AAPL", "label": "ORG"}, {"text": "Technology", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/today_tech_partnership", "published_at": TODAY, 
     "title": "Microsoft and NVIDIA Form Strategic AI Partnership", 
     "description": "Major collaboration announced for next-generation AI infrastructure",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.95}, 
                      "entities": [{"text": "Microsoft", "label": "ORG"}, {"text": "MSFT", "label": "ORG"}, {"text": "NVIDIA", "label": "ORG"}, {"text": "NVDA", "label": "ORG"}, {"text": "Technology", "label": "SECTOR"}]}},
    
    # 3. HISTORICAL NOISE ARTICLES (mixed sectors, should not interfere)
    {"url": "https://e2e.test/hist_fin_1", "published_at": TODAY - timedelta(days=2), 
     "title": "Banking Sector Reports Mixed Results", 
     "description": "Financial institutions show varied performance in Q3",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.7}, 
                      "entities": [{"text": "JPMorgan", "label": "ORG"}, {"text": "Financial", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_health_1", "published_at": TODAY - timedelta(days=3), 
     "title": "Healthcare Innovation Slows", 
     "description": "Clinical trials face regulatory delays",
     "nlp_features": {"sentiment": {"label": "negative", "score": 0.8}, 
                      "entities": [{"text": "Pfizer", "label": "ORG"}, {"text": "Healthcare", "label": "SECTOR"}]}},
    
    # 4. TODAY'S NOISE ARTICLES (should be filtered out)
    {"url": "https://e2e.test/noise_energy_1", "published_at": TODAY, 
     "title": "Oil Prices Stabilize", 
     "description": "Energy markets show minimal movement",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.6}, 
                      "entities": [{"text": "Exxon", "label": "ORG"}, {"text": "Energy", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/noise_consumer_1", "published_at": TODAY, 
     "title": "Retail Sales Flat", 
     "description": "Consumer spending remains unchanged",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.5}, 
                      "entities": [{"text": "Walmart", "label": "ORG"}, {"text": "Consumer", "label": "SECTOR"}]}}
]

def setup_test_environment():
    """Creates test environment using staging database."""
    print("--- [SETUP] Creating bullish tech test environment in staging database ---")
    
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
                
        print(f"Bullish tech test environment created successfully with {len(DUMMY_ARTICLES)} articles.")
        
    except Exception as e:
        print(f"Error setting up staging database: {e}")
        raise

def cleanup_test_environment():
    """Cleans up test environment in staging database."""
    print("\n--- [CLEANUP] Cleaning up bullish tech test environment ---")
    
    from src.database import get_db_connection_string
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
    
    print("Bullish tech test environment cleaned up.")

def run_bullish_tech_test():
    """Runs the bullish technology sector test."""
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
            
            print("\n--- [EXECUTION] Running bullish tech analysis pipeline ---")
            from stockometry.core.analysis.synthesizer import synthesize_analyses
            
            report_object = synthesize_analyses()
            
            if report_object:
                # Create OutputProcessor with staging database connection
                processor = OutputProcessor(report_object, run_source="SCHEDULED")
                
                # Patch the processor's database connection
                with patch('stockometry.core.output.processor.get_db_connection', side_effect=get_staging_db_connection):
                    report_id = processor.process_and_save()
                    
                    if report_id:
                        print("Bullish tech report saved to database successfully")
                        print("Report ID:", report_id)
                    else:
                        print("Failed to save bullish tech report to database")
            else:
                print("Synthesizer did not return a report. Skipping output processing.")

        # Verification
        print("\n--- [VERIFICATION] Checking bullish tech test results ---")
        
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
            
            # Should have historical bullish signal for Technology
            assert len(json_data['signals']['historical']) >= 1, "No historical signals found!"
            tech_historical = [s for s in json_data['signals']['historical'] if s['sector'] == 'Technology']
            assert len(tech_historical) >= 1, "No Technology historical signal found!"
            assert tech_historical[0]['direction'] == 'Bullish', "Technology signal should be Bullish!"
            print("✅  Historical Technology bullish signal found.")
            
            # Should have impact signals for Technology
            if json_data['signals']['impact']:
                tech_impact = [s for s in json_data['signals']['impact'] if s['sector'] == 'Technology']
                if tech_impact:
                    print(f"✅  Technology impact signals found: {len(tech_impact)}")
            
            # Should have confidence signals if both historical and impact align
            if json_data['signals']['confidence']:
                tech_confidence = [s for s in json_data['signals']['confidence'] if s['sector'] == 'Technology']
                if tech_confidence:
                    print(f"✅  Technology confidence signals found: {len(tech_confidence)}")
                    # Check for predicted stocks
                    for signal in tech_confidence:
                        if 'predicted_stocks' in signal:
                            print(f"✅  Predicted stocks: {[s['symbol'] for s in signal['predicted_stocks']]}")
            
            print("✅  JSON export content structure is correct.")
            
            # Test file export
            file_path = processor.save_json_to_file(json_data, "exports")
            assert file_path is not None, "File export failed!"
            assert os.path.exists(file_path), "Export file was not created!"
            print(f"✅  JSON file export working: {file_path}")
                
        print("✅  Bullish tech test completed successfully!")

    except Exception as e:
        print(f"\n❌  An error occurred during the bullish tech test: {e}")
        raise
    finally:
        cleanup_test_environment()

if __name__ == '__main__':
    run_bullish_tech_test()
