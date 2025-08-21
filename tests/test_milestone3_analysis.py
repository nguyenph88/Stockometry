import json
from src.database import get_db_connection, init_db
from src.analysis.historical_analyzer import analyze_historical_trends
from datetime import datetime, timedelta, timezone

def create_fake_trend_data():
    """Inserts fake processed articles to create a clear trend for testing."""
    print("[STEP 1] Inserting fake historical articles to create a testable trend...")
    
    # Create a strong positive trend for the 'Technology' sector over the last 3 days
    fake_articles = []
    for i in range(1, 4):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        article = {
            "url": f"https://example.com/verify_m3_tech_positive_{i}",
            "published_at": day,
            "nlp_features": {
                "sentiment": {"label": "positive", "score": 0.95},
                "entities": [{"text": "Apple", "label": "ORG"}]
            }
        }
        fake_articles.append(article)

    # Create a strong negative trend for 'Consumer Discretionary'
    for i in range(1, 4):
        day = datetime.now(timezone.utc) - timedelta(days=i)
        article = {
            "url": f"https://example.com/verify_m3_consumer_negative_{i}",
            "published_at": day,
            "nlp_features": {
                "sentiment": {"label": "negative", "score": 0.9},
                "entities": [{"text": "Amazon", "label": "ORG"}]
            }
        }
        fake_articles.append(article)

    inserted_urls = [a['url'] for a in fake_articles]

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Ensure nlp_features column exists
            cursor.execute("ALTER TABLE articles ADD COLUMN IF NOT EXISTS nlp_features JSONB;")
            
            for article in fake_articles:
                cursor.execute(
                    """
                    INSERT INTO articles (url, published_at, nlp_features, title)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE SET nlp_features = EXCLUDED.nlp_features;
                    """,
                    (article['url'], article['published_at'], json.dumps(article['nlp_features']), f"Fake Title {article['url']}")
                )
        conn.commit()
    
    print("Fake data inserted successfully.")
    return inserted_urls

def cleanup_fake_data(urls):
    """Removes the fake articles from the database."""
    if not urls:
        return
    print("\n[STEP 3] Cleaning up fake historical data...")
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM articles WHERE url = ANY(%s::text[]);", (urls,))
        conn.commit()
    print("Cleanup complete.")

def run_verification():
    """
    Runs the full verification process for the historical analyzer.
    """
    print("--- Starting Milestone 3 Verification ---")
    init_db()
    fake_data_urls = []
    try:
        fake_data_urls = create_fake_trend_data()
        
        print("\n[STEP 2] Running the historical trend analyzer...")
        analyze_historical_trends()
        
    finally:
        cleanup_fake_data(fake_data_urls)
    
    print("\n--- Verification Finished ---")

if __name__ == '__main__':
    run_verification()
