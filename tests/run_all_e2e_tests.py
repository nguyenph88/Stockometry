# run_all_e2e_tests.py
# Test runner script that executes all e2e test scenarios
import sys
import os
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test(test_name, test_function):
    """Runs a single test and reports the result."""
    print(f"\n{'='*80}")
    print(f"🧪 RUNNING TEST: {test_name}")
    print(f"{'='*80}")
    
    start_time = time.time()
    try:
        test_function()
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n✅ {test_name} PASSED in {duration:.2f} seconds")
        return True, duration
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        print(f"\n❌ {test_name} FAILED in {duration:.2f} seconds")
        print(f"Error: {e}")
        return False, duration

def main():
    """Main test runner function."""
    print("🚀 STOCKOMETRY E2E TEST SUITE")
    print("=" * 80)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Test results tracking
    results = []
    total_start_time = time.time()
    
    # Import and run all tests
    try:
        # Test 1: Bullish Technology Sector
        from tests.test_e2e_bullish_tech import run_bullish_tech_test
        success, duration = run_test("Bullish Technology Sector", run_bullish_tech_test)
        results.append(("Bullish Technology Sector", success, duration))
        
        # Test 2: Bearish Financial Sector
        from tests.test_e2e_bearish_financial import run_bearish_financial_test
        success, duration = run_test("Bearish Financial Sector", run_bearish_financial_test)
        results.append(("Bearish Financial Sector", success, duration))
        
        # Test 3: Mixed Market Signals
        from tests.test_e2e_mixed_signals import run_mixed_signals_test
        success, duration = run_test("Mixed Market Signals", run_mixed_signals_test)
        results.append(("Mixed Market Signals", success, duration))
        
        # Test 4: Edge Cases and No-Signals
        from tests.test_e2e_edge_cases import run_edge_cases_test
        success, duration = run_test("Edge Cases and No-Signals", run_edge_cases_test)
        results.append(("Edge Cases and No-Signals", success, duration))
        
        # Test 5: Original E2E Test
        from tests.test_e2e import run_e2e_test
        success, duration = run_test("Original E2E Test", run_e2e_test)
        results.append(("Original E2E Test", success, duration))
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all test files are in the tests/ directory")
        return 1
    
    # Calculate total time
    total_end_time = time.time()
    total_duration = total_end_time - total_start_time
    
    # Print summary
    print(f"\n{'='*80}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*80}")
    
    passed = 0
    failed = 0
    total_test_time = 0
    
    for test_name, success, duration in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name:<30} ({duration:.2f}s)")
        if success:
            passed += 1
        else:
            failed += 1
        total_test_time += duration
    
    print(f"\n{'='*80}")
    print(f"📈 FINAL RESULTS:")
    print(f"   Total Tests: {len(results)}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {failed}")
    print(f"   Success Rate: {(passed/len(results)*100):.1f}%")
    print(f"   Total Test Time: {total_test_time:.2f}s")
    print(f"   Total Time (including setup): {total_duration:.2f}s")
    print(f"{'='*80}")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! The system is working correctly.")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
