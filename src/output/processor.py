# src/output/processor.py
import json
import os
import re
from datetime import datetime
from src.database import get_db_connection

class OutputProcessor:
    """
    Handles processing the final report into structured formats (DB and JSON).
    """
    def __init__(self, report_string: str):
        self.report_string = report_string
        self.report_date = datetime.utcnow().date()
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)

    def process_and_save(self):
        """
        Main method to run all processing and saving steps.
        """
        print("Processing and saving the final report...")
        parsed_data = self._parse_report()
        report_id = self._save_to_db(parsed_data)
        self._save_to_json(parsed_data, report_id)
        print("Report processing and saving complete.")

    def _parse_report(self):
        """
        Parses the raw report string into a structured dictionary.
        """
        data = {
            "historical_signals": [],
            "impact_signals": [],
            "confidence_signals": []
        }
        # Regex to capture signal type, sector, and details
        historical_pattern = re.compile(r"\[(Bullish|Bearish) Signal\] Sector '([^']+)'.*")
        impact_pattern = re.compile(r"\[Impact Alert\] Sector '([^']+)'.*predicted to go (\w+)\..*Reason: (.*)")
        confidence_pattern = re.
