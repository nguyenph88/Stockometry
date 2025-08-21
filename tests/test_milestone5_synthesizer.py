# verify_milestone5.py
import json
from src.database import get_db_connection, init_db
from src.analysis.synthesizer import synthesize_analyses
from datetime import datetime, timedelta

def create_confluence_data():
    """
    Creates the perfect test case: a sector with a positive historical trend
    and a positive high-impact event today.
    """
    print("[STEP 1] Inserting fake data to create a high-confidence signal...")
    
    today = datetime.utcnow()
    fake_articles = []
    
    # 1. Create the positive historical trend for 'Technology'
    for i in range(1, 4):
        day = today - timedelta(days=i)
        fake_articles.append({
            "url": f"https://example.com/verify_m5_tech_hist_{i}",
            "published_at": day, "title": "Fake historical tech news",
            "nlp_features": {
                "sentiment": {"label": "positive", "score": 0.9},
                "entities": [{"text": "Apple", "label": "ORG"}]
            }
        })
        
    # 2. Create the positive high-impact event for 'Technology' TODAY
    #    Also, add specific news for MSFT to test the stock prediction.
    fake_articles.append({
        "url": "https://example.com/verify_m5_tech_today_deal",
        "published_at": today, "title": "Microsoft Announces Groundbreaking AI Deal",
        "nlp_features": {
            "sentiment": {"label": "positive", "score": 0.98},
            "entities": [{"text": "Microsoft", "label": "ORG"}, {"text": "MSFT", "label": "ORG"}]
        }
    })

    inserted_urls = [a['url'] for a in fake_articles]

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("ALTER TABLE articles ADD COLUMN IF NOT EXISTS nlp_features JSONB;")
            for article in fake_articles:
                cursor.execute(
                    """
                    INSERT INTO articles (url, published_at, nlp_features, title)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE SET nlp_features = EXCLUDED.nlp_features;
                    """,
                    (article['url'], article['published_at'], json.dumps(article['nlp_features']), article['title'])
                )
        conn.commit()
    
    print("Fake data for synthesis test inserted successfully.")
    return inserted_urls

def cleanup_fake_data(urls):
    if not urls: return
    print("\n[STEP 3] Cleaning up all fake data...")
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM articles WHERE url = ANY(%s::text[]);", (urls,))
        conn.commit()
    print("Cleanup complete.")

def run_verification():
    """
    Runs the full verification for the final synthesizer.
    """
    print("--- Starting Milestone 5 Verification ---")
    init_db()
    fake_data_urls = []
    try:
        fake_data_urls = create_confluence_data()
        
        print("\n[STEP 2] Running the final analysis synthesizer...")
        synthesize_analyses()
        
    finally:
        cleanup_fake_data(fake_data_urls)
    
    print("\n--- Verification Finished ---")

if __name__ == '__main__':
    run_verification()
