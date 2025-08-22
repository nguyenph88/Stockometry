import json
from stockometry.database import get_db_connection, init_db
from stockometry.core.nlp.processor import process_articles_and_store_features

# Sample articles to test the NLP pipeline
SAMPLE_ARTICLES = [
    {
        "title": "Tech Giant Announces Record Profits Amidst New Regulations",
        "description": "Shares of NVDA surged today after the company reported stellar earnings, defying concerns over new government oversight.",
        "url": "https://example.com/verify_article1"
    },
    {
        "title": "Global Markets Tumble as New Tariffs Imposed",
        "description": "A sense of fear grips Wall Street. The Dow Jones Industrial Average plummeted following the announcement of new trade tariffs.",
        "url": "https://example.com/verify_article2"
    },
    {
        "title": "Neutral Report on Corn Futures",
        "description": "The weekly agricultural report showed stable yields for corn, with no significant changes expected in the short term.",
        "url": "https://example.com/verify_article3"
    }
]

def run_verification():
    """
    A simple test script to insert sample data, run the NLP processor,
    and print the output to verify Milestone 2 is working.
    """
    print("--- Starting Milestone 2 Verification ---")
    
    # Ensure DB is initialized
    init_db()
    
    inserted_ids = []

    try:
        # Step 1: Insert sample raw articles into the database
        print("\n[STEP 1] Inserting 3 sample articles for processing...")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                for article in SAMPLE_ARTICLES:
                    # Use ON CONFLICT to avoid errors if the script is run multiple times
                    cursor.execute(
                        """
                        INSERT INTO articles (title, description, url, published_at)
                        VALUES (%s, %s, %s, NOW())
                        ON CONFLICT (url) DO UPDATE SET title = EXCLUDED.title
                        RETURNING id;
                        """,
                        (article['title'], article['description'], article['url'])
                    )
                    article_id = cursor.fetchone()[0]
                    inserted_ids.append(article_id)
            conn.commit()
        print(f"Successfully inserted/verified articles with IDs: {inserted_ids}")

        # Step 2: Run the NLP processor
        print("\n[STEP 2] Running the NLP feature processor...")
        # The processor will find and update the articles we just inserted
        process_articles_and_store_features()

        # Step 3: Fetch the articles back and print the results
        print("\n[STEP 3] Fetching processed articles and displaying NLP features:")
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Use a tuple for the ANY clause
                cursor.execute(
                    "SELECT id, title, nlp_features FROM articles WHERE id = ANY(%s::int[]) ORDER BY id;",
                    (inserted_ids,)
                )
                results = cursor.fetchall()
                if not results:
                    print("ERROR: Could not fetch processed articles.")
                    return

                for row in results:
                    article_id, title, features = row
                    print("-" * 40)
                    print(f"  Article ID: {article_id}")
                    print(f"  Title: {title}")
                    if features:
                        # Pretty-print the JSON for readability
                        print("  NLP Features:")
                        print(json.dumps(features, indent=4))
                    else:
                        print("  NLP Features: [FAILED TO PROCESS]")
                    print("-" * 40)

    finally:
        # Step 4: Clean up the database by deleting the sample articles
        if inserted_ids:
            print("\n[STEP 4] Cleaning up by deleting sample articles...")
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM articles WHERE id = ANY(%s::int[]);", (inserted_ids,))
                conn.commit()
            print("Cleanup complete.")

    print("\n--- Verification Finished ---")

if __name__ == '__main__':
    run_verification()
