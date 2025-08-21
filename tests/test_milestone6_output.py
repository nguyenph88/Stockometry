# verify_milestone6.py
import os
import json
from src.database import get_db_connection, init_db
from src.analysis.synthesizer import synthesize_analyses
from datetime import datetime, timedelta, timezone

def create_final_test_data():
    """Creates the data needed for the final synthesizer and output processor test."""
    print("[STEP 1] Inserting fake data for end-to-end test...")
    today = datetime.now(timezone.utc)
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
            for article in fake_articles:
                cursor.execute(
                    "INSERT INTO articles (url, published_at, nlp_features, title) VALUES (%s, %s, %s, %s) ON CONFLICT (url) DO UPDATE SET nlp_features = EXCLUDED.nlp_features;",
                    (article['url'], article['published_at'], json.dumps(article['nlp_features']), article['title'])
                )
        conn.commit()
    print("Fake data inserted.")
    return inserted_urls

def cleanup_fake_data(urls):
    if not urls: return
    print("\n[STEP 3] Cleaning up fake data...")
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM articles WHERE url = ANY(%s::text[]);", (urls,))
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

        # Verify the output file was created
        output_file = os.path.join("output", f"report_{datetime.now(timezone.utc).date()}.json")
        print(f"\n[VERIFICATION] Checking for output file at: {output_file}")
        if os.path.exists(output_file):
            print(f"SUCCESS: Output JSON file found.")
            with open(output_file, 'r') as f:
                data = json.load(f)
                print("File content snippet:")
                print(json.dumps(data['signals']['confidence_signals'], indent=2))
        else:
            print(f"FAILURE: Output JSON file was not created.")

    finally:
        cleanup_fake_data(fake_data_urls)
    
    print("\n--- Verification Finished ---")

if __name__ == '__main__':
    run_verification()
