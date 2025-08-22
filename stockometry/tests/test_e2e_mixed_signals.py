# test_e2e_mixed_signals.py
# Tests mixed market signals across multiple sectors
from stockometry.tests.test_setup import (
    E2ETestSetup, 
    TestDataGenerator, 
    TestVerification
)

def run_mixed_signals_test():
    """Runs the mixed signals test."""
    # Generate test data using the shared generator
    test_articles = (
        # 1. HISTORICAL BULLISH TREND for Technology
        TestDataGenerator.create_historical_trend_articles("Technology", "Bullish", days=6, base_score=0.85) +
        
        # 2. HISTORICAL BEARISH TREND for Healthcare
        TestDataGenerator.create_historical_trend_articles("Healthcare", "Bearish", days=6, base_score=0.85) +
        
        # 3. TODAY'S HIGH-IMPACT EVENTS for various sectors
        TestDataGenerator.create_impact_articles("Communication Services", "UP", count=1, base_score=0.99) +
        TestDataGenerator.create_impact_articles("Industrials", "DOWN", count=1, base_score=0.5) +
        
        # 4. HISTORICAL NOISE ARTICLES (mixed sectors)
        TestDataGenerator.create_historical_trend_articles("Financial", "Neutral", days=3, base_score=0.7) +
        TestDataGenerator.create_historical_trend_articles("Energy", "Positive", days=2, base_score=0.8) +
        
        # 5. TODAY'S NOISE ARTICLES (should be filtered out)
        TestDataGenerator.create_noise_articles(["Consumer", "Materials"], count_per_sector=3)
    )
    
    # Run the complete test using shared setup
    E2ETestSetup.run_complete_e2e_test(
        test_name="Mixed Market Signals",
        dummy_articles=test_articles,
        verification_callback=TestVerification.verify_mixed_signals
    )

if __name__ == '__main__':
    run_mixed_signals_test()
