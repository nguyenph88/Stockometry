# verify_output_processor.py
import os
import sys
import json

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import get_db_connection, init_db
from src.output.processor import OutputProcessor
from datetime import datetime, timezone

# A pre-defined, multi-line report string to simulate the output from the synthesizer.
# This makes the test predictable and independent of the other analysis modules.
SAMPLE_REPORT_STRING = """
--- Synthesized Market Report ---

## Historical Trend Analysis ##
--- Historical Trend Analysis Report ---
[Bullish Signal] Sector 'Technology' shows strong positive sentiment for the last 3 days.
[Bearish Signal] Sector 'Consumer Discretionary' shows strong negative sentiment for the last 3 days.

## Today's High-Impact Analysis ##
--- Today's High-Impact Analysis Report ---
[Impact Alert] Sector 'Technology' predicted to go UP. Reason: High-impact news titled 'Microsoft AI Breakthrough' (Sentiment: positive @ 0.98).

## High-Confidence Signals (Confluence) ##
[HIGH CONFIDENCE BULLISH] Sector 'Technology' shows a positive historical trend and a positive high-impact event today.
    -> Predicted top stock movers in 'Technology':
        - MSFT: Strong positive news: 'Microsoft AI Breakthrough' (Score: 0.98)
"""

def cleanup_test_data():
    """Ensures the database is clean before and after the test."""
    print("--- Cleaning up previous test data (if any) ---")
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # The ON DELETE CASCADE on the report_signals table handles associated signals.
                cursor.execute("DELETE FROM daily_reports WHERE report_date = %s;", (datetime.now(timezone.utc).date(),))
            conn.commit()
        print("Cleanup complete.")
    except Exception as e:
        print(f"Cleanup failed or was not needed: {e}")

def run_verification():
    """
    Runs a focused test on the OutputProcessor to ensure it parses, saves to DB,
    and exports JSON correctly.
    """
    print("--- Starting Output Processor Verification ---")
    
    # 1. Setup: Ensure DB and tables exist and are clean for today's date.
    init_db()
    cleanup_test_data()
    
    report_id = None
    
    try:
        # 2. Action: Instantiate the processor and run the main method.
        print("\n[STEP 1] Initializing OutputProcessor with sample report...")
        processor = OutputProcessor(SAMPLE_REPORT_STRING)
        
        print("[STEP 2] Calling process_and_save() to parse and save to DB...")
        report_id = processor.process_and_save()
        
        if not report_id:
            print("FAILURE: process_and_save() returned None - database save failed")
            return

        # 3. Verification: Check the results in the database and test export functionality.
        print("\n--- Verifying Results ---")
        
        # 3a. Verify Database Records
        print("\n[VERIFICATION 1] Checking database for new records...")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM daily_reports WHERE report_date = %s;", (datetime.now(timezone.utc).date(),))
                report_row = cursor.fetchone()
                if report_row:
                    report_id = report_row[0]
                    cursor.execute("SELECT COUNT(*) FROM report_signals WHERE report_id = %s;", (report_id,))
                    signal_count = cursor.fetchone()[0]
                    print(f"SUCCESS: Found report with ID {report_id} and {signal_count} signals in the database.")
                else:
                    print("FAILURE: No report record was created in the database.")

        # 3b. Test JSON Export Functionality
        print("\n[VERIFICATION 2] Testing JSON export functionality...")
        json_data = processor.export_to_json(report_id=report_id)
        
        if json_data:
            print("SUCCESS: JSON export functionality working correctly.")
            print(f"    -> Report ID: {json_data.get('report_id')}")
            print(f"    -> Report Date: {json_data.get('report_date')}")
            print(f"    -> Run Source: {json_data.get('run_source')}")
            print(f"    -> Executive Summary: {json_data.get('executive_summary', 'MISSING!')[:100]}...")
            
            # Test file export
            file_path = processor.save_json_to_file(json_data, "exports")
            if file_path and os.path.exists(file_path):
                print(f"SUCCESS: JSON file export working: {file_path}")
            else:
                print("FAILURE: JSON file export failed")
        else:
            print("FAILURE: JSON export functionality failed")

    finally:
        # 4. Cleanup
        print("\n--- Final Cleanup ---")
        cleanup_test_data()
        
        # Clean up any test export files
        if os.path.exists("exports"):
            for file in os.listdir("exports"):
                if file.startswith(f"report_{datetime.now(timezone.utc).date()}_") and file.endswith("_scheduled.json"):
                    os.remove(os.path.join("exports", file))
                    print(f"Removed test export file: {file}")

if __name__ == "__main__":
    run_verification()
