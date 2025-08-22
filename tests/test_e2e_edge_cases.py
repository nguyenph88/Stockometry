# test_e2e_edge_cases.py
# Tests edge cases and no-signal scenarios
import os
import json
import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from src.database import get_db_connection, init_db
from src.scheduler import run_synthesis_and_save
from src.output.processor import OutputProcessor

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
                
        print(f"Edge cases test environment created successfully with {len(DUMMY_ARTICLES)} articles.")
        
    except Exception as e:
        print(f"Error setting up staging database: {e}")
        raise

def cleanup_test_environment():
    """Cleans up test environment in staging database."""
    print("\n--- [CLEANUP] Cleaning up edge cases test environment ---")
    
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
    
    print("Edge cases test environment cleaned up.")

def run_edge_cases_test():
    """Runs the edge cases test."""
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
            
            print("\n--- [EXECUTION] Running edge cases analysis pipeline ---")
            run_synthesis_and_save()

        # Verification
        print("\n--- [VERIFICATION] Checking edge cases test results ---")
        output_file = os.path.join("output", f"report_{TODAY.date()}.json")
        assert os.path.exists(output_file), "Output JSON file was not created!"
        print("✅  JSON file was created successfully.")
        
        with open(output_file, 'r') as f:
            data = json.load(f)
            print(f"✅  Executive Summary: {data.get('executive_summary', 'MISSING!')}")
            
            # Test edge case scenarios
            print("\n--- Testing Edge Cases ---")
            
            # 1. Insufficient historical data (should not generate historical signal)
            if data['signals']['historical']:
                tech_insufficient = [s for s in data['signals']['historical'] if s['sector'] == 'Technology']
                if tech_insufficient:
                    print(f"⚠️  Technology historical signal found despite insufficient data: {tech_insufficient[0]['direction']}")
                else:
                    print("✅  No Technology historical signal (correct - insufficient data)")
            else:
                print("✅  No historical signals (correct - edge case scenario)")
            
            # 2. Mixed sentiment (should not generate clear historical signal)
            if data['signals']['historical']:
                health_mixed = [s for s in data['signals']['historical'] if s['sector'] == 'Healthcare']
                if health_mixed:
                    print(f"⚠️  Healthcare historical signal found despite mixed sentiment: {health_mixed[0]['direction']}")
                else:
                    print("✅  No Healthcare historical signal (correct - mixed sentiment)")
            
            # 3. Weak sentiment scores
            if data['signals']['historical']:
                energy_weak = [s for s in data['signals']['historical'] if s['sector'] == 'Energy']
                if energy_weak:
                    print(f"⚠️  Energy historical signal found despite weak sentiment: {energy_weak[0]['direction']}")
                else:
                    print("✅  No Energy historical signal (correct - weak sentiment)")
            
            # 4. No high-impact news today
            if data['signals']['impact']:
                print(f"⚠️  Impact signals found despite low-impact news: {len(data['signals']['impact'])}")
                for signal in data['signals']['impact']:
                    print(f"   - {signal['sector']}: {signal['direction']}")
            else:
                print("✅  No impact signals (correct - no high-impact news)")
            
            # 5. No sector classification
            if data['signals']['historical']:
                no_sector = [s for s in data['signals']['historical'] if not s.get('sector')]
                if no_sector:
                    print(f"⚠️  Signals without sector classification found: {len(no_sector)}")
                else:
                    print("✅  All signals have proper sector classification")
            
            # Check confidence signals
            if data['signals']['confidence']:
                print(f"⚠️  Confidence signals found in edge case scenario: {len(data['signals']['confidence'])}")
                for signal in data['signals']['confidence']:
                    print(f"   - {signal['sector']}: {signal['direction']}")
            else:
                print("✅  No confidence signals (correct - edge case scenario)")
            
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
                
        print("✅  Edge cases test completed successfully!")

    except Exception as e:
        print(f"\n❌  An error occurred during the edge cases test: {e}")
        raise
    finally:
        cleanup_test_environment()

if __name__ == '__main__':
    run_edge_cases_test()
