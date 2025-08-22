import yfinance as yf
import numpy as np
from src.config import settings
from src.database import get_db_connection

def fetch_and_store_market_data():
    """Fetches historical market data and stores it in the database."""
    tickers = settings.api.market_data.get("tickers", [])
    period = settings.api.market_data.get("period", "1mo")
    
    if not tickers:
        print("No tickers defined in settings.yml. Skipping market data collection.")
        return
        
    print(f"Fetching market data for tickers: {tickers}...")

    try:
        data = yf.download(tickers, period=period, group_by='ticker')
        if data.empty:
            print("No market data downloaded from yfinance.")
            return

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                insert_query = """
                    INSERT INTO stock_data (ticker, date, open, high, low, close, volume)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (ticker, date) DO NOTHING;
                """
                count = 0
                for ticker in tickers:
                    # yfinance returns a multi-level column df for multiple tickers
                    ticker_data = data[ticker] if len(tickers) > 1 else data
                    
                    # Filter out rows where all values are NaN
                    ticker_data = ticker_data.dropna(how='all')

                    for index, row in ticker_data.iterrows():
                        # Convert numpy types to Python types to avoid PostgreSQL schema issues
                        open_val = float(row['Open']) if not np.isnan(row['Open']) else None
                        high_val = float(row['High']) if not np.isnan(row['High']) else None
                        low_val = float(row['Low']) if not np.isnan(row['Low']) else None
                        close_val = float(row['Close']) if not np.isnan(row['Close']) else None
                        volume_val = int(row['Volume']) if not np.isnan(row['Volume']) else None
                        
                        cursor.execute(insert_query, (
                            ticker,
                            index.date(),
                            open_val,
                            high_val,
                            low_val,
                            close_val,
                            volume_val
                        ))
                        count += cursor.rowcount
            conn.commit()
        print(f"Successfully inserted {count} new market data records.")

    except Exception as e:
        print(f"An error occurred while fetching or storing market data: {e}")

if __name__ == '__main__':
    fetch_and_store_market_data()
