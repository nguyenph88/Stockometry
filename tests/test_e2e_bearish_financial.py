# test_e2e_bearish_financial.py
# Tests bearish financial sector scenarios with various signal combinations
import os
import json
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from src.database import get_db_connection, init_db
from src.scheduler import run_synthesis_and_save
from src.output.processor import OutputProcessor

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
                
        print(f"Bearish financial test environment created successfully with {len(DUMMY_ARTICLES)} articles.")
        
    except Exception as e:
        print(f"Error setting up staging database: {e}")
        raise

def cleanup_test_environment():
    """Cleans up test environment in staging database."""
    print("\n--- [CLEANUP] Cleaning up bearish financial test environment ---")
    
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
    
    print("Bearish financial test environment cleaned up.")

def run_bearish_financial_test():
    """Runs the bearish financial sector test."""
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
            
            print("\n--- [EXECUTION] Running bearish financial analysis pipeline ---")
            run_synthesis_and_save()

        # Verification
        print("\n--- [VERIFICATION] Checking bearish financial test results ---")
        output_file = os.path.join("output", f"report_{TODAY.date()}.json")
        assert os.path.exists(output_file), "Output JSON file was not created!"
        print("✅  JSON file was created successfully.")
        
        with open(output_file, 'r') as f:
            data = json.load(f)
            print(f"✅  Executive Summary: {data.get('executive_summary', 'MISSING!')}")
            
            # Should have historical bearish signal for Financial Services
            assert len(data['signals']['historical']) >= 1, "No historical signals found!"
            fin_historical = [s for s in data['signals']['historical'] if s['sector'] == 'Financial Services']
            assert len(fin_historical) >= 1, "No Financial Services historical signal found!"
            assert fin_historical[0]['direction'] == 'Bearish', "Financial Services signal should be Bearish!"
            print("✅  Historical Financial Services bearish signal found.")
            
            # Should have impact signals for Financial Services
            if data['signals']['impact']:
                fin_impact = [s for s in data['signals']['impact'] if s['sector'] == 'Financial Services']
                if fin_impact:
                    print(f"✅  Financial Services impact signals found: {len(fin_impact)}")
                    for signal in fin_impact:
                        print(f"   - {signal['direction']}: {signal['details']}")
            
            # Should have confidence signals if both historical and impact align
            if data['signals']['confidence']:
                fin_confidence = [s for s in data['signals']['confidence'] if s['sector'] == 'Financial Services']
                if fin_confidence:
                    print(f"✅  Financial Services confidence signals found: {len(fin_confidence)}")
                    # Check for predicted stocks
                    for signal in fin_confidence:
                        if 'predicted_stocks' in signal:
                            print(f"✅  Predicted stocks: {[s['symbol'] for s in signal['predicted_stocks']]}")
            
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
                
        print("✅  Bearish financial test completed successfully!")

    except Exception as e:
        print(f"\n❌  An error occurred during the bearish financial test: {e}")
        raise
    finally:
        cleanup_test_environment()

if __name__ == '__main__':
    run_bearish_financial_test()
