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
        self._init_db_tables()

    def _init_db_tables(self):
        """Ensures the necessary tables for storing reports exist."""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS daily_reports (
                            id SERIAL PRIMARY KEY,
                            report_date DATE UNIQUE NOT NULL,
                            summary TEXT,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                        );
                    """)
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS report_signals (
                            id SERIAL PRIMARY KEY,
                            report_id INTEGER REFERENCES daily_reports(id) ON DELETE CASCADE,
                            signal_type VARCHAR(50) NOT NULL, -- 'HISTORICAL', 'IMPACT', 'CONFIDENCE'
                            sector VARCHAR(255),
                            direction VARCHAR(50), -- 'Bullish', 'Bearish', 'UP', 'DOWN'
                            details TEXT,
                            stock_symbol VARCHAR(20)
                        );
                    """)
                conn.commit()
        except Exception as e:
            print(f"Error initializing output DB tables: {e}")
            raise

    def process_and_save(self):
        """Main method to run all processing and saving steps."""
        print("Processing and saving the final report...")
        parsed_data = self._parse_report()
        if not parsed_data:
            print("Parsing failed. Aborting save.")
            return
        report_id = self._save_to_db(parsed_data)
        if report_id:
            self._save_to_json(parsed_data, report_id)
            print("Report processing and saving complete.")
        else:
            print("Failed to save report to database.")

    def _parse_report(self):
        """Parses the raw report string into a structured dictionary."""
        data = {
            "historical_signals": [], "impact_signals": [], "confidence_signals": []
        }
        # Regex patterns to capture signals
        historical_pattern = re.compile(r"\[(Bullish|Bearish) Signal\] Sector '([^']+)'.*")
        impact_pattern = re.compile(r"\[Impact Alert\] Sector '([^']+)'.*predicted to go (\w+)\..*Reason: (.*)")
        confidence_pattern = re.compile(r"\[HIGH CONFIDENCE (\w+)\] Sector '([^']+)'.*")
        stock_pattern = re.compile(r"-\s(\w+): Strong positive news: '(.*)' \(Score: (.*)\)")

        for line in self.report_string.split('\n'):
            hist_match = historical_pattern.match(line)
            if hist_match:
                data["historical_signals"].append({"direction": hist_match.group(1), "sector": hist_match.group(2)})
                continue

            impact_match = impact_pattern.match(line)
            if impact_match:
                data["impact_signals"].append({"sector": impact_match.group(1), "direction": impact_match.group(2), "details": impact_match.group(3).strip()})
                continue
            
            conf_match = confidence_pattern.match(line)
            if conf_match:
                signal = {"direction": conf_match.group(1), "sector": conf_match.group(2), "predicted_stocks": []}
                data["confidence_signals"].append(signal)
                continue

            stock_match = stock_pattern.search(line)
            if stock_match and data["confidence_signals"]:
                # Attach the stock prediction to the last confidence signal
                data["confidence_signals"][-1]["predicted_stocks"].append({
                    "symbol": stock_match.group(1), "reason": stock_match.group(2), "score": float(stock_match.group(3))
                })
        return data

    def _save_to_db(self, parsed_data):
        """Saves the parsed data into the database tables."""
        summary = f"Generated {len(parsed_data['confidence_signals'])} high-confidence signals."
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    # Insert the main report record
                    cursor.execute(
                        "INSERT INTO daily_reports (report_date, summary) VALUES (%s, %s) ON CONFLICT (report_date) DO UPDATE SET summary = EXCLUDED.summary RETURNING id;",
                        (self.report_date, summary)
                    )
                    report_id = cursor.fetchone()[0]

                    # Clear old signals for this report to prevent duplicates
                    cursor.execute("DELETE FROM report_signals WHERE report_id = %s;", (report_id,))

                    # Insert all signals
                    for signal in parsed_data['historical_signals']:
                        cursor.execute("INSERT INTO report_signals (report_id, signal_type, sector, direction) VALUES (%s, %s, %s, %s);",
                                       (report_id, 'HISTORICAL', signal['sector'], signal['direction']))
                    for signal in parsed_data['impact_signals']:
                        cursor.execute("INSERT INTO report_signals (report_id, signal_type, sector, direction, details) VALUES (%s, %s, %s, %s, %s);",
                                       (report_id, 'IMPACT', signal['sector'], signal['direction'], signal['details']))
                    for signal in parsed_data['confidence_signals']:
                        cursor.execute("INSERT INTO report_signals (report_id, signal_type, sector, direction) VALUES (%s, %s, %s, %s);",
                                       (report_id, 'CONFIDENCE', signal['sector'], signal['direction']))
                        for stock in signal['predicted_stocks']:
                             cursor.execute("INSERT INTO report_signals (report_id, signal_type, sector, stock_symbol, details) VALUES (%s, %s, %s, %s, %s);",
                                       (report_id, 'STOCK_PREDICTION', signal['sector'], stock['symbol'], stock['reason']))
                conn.commit()
            return report_id
        except Exception as e:
            print(f"Error saving report to DB: {e}")
            return None

    def _save_to_json(self, parsed_data, report_id):
        """Saves the parsed data as a JSON file."""
        file_path = os.path.join(self.output_dir, f"report_{self.report_date}.json")
        output_data = {
            "report_id": report_id,
            "report_date": str(self.report_date),
            "generated_at_utc": datetime.utcnow().isoformat(),
            "signals": parsed_data
        }
        with open(file_path, 'w') as f:
            json.dump(output_data, f, indent=4)
        print(f"Report saved to {file_path}")
