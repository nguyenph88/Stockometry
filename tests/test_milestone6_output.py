# verify_output_processor.py
import os
import json
from src.database import get_db_connection, init_db
from src.output.processor import OutputProcessor
from datetime import datetime

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
                cursor.execute("DELETE FROM daily_reports WHERE report_date = %s;", (datetime.utcnow().date(),))
            conn.commit()
        print("Cleanup complete.")
    except Exception as e:
        print(f"Cleanup failed or was not needed: {e}")

def run_verification():
    """
    Runs a focused test on the OutputProcessor to ensure it parses, saves to DB,
    and writes the JSON file correctly.
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
        
        print("[STEP 2] Calling process_and_save() to parse, save to DB, and write file...")
        processor.process_and_save()

        # 3. Verification: Check the results in the database and file system.
        print("\n--- Verifying Results ---")
        
        # 3a. Verify Database Records
        print("\n[VERIFICATION 1] Checking database for new records...")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM daily_reports WHERE report_date = %s;", (datetime.utcnow().date(),))
                report_row = cursor.fetchone()
                if report_row:
                    report_id = report_row[0]
                    cursor.execute("SELECT COUNT(*) FROM report_signals WHERE report_id = %s;", (report_id,))
                    signal_count = cursor.fetchone()[0]
                    print(f"SUCCESS: Found report with ID {report_id} and {signal_count} signals in the database.")
                else:
                    print("FAILURE: No report record was created in the database.")

        # 3b. Verify JSON File Creation
        output_file = os.path.join("output", f"report_{datetime.utcnow().date()}.json")
        print(f"\n[VERIFICATION 2] Checking for output file at: {output_file}")
        if os.path.exists(output_file):
            print(f"SUCCESS: Output JSON file was created.")
            # Optional: print content to verify
            with open(output_file, 'r') as f:
                data = json.load(f)
                print("    -> File content looks valid.")
        else:
            print(f"FAILURE: Output JSON file was NOT created. This is likely because the database save failed.")

    finally:
        # 4. Cleanup
        print("\n--- Final Cleanup ---")
        cleanup_test_data()
        # Also remove the generated file
        output_file = os.path.join("output", f"report_{datetime.utcnow().date()}.json")
        if os.path.exists(output_file):
            os.remove(output_file)
            print(f"Removed test file: {output_file}")

    print("\n--- Verification Finished ---")

if __name__ == '__main__':
    run_verification()
