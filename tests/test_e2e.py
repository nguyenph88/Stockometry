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

# --- Test Environment Management ---

def setup_test_environment():
    """Creates test environment using staging database."""
    print("--- [SETUP] Creating test environment in staging database ---")
    
    # Use staging database for testing
    from src.database import get_db_connection_string
    from src.config import settings
    import psycopg2
    
    # Connect to staging database
    staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
    
    try:
        with psycopg2.connect(staging_conn_string) as conn:
            conn.autocommit = True
            with conn.cursor() as cursor:
                # Drop existing tables to ensure clean schema
                cursor.execute("DROP TABLE IF EXISTS signal_sources CASCADE;")
                cursor.execute("DROP TABLE IF EXISTS report_signals CASCADE;")
                cursor.execute("DROP TABLE IF EXISTS daily_reports CASCADE;")
                cursor.execute("DROP TABLE IF EXISTS articles CASCADE;")
                
                # Create tables with correct schema
                cursor.execute("""
                    CREATE TABLE articles (
                        id SERIAL PRIMARY KEY,
                        source_id VARCHAR(255),
                        source_name VARCHAR(255),
                        author VARCHAR(255),
                        title TEXT NOT NULL,
                        url TEXT UNIQUE NOT NULL,
                        description TEXT,
                        content TEXT,
                        published_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        nlp_features JSONB
                    );
                """)
                
                # Insert test data
                for article in DUMMY_ARTICLES:
                    cursor.execute(
                        "INSERT INTO articles (url, published_at, nlp_features, title, description) VALUES (%s, %s, %s, %s, %s);",
                        (article['url'], article['published_at'], json.dumps(article['nlp_features']), article['title'], article.get('description', ''))
                    )
                
                # Create output tables with correct schema (matching OutputProcessor)
                cursor.execute("""
                    CREATE TABLE daily_reports (
                        id SERIAL PRIMARY KEY,
                        report_date DATE UNIQUE NOT NULL,
                        summary TEXT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                cursor.execute("""
                    CREATE TABLE report_signals (
                        id SERIAL PRIMARY KEY,
                        report_id INTEGER REFERENCES daily_reports(id) ON DELETE CASCADE,
                        signal_type VARCHAR(50) NOT NULL,
                        sector VARCHAR(255),
                        direction VARCHAR(50),
                        details TEXT,
                        stock_symbol VARCHAR(20)
                    );
                """)
                
                cursor.execute("""
                    CREATE TABLE signal_sources (
                        id SERIAL PRIMARY KEY,
                        signal_id INTEGER REFERENCES report_signals(id) ON DELETE CASCADE,
                        title TEXT,
                        url TEXT UNIQUE
                    );
                """)
                
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
    
    # Remove test output file
    output_file = os.path.join("output", f"report_{TODAY.date()}.json")
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"Removed test output file: {output_file}")
    
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
            return psycopg2.connect(staging_conn_string)
        
        # Patch the database connection in all analysis modules
        with patch('src.analysis.historical_analyzer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('src.analysis.today_analyzer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('src.analysis.synthesizer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('src.output.processor.get_db_connection', side_effect=get_staging_db_connection):
            
            print("\n--- [EXECUTION] Running the end-to-end pipeline on test data in staging database ---")
            run_synthesis_and_save()

        # --- [VERIFICATION] ---
        print("\n--- [VERIFICATION] Checking test results ---")
        # 1. Verify JSON file
        output_file = os.path.join("output", f"report_{TODAY.date()}.json")
        assert os.path.exists(output_file), "Output JSON file was not created!"
        print("✅  JSON file was created successfully.")
        with open(output_file, 'r') as f:
            data = json.load(f)
            assert len(data['signals']['confidence']) == 1, "Incorrect number of confidence signals in JSON!"
            assert data['signals']['confidence'][0]['sector'] == 'Technology', "Incorrect sector in JSON!"
            print("✅  JSON content is correct.")

        # 2. Verify Database records in staging database
        staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
        with psycopg2.connect(staging_conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM daily_reports WHERE report_date = %s;", (TODAY.date(),))
                report_id = cursor.fetchone()[0]
                assert report_id is not None, "Report was not saved to the database!"
                
                cursor.execute("SELECT COUNT(*) FROM report_signals WHERE report_id = %s AND signal_type = 'CONFIDENCE';", (report_id,))
                signal_count = cursor.fetchone()[0]
                assert signal_count == 1, "Incorrect number of confidence signals in database!"
                print("✅  Database records were saved correctly.")

    except Exception as e:
        print(f"\n❌  An error occurred during the test: {e}")
    finally:
        cleanup_test_environment()

if __name__ == '__main__':
    run_e2e_test()
