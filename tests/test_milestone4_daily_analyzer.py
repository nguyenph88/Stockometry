import json
from src.database import get_db_connection, init_db
from src.analysis.today_analyzer import analyze_todays_impact
from datetime import datetime

def create_fake_todays_data():
    """Inserts fake processed articles published 'today' for testing."""
    print("[STEP 1] Inserting fake 'today' articles for impact analysis...")
    
    today = datetime.utcnow()
    
    fake_articles = [
        # 1. High-impact due to keyword 'regulation'
        {
            "url": "https://example.com/verify_m4_tech_regulation",
            "published_at": today,
            "title": "New AI Regulation Bill Proposed, Nvidia Shares Volatile",
            "nlp_features": {
                "sentiment": {"label": "negative", "score": 0.85},
                "entities": [{"text": "Nvidia", "label": "ORG"}]
            }
        },
        # 2. High-impact due to extreme positive sentiment
        {
            "url": "https://example.com/verify_m4_consumer_deal",
            "published_at": today,
            "title": "Amazon Finalizes Major Acquisition, Market Cheers",
            "nlp_features": {
                "sentiment": {"label": "positive", "score": 0.98},
                "entities": [{"text": "Amazon", "label": "ORG"}]
            }
        },
        # 3. Low-impact, should be ignored by the analyzer
        {
            "url": "https://example.com/verify_m4_low_impact",
            "published_at": today,
            "title": "Microsoft Releases Minor Software Update",
            "nlp_features": {
                "sentiment": {"label": "neutral", "score": 0.7},
                "entities": [{"text": "Microsoft", "label": "ORG"}]
            }
        }
    ]

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
    
    print("Fake 'today' data inserted successfully.")
    return inserted_urls

def cleanup_fake_data(urls):
    """Removes the fake articles from the database."""
    if not urls: return
    print("\n[STEP 3] Cleaning up fake 'today' data...")
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM articles WHERE url = ANY(%s::text[]);", (urls,))
        conn.commit()
    print("Cleanup complete.")

def run_verification():
    """
    Runs the full verification process for the today's impact analyzer.
    """
    print("--- Starting Milestone 4 Verification ---")
    init_db()
    fake_data_urls = []
    try:
        fake_data_urls = create_fake_todays_data()
        
        print("\n[STEP 2] Running the today's impact analyzer...")
        analyze_todays_impact()
        
    finally:
        cleanup_fake_data(fake_data_urls)
    
    print("\n--- Verification Finished ---")

if __name__ == '__main__':
    run_verification()
