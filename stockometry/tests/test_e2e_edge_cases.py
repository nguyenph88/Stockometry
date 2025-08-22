# test_e2e_edge_cases.py
# Tests edge cases and no-signal scenarios
from stockometry.tests.test_setup import (
    E2ETestSetup, 
    TestDataGenerator, 
    TestVerification
)

def run_edge_cases_test():
    """Runs the edge cases test."""
    # Generate test data using the shared generator
    test_articles = TestDataGenerator.create_edge_case_articles()
    
    # Run the complete test using shared setup
    E2ETestSetup.run_complete_e2e_test(
        test_name="Edge Cases and No-Signals",
        dummy_articles=test_articles,
        verification_callback=TestVerification.verify_edge_cases
    )

if __name__ == '__main__':
    run_edge_cases_test()
