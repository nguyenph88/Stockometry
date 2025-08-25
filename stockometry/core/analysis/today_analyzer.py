# src/analysis/today_analyzer.py
from ...database import get_db_connection
from datetime import datetime, timezone, timedelta
from .historical_analyzer import SECTOR_MAP

IMPACT_KEYWORDS = ['regulation', 'act', 'tariff', 'subsidy', 'ban', 'approval', 'deal', 'acquisition', 'merger', 'lawsuit']
EXTREME_SENTIMENT_THRESHOLD = 0.90

def _analyze_articles_for_date(articles, target_date_description):
    """
    Common logic for analyzing articles for high-impact events.
    This is a private helper function to avoid code duplication.
    """
    if not articles:
        return {"signals": [], "summary_points": [f"No articles found for {target_date_description}."]}
    
    signals = []
    summary_points = []
    
    for title, description, features, url in articles:
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
        summary_points.append(f"Analyzed {len(articles)} articles for {target_date_description}, but no high-impact signals were generated. Articles may not contain impact keywords or extreme sentiment scores above the {EXTREME_SENTIMENT_THRESHOLD} threshold.")

    return {"signals": signals, "summary_points": summary_points}

def analyze_impact_for_date(target_date: datetime.date):
    """
    Analyzes news for a specific date for high-impact events.
    
    ⚠️  STRICTLY FOR BACKFILL USE ONLY - DO NOT CALL OR USE IN OTHER CONTEXTS ⚠️
    
    This function is a backfill-specific version of analyze_todays_impact() that allows
    analyzing impact for any date instead of being hardcoded to today.
    
    Args:
        target_date (datetime.date): The specific date to analyze
        
    Returns:
        dict: Same structure as analyze_todays_impact() with signals and summary_points
    """
    print(f"Starting analysis of {target_date}'s high-impact news...")
    yesterday_date = target_date - timedelta(days=1)
    
    # First try to get articles for the target date
    query = "SELECT title, description, nlp_features, url FROM articles WHERE nlp_features IS NOT NULL AND published_at::date = %s;"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (target_date,))
            date_articles = cursor.fetchall()

            # If no articles found for target date, fall back to previous day
            if not date_articles:
                print(f"No articles found for {target_date}, falling back to {yesterday_date}")
                cursor.execute(query, (yesterday_date,))
                date_articles = cursor.fetchall()
                
                if not date_articles:
                    return {"signals": [], "summary_points": [f"No articles found for {target_date} or {yesterday_date}."]}
                else:
                    print(f"Found {len(date_articles)} articles from {yesterday_date} for analysis")
            else:
                print(f"Found {len(date_articles)} articles for {target_date}'s analysis")
        
        # Use common analysis logic
        return _analyze_articles_for_date(date_articles, f"{target_date}")

    except Exception as e:
        print(f"An error occurred during {target_date}'s impact analysis: {e}")
        return {"signals": [], "summary_points": [f"An error occurred during analysis for {target_date}."]}

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
        
        # Use common analysis logic
        return _analyze_articles_for_date(todays_articles, "today")

    except Exception as e:
        print(f"An error occurred during today's impact analysis: {e}")
        return {"signals": [], "summary_points": ["An error occurred during analysis."]}
