#!/usr/bin/env python3
"""
Simple Runner for Comprehensive E2E Test
Run this script to execute the complete Stockometry workflow test
"""

import sys
import os

def main():
    """Main function to run the comprehensive E2E test"""
    print("🚀 Stockometry Comprehensive E2E Test Runner")
    print("=" * 50)
    
    try:
        # Import and run the comprehensive test
        from stockometry.tests.test_comprehensive_e2e import run_comprehensive_e2e_test
        
        print("✅ Test module imported successfully")
        print("🌍 Starting comprehensive end-to-end test...")
        print("📋 This test will validate:")
        print("   0. Drop all existing tables")
        print("   1. Database connection & schema")
        print("   2. News collection & storage")
        print("   3. Market data collection & storage")
        print("   4. NLP processing & storage")
        print("   5. Analysis generation")
        print("   6. Report saving & database storage")
        print("   7. JSON export functionality")
        print("   8. API endpoints (if server running)")
        print("   9. Test data cleanup")
        print("   10. Complete staging database cleanup")
        print()
        
        # Run the test
        success = run_comprehensive_e2e_test()
        
        if success:
            print("\n🎉 All tests passed! Stockometry is working correctly.")
            sys.exit(0)
        else:
            print("\n💥 Tests failed! Check the output above for details.")
            sys.exit(1)
            
    except ImportError as e:
        print(f"❌ Failed to import test module: {e}")
        print("💡 Make sure you're running this from the tests directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
