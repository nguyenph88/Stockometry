# src/analysis/historical_analyzer.py
import pandas as pd
from collections import defaultdict
from src.database import get_db_connection
from datetime import datetime, timedelta, timezone

SECTOR_MAP = {
    # Technology
    'AAPL': 'Technology', 'Apple': 'Technology',
    'MSFT': 'Technology', 'Microsoft': 'Technology',
    'GOOGL': 'Technology', 'Google': 'Technology', 'Alphabet': 'Technology',
    'NVDA': 'Technology', 'Nvidia': 'Technology',
    'TSLA': 'Technology', 'Tesla': 'Technology',
    'META': 'Technology', 'Facebook': 'Technology', 'Meta': 'Technology',
    'NFLX': 'Technology', 'Netflix': 'Technology',
    'ADBE': 'Technology', 'Adobe': 'Technology',
    'CRM': 'Technology', 'Salesforce': 'Technology',
    'ORCL': 'Technology', 'Oracle': 'Technology',
    'INTC': 'Technology', 'Intel': 'Technology',
    'AMD': 'Technology', 'Advanced Micro Devices': 'Technology',
    
    # Consumer Discretionary
    'AMZN': 'Consumer Discretionary', 'Amazon': 'Consumer Discretionary',
    'HD': 'Consumer Discretionary', 'Home Depot': 'Consumer Discretionary',
    'MCD': 'Consumer Discretionary', 'McDonald': 'Consumer Discretionary', 'McDonald\'s': 'Consumer Discretionary',
    'NKE': 'Consumer Discretionary', 'Nike': 'Consumer Discretionary',
    'SBUX': 'Consumer Discretionary', 'Starbucks': 'Consumer Discretionary',
    'DIS': 'Consumer Discretionary', 'Disney': 'Consumer Discretionary', 'Walt Disney': 'Consumer Discretionary',
    'CMCSA': 'Consumer Discretionary', 'Comcast': 'Consumer Discretionary',
    
    # Financial Services
    'JPM': 'Financial Services', 'JPMorgan': 'Financial Services', 'JPMorgan Chase': 'Financial Services',
    'GS': 'Financial Services', 'Goldman Sachs': 'Financial Services',
    'BAC': 'Financial Services', 'Bank of America': 'Financial Services',
    'WFC': 'Financial Services', 'Wells Fargo': 'Financial Services',
    'C': 'Financial Services', 'Citigroup': 'Financial Services',
    'MS': 'Financial Services', 'Morgan Stanley': 'Financial Services',
    'BLK': 'Financial Services', 'BlackRock': 'Financial Services',
    'AXP': 'Financial Services', 'American Express': 'Financial Services',
    'V': 'Financial Services', 'Visa': 'Financial Services',
    'MA': 'Financial Services', 'Mastercard': 'Financial Services',
    'BRK.A': 'Financial Services', 'Berkshire Hathaway': 'Financial Services',
    'BRK.B': 'Financial Services', 'Berkshire Hathaway': 'Financial Services',
    
    # Healthcare
    'JNJ': 'Healthcare', 'Johnson & Johnson': 'Healthcare',
    'UNH': 'Healthcare', 'UnitedHealth': 'Healthcare',
    'PFE': 'Healthcare', 'Pfizer': 'Healthcare',
    'ABBV': 'Healthcare', 'AbbVie': 'Healthcare',
    'TMO': 'Healthcare', 'Thermo Fisher Scientific': 'Healthcare',
    'ABT': 'Healthcare', 'Abbott': 'Healthcare', 'Abbott Laboratories': 'Healthcare',
    'LLY': 'Healthcare', 'Eli Lilly': 'Healthcare', 'Eli Lilly and Company': 'Healthcare',
    'DHR': 'Healthcare', 'Danaher': 'Healthcare',
    'BMY': 'Healthcare', 'Bristol-Myers Squibb': 'Healthcare',
    'AMGN': 'Healthcare', 'Amgen': 'Healthcare',
    'GILD': 'Healthcare', 'Gilead': 'Healthcare', 'Gilead Sciences': 'Healthcare',
    
    # Energy
    'XOM': 'Energy', 'Exxon': 'Energy', 'ExxonMobil': 'Energy',
    'CVX': 'Energy', 'Chevron': 'Energy',
    'COP': 'Energy', 'ConocoPhillips': 'Energy',
    'EOG': 'Energy', 'EOG Resources': 'Energy',
    'SLB': 'Energy', 'Schlumberger': 'Energy',
    'PSX': 'Energy', 'Phillips 66': 'Energy',
    'KMI': 'Energy', 'Kinder Morgan': 'Energy',
    'MPC': 'Energy', 'Marathon Petroleum': 'Energy',
    'VLO': 'Energy', 'Valero Energy': 'Energy',
    
    # Consumer Staples
    'PG': 'Consumer Staples', 'Procter & Gamble': 'Consumer Staples',
    'KO': 'Consumer Staples', 'Coca-Cola': 'Consumer Staples',
    'PEP': 'Consumer Staples', 'PepsiCo': 'Consumer Staples',
    'WMT': 'Consumer Staples', 'Walmart': 'Consumer Staples',
    'COST': 'Consumer Staples', 'Costco': 'Consumer Staples', 'Costco Wholesale': 'Consumer Staples',
    'PM': 'Consumer Staples', 'Philip Morris': 'Consumer Staples', 'Philip Morris International': 'Consumer Staples',
    'MO': 'Consumer Staples', 'Altria': 'Consumer Staples', 'Altria Group': 'Consumer Staples',
    'CL': 'Consumer Staples', 'Colgate-Palmolive': 'Consumer Staples',
    'GIS': 'Consumer Staples', 'General Mills': 'Consumer Staples',
    'K': 'Consumer Staples', 'Kellogg': 'Consumer Staples', 'Kellogg Company': 'Consumer Staples',
    
    # Industrials
    'BA': 'Industrials', 'Boeing': 'Industrials',
    'CAT': 'Industrials', 'Caterpillar': 'Industrials',
    'MMM': 'Industrials', '3M': 'Industrials',
    'UPS': 'Industrials', 'United Parcel Service': 'Industrials',
    'FDX': 'Industrials', 'FedEx': 'Industrials', 'Federal Express': 'Industrials',
    'GE': 'Industrials', 'General Electric': 'Industrials',
    'HON': 'Industrials', 'Honeywell': 'Industrials', 'Honeywell International': 'Industrials',
    'LMT': 'Industrials', 'Lockheed Martin': 'Industrials',
    'RTX': 'Industrials', 'Raytheon': 'Industrials', 'Raytheon Technologies': 'Industrials',
    'UNP': 'Industrials', 'Union Pacific': 'Industrials',
    
    # Materials
    'LIN': 'Materials', 'Linde': 'Materials', 'Linde plc': 'Materials',
    'APD': 'Materials', 'Air Products': 'Materials', 'Air Products and Chemicals': 'Materials',
    'FCX': 'Materials', 'Freeport-McMoRan': 'Materials',
    'NEM': 'Materials', 'Newmont': 'Materials', 'Newmont Corporation': 'Materials',
    'BHP': 'Materials', 'BHP Group': 'Materials',
    'RIO': 'Materials', 'Rio Tinto': 'Materials',
    'VALE': 'Materials', 'Vale': 'Materials', 'Vale S.A.': 'Materials',
    'DD': 'Materials', 'DuPont': 'Materials', 'DuPont de Nemours': 'Materials',
    'DOW': 'Materials', 'Dow': 'Materials', 'Dow Inc.': 'Materials',
    'NUE': 'Materials', 'Nucor': 'Materials',
    
    # Real Estate
    'PLD': 'Real Estate', 'Prologis': 'Real Estate',
    'AMT': 'Real Estate', 'American Tower': 'Real Estate',
    'CCI': 'Real Estate', 'Crown Castle': 'Real Estate', 'Crown Castle International': 'Real Estate',
    'EQIX': 'Real Estate', 'Equinix': 'Real Estate',
    'PSA': 'Real Estate', 'Public Storage': 'Real Estate',
    'O': 'Real Estate', 'Realty Income': 'Real Estate',
    'SPG': 'Real Estate', 'Simon Property Group': 'Real Estate',
    'WELL': 'Real Estate', 'Welltower': 'Real Estate',
    'DLR': 'Real Estate', 'Digital Realty': 'Real Estate', 'Digital Realty Trust': 'Real Estate',
    'AVB': 'Real Estate', 'AvalonBay': 'Real Estate', 'AvalonBay Communities': 'Real Estate',
    
    # Utilities
    'NEE': 'Utilities', 'NextEra Energy': 'Utilities',
    'DUK': 'Utilities', 'Duke Energy': 'Utilities',
    'SO': 'Utilities', 'Southern Company': 'Utilities',
    'D': 'Utilities', 'Dominion Energy': 'Utilities',
    'AEP': 'Utilities', 'American Electric Power': 'Utilities',
    'XEL': 'Utilities', 'Xcel Energy': 'Utilities',
    'SRE': 'Utilities', 'Sempra Energy': 'Utilities',
    'WEC': 'Utilities', 'WEC Energy Group': 'Utilities',
    'DTE': 'Utilities', 'DTE Energy': 'Utilities',
    'EIX': 'Utilities', 'Edison International': 'Utilities',
    
    # Communication Services
    'GOOGL': 'Communication Services', 'Google': 'Communication Services', 'Alphabet': 'Communication Services',
    'META': 'Communication Services', 'Facebook': 'Communication Services', 'Meta': 'Communication Services',
    'NFLX': 'Communication Services', 'Netflix': 'Communication Services',
    'DIS': 'Communication Services', 'Disney': 'Communication Services', 'Walt Disney': 'Communication Services',
    'CMCSA': 'Communication Services', 'Comcast': 'Communication Services',
    'T': 'Communication Services', 'AT&T': 'Communication Services',
    'VZ': 'Communication Services', 'Verizon': 'Communication Services', 'Verizon Communications': 'Communication Services',
    'TMUS': 'Communication Services', 'T-Mobile': 'Communication Services', 'T-Mobile US': 'Communication Services',
    'CHTR': 'Communication Services', 'Charter': 'Communication Services', 'Charter Communications': 'Communication Services',
    'PARA': 'Communication Services', 'Paramount': 'Communication Services', 'Paramount Global': 'Communication Services',
}

def analyze_historical_trends():
    """
    Analyzes NLP features from the last 6 days to identify sector trends,
    now including the source articles that contributed to the trend.
    """
    print("Starting historical trend analysis...")
    end_date = datetime.now(timezone.utc).date()
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
