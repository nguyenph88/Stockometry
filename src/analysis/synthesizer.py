# src/analysis/synthesizer.py
from .historical_analyzer import analyze_historical_trends, SECTOR_MAP
from .today_analyzer import analyze_todays_impact
from src.database import get_db_connection
from datetime import datetime

def synthesize_analyses():
    """
    Runs both historical and today's analysis and compares them to generate a final report string.
    This function is now only responsible for creating the report, not saving it.
    """
    print("--- Starting Final Analysis Synthesis ---")
    
    historical_report = analyze_historical_trends()
    today_report = analyze_todays_impact()
    
    final_report_lines = ["--- Synthesized Market Report ---"]
    final_report_lines.append("\n## Historical Trend Analysis ##")
    final_report_lines.append(historical_report)
    final_report_lines.append("\n## Today's High-Impact Analysis ##")
    final_report_lines.append(today_report)
    
    bullish_trend_sectors = [s.split("'")[1] for s in historical_report.split('\n') if "Bullish Signal" in s]
    bullish_impact_sectors = [s.split("'")[1] for s in today_report.split('\n') if "predicted to go UP" in s]
    
    high_confidence_bullish = set(bullish_trend_sectors) & set(bullish_impact_sectors)
    
    final_report_lines.append("\n## High-Confidence Signals (Confluence) ##")
    if high_confidence_bullish:
        for sector in high_confidence_bullish:
            final_report_lines.append(
                f"[HIGH CONFIDENCE BULLISH] Sector '{sector}' shows a positive historical trend and a positive high-impact event today."
            )
            predicted_stocks = predict_stocks_for_sector(sector)
            if predicted_stocks:
                final_report_lines.append(f"    -> Predicted top stock movers in '{sector}':")
                for stock, reason in predicted_stocks.items():
                    final_report_lines.append(f"        - {stock}: {reason}")
            else:
                final_report_lines.append(f"    -> Could not identify specific stock movers in '{sector}'.")
    else:
        final_report_lines.append("No high-confidence signals where historical trends and today's events align.")
        
    final_report = "\n".join(final_report_lines)
    
    # The report is printed here for real-time console output
    print("\n" + "="*50)
    print("FINAL REPORT GENERATED:")
    print(final_report)
    print("="*50 + "\n")
    
    return final_report

def predict_stocks_for_sector(sector: str):
    """
    Advanced Mode: For a given sector, find the stocks with the most positive news today.
    """
    print(f"Running Advanced Mode for sector: {sector}")
    target_tickers = [ticker for ticker, s in SECTOR_MAP.items() if s == sector]
    if not target_tickers: return None
    today_date = datetime.utcnow().date()
    query = "SELECT nlp_features, title FROM articles WHERE nlp_features IS NOT NULL AND published_at::date = %s;"
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (today_date,))
                todays_articles = cursor.fetchall()
        stock_scores = {}
        for features, title in todays_articles:
            sentiment = features.get('sentiment', {})
            if sentiment.get('label') != 'positive': continue
            for entity in features.get('entities', []):
                if entity.get('text') in target_tickers:
                    ticker = entity['text']
                    score = sentiment.get('score', 0)
                    if score > stock_scores.get(ticker, (0, ''))[0]:
                         stock_scores[ticker] = (score, title)
        if not stock_scores: return None
        sorted_stocks = sorted(stock_scores.items(), key=lambda item: item[1][0], reverse=True)
        return {stock: f"Strong positive news: '{reason}' (Score: {score:.2f})" for stock, (score, reason) in sorted_stocks[:2]}
    except Exception as e:
        print(f"An error occurred during stock prediction: {e}")
        return None
