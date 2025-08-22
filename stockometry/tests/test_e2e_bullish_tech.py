# test_e2e_bullish_tech.py
# Tests bullish technology sector scenarios with various signal combinations
from stockometry.tests.test_setup import (
    E2ETestSetup, 
    TestDataGenerator, 
    TestVerification
)

def run_bullish_tech_test():
    """Runs the bullish technology sector test."""
    # Generate test data using the shared generator
    test_articles = (
        # 1. HISTORICAL BULLISH TREND for Technology (6 days of positive sentiment)
        TestDataGenerator.create_historical_trend_articles("Technology", "Bullish", days=6, base_score=0.85) +
        
        # 2. TODAY'S HIGH-IMPACT BULLISH EVENTS for Technology
        TestDataGenerator.create_impact_articles("Technology", "UP", count=2, base_score=0.95) +
        
        # 3. HISTORICAL NOISE ARTICLES (mixed sectors, should not interfere)
        TestDataGenerator.create_historical_trend_articles("Financial", "Neutral", days=2, base_score=0.7) +
        TestDataGenerator.create_historical_trend_articles("Healthcare", "Bearish", days=1, base_score=0.8) +
        
        # 4. TODAY'S NOISE ARTICLES (should be filtered out)
        TestDataGenerator.create_noise_articles(["Energy", "Consumer"], count_per_sector=1)
    )
    
    # Run the complete test using shared setup
    E2ETestSetup.run_complete_e2e_test(
        test_name="Bullish Technology Sector",
        dummy_articles=test_articles,
        verification_callback=TestVerification.verify_bullish_tech_signals
    )

if __name__ == '__main__':
    run_bullish_tech_test()
