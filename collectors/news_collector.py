import requests
from src.config import settings
from src.database import get_db_connection

def fetch_and_store_news():
    """Fetches news from NewsAPI and stores it in the database."""
    print("Fetching news from NewsAPI...")
    params = {
        "apiKey": settings.news_api_key,
        **settings.api.news_api.get("query_params", {})
    }
    try:
        response = requests.get(settings.api.news_api["base_url"], params=params)
        response.raise_for_status()
        articles = response.json().get("articles", [])

        if not articles:
            print("No new articles found.")
            return

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                insert_query = """
                    INSERT INTO articles (source_id, source_name, author, title, url, description, content, published_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO NOTHING;
                """
                for article in articles:
                    cursor.execute(insert_query, (
                        article.get("source", {}).get("id"),
                        article.get("source", {}).get("name"),
                        article.get("author"),
                        article.get("title"),
                        article.get("url"),
                        article.get("description"),
                        article.get("content"),
                        article.get("publishedAt")
                    ))
            conn.commit()
        print(f"Successfully processed {len(articles)} articles.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching news from NewsAPI: {e}")
    except Exception as e:
        print(f"An error occurred while storing news: {e}")

if __name__ == '__main__':
    fetch_and_store_news()
