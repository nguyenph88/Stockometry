# test_e2e_bearish_financial.py
# Tests bearish financial sector scenarios
from stockometry.tests.test_setup import (
    E2ETestSetup, 
    TestDataGenerator, 
    TestVerification
)

def run_bearish_financial_test():
    """Runs the bearish financial sector test."""
    # Generate test data using the shared generator
    test_articles = (
        # 1. HISTORICAL BEARISH TREND for Financial Services (6 days of negative sentiment)
        TestDataGenerator.create_historical_trend_articles("Financial Services", "Bearish", days=6, base_score=0.85) +
        
        # 2. TODAY'S HIGH-IMPACT BEARISH EVENTS for Financial Services
        TestDataGenerator.create_impact_articles("Financial Services", "DOWN", count=2, base_score=0.95) +
        
        # 3. HISTORICAL NOISE ARTICLES (mixed sectors, should not interfere)
        TestDataGenerator.create_historical_trend_articles("Technology", "Neutral", days=2, base_score=0.7) +
        TestDataGenerator.create_historical_trend_articles("Healthcare", "Positive", days=1, base_score=0.8) +
        
        # 4. TODAY'S NOISE ARTICLES (should be filtered out)
        TestDataGenerator.create_noise_articles(["Energy", "Consumer"], count_per_sector=1)
    )
    
    # Run the complete test using shared setup
    E2ETestSetup.run_complete_e2e_test(
        test_name="Bearish Financial Sector",
        dummy_articles=test_articles,
        verification_callback=TestVerification.verify_bearish_financial_signals
    )

if __name__ == '__main__':
    run_bearish_financial_test()
