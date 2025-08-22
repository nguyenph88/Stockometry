import unittest
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd
from stockometry.core.collectors.news_collector import fetch_and_store_news
from stockometry.core.collectors.market_data_collector import fetch_and_store_market_data


class TestNewsCollector(unittest.TestCase):
    """Test cases for the news collector functionality."""

    @patch('collectors.news_collector.get_db_connection')
    @patch('collectors.news_collector.requests.get')
    @patch('collectors.news_collector.settings')
    def test_news_collector_success(self, mock_settings, mock_requests_get, mock_db_conn):
        """Test successful news collection and storage."""
        # Mock settings
        mock_settings.news_api_key = "test-api-key"
        mock_settings.news_api = {
            "base_url": "https://newsapi.org/v2/everything",
            "query_params": {"q": "stocks", "language": "en"}
        }

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [{
                "source": {"id": "test-source", "name": "Test Source"},
                "author": "John Doe",
                "title": "Test Article",
                "url": "http://test.com/article",
                "description": "A test article.",
                "content": "Full content.",
                "publishedAt": "2023-01-01T12:00:00Z"
            }]
        }
        mock_requests_get.return_value = mock_response

        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Run the function
        fetch_and_store_news()

        # Assertions
        mock_requests_get.assert_called_once_with(
            "https://newsapi.org/v2/everything",
            params={
                "apiKey": "test-api-key",
                "q": "stocks",
                "language": "en"
            }
        )
        self.assertTrue(mock_cursor.execute.called)
        self.assertTrue(mock_conn.commit.called)

    @patch('collectors.news_collector.get_db_connection')
    @patch('collectors.news_collector.requests.get')
    @patch('collectors.news_collector.settings')
    def test_news_collector_no_articles(self, mock_settings, mock_requests_get, mock_db_conn):
        """Test news collector when no articles are returned."""
        # Mock settings
        mock_settings.news_api_key = "test-api-key"
        mock_settings.news_api = {
            "base_url": "https://newsapi.org/v2/everything",
            "query_params": {"q": "stocks", "language": "en"}
        }

        # Mock API response with no articles
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"articles": []}
        mock_requests_get.return_value = mock_response

        # Run the function
        fetch_and_store_news()

        # Should not interact with database when no articles
        mock_db_conn.assert_not_called()

    @patch('collectors.news_collector.requests.get')
    @patch('collectors.news_collector.settings')
    def test_news_collector_api_error(self, mock_settings, mock_requests_get):
        """Test news collector when API returns an error."""
        # Mock settings
        mock_settings.news_api_key = "test-api-key"
        mock_settings.news_api = {
            "base_url": "https://newsapi.org/v2/everything",
            "query_params": {"q": "stocks", "language": "en"}
        }

        # Mock API error
        mock_requests_get.side_effect = Exception("API Error")

        # Run the function - should not raise exception
        try:
            fetch_and_store_news()
        except Exception:
            self.fail("fetch_and_store_news() raised an exception unexpectedly!")

    @patch('collectors.news_collector.get_db_connection')
    @patch('collectors.news_collector.requests.get')
    @patch('collectors.news_collector.settings')
    def test_news_collector_database_error(self, mock_settings, mock_requests_get, mock_db_conn):
        """Test news collector when database operations fail."""
        # Mock settings
        mock_settings.news_api_key = "test-api-key"
        mock_settings.news_api = {
            "base_url": "https://newsapi.org/v2/everything",
            "query_params": {"q": "stocks", "language": "en"}
        }

        # Mock API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "articles": [{
                "source": {"id": "test-source", "name": "Test Source"},
                "author": "John Doe",
                "title": "Test Article",
                "url": "http://test.com/article",
                "description": "A test article.",
                "content": "Full content.",
                "publishedAt": "2023-01-01T12:00:00Z"
            }]
        }
        mock_requests_get.return_value = mock_response

        # Mock database error
        mock_db_conn.side_effect = Exception("Database Error")

        # Run the function - should not raise exception
        try:
            fetch_and_store_news()
        except Exception:
            self.fail("fetch_and_store_news() raised an exception unexpectedly!")


