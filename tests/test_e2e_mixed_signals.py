# test_e2e_mixed_signals.py
# Tests mixed market scenarios with both bullish and bearish sectors
import os
import json
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from src.database import get_db_connection, init_db
from src.scheduler import run_synthesis_and_save
from src.output.processor import OutputProcessor

# --- Test Scenario: Mixed Market Signals ---
TODAY = datetime.now(timezone.utc)
DUMMY_ARTICLES = [
    # 1. HISTORICAL BULLISH TREND for Technology (6 days of positive sentiment)
    {"url": f"https://e2e.test/hist_tech_bull_{i}", "published_at": TODAY - timedelta(days=i), 
     "title": f"Tech Innovation Continues Day {i}", 
     "description": f"Technology sector shows consistent growth and innovation on day {i}",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.8 + (i * 0.02)}, 
                      "entities": [{"text": "Apple", "label": "ORG"}, {"text": "Technology", "label": "SECTOR"}]}}
    for i in range(1, 7)
] + [
    # 2. HISTORICAL BEARISH TREND for Healthcare (6 days of negative sentiment)
    {"url": f"https://e2e.test/hist_health_bear_{i}", "published_at": TODAY - timedelta(days=i), 
     "title": f"Healthcare Regulatory Issues Day {i}", 
     "description": f"Healthcare sector faces ongoing regulatory challenges on day {i}",
     "nlp_features": {"sentiment": {"label": "negative", "score": 0.95}, 
                      "entities": [{"text": "Pfizer", "label": "ORG"}]}}
    for i in range(1, 7)
] + [
    # 3. HISTORICAL NEUTRAL TREND for Energy (6 days of mixed sentiment)
    {"url": f"https://e2e.test/hist_energy_neutral_{i}", "published_at": TODAY - timedelta(days=i), 
     "title": f"Energy Market Mixed Day {i}", 
     "description": f"Energy sector shows mixed performance on day {i}",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.5 + (i * 0.05)}, 
                      "entities": [{"text": "Exxon", "label": "ORG"}]}}
    for i in range(1, 7)
] + [
    # 4. TODAY'S HIGH-IMPACT BULLISH EVENTS for Technology
    {"url": "https://e2e.test/today_tech_ai", "published_at": TODAY, 
     "title": "Google Announces Revolutionary AI Breakthrough", 
     "description": "New AI model outperforms all existing benchmarks by 10x",
     "nlp_features": {"sentiment": {"label": "positive", "score": 0.99}, 
                      "entities": [{"text": "Google", "label": "ORG"}, {"text": "GOOGL", "label": "ORG"}, {"text": "Technology", "label": "SECTOR"}]}},
    
    # 5. TODAY'S HIGH-IMPACT BEARISH EVENTS for Healthcare
    {"url": "https://e2e.test/today_health_recall", "published_at": TODAY, 
     "title": "Major Drug Recall Announced by FDA", 
     "description": "Popular medication pulled from market due to safety concerns",
     "nlp_features": {"sentiment": {"label": "negative", "score": 0.97}, 
                      "entities": [{"text": "FDA", "label": "ORG"}, {"text": "Healthcare", "label": "SECTOR"}]}},
    
    # 6. TODAY'S HIGH-IMPACT NEUTRAL EVENTS for Energy
    {"url": "https://e2e.test/today_energy_opec", "published_at": TODAY, 
     "title": "OPEC+ Maintains Current Production Levels", 
     "description": "Oil cartel decides to keep existing output quotas unchanged",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.6}, 
                      "entities": [{"text": "OPEC+", "label": "ORG"}, {"text": "Energy", "label": "SECTOR"}]}},
    
    # 7. HISTORICAL NOISE ARTICLES (mixed sectors, should not interfere)
    {"url": "https://e2e.test/hist_fin_1", "published_at": TODAY - timedelta(days=2), 
     "title": "Banking Sector Reports Stable Results", 
     "description": "Financial institutions show consistent performance",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.7}, 
                      "entities": [{"text": "JPMorgan", "label": "ORG"}, {"text": "Financial", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/hist_consumer_1", "published_at": TODAY - timedelta(days=3), 
     "title": "Retail Sales Show Seasonal Patterns", 
     "description": "Consumer spending follows expected trends",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.6}, 
                      "entities": [{"text": "Walmart", "label": "ORG"}, {"text": "Consumer", "label": "SECTOR"}]}},
    
    # 8. TODAY'S NOISE ARTICLES (should be filtered out)
    {"url": "https://e2e.test/noise_industrial_1", "published_at": TODAY, 
     "title": "Manufacturing Index Stable", 
     "description": "Industrial production shows minimal change",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.5}, 
                      "entities": [{"text": "Boeing", "label": "ORG"}, {"text": "Industrial", "label": "SECTOR"}]}},
    
    {"url": "https://e2e.test/noise_utilities_1", "published_at": TODAY, 
     "title": "Utility Companies Report Normal Operations", 
     "description": "Power generation continues as expected",
     "nlp_features": {"sentiment": {"label": "neutral", "score": 0.5}, 
                      "entities": [{"text": "Duke Energy", "label": "ORG"}, {"text": "Utilities", "label": "SECTOR"}]}}
]

