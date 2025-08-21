# src/analysis/historical_analyzer.py
import pandas as pd
from collections import defaultdict
from src.database import get_db_connection
from datetime import datetime, timedelta

# A simple mapping of company tickers/names to sectors.
# In a real-world application, this would be more extensive or come from an external source.
SECTOR_MAP = {
    'AAPL': 'Technology', 'Apple': 'Technology',
    'MSFT': 'Technology', 'Microsoft': 'Technology',
    'GOOGL': 'Technology', 'Google': 'Technology',
    'AMZN': 'Consumer Discretionary', 'Amazon': 'Consumer Discretionary',
    'NVDA': 'Technology', 'Nvidia': 'Technology',
}

def analyze_historical_trends():
    """
    Analyzes NLP features from the last 6 days to identify sector trends.
    """
    print("Starting historical trend analysis...")
    
    # Define the time range: from 7 days ago up to yesterday.
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=7)
    
    query = """
        SELECT published_at, nlp_features
        FROM articles
        WHERE nlp_features IS NOT NULL
        AND published_at::date >= %s
        AND published_at::date < %s;
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (start_date, end_date))
                data = cursor.fetchall()

        if not data:
            print("No articles with NLP features found in the last 6 days.")
            return "No recent data available for historical analysis."

        # --- Data Processing ---
        # Aggregate sentiment scores by sector and day
        daily_sector_sentiments = defaultdict(lambda: defaultdict(list))

        for published_at, features in data:
            sentiment = features.get('sentiment', {})
            entities = features.get('entities', [])
            
            if not sentiment or not entities:
                continue

            # Convert sentiment label to a numerical score
            score = 0
            if sentiment['label'] == 'positive':
                score = sentiment['score']
            elif sentiment['label'] == 'negative':
                score = -sentiment['score']

            # Assign the article's sentiment to all relevant sectors
            article_date = published_at.date()
            found_sectors = set()
            for entity in entities:
                sector = SECTOR_MAP.get(entity['text'])
                if sector and sector not in found_sectors:
                    daily_sector_sentiments[sector][article_date].append(score)
                    found_sectors.add(sector)

        # Calculate average sentiment per sector per day
        avg_daily_sector_sentiment = defaultdict(dict)
        for sector, daily_scores in daily_sector_sentiments.items():
            for day, scores in daily_scores.items():
                if scores:
                    avg_daily_sector_sentiment[sector][day] = sum(scores) / len(scores)

        if not avg_daily_sector_sentiment:
            print("Could not derive any sector sentiment from recent articles.")
            return "Insufficient sector-specific news for historical analysis."

        # --- Trend Analysis ---
        report_lines = ["--- Historical Trend Analysis Report ---"]
        
        for sector, daily_avg in avg_daily_sector_sentiment.items():
            # Create a pandas Series for easy trend analysis, sorted by date
            series = pd.Series(daily_avg).sort_index()
            
            # Look for a consistent positive trend (e.g., positive for 3+ consecutive days)
            if len(series) >= 3:
                # Check if the last 3 days are consistently positive
                if all(series.iloc[-3:] > 0.1): # Using 0.1 to avoid neutral scores
                    report_lines.append(
                        f"[Bullish Signal] Sector '{sector}' shows strong positive sentiment for the last {len(series.iloc[-3:])} days."
                    )
                # Check if the last 3 days are consistently negative
                elif all(series.iloc[-3:] < -0.1):
                     report_lines.append(
                        f"[Bearish Signal] Sector '{sector}' shows strong negative sentiment for the last {len(series.iloc[-3:])} days."
                    )

        if len(report_lines) == 1:
            report_lines.append("No significant multi-day trends identified in any sector.")

        final_report = "\n".join(report_lines)
        print("Historical analysis complete.")
        print(final_report)
        return final_report

    except Exception as e:
        print(f"An error occurred during historical analysis: {e}")
        return "An error occurred during analysis."


if __name__ == '__main__':
    analyze_historical_trends()
