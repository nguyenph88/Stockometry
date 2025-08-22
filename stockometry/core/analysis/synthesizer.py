# src/analysis/synthesizer.py
from .historical_analyzer import analyze_historical_trends, SECTOR_MAP
from .today_analyzer import analyze_todays_impact
from ...database import get_db_connection
from datetime import datetime, timezone

def synthesize_analyses():
    """
    Runs all analyses, generates an executive summary, and creates a final
    structured report object for processing.
    """
    print("--- Starting Final Analysis Synthesis ---")
    
    historical_result = analyze_historical_trends()
    today_result = analyze_todays_impact()
    
    all_signals = historical_result['signals'] + today_result['signals']
    
    # --- Confluence Logic ---
    bullish_trends = {s['sector'] for s in historical_result['signals'] if s['direction'] == 'Bullish'}
    impact_up = {s['sector'] for s in today_result['signals'] if s['direction'] == 'UP'}
    high_confidence_bullish = bullish_trends & impact_up
    
    confidence_signals = []
    for sector in high_confidence_bullish:
        predicted_stocks = predict_stocks_for_sector(sector)
        # Aggregate source articles from both trend and impact signals
        sources = next((s['source_articles'] for s in historical_result['signals'] if s['sector'] == sector), []) + \
                  next((s['source_articles'] for s in today_result['signals'] if s['sector'] == sector), [])
        
        confidence_signals.append({
            "type": "CONFIDENCE", "direction": "BULLISH", "sector": sector,
            "predicted_stocks": predicted_stocks or [],
            "source_articles": list({v['url']:v for v in sources}.values()) # Unique sources
        })

    # --- Executive Summary Generation ---
    summary_points = historical_result['summary_points'] + today_result['summary_points']
    if high_confidence_bullish:
        summary_points.append(f"High-confidence bullish signals were found for the following sectors: {', '.join(high_confidence_bullish)}.")
    
    executive_summary = " ".join(summary_points)
    
    # --- Final Report Object ---
    final_report_object = {
        "executive_summary": executive_summary,
        "signals": {
            "historical": historical_result['signals'],
            "impact": today_result['signals'],
            "confidence": confidence_signals
        }
    }
    
    print("\n" + "="*50)
    print("FINAL REPORT OBJECT GENERATED:")
    import json
    print(json.dumps(final_report_object, indent=2))
    print("="*50 + "\n")
    
    return final_report_object

def predict_stocks_for_sector(sector: str):
    """Advanced Mode: Predicts individual stock movers for a sector."""
    print(f"Running Advanced Mode for sector: {sector}")
    target_tickers = [ticker for ticker, s in SECTOR_MAP.items() if s == sector]
    if not target_tickers: return []
    today_date = datetime.now(timezone.utc).date()
    query = "SELECT nlp_features, title, url FROM articles WHERE nlp_features IS NOT NULL AND published_at::date = %s;"
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (today_date,))
            todays_articles = cursor.fetchall()
            
        stock_scores = {}
        for features, title, url in todays_articles:
            sentiment = features.get('sentiment', {})
            if sentiment.get('label') != 'positive': continue
            for entity in features.get('entities', []):
                if entity.get('text') in target_tickers:
                    ticker = entity['text']
                    score = sentiment.get('score', 0)
                    if score > stock_scores.get(ticker, {}).get('score', 0):
                         stock_scores[ticker] = {"score": score, "reason": title, "url": url}
        
        if not stock_scores: return []
        
        sorted_stocks = sorted(stock_scores.items(), key=lambda item: item[1]['score'], reverse=True)
        
        return [{"symbol": stock, "reason": data['reason'], "url": data['url'], "score": round(data['score'], 4)} for stock, data in sorted_stocks[:2]]

    except Exception as e:
        print(f"An error during stock prediction: {e}")
        return []
