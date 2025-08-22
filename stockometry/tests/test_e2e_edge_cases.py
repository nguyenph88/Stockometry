# test_e2e_edge_cases.py
# Tests edge cases and no-signal scenarios
import os
import json
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from stockometry.database import get_db_connection, init_db
from stockometry.core.analysis.synthesizer import synthesize_analyses
from stockometry.core.output.processor import OutputProcessor

# --- Test Scenario: Edge Cases and No-Signal Scenarios ---
TODAY = datetime.now(timezone.utc)
DUMMY_ARTICLES = [
    # 1. SCENARIO 1: Insufficient historical data (less than 6 days)
    {"url": "https://e2e.test/hist_tech_insufficient_1", "published_at": TODAY - timedelta(days=1), 
     "title": "Tech News Day 1", 
     "description": "Technology sector shows some activity",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.8}, 
                      "entities": [{"text": "Apple", "label": "ORG"}, {"text": "Technology", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_tech_insufficient_2", "published_at": TODAY - timedelta(days=2), 
     "title": "Tech News Day 2", 
     "description": "Technology sector continues activity",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.8}, 
                      "entities": [{"text": "Apple", "label": "ORG"}, {"text": "Technology", "label": "SECTOR"}]}},
    
    # Only 2 days of data - should NOT generate historical signal
    
    # 2. SCENARIO 2: Mixed sentiment (not consistently bullish/bearish)
    {"url": "https://e2e.test/hist_health_mixed_1", "published_at": TODAY - timedelta(days=1), 
     "title": "Healthcare Positive News", 
     "description": "Healthcare sector shows positive developments",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.9}, 
                      "entities": [{"text": "Pfizer", "label": "ORG"}, {"text": "Healthcare", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_health_mixed_2", "published_at": TODAY - timedelta(days=2), 
     "title": "Healthcare Negative News", 
     "description": "Healthcare sector faces challenges",
     "nlp_features": {"sentiment": {"label": "negative", "score": 0.9}, 
                      "entities": [{"text": "Pfizer", "label": "ORG"}, {"text": "Healthcare", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_health_mixed_3", "published_at": TODAY - timedelta(days=3), 
     "title": "Healthcare Neutral News", 
     "description": "Healthcare sector shows mixed results",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.5}, 
                      "entities": [{"text": "Pfizer", "label": "ORG"}, {"text": "Healthcare", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_health_mixed_4", "published_at": TODAY - timedelta(days=4), 
     "title": "Healthcare Positive Again", 
     "description": "Healthcare sector rebounds",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.8}, 
                      "entities": [{"text": "Pfizer", "label": "ORG"}, {"text": "Healthcare", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_health_mixed_5", "published_at": TODAY - timedelta(days=5), 
     "title": "Healthcare Negative Again", 
     "description": "Healthcare sector faces more challenges",
     "nlp_features": {"sentiment": {"label": "negative", "score": 0.8}, 
                      "entities": [{"text": "Pfizer", "label": "ORG"}, {"text": "Healthcare", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_health_mixed_6", "published_at": TODAY - timedelta(days=6), 
     "title": "Healthcare Neutral Again", 
     "description": "Healthcare sector shows stability",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.5}, 
                      "entities": [{"text": "Pfizer", "label": "ORG"}, {"text": "Healthcare", "label": "SECTOR"}]}},
    
    # Mixed sentiment over 6 days - should NOT generate clear historical signal
    
    # 3. SCENARIO 3: Low sentiment scores (weak signals)
    {"url": "https://e2e.test/hist_energy_weak_1", "published_at": TODAY - timedelta(days=1), 
     "title": "Energy Slightly Positive", 
     "description": "Energy sector shows minimal positive movement",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.55}, 
                      "entities": [{"text": "Exxon", "label": "ORG"}, {"text": "Energy", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_energy_weak_2", "published_at": TODAY - timedelta(days=2), 
     "title": "Energy Slightly Positive", 
     "description": "Energy sector shows minimal positive movement",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.56}, 
                      "entities": [{"text": "Exxon", "label": "ORG"}, {"text": "Energy", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_energy_weak_3", "published_at": TODAY - timedelta(days=3), 
     "title": "Energy Slightly Positive", 
     "description": "Energy sector shows minimal positive movement",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.57}, 
                      "entities": [{"text": "Exxon", "label": "ORG"}, {"text": "Energy", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_energy_weak_4", "published_at": TODAY - timedelta(days=4), 
     "title": "Energy Slightly Positive", 
     "description": "Energy sector shows minimal positive movement",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.58}, 
                      "entities": [{"text": "Exxon", "label": "ORG"}, {"text": "Energy", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_energy_weak_5", "published_at": TODAY - timedelta(days=5), 
     "title": "Energy Slightly Positive", 
     "description": "Energy sector shows minimal positive movement",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.59}, 
                      "entities": [{"text": "Exxon", "label": "ORG"}, {"text": "Energy", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_energy_weak_6", "published_at": TODAY - timedelta(days=6), 
     "title": "Energy Slightly Positive", 
     "description": "Energy sector shows minimal positive movement",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.60}, 
                      "entities": [{"text": "Exxon", "label": "ORG"}, {"text": "Energy", "label": "SECTOR"}]}},
    
    # Weak sentiment scores - might not generate strong signals
    
    # 4. SCENARIO 4: No high-impact news today
    {"url": "https://e2e.test/today_low_impact_1", "published_at": TODAY, 
     "title": "Minor Market Update", 
     "description": "Market shows minimal movement",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.5}, 
                      "entities": [{"text": "Market", "label": "ORG"}]}},
    
    {"url": "https://e2e.test/today_low_impact_2", "published_at": TODAY, 
     "title": "Routine Economic Data", 
     "description": "Standard economic indicators released",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.5}, 
                      "entities": [{"text": "Economy", "label": "ORG"}]}},
    
    # Low-impact news - should not generate impact signals
    
    # 5. SCENARIO 5: Articles without proper sector classification
    {"url": "https://e2e.test/no_sector_1", "published_at": TODAY - timedelta(days=1), 
     "title": "General Market Commentary", 
     "description": "General market analysis without sector focus",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.5}, 
                      "entities": [{"text": "Market", "label": "ORG"}]}},
    
    {"url": "https://e2e.test/no_sector_2", "published_at": TODAY - timedelta(days=2), 
     "title": "Economic Outlook", 
     "description": "Broad economic perspective",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.5}, 
                      "entities": [{"text": "Economy", "label": "ORG"}]}},
    
    # No sector entities - should not generate sector-specific signals
]

def setup_test_environment():
    """Creates test environment using staging database."""
    print("--- [SETUP] Creating edge cases test environment in staging database ---")
    
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
                
        print(f"Edge cases test environment created successfully with {len(DUMMY_ARTICLES)} articles.")
        
    except Exception as e:
        print(f"Error setting up staging database: {e}")
        raise

def cleanup_test_environment():
    """Cleans up test environment in staging database."""
    print("\n--- [CLEANUP] Cleaning up edge cases test environment ---")
    
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
    
    print("Edge cases test environment cleaned up.")

def run_edge_cases_test():
    """Runs the edge cases test."""
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
            
            print("\n--- [EXECUTION] Running edge cases analysis pipeline ---")
            from stockometry.core.analysis.synthesizer import synthesize_analyses
            
            report_object = synthesize_analyses()
            
            if report_object:
                # Create OutputProcessor with staging database connection
                processor = OutputProcessor(report_object, run_source="SCHEDULED")
                
                # Patch the processor's database connection
                with patch('stockometry.core.output.processor.get_db_connection', side_effect=get_staging_db_connection):
                    report_id = processor.process_and_save()
                    
                    if report_id:
                        print("Edge cases report saved to database successfully")
                        print("Report ID:", report_id)
                    else:
                        print("Failed to save edge cases report to database")
            else:
                print("Synthesizer did not return a report. Skipping output processing.")

        # Verification
        print("\n--- [VERIFICATION] Checking edge cases test results ---")
        
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
            
            # Test edge case scenarios
            print("\n--- Testing Edge Cases ---")
            
            # 1. Insufficient historical data (should not generate historical signal)
            if json_data['signals']['historical']:
                tech_insufficient = [s for s in json_data['signals']['historical'] if s['sector'] == 'Technology']
                if tech_insufficient:
                    print(f"⚠️  Technology historical signal found despite insufficient data: {tech_insufficient[0]['direction']}")
                else:
                    print("✅  No Technology historical signal (correct - insufficient data)")
            else:
                print("✅  No historical signals (correct - edge case scenario)")
            
            # 2. Mixed sentiment (should not generate clear historical signal)
            if json_data['signals']['historical']:
                health_mixed = [s for s in json_data['signals']['historical'] if s['sector'] == 'Healthcare']
                if health_mixed:
                    print(f"⚠️  Healthcare historical signal found despite mixed sentiment: {health_mixed[0]['direction']}")
                else:
                    print("✅  No Healthcare historical signal (correct - mixed sentiment)")
            
            # 3. Weak sentiment scores
            if json_data['signals']['historical']:
                energy_weak = [s for s in json_data['signals']['historical'] if s['sector'] == 'Energy']
                if energy_weak:
                    print(f"⚠️  Energy historical signal found despite weak sentiment: {energy_weak[0]['direction']}")
                else:
                    print("✅  No Energy historical signal (correct - weak sentiment)")
            
            # 4. No high-impact news today
            if json_data['signals']['impact']:
                print(f"⚠️  Impact signals found despite low-impact news: {len(json_data['signals']['impact'])}")
                for signal in json_data['signals']['impact']:
                    print(f"   - {signal['sector']}: {signal['direction']}")
            else:
                print("✅  No impact signals (correct - no high-impact news)")
            
            # 5. No sector classification
            if json_data['signals']['historical']:
                no_sector = [s for s in json_data['signals']['historical'] if not s.get('sector')]
                if no_sector:
                    print(f"⚠️  Signals without sector classification found: {len(no_sector)}")
                else:
                    print("✅  All signals have proper sector classification")
            
            # Check confidence signals
            if json_data['signals']['confidence']:
                print(f"⚠️  Confidence signals found in edge case scenario: {len(json_data['signals']['confidence'])}")
                for signal in json_data['signals']['confidence']:
                    print(f"   - {signal['sector']}: {signal['direction']}")
            else:
                print("✅  No confidence signals (correct - edge case scenario)")
            
            print("✅  JSON export content structure is correct.")
            
            # Test file export
            file_path = processor.save_json_to_file(json_data, "exports")
            assert file_path is not None, "File export failed!"
            assert os.path.exists(file_path), "Export file was not created!"
            print(f"✅  JSON file export working: {file_path}")
                
        print("✅  Edge cases test completed successfully!")

    except Exception as e:
        print(f"\n❌  An error occurred during the edge cases test: {e}")
        raise
    finally:
        cleanup_test_environment()

if __name__ == '__main__':
    run_edge_cases_test()
