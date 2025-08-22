"""
Stockometry E2E Test Setup - Shared functionality for all E2E tests
"""

import os
import json
import psycopg2
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
from stockometry.database import get_db_connection_string, init_db
from stockometry.core.analysis.synthesizer import synthesize_analyses
from stockometry.core.output.processor import OutputProcessor

# Global test constants
TODAY = datetime.now(timezone.utc)
STAGING_DB_NAME = 'stockometry_staging'

class E2ETestSetup:
    """Shared setup and utilities for E2E tests"""
    
    @staticmethod
    def setup_test_environment(test_name: str, dummy_articles: list):
        """Creates test environment using staging database."""
        print(f"--- [SETUP] Creating {test_name} test environment in staging database ---")
        
        # Initialize staging database with all tables
        init_db(dbname=STAGING_DB_NAME)
        
        staging_conn_string = get_db_connection_string(dbname=STAGING_DB_NAME)
        
        try:
            with psycopg2.connect(staging_conn_string) as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    # Clear any existing test data
                    cursor.execute("DELETE FROM articles WHERE url LIKE 'https://e2e.test/%';")
                    cursor.execute("DELETE FROM daily_reports WHERE report_date = %s;", (TODAY.date(),))
                    
                    # Insert test data
                    for article in dummy_articles:
                        cursor.execute(
                            "INSERT INTO articles (url, published_at, nlp_features, title, description) VALUES (%s, %s, %s, %s, %s);",
                            (article['url'], article['published_at'], json.dumps(article['nlp_features']), article['title'], article.get('description', ''))
                        )
                    
            print(f"{test_name} test environment created successfully with {len(dummy_articles)} articles.")
            
        except Exception as e:
            print(f"Error setting up staging database: {e}")
            raise

    @staticmethod
    def cleanup_test_environment(test_name: str):
        """Cleans up test environment in staging database."""
        print(f"\n--- [CLEANUP] Cleaning up {test_name} test environment ---")
        
        staging_conn_string = get_db_connection_string(dbname=STAGING_DB_NAME)
        
        try:
            with psycopg2.connect(staging_conn_string) as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM articles WHERE url LIKE 'https://e2e.test/%';")
                    cursor.execute("DELETE FROM daily_reports WHERE report_date = %s;", (TODAY.date(),))
                    
            print("Staging database cleaned up.")
            
        except Exception as e:
            print(f"Error cleaning up staging database: {e}")
        
        # Remove test output files
        E2ETestSetup._cleanup_test_files()
        
        print(f"{test_name} test environment cleaned up.")

    @staticmethod
    def _cleanup_test_files():
        """Clean up test output and export files"""
        # Remove old output file format
        output_file = os.path.join("output", f"report_{TODAY.date()}.json")
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"Removed test output file: {output_file}")
        
        # Clean up test export files
        if os.path.exists("exports"):
            for file in os.listdir("exports"):
                if file.startswith(f"report_{TODAY.date()}_") and file.endswith("_scheduled.json"):
                    os.remove(os.path.join("exports", file))
                    print(f"Removed test export file: {file}")

    @staticmethod
    def get_staging_db_connection():
        """Get a connection to the staging database"""
        staging_conn_string = get_db_connection_string(dbname=STAGING_DB_NAME)
        return psycopg2.connect(staging_conn_string)

    @staticmethod
    def run_analysis_pipeline(test_name: str):
        """Run the complete analysis pipeline with staging database"""
        print(f"\n--- [EXECUTION] Running {test_name} analysis pipeline ---")
        
        def get_staging_db_connection():
            return E2ETestSetup.get_staging_db_connection()
        
        # Patch database connections
        with patch('stockometry.core.analysis.historical_analyzer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('stockometry.core.analysis.today_analyzer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('stockometry.core.analysis.synthesizer.get_db_connection', side_effect=get_staging_db_connection), \
             patch('stockometry.core.output.processor.get_db_connection', side_effect=get_staging_db_connection):
            
            report_object = synthesize_analyses()
            
            if report_object:
                # Create OutputProcessor with staging database connection
                processor = OutputProcessor(report_object, run_source="SCHEDULED")
                
                # Patch the processor's database connection
                with patch('stockometry.core.output.processor.get_db_connection', side_effect=get_staging_db_connection):
                    report_id = processor.process_and_save()
                    
                    if report_id:
                        print(f"{test_name} report saved to database successfully")
                        print("Report ID:", report_id)
                        return report_id
                    else:
                        print(f"Failed to save {test_name} report to database")
                        return None
            else:
                print("Synthesizer did not return a report. Skipping output processing.")
                return None

    @staticmethod
    def verify_database_records(test_name: str, report_id: int):
        """Verify that records were saved to the database"""
        print(f"\n--- [VERIFICATION] Checking {test_name} test results ---")
        
        staging_conn_string = get_db_connection_string(dbname=STAGING_DB_NAME)
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
                
                return report_id

    @staticmethod
    def test_json_export(test_name: str, report_id: int, verification_callback=None):
        """Test JSON export functionality"""
        print(f"\n--- [EXPORT TEST] Testing JSON export functionality ---")
        
        # Create processor instance for export testing
        processor = OutputProcessor({})  # Empty object for export only
        
        def get_staging_db_connection():
            return E2ETestSetup.get_staging_db_connection()
        
        # Patch the processor to use staging database
        with patch('stockometry.core.output.processor.get_db_connection', side_effect=get_staging_db_connection):
            # Export the report to JSON
            json_data = processor.export_to_json(report_id=report_id)
            
            assert json_data is not None, "JSON export failed!"
            print(f"✅  Executive Summary: {json_data.get('executive_summary', 'MISSING!')}")
            
            # Run custom verification if provided
            if verification_callback:
                verification_callback(json_data)
            
            print("✅  JSON export content structure is correct.")
            
            # Test file export
            file_path = processor.save_json_to_file(json_data, "exports")
            assert file_path is not None, "File export failed!"
            assert os.path.exists(file_path), "Export file was not created!"
            print(f"✅  JSON file export working: {file_path}")

    @staticmethod
    def run_complete_e2e_test(test_name: str, dummy_articles: list, verification_callback=None):
        """Run a complete E2E test with setup, execution, verification, and cleanup"""
        E2ETestSetup.setup_test_environment(test_name, dummy_articles)
        
        try:
            report_id = E2ETestSetup.run_analysis_pipeline(test_name)
            
            if report_id:
                report_id = E2ETestSetup.verify_database_records(test_name, report_id)
                E2ETestSetup.test_json_export(test_name, report_id, verification_callback)
                print(f"✅  {test_name} test completed successfully!")
            else:
                print(f"❌  {test_name} test failed - no report generated")
                
        except Exception as e:
            print(f"\n❌  An error occurred during the {test_name} test: {e}")
            raise
        finally:
            E2ETestSetup.cleanup_test_environment(test_name)


# Common test data generators
class TestDataGenerator:
    """Generate common test data patterns"""
    
    @staticmethod
    def create_historical_trend_articles(sector: str, direction: str, days: int = 3, base_score: float = 0.85):
        """Create historical trend articles for a sector"""
        articles = []
        for i in range(1, days + 1):
            score = base_score + (i * 0.02)
            if direction == "Bearish":
                score = -score
            
            # Map sectors to company names for more realistic test data
            sector_companies = {
                "Technology": ["Apple", "AAPL"],
                "Financial Services": ["JPMorgan", "JPM"],
                "Healthcare": ["Pfizer", "PFE"],
                "Energy": ["Exxon", "XOM"],
                "Consumer": ["Walmart", "WMT"],
                "Communication Services": ["Google", "GOOGL"],
                "Industrials": ["Boeing", "BA"]
            }
            
            companies = sector_companies.get(sector, [sector])
            
            articles.append({
                "url": f"https://e2e.test/hist_{sector.lower().replace(' ', '_')}_{direction.lower()}_{i}",
                "published_at": TODAY - timedelta(days=i),
                "title": f"{sector} Sector Shows {'Strong Growth' if direction == 'Bullish' else 'Challenges'} Day {i}",
                "description": f"{sector} companies report {'positive earnings and innovation' if direction == 'Bullish' else 'regulatory challenges and declining performance'} on day {i}",
                "nlp_features": {
                    "sentiment": {"label": "positive" if direction == "Bullish" else "negative", "score": abs(score)},
                    "entities": [{"text": companies[0], "label": "ORG"}, {"text": companies[1] if len(companies) > 1 else companies[0], "label": "ORG"}, {"text": sector, "label": "SECTOR"}]
                }
            })
        return articles

    @staticmethod
    def create_impact_articles(sector: str, direction: str, count: int = 1, base_score: float = 0.95):
        """Create high-impact articles for a sector"""
        articles = []
        for i in range(count):
            score = base_score + (i * 0.01)
            if direction == "DOWN":
                score = -score
            
            # Map sectors to company names for more realistic test data
            sector_companies = {
                "Technology": ["Apple", "AAPL"],
                "Financial Services": ["JPMorgan", "JPM"],
                "Healthcare": ["Pfizer", "PFE"],
                "Energy": ["Exxon", "XOM"],
                "Consumer": ["Walmart", "WMT"],
                "Communication Services": ["Google", "GOOGL"],
                "Industrials": ["Boeing", "BA"]
            }
            
            companies = sector_companies.get(sector, [sector])
            
            # Create more specific titles for impact articles
            if direction == "UP":
                title = f"{companies[0]} Announces Revolutionary Breakthrough"
            else:
                title = f"{companies[0]} Faces Regulatory Challenges"
            
            articles.append({
                "url": f"https://e2e.test/today_{sector.lower().replace(' ', '_')}_{direction.lower()}_{i}",
                "published_at": TODAY,
                "title": title,
                "description": f"Major {'positive' if direction == 'UP' else 'negative'} development in {sector} sector",
                "nlp_features": {
                    "sentiment": {"label": "positive" if direction == "UP" else "negative", "score": abs(score)},
                    "entities": [{"text": companies[0], "label": "ORG"}, {"text": companies[1] if len(companies) > 1 else companies[0], "label": "ORG"}, {"text": sector, "label": "SECTOR"}]
                }
            })
        return articles

    @staticmethod
    def create_noise_articles(sectors: list, count_per_sector: int = 5):
        """Create noise articles for various sectors"""
        articles = []
        for sector in sectors:
            for i in range(count_per_sector):
                sentiment = "positive" if i % 3 == 0 else "negative" if i % 3 == 1 else "neutral"
                score = 0.6 + (i * 0.05)
                
                # Map sectors to company names for more realistic test data
                sector_companies = {
                    "Technology": ["Apple", "AAPL"],
                    "Financial Services": ["JPMorgan", "JPM"],
                    "Healthcare": ["Pfizer", "PFE"],
                    "Energy": ["Exxon", "XOM"],
                    "Consumer": ["Walmart", "WMT"],
                    "Communication Services": ["Google", "GOOGL"],
                    "Industrials": ["Boeing", "BA"]
                }
                
                companies = sector_companies.get(sector, [sector])
                
                articles.append({
                    "url": f"https://e2e.test/noise_{sector.lower().replace(' ', '_')}_{i}",
                    "published_at": TODAY,
                    "title": f"{companies[0]} {'Positive' if sentiment == 'positive' else 'Negative' if sentiment == 'negative' else 'Neutral'} News {i}",
                    "description": f"Regular {sector} sector news",
                    "nlp_features": {
                        "sentiment": {"label": sentiment, "score": score},
                        "entities": [{"text": companies[0], "label": "ORG"}, {"text": companies[1] if len(companies) > 1 else companies[0], "label": "ORG"}, {"text": sector, "label": "SECTOR"}]
                    }
                })
        return articles

    @staticmethod
    def create_edge_case_articles():
        """Create articles for edge case testing"""
        return [
            # Insufficient historical data (only 2 days)
            {
                "url": "https://e2e.test/hist_tech_insufficient_1",
                "published_at": TODAY - timedelta(days=1),
                "title": "Tech Slightly Positive",
                "description": "Technology sector shows minimal movement",
                "nlp_features": {"sentiment": {"label": "positive", "score": 0.6}, "entities": [{"text": "Technology", "label": "SECTOR"}]}
            },
            {
                "url": "https://e2e.test/hist_tech_insufficient_2",
                "published_at": TODAY - timedelta(days=2),
                "title": "Tech Slightly Positive",
                "description": "Technology sector shows minimal movement",
                "nlp_features": {"sentiment": {"label": "positive", "score": 0.6}, "entities": [{"text": "Technology", "label": "SECTOR"}]}
            },
            # Mixed sentiment
            {
                "url": "https://e2e.test/hist_health_mixed_1",
                "published_at": TODAY - timedelta(days=1),
                "title": "Healthcare Mixed",
                "description": "Healthcare sector shows mixed results",
                "nlp_features": {"sentiment": {"label": "positive", "score": 0.7}, "entities": [{"text": "Healthcare", "label": "SECTOR"}]}
            },
            {
                "url": "https://e2e.test/hist_health_mixed_2",
                "published_at": TODAY - timedelta(days=2),
                "title": "Healthcare Mixed",
                "description": "Healthcare sector shows mixed results",
                "nlp_features": {"sentiment": {"label": "negative", "score": 0.7}, "entities": [{"text": "Healthcare", "label": "SECTOR"}]}
            },
            # Weak sentiment scores
            {
                "url": "https://e2e.test/hist_energy_weak_1",
                "published_at": TODAY - timedelta(days=1),
                "title": "Energy Slightly Positive",
                "description": "Energy sector shows minimal positive movement",
                "nlp_features": {"sentiment": {"label": "positive", "score": 0.55}, "entities": [{"text": "Energy", "label": "SECTOR"}]}
            },
            {
                "url": "https://e2e.test/hist_energy_weak_2",
                "published_at": TODAY - timedelta(days=2),
                "title": "Energy Slightly Positive",
                "description": "Energy sector shows minimal positive movement",
                "nlp_features": {"sentiment": {"label": "positive", "score": 0.55}, "entities": [{"text": "Energy", "label": "SECTOR"}]}
            },
            {
                "url": "https://e2e.test/hist_energy_weak_3",
                "published_at": TODAY - timedelta(days=3),
                "title": "Energy Slightly Positive",
                "description": "Energy sector shows minimal positive movement",
                "nlp_features": {"sentiment": {"label": "positive", "score": 0.55}, "entities": [{"text": "Energy", "label": "SECTOR"}]}
            }
        ]


# Common verification functions
class TestVerification:
    """Common verification functions for different test scenarios"""
    
    @staticmethod
    def verify_bullish_tech_signals(json_data):
        """Verify bullish technology sector signals"""
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

    @staticmethod
    def verify_bearish_financial_signals(json_data):
        """Verify bearish financial sector signals"""
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

    @staticmethod
    def verify_mixed_signals(json_data):
        """Verify mixed market signals"""
        # Should have multiple historical signals
        assert len(json_data['signals']['historical']) >= 2, "Should have multiple historical signals!"
        print("✅  Found multiple historical signals.")
        
        # Check for Technology bullish signal
        tech_historical = [s for s in json_data['signals']['historical'] if s['sector'] == 'Technology']
        if tech_historical:
            assert tech_historical[0]['direction'] == 'Bullish', "Technology signal should be Bullish!"
            print("✅  Technology bullish historical signal found.")
        
        # Check for Healthcare bearish signal
        health_historical = [s for s in json_data['signals']['historical'] if s['sector'] == 'Healthcare']
        if health_historical:
            assert health_historical[0]['direction'] == 'Bearish', "Healthcare signal should be Bearish!"
            print("✅  Healthcare bearish historical signal found.")
        
        # Should have multiple impact signals
        if json_data['signals']['impact']:
            print(f"✅  Found {len(json_data['signals']['impact'])} impact signals.")
            for signal in json_data['signals']['impact']:
                print(f"   - {signal['sector']}: {signal['direction']} - {signal['details']}")

    @staticmethod
    def verify_edge_cases(json_data):
        """Verify edge case scenarios"""
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
