from src.database import get_db_connection
from datetime import datetime
from .historical_analyzer import SECTOR_MAP # Reuse the sector map

# Define keywords that signal a high-impact event
IMPACT_KEYWORDS = [
    'regulation', 'act', 'tariff', 'subsidy', 'incentive',
    'ban', 'approval', 'deal', 'acquisition', 'merger', 'lawsuit'
]
# Define a sentiment threshold for what is considered "extreme"
EXTREME_SENTIMENT_THRESHOLD = 0.90

def analyze_todays_impact():
    """
    Analyzes today's news for high-impact events and predicts sector movements.
    """
    print("Starting analysis of today's high-impact news...")
    
    today_date = datetime.utcnow().date()
    
    query = """
        SELECT title, description, nlp_features
        FROM articles
        WHERE nlp_features IS NOT NULL
        AND published_at::date = %s;
    """
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (today_date,))
                todays_articles = cursor.fetchall()

        if not todays_articles:
            print("No processed articles found for today.")
            return "No new articles available for today's impact analysis."

        high_impact_events = []

        for title, description, features in todays_articles:
            text_to_check = (title.lower() if title else "") + (description.lower() if description else "")
            sentiment = features.get('sentiment', {})
            
            is_keyword_event = any(keyword in text_to_check for keyword in IMPACT_KEYWORDS)
            is_extreme_sentiment = sentiment and sentiment.get('score', 0) > EXTREME_SENTIMENT_THRESHOLD

            # An article is high-impact if it contains a keyword OR has extreme sentiment
            if is_keyword_event or is_extreme_sentiment:
                entities = features.get('entities', [])
                found_sectors = set()
                for entity in entities:
                    sector = SECTOR_MAP.get(entity['text'])
                    if sector and sector not in found_sectors:
                        high_impact_events.append({
                            "sector": sector,
                            "sentiment_label": sentiment.get('label'),
                            "sentiment_score": sentiment.get('score'),
                            "source_title": title
                        })
                        found_sectors.add(sector)
        
        # --- Generate Report ---
        report_lines = ["--- Today's High-Impact Analysis Report ---"]
        
        if not high_impact_events:
            report_lines.append("No high-impact news events identified for any tracked sectors today.")
        else:
            for event in high_impact_events:
                direction = "NEUTRAL"
                if event['sentiment_label'] == 'positive':
                    direction = "UP"
                elif event['sentiment_label'] == 'negative':
                    direction = "DOWN"
                
                report_lines.append(
                    f"[Impact Alert] Sector '{event['sector']}' predicted to go {direction}. "
                    f"Reason: High-impact news titled '{event['source_title']}' "
                    f"(Sentiment: {event['sentiment_label']} @ {event['sentiment_score']})."
                )

        final_report = "\n".join(report_lines)
        print("Today's impact analysis complete.")
        print(final_report)
        return final_report

    except Exception as e:
        print(f"An error occurred during today's impact analysis: {e}")
        return "An error occurred during analysis."

if __name__ == '__main__':
    analyze_todays_impact()
