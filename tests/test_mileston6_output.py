# verify_milestone6.py
import os
import json
from src.database import get_db_connection, init_db
from src.analysis.synthesizer import synthesize_analyses
from datetime import datetime, timedelta

def create_final_test_data():
    """Creates the data needed for the final synthesizer and output processor test."""
    print("[STEP 1] Inserting fake data for end-to-end test...")
    today = datetime.utcnow()
    fake_articles = [
        # Historical trend data for 'Technology'
        {"url": f"https://example.com/verify_m6_hist_{i}", "published_at": today - timedelta(days=i), "title": "Fake hist news",
         "nlp_features": {"sentiment": {"label": "positive", "score": 0.9}, "entities": [{"text": "Apple", "label": "ORG"}]}}
        for i in range(1, 4)
    ]
    # Today's high-impact event for 'Technology' and 'MSFT'
    fake_articles.append({
        "url": "https://example.com/verify_m6_today", "published_at": today, "title": "Microsoft AI Breakthrough",
        "nlp_features": {"sentiment": {"label": "positive", "score": 0.98}, "entities": [{"text": "Microsoft", "label": "ORG"}, {"text": "MSFT", "label": "ORG"}]}
    })
    inserted_urls = [a['url'] for a in fake_articles]
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # This ensures the nlp_features column exists before inserting.
            cursor.execute("ALTER TABLE articles ADD COLUMN IF NOT EXISTS nlp_features JSONB;")
            for article in fake_articles:
                cursor.execute(
                    "INSERT INTO articles (url, published_at, nlp_features, title) VALUES (%s, %s, %s, %s) ON CONFLICT (url) DO UPDATE SET nlp_features = EXCLUDED.nlp_features;",
                    (article['url'], article['published_at'], json.dumps(article['nlp_features']), article['title'])
                )
        conn.commit()
    print("Fake data inserted.")
    return inserted_urls

def cleanup_fake_data(urls):
    """Cleans up both articles and the reports generated during the test."""
    if not urls: return
    print("\n[STEP 3] Cleaning up fake data...")
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Clean up the temporary articles
            cursor.execute("DELETE FROM articles WHERE url = ANY(%s::text[]);", (urls,))
            # Clean up the report generated today to ensure test is repeatable
            # The ON DELETE CASCADE on the report_signals table will handle the rest.
            cursor.execute("DELETE FROM daily_reports WHERE report_date = %s;", (datetime.utcnow().date(),))
        conn.commit()
    print("Cleanup complete.")

def run_verification():
    """Runs the synthesizer and verifies the output processor's work."""
    print("--- Starting Final Output Verification ---")
    init_db()
    fake_data_urls = []
    try:
        fake_data_urls = create_final_test_data()
        
        print("\n[STEP 2] Running the final synthesizer and output processor...")
        synthesize_analyses()

        # --- Verification Step ---
        # 1. File Verification
        output_file = os.path.join("output", f"report_{datetime.utcnow().date()}.json")
        print(f"\n[VERIFICATION] Checking for output file at: {output_file}")
        file_exists = os.path.exists(output_file)
        if file_exists:
            print(f"SUCCESS: Output JSON file found.")
            with open(output_file, 'r') as f:
                data = json.load(f)
                print("File content snippet (confidence signals):")
                print(json.dumps(data.get('signals', {}).get('confidence_signals', []), indent=2))
        else:
            print(f"FAILURE: Output JSON file was not created.")

        # 2. Database Verification
        print("\n[VERIFICATION] Checking database for report records...")
        db_records_found = False
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM daily_reports WHERE report_date = %s;", (datetime.utcnow().date(),))
                    report_row = cursor.fetchone()
                    if report_row:
                        report_id = report_row[0]
                        cursor.execute("SELECT COUNT(*) FROM report_signals WHERE report_id = %s;", (report_id,))
                        signal_count = cursor.fetchone()[0]
                        if signal_count > 0:
                            print(f"SUCCESS: Found report with ID {report_id} and {signal_count} signals in the database.")
                            db_records_found = True
            if not db_records_found:
                 print("FAILURE: Did not find corresponding records in the database. This is likely why the file was not created.")
        except Exception as e:
            print(f"FAILURE: An error occurred while checking the database: {e}")

    finally:
        cleanup_fake_data(fake_data_urls)
    
    print("\n--- Verification Finished ---")

if __name__ == '__main__':
    run_verification()
