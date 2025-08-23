# src/analysis/today_analyzer.py
from ...database import get_db_connection
from datetime import datetime, timezone, timedelta
from .historical_analyzer import SECTOR_MAP

IMPACT_KEYWORDS = ['regulation', 'act', 'tariff', 'subsidy', 'ban', 'approval', 'deal', 'acquisition', 'merger', 'lawsuit']
EXTREME_SENTIMENT_THRESHOLD = 0.90

def analyze_todays_impact():
    """
    Analyzes today's news for high-impact events, now including source articles.
    Falls back to yesterday's articles if no articles found for today.
    """
    print("Starting analysis of today's high-impact news...")
    today_date = datetime.now(timezone.utc).date()  # Use UTC to match database timestamps
    yesterday_date = today_date - timedelta(days=1)
    
    # First try to get today's articles
    query = "SELECT title, description, nlp_features, url FROM articles WHERE nlp_features IS NOT NULL AND published_at::date = %s;"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (today_date,))
            todays_articles = cursor.fetchall()

            # If no articles found for today, fall back to yesterday
            if not todays_articles:
                print(f"No articles found for today ({today_date}), falling back to yesterday ({yesterday_date})")
                cursor.execute(query, (yesterday_date,))
                todays_articles = cursor.fetchall()
                
                if not todays_articles:
                    return {"signals": [], "summary_points": ["No articles found for today's date or yesterday."]}
                else:
                    print(f"Found {len(todays_articles)} articles from yesterday for analysis")
            else:
                print(f"Found {len(todays_articles)} articles for today's analysis")
        
        signals = []
        summary_points = []
        for title, description, features, url in todays_articles:
            text_to_check = (title.lower() if title else "") + (description.lower() if description else "")
            sentiment = features.get('sentiment', {})
            
            is_keyword_event = any(keyword in text_to_check for keyword in IMPACT_KEYWORDS)
            is_extreme_sentiment = sentiment and sentiment.get('score', 0) > EXTREME_SENTIMENT_THRESHOLD

            if is_keyword_event or is_extreme_sentiment:
                entities = features.get('entities', [])
                for entity in entities:
                    sector = SECTOR_MAP.get(entity['text'])
                    if sector:
                        direction = "UP" if sentiment.get('label') == 'positive' else "DOWN"
                        signals.append({
                            "type": "IMPACT", "sector": sector, "direction": direction,
                            "details": f"High-impact news titled '{title}' (Sentiment: {sentiment.get('label')} @ {sentiment.get('score')}).",
                            "source_articles": [{"title": title, "url": url}]
                        })
                        summary_points.append(f"A high-impact event for the '{sector}' sector suggests a short-term move {direction.lower()}.")
                        break # Process first sector found in an article

        if not summary_points:
            summary_points.append(f"Analyzed {len(todays_articles)} articles today, but no high-impact signals were generated. Articles may not contain impact keywords or extreme sentiment scores above the {EXTREME_SENTIMENT_THRESHOLD} threshold.")

        return {"signals": signals, "summary_points": summary_points}

    except Exception as e:
        print(f"An error occurred during today's impact analysis: {e}")
        return {"signals": [], "summary_points": ["An error occurred during analysis."]}