def setup_test_environment():
    """Creates test environment using staging database."""
    print("--- [SETUP] Creating mixed signals test environment in staging database ---")
    
    from src.database import get_db_connection_string
    import psycopg2
    
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
                
                # Create output tables
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
                
        print(f"Mixed signals test environment created successfully with {len(DUMMY_ARTICLES)} articles.")
        
    except Exception as e:
        print(f"Error setting up staging database: {e}")
        raise

def cleanup_test_environment():
    """Cleans up test environment in staging database."""
    print("\n--- [CLEANUP] Cleaning up mixed signals test environment ---")
    
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
    
    print("Mixed signals test environment cleaned up.")

def run_mixed_signals_test():
    """Runs the mixed signals test."""
    setup_test_environment()
    
    try:
        from src.database import get_db_connection_string
        import psycopg2
        
        def get_staging_db_connection():
            staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
            return psycopg2.connect(staging_conn_string)
        
        # Patch database connections
        with patch('src.analysis.historical_analyzer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('src.analysis.today_analyzer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('src.analysis.synthesizer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('src.output.processor.get_db_connection', side_effect=get_staging_db_connection):
            
            print("\n--- [EXECUTION] Running mixed signals analysis pipeline ---")
            run_synthesis_and_save()

        # Verification
        print("\n--- [VERIFICATION] Checking mixed signals test results ---")
        output_file = os.path.join("output", f"report_{TODAY.date()}.json")
        assert os.path.exists(output_file), "Output JSON file was not created!"
        print("✅  JSON file was created successfully.")
        
        with open(output_file, 'r') as f:
            data = json.load(f)
            print(f"✅  Executive Summary: {data.get('executive_summary', 'MISSING!')}")
            
            # Should have multiple historical signals
            assert len(data['signals']['historical']) >= 2, f"Expected at least 2 historical signals, got {len(data['signals']['historical'])}"
            print(f"✅  Found {len(data['signals']['historical'])} historical signals.")
            
            # Check for Technology bullish signal
            tech_historical = [s for s in data['signals']['historical'] if s['sector'] == 'Technology']
            if tech_historical:
                assert tech_historical[0]['direction'] == 'Bullish', "Technology signal should be Bullish!"
                print("✅  Technology bullish historical signal found.")
            
            # Check for Healthcare bearish signal
            health_historical = [s for s in data['signals']['historical'] if s['sector'] == 'Healthcare']
            if health_historical:
                assert health_historical[0]['direction'] == 'Bearish', "Healthcare signal should be Bearish!"
                print("✅  Healthcare bearish historical signal found.")
            
            # Should have impact signals
            if data['signals']['impact']:
                print(f"✅  Found {len(data['signals']['impact'])} impact signals.")
                for signal in data['signals']['impact']:
                    print(f"   - {signal['sector']}: {signal['direction']} - {signal['details']}")
            
            # Should have confidence signals if historical and impact align
            if data['signals']['confidence']:
                print(f"✅  Found {len(data['signals']['confidence'])} confidence signals.")
                for signal in data['signals']['confidence']:
                    print(f"   - {signal['sector']}: {signal['direction']}")
                    if 'predicted_stocks' in signal:
                        print(f"     Predicted stocks: {[s['symbol'] for s in signal['predicted_stocks']]}")
            
            print("✅  JSON content structure is correct.")

        # Database verification
        staging_conn_string = get_db_connection_string(dbname='stockometry_staging')
        with psycopg2.connect(staging_conn_string) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM daily_reports WHERE report_date = %s;", (TODAY.date(),))
                report_id = cursor.fetchone()[0]
                assert report_id is not None, "Report was not saved to the database!"
                
                cursor.execute("SELECT COUNT(*) FROM report_signals WHERE report_id = %s;", (report_id,))
                signal_count = cursor.fetchone()[0]
                print(f"✅  {signal_count} signals saved to database.")
                
        print("✅  Mixed signals test completed successfully!")

    except Exception as e:
        print(f"\n❌  An error occurred during the mixed signals test: {e}")
        raise
    finally:
        cleanup_test_environment()

if __name__ == '__main__':
    run_mixed_signals_test()
