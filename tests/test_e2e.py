# e2e_test.py
import os
import json
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

# Import the core functions and classes we need to test
from src.database import get_db_connection, init_db
from src.scheduler import run_synthesis_and_save
from src.output.processor import OutputProcessor

# --- Dummy Data Definition ---
# This data is crafted to produce a predictable outcome for our test.
TODAY = datetime.now(timezone.utc)
DUMMY_ARTICLES = [
    # 1. Historical Positive Trend for 'Technology' (3 articles) - THIS IS THE TARGET SIGNAL
    {"url": f"https://e2e.test/hist_tech_{i}", "published_at": TODAY - timedelta(days=i), "title": f"Old Tech News Day {i}", "description": f"Technology sector shows positive momentum on day {i}",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.9}, "entities": [{"text": "Apple", "label": "ORG"}]}}
    for i in range(1, 4)
] + [
    # 2. Today's High-Impact Positive Event for 'Technology' and 'MSFT' (1 article)
    {"url": "https://e2e.test/today_tech_signal", "published_at": TODAY, "title": "Microsoft Unveils New AI Chip in Major Deal", "description": "Microsoft announces groundbreaking AI chip deal that could revolutionize the industry",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.98}, "entities": [{"text": "Microsoft", "label": "ORG"}, {"text": "MSFT", "label": "ORG"}]}},

    # 3. HISTORICAL NOISE ARTICLES (NEW) - To test the filter
    # Day -2
    {"url": "https://e2e.test/hist_noise_d2_1", "published_at": TODAY - timedelta(days=2), "title": "Oil Prices Fluctuate", "description": "Oil prices show mixed movement in global markets", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.8}, "entities": [{"text": "ExxonMobil", "label": "ORG"}]}},
    {"url": "https://e2e.test/hist_noise_d2_2", "published_at": TODAY - timedelta(days=2), "title": "Healthcare Stocks Dip", "description": "Healthcare sector faces regulatory challenges", "nlp_features": {"sentiment": {"label": "negative", "score": 0.85}, "entities": [{"text": "Pfizer", "label": "ORG"}]}},
    # Day -3
    {"url": "https://e2e.test/hist_noise_d3_1", "published_at": TODAY - timedelta(days=3), "title": "Retail Sales Numbers Miss Estimates", "description": "Retail sector underperforms market expectations", "nlp_features": {"sentiment": {"label": "negative", "score": 0.9}, "entities": [{"text": "Walmart", "label": "ORG"}]}},
    {"url": "https://e2e.test/hist_noise_d3_2", "published_at": TODAY - timedelta(days=3), "title": "Industrial Output Rises", "nlp_features": {"sentiment": {"label": "positive", "score": 0.88}, "entities": [{"text": "Boeing", "label": "ORG"}]}},
    # Day -4
    {"url": "https://e2e.test/hist_noise_d4_1", "published_at": TODAY - timedelta(days=4), "title": "Bank Earnings Positive", "description": "Banking sector reports strong quarterly results", "nlp_features": {"sentiment": {"label": "positive", "score": 0.91}, "entities": [{"text": "JPMorgan Chase", "label": "ORG"}]}},
    {"url": "https://e2e.test/hist_noise_d4_2", "published_at": TODAY - timedelta(days=4), "title": "New Drug Trial Fails", "description": "Clinical trial results disappoint investors", "nlp_features": {"sentiment": {"label": "negative", "score": 0.99}, "entities": [{"text": "Moderna", "label": "ORG"}]}},
    # Day -5
    {"url": "https://e2e.test/hist_noise_d5_1", "published_at": TODAY - timedelta(days=5), "title": "Consumer Confidence Report Stable", "description": "Consumer sentiment remains unchanged", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.9}, "entities": []}},
    {"url": "https://e2e.test/hist_noise_d5_2", "published_at": TODAY - timedelta(days=5), "title": "Energy Sector Outlook Mixed", "description": "Energy sector faces uncertain future", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.7}, "entities": [{"text": "Chevron", "label": "ORG"}]}},
    # Day -6
    {"url": "https://e2e.test/hist_noise_d6_1", "published_at": TODAY - timedelta(days=6), "title": "Geopolitical Tensions Ease Slightly", "description": "International relations show improvement", "nlp_features": {"sentiment": {"label": "positive", "score": 0.75}, "entities": []}},
    {"url": "https://e2e.test/hist_noise_d6_2", "published_at": TODAY - timedelta(days=6), "title": "Automaker Announces Recalls", "description": "Vehicle manufacturer issues safety recall", "nlp_features": {"sentiment": {"label": "negative", "score": 0.92}, "entities": [{"text": "Ford", "label": "ORG"}]}},


    # 4. Noise Articles for Today (46 articles) - These should be filtered out by the analysis
    # --- Financial Sector Noise ---
    {"url": "https://e2e.test/noise_fin_1", "published_at": TODAY, "title": "JPMorgan Chase reports steady earnings", "description": "Bank reports consistent financial performance", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.8}, "entities": [{"text": "JPMorgan Chase", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_fin_2", "published_at": TODAY, "title": "Goldman Sachs faces new regulatory probe", "nlp_features": {"sentiment": {"label": "negative", "score": 0.95}, "entities": [{"text": "Goldman Sachs", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_fin_3", "published_at": TODAY, "title": "Federal Reserve hints at interest rate stability", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.9}, "entities": [{"text": "Federal Reserve", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_fin_4", "published_at": TODAY, "title": "Visa transaction volume up 5%", "nlp_features": {"sentiment": {"label": "positive", "score": 0.88}, "entities": [{"text": "Visa", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_fin_5", "published_at": TODAY, "title": "Bank of America expands mobile banking features", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.7}, "entities": [{"text": "Bank of America", "label": "ORG"}]}},

    # --- Healthcare Sector Noise ---
    {"url": "https://e2e.test/noise_health_1", "published_at": TODAY, "title": "Pfizer announces successful trial for new vaccine", "nlp_features": {"sentiment": {"label": "positive", "score": 0.99}, "entities": [{"text": "Pfizer", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_health_2", "published_at": TODAY, "title": "Johnson & Johnson recalls batch of consumer product", "nlp_features": {"sentiment": {"label": "negative", "score": 0.92}, "entities": [{"text": "Johnson & Johnson", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_health_3", "published_at": TODAY, "title": "UnitedHealth Group posts mixed quarterly results", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.6}, "entities": [{"text": "UnitedHealth Group", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_health_4", "published_at": TODAY, "title": "Moderna partners with research institute on mRNA technology", "nlp_features": {"sentiment": {"label": "positive", "score": 0.91}, "entities": [{"text": "Moderna", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_health_5", "published_at": TODAY, "title": "FDA issues new guidelines for medical devices", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.85}, "entities": [{"text": "FDA", "label": "ORG"}]}},

    # --- Energy Sector Noise ---
    {"url": "https://e2e.test/noise_energy_1", "published_at": TODAY, "title": "ExxonMobil to increase dividend payout", "nlp_features": {"sentiment": {"label": "positive", "score": 0.9}, "entities": [{"text": "ExxonMobil", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_energy_2", "published_at": TODAY, "title": "Chevron scales back on renewable energy projects", "nlp_features": {"sentiment": {"label": "negative", "score": 0.8}, "entities": [{"text": "Chevron", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_energy_3", "published_at": TODAY, "title": "OPEC+ meeting concludes with no change to output quotas", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.95}, "entities": [{"text": "OPEC+", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_energy_4", "published_at": TODAY, "title": "Crude oil inventories see surprise draw down", "nlp_features": {"sentiment": {"label": "positive", "score": 0.75}, "entities": []}},
    {"url": "https://e2e.test/noise_energy_5", "published_at": TODAY, "title": "Natural gas prices fall on warmer weather forecasts", "nlp_features": {"sentiment": {"label": "negative", "score": 0.88}, "entities": []}},

    # --- Consumer Goods Noise ---
    {"url": "https://e2e.test/noise_consumer_1", "published_at": TODAY, "title": "Procter & Gamble sales beat expectations", "nlp_features": {"sentiment": {"label": "positive", "score": 0.93}, "entities": [{"text": "Procter & Gamble", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_consumer_2", "published_at": TODAY, "title": "Coca-Cola launches new marketing campaign", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.7}, "entities": [{"text": "Coca-Cola", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_consumer_3", "published_at": TODAY, "title": "Walmart to invest in supply chain automation", "nlp_features": {"sentiment": {"label": "positive", "score": 0.85}, "entities": [{"text": "Walmart", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_consumer_4", "published_at": TODAY, "title": "Home Depot sees slowing demand in housing market", "nlp_features": {"sentiment": {"label": "negative", "score": 0.9}, "entities": [{"text": "Home Depot", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_consumer_5", "published_at": TODAY, "title": "Nike faces backlash over new shoe design", "nlp_features": {"sentiment": {"label": "negative", "score": 0.82}, "entities": [{"text": "Nike", "label": "ORG"}]}},
    
    # --- Industrial Sector Noise ---
    {"url": "https://e2e.test/noise_industrial_1", "published_at": TODAY, "title": "Boeing receives large order from airline", "nlp_features": {"sentiment": {"label": "positive", "score": 0.97}, "entities": [{"text": "Boeing", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_industrial_2", "published_at": TODAY, "title": "Caterpillar reports decline in machinery sales", "nlp_features": {"sentiment": {"label": "negative", "score": 0.91}, "entities": [{"text": "Caterpillar", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_industrial_3", "published_at": TODAY, "title": "General Electric completes spin-off of healthcare unit", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.8}, "entities": [{"text": "General Electric", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_industrial_4", "published_at": TODAY, "title": "Union Pacific rail volumes increase slightly", "nlp_features": {"sentiment": {"label": "positive", "score": 0.6}, "entities": [{"text": "Union Pacific", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_industrial_5", "published_at": TODAY, "title": "3M announces restructuring plan", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.75}, "entities": [{"text": "3M", "label": "ORG"}]}},

    # --- More Tech Noise (should not interfere with signal) ---
    {"url": "https://e2e.test/noise_tech_1", "published_at": TODAY, "title": "Intel delays launch of next-gen processor", "nlp_features": {"sentiment": {"label": "negative", "score": 0.94}, "entities": [{"text": "Intel", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_tech_2", "published_at": TODAY, "title": "IBM secures cloud computing contract with government", "nlp_features": {"sentiment": {"label": "positive", "score": 0.92}, "entities": [{"text": "IBM", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_tech_3", "published_at": TODAY, "title": "Oracle database update patch released", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.8}, "entities": [{"text": "Oracle", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_tech_4", "published_at": TODAY, "title": "Cisco Systems acquires cybersecurity startup", "nlp_features": {"sentiment": {"label": "positive", "score": 0.88}, "entities": [{"text": "Cisco Systems", "label": "ORG"}]}},
    {"url": "https://e2e.test/noise_tech_5", "published_at": TODAY, "title": "Salesforce user conference highlights new features", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.7}, "entities": [{"text": "Salesforce", "label": "ORG"}]}},

    # --- General Market Commentary Noise ---
    {"url": "https://e2e.test/noise_market_1", "published_at": TODAY, "title": "Analysts debate potential for market correction", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.9}, "entities": []}},
    {"url": "https://e2e.test/noise_market_2", "published_at": TODAY, "title": "Inflation data comes in hotter than expected", "nlp_features": {"sentiment": {"label": "negative", "score": 0.96}, "entities": []}},
    {"url": "https://e2e.test/noise_market_3", "published_at": TODAY, "title": "Consumer confidence index shows slight improvement", "nlp_features": {"sentiment": {"label": "positive", "score": 0.7}, "entities": []}},
    {"url": "https://e2e.test/noise_market_4", "published_at": TODAY, "title": "Global supply chain pressures begin to ease", "nlp_features": {"sentiment": {"label": "positive", "score": 0.8}, "entities": []}},
    {"url": "https://e2e.test/noise_market_5", "published_at": TODAY, "title": "Trading volumes are light ahead of holiday weekend", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.98}, "entities": []}},
    {"url": "https://e2e.test/noise_market_6", "published_at": TODAY, "title": "Geopolitical tensions in Asia weigh on investor sentiment", "nlp_features": {"sentiment": {"label": "negative", "score": 0.93}, "entities": []}},
    {"url": "https://e2e.test/noise_market_7", "published_at": TODAY, "title": "Bond yields tick higher on central bank comments", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.85}, "entities": []}},
    {"url": "https://e2e.test/noise_market_8", "published_at": TODAY, "title": "Venture capital funding slows in Q3", "nlp_features": {"sentiment": {"label": "negative", "score": 0.88}, "entities": []}},
    {"url": "https://e2e.test/noise_market_9", "published_at": TODAY, "title": "The future of remote work and its impact on commercial real estate", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.91}, "entities": []}},
    {"url": "https://e2e.test/noise_market_10", "published_at": TODAY, "title": "Emerging markets show surprising resilience", "nlp_features": {"sentiment": {"label": "positive", "score": 0.82}, "entities": []}},
    {"url": "https://e2e.test/noise_market_11", "published_at": TODAY, "title": "Cryptocurrency market remains volatile", "nlp_features": {"sentiment": {"label": "neutral", "score": 0.78}, "entities": []}},
]

def setup_test_environment():
    """Sets up test environment in staging database."""
    print("--- [SETUP] Setting up test environment in staging database ---")
    
    # Initialize staging database with all tables
    from src.database import init_db
    init_db(dbname='stockometry_staging')
    
    # Use staging database for testing
    from src.database import get_db_connection_string
    import psycopg2
    
    staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
    
    try:
        with psycopg2.connect(staging_conn_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                # Clear any existing test data
                cursor.execute("DELETE FROM articles WHERE url LIKE 'https://e2e.test/%';")
                cursor.execute("DELETE FROM daily_reports WHERE report_date = %s;", (TODAY.date(),))
                
                # Insert test articles
                for article in DUMMY_ARTICLES:
                    cursor.execute("""
                        INSERT INTO articles (url, title, description, published_at, nlp_features)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (url) DO NOTHING;
                    """, (
                        article['url'],
                        article['title'],
                        article.get('description', ''),
                        article['published_at'],
                        json.dumps(article['nlp_features'])
                    ))
                
        print(f"Test environment created successfully with {len(DUMMY_ARTICLES)} articles in staging database.")
        
    except Exception as e:
        print(f"Error setting up staging database: {e}")
        raise

def cleanup_test_environment():
    """Cleans up test environment in staging database."""
    print("\n--- [CLEANUP] Cleaning up staging database ---")
    
    # Use staging database for cleanup
    from src.database import get_db_connection_string
    import psycopg2
    
    staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
    
    try:
        with psycopg2.connect(staging_conn_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                # Remove test data from staging database
                cursor.execute("DELETE FROM articles WHERE url LIKE 'https://e2e.test/%';")
                cursor.execute("DELETE FROM daily_reports WHERE report_date = %s;", (TODAY.date(),))
                # report_signals and signal_sources will be deleted automatically due to CASCADE
                
        print("Staging database cleaned up.")
        
    except Exception as e:
        print(f"Error cleaning up staging database: {e}")
    
    # Clean up any test export files
    if os.path.exists("exports"):
        for file in os.listdir("exports"):
            if file.startswith(f"report_{TODAY.date()}_") and file.endswith("_scheduled.json"):
                os.remove(os.path.join("exports", file))
                print(f"Removed test export file: {file}")
    
    print("Test environment cleaned up.")

# --- The Main Test Execution ---
def run_e2e_test():
    """
    Runs the full end-to-end test pipeline.
    """
    setup_test_environment()
    
    try:
        # Patch the database connection to use staging database for analysis
        from src.database import get_db_connection_string
        import psycopg2
        
        def get_staging_db_connection():
            staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
            print(f"DEBUG: Connecting to staging database: {staging_conn_string}")
            return psycopg2.connect(staging_conn_string)
        
        # Patch the database connection in all analysis modules
        with patch('src.analysis.historical_analyzer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('src.analysis.today_analyzer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('src.analysis.synthesizer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('src.output.processor.get_db_connection', side_effect=get_staging_db_connection):
            
            print("\n--- [EXECUTION] Running the end-to-end pipeline on test data in staging database ---")
            
            # Instead of calling run_synthesis_and_save, let's call the analysis directly
            # and then create the OutputProcessor manually with staging database
            from src.analysis.synthesizer import synthesize_analyses
            
            report_object = synthesize_analyses()
            
            if report_object:
                # Create OutputProcessor with staging database connection
                processor = OutputProcessor(report_object, run_source="SCHEDULED")
                
                # Patch the processor's database connection
                with patch('src.output.processor.get_db_connection', side_effect=get_staging_db_connection):
                    report_id = processor.process_and_save()
                    
                    if report_id:
                        print("Scheduled report saved to database successfully")
                        print("Report ID:", report_id)
                    else:
                        print("Failed to save scheduled report to database")
            else:
                print("Synthesizer did not return a report. Skipping output processing.")

        # --- [VERIFICATION] ---
        print("\n--- [VERIFICATION] Checking test results ---")
        
        # 1. Verify Database records in staging database
        staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
        with psycopg2.connect(staging_conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM daily_reports WHERE report_date = %s;", (TODAY.date(),))
                report_row = cursor.fetchone()
                assert report_row is not None, "Report was not saved to the database!"
                report_id = report_row[0]
                print("✅  Report saved to database successfully.")
                
                cursor.execute("SELECT COUNT(*) FROM report_signals WHERE report_id = %s AND signal_type = 'CONFIDENCE';", (report_id,))
                signal_count = cursor.fetchone()[0]
                assert signal_count == 1, "Incorrect number of confidence signals in database!"
                print("✅  Database records were saved correctly.")

        # 2. Test JSON export functionality
        print("\n--- [EXPORT TEST] Testing JSON export functionality ---")
        
        # Create processor instance for export testing
        processor = OutputProcessor({})  # Empty object for export only
        
        # Patch the processor to use staging database
        with patch('src.output.processor.get_db_connection', side_effect=get_staging_db_connection):
            # Export the report to JSON
            json_data = processor.export_to_json(report_id=report_id)
            
            assert json_data is not None, "JSON export failed!"
            assert len(json_data['signals']['confidence']) == 1, "Incorrect number of confidence signals in JSON export!"
            assert json_data['signals']['confidence'][0]['sector'] == 'Technology', "Incorrect sector in JSON export!"
            print("✅  JSON export functionality working correctly.")
            
            # Test file export
            file_path = processor.save_json_to_file(json_data, "exports")
            assert file_path is not None, "File export failed!"
            assert os.path.exists(file_path), "Export file was not created!"
            print(f"✅  JSON file export working: {file_path}")

    except Exception as e:
        print(f"\n❌  An error occurred during the test: {e}")
        raise
    finally:
        cleanup_test_environment()

if __name__ == '__main__':
    run_e2e_test()
