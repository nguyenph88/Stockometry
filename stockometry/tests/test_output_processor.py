# tests/test_output_processor.py
import unittest
import os
import json
from unittest.mock import patch, MagicMock, mock_open

# We need to patch the DB connection BEFORE importing the class
@patch('src.output.processor.get_db_connection')
class TestOutputProcessor(unittest.TestCase):

    # The mock_db_conn is passed from the class-level patch
    def test_full_processing(self, mock_db_conn):
        """
        Tests the entire process: parsing, DB saving, and JSON writing.
        """
        from src.output.processor import OutputProcessor
        
        # 1. Setup
        # A sample report string that mimics the real output
        sample_report = """
--- Synthesized Market Report ---
## Historical Trend Analysis ##
[Bullish Signal] Sector 'Technology' shows strong positive sentiment...
## Today's High-Impact Analysis ##
[Impact Alert] Sector 'Technology' predicted to go UP. Reason: News about AI.
## High-Confidence Signals (Confluence) ##
[HIGH CONFIDENCE BULLISH] Sector 'Technology' shows a positive trend...
    -> Predicted top stock movers in 'Technology':
        - MSFT: Strong positive news: 'AI Deal' (Score: 0.98)
"""
        # Mock the database to return a fake report_id
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [1] # Fake report_id = 1
        mock_db_conn.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        # 2. Action
        # Use mock_open to simulate writing to a file without actually touching the disk
        with patch("builtins.open", mock_open()) as mock_file:
            processor = OutputProcessor(sample_report)
            processor.process_and_save()

        # 3. Assertions
        # Assert parsing was correct
        parsed_data = processor._parse_report()
        self.assertEqual(len(parsed_data['confidence_signals']), 1)
        self.assertEqual(parsed_data['confidence_signals'][0]['sector'], 'Technology')
        self.assertEqual(len(parsed_data['confidence_signals'][0]['predicted_stocks']), 1)
        self.assertEqual(parsed_data['confidence_signals'][0]['predicted_stocks'][0]['symbol'], 'MSFT')

        # Assert database was called correctly
        self.assertTrue(mock_cursor.execute.called)
        # Check that it tried to insert a 'CONFIDENCE' signal
        execute_calls = [call[0][0] for call in mock_cursor.execute.call_args_list]
        self.assertTrue(any("INSERT INTO report_signals" in call and "'CONFIDENCE'" in call for call in execute_calls))
        
        # Assert JSON file was written to
        mock_file.assert_called_once_with(os.path.join("output", f"report_{processor.report_date}.json"), 'w')
        # To check content, you'd need a more complex mock, but this confirms it was called.

if __name__ == '__main__':
    unittest.main()