class TestMarketDataCollector(unittest.TestCase):
    """Test cases for the market data collector functionality."""

    @patch('collectors.market_data_collector.get_db_connection')
    @patch('collectors.market_data_collector.yf.download')
    @patch('collectors.market_data_collector.settings')
    def test_market_data_collector_success(self, mock_settings, mock_yf_download, mock_db_conn):
        """Test successful market data collection and storage."""
        # Mock settings
        mock_settings.market_data = {
            "tickers": ["AAPL", "GOOGL"],
            "period": "1mo"
        }

        # Mock yfinance response
        test_data = {
            'Open': [150.0, 151.0], 
            'High': [152.0, 153.0], 
            'Low': [149.0, 150.0], 
            'Close': [151.0, 152.0], 
            'Volume': [1000000, 1100000]
        }
        test_df = pd.DataFrame(test_data, index=pd.to_datetime(['2023-01-01', '2023-01-02']))
        
        # Create multi-level DataFrame for multiple tickers
        multi_df = pd.concat([test_df, test_df], axis=1, keys=['AAPL', 'GOOGL'])
        mock_yf_download.return_value = multi_df

        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Run the function
        fetch_and_store_market_data()

        # Assertions
        mock_yf_download.assert_called_once_with(["AAPL", "GOOGL"], period="1mo", group_by='ticker')
        self.assertTrue(mock_cursor.execute.called)
        self.assertTrue(mock_conn.commit.called)

    @patch('collectors.market_data_collector.get_db_connection')
    @patch('collectors.market_data_collector.yf.download')
    @patch('collectors.market_data_collector.settings')
    def test_market_data_collector_single_ticker(self, mock_settings, mock_yf_download, mock_db_conn):
        """Test market data collector with single ticker."""
        # Mock settings
        mock_settings.market_data = {
            "tickers": ["AAPL"],
            "period": "1mo"
        }

        # Mock yfinance response for single ticker
        test_data = {
            'Open': [150.0], 
            'High': [152.0], 
            'Low': [149.0], 
            'Close': [151.0], 
            'Volume': [1000000]
        }
        test_df = pd.DataFrame(test_data, index=pd.to_datetime(['2023-01-01']))
        mock_yf_download.return_value = test_df

        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # Run the function
        fetch_and_store_market_data()

        # Assertions
        mock_yf_download.assert_called_once_with(["AAPL"], period="1mo", group_by='ticker')
        self.assertTrue(mock_cursor.execute.called)

    @patch('collectors.market_data_collector.settings')
    def test_market_data_collector_no_tickers(self, mock_settings):
        """Test market data collector when no tickers are defined."""
        # Mock settings with no tickers
        mock_settings.market_data = {
            "tickers": [],
            "period": "1mo"
        }

        # Run the function
        fetch_and_store_market_data()

        # Should not call yfinance or database when no tickers

    @patch('collectors.market_data_collector.yf.download')
    @patch('collectors.market_data_collector.settings')
    def test_market_data_collector_empty_data(self, mock_settings, mock_yf_download):
        """Test market data collector when yfinance returns empty data."""
        # Mock settings
        mock_settings.market_data = {
            "tickers": ["AAPL"],
            "period": "1mo"
        }

        # Mock empty yfinance response
        mock_yf_download.return_value = pd.DataFrame()

        # Run the function
        fetch_and_store_market_data()

        # Should not interact with database when data is empty

    @patch('collectors.market_data_collector.yf.download')
    @patch('collectors.market_data_collector.settings')
    def test_market_data_collector_yfinance_error(self, mock_settings, mock_yf_download):
        """Test market data collector when yfinance fails."""
        # Mock settings
        mock_settings.market_data = {
            "tickers": ["AAPL"],
            "period": "1mo"
        }

        # Mock yfinance error
        mock_yf_download.side_effect = Exception("yfinance Error")

        # Run the function - should not raise exception
        try:
            fetch_and_store_market_data()
        except Exception:
            self.fail("fetch_and_store_market_data() raised an exception unexpectedly!")

    @patch('collectors.market_data_collector.get_db_connection')
    @patch('collectors.market_data_collector.yf.download')
    @patch('collectors.market_data_collector.settings')
    def test_market_data_collector_database_error(self, mock_settings, mock_yf_download, mock_db_conn):
        """Test market data collector when database operations fail."""
        # Mock settings
        mock_settings.market_data = {
            "tickers": ["AAPL"],
            "period": "1mo"
        }

        # Mock yfinance response
        test_data = {
            'Open': [150.0], 
            'High': [152.0], 
            'Low': [149.0], 
            'Close': [151.0], 
            'Volume': [1000000]
        }
        test_df = pd.DataFrame(test_data, index=pd.to_datetime(['2023-01-01']))
        mock_yf_download.return_value = test_df

        # Mock database error
        mock_db_conn.side_effect = Exception("Database Error")

        # Run the function - should not raise exception
        try:
            fetch_and_store_market_data()
        except Exception:
            self.fail("fetch_and_store_market_data() raised an exception unexpectedly!")


if __name__ == '__main__':
    unittest.main()
