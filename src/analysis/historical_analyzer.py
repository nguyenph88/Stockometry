# src/analysis/historical_analyzer.py
import pandas as pd
from collections import defaultdict
from src.database import get_db_connection
from datetime import datetime, timedelta

SECTOR_MAP = {
    'AAPL': 'Technology', 'Apple': 'Technology',
    'MSFT': 'Technology', 'Microsoft': 'Technology',
    'GOOGL': 'Technology', 'Google': 'Technology',
    'AMZN': 'Consumer Discretionary', 'Amazon': 'Consumer Discretionary',
    'NVDA': 'Technology', 'Nvidia': 'Technology',
}

def analyze_historical_trends():
    """
    Analyzes NLP features from the last 6 days to identify sector trends,
    now including the source articles that contributed to the trend.
    """
    print("Starting historical trend analysis...")
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=7)
    
    query = "SELECT published_at, nlp_features, title, url FROM articles WHERE nlp_features IS NOT NULL AND published_at::date >= %s AND published_at::date < %s;"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (start_date, end_date))
            data = cursor.fetchall()

        if not data:
            return {"signals": [], "summary_points": ["No recent data available for historical analysis."]}

        daily_sector_sentiments = defaultdict(lambda: defaultdict(list))
        article_sources = defaultdict(list)

        for published_at, features, title, url in data:
            sentiment = features.get('sentiment', {})
            entities = features.get('entities', [])
            if not sentiment or not entities: continue

            score = 0
            if sentiment['label'] == 'positive': score = sentiment['score']
            elif sentiment['label'] == 'negative': score = -sentiment['score']

            article_date = published_at.date()
            for entity in entities:
                sector = SECTOR_MAP.get(entity['text'])
                if sector:
                    daily_sector_sentiments[sector][article_date].append(score)
                    article_sources[sector].append({"title": title, "url": url})

        avg_daily_sector_sentiment = defaultdict(dict)
        for sector, daily_scores in daily_sector_sentiments.items():
            for day, scores in daily_scores.items():
                if scores:
                    avg_daily_sector_sentiment[sector][day] = sum(scores) / len(scores)

        signals = []
        summary_points = []
        for sector, daily_avg in avg_daily_sector_sentiment.items():
            series = pd.Series(daily_avg).sort_index()
            if len(series) >= 3:
                direction = None
                if all(series.iloc[-3:] > 0.1): direction = "Bullish"
                elif all(series.iloc[-3:] < -0.1): direction = "Bearish"
                
                if direction:
                    signals.append({
                        "type": "HISTORICAL", "direction": direction, "sector": sector,
                        "source_articles": list({v['url']:v for v in article_sources[sector]}.values())[:3] # Top 3 unique sources
                    })
                    summary_points.append(f"A consistent {direction.lower()} trend was observed for the '{sector}' sector.")

        if not summary_points:
            summary_points.append("No significant multi-day trends identified.")

        return {"signals": signals, "summary_points": summary_points}

    except Exception as e:
        print(f"An error occurred during historical analysis: {e}")
        return {"signals": [], "summary_points": ["An error occurred during analysis."]}
