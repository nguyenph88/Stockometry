# src/output/processor.py
import json
import os
from datetime import datetime
from src.database import get_db_connection

class OutputProcessor:
    def __init__(self, report_object: dict):
        self.report_object = report_object
        self.report_date = datetime.utcnow().date()
        self.output_dir = "output"
        os.makedirs(self.output_dir, exist_ok=True)
        self._init_db_tables()

    def _init_db_tables(self):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS daily_reports (id SERIAL PRIMARY KEY, report_date DATE UNIQUE NOT NULL, summary TEXT, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP);")
            cursor.execute("CREATE TABLE IF NOT EXISTS report_signals (id SERIAL PRIMARY KEY, report_id INTEGER REFERENCES daily_reports(id) ON DELETE CASCADE, signal_type VARCHAR(50) NOT NULL, sector VARCHAR(255), direction VARCHAR(50), details TEXT, stock_symbol VARCHAR(20));")
            # New table to store source articles for each signal
            cursor.execute("CREATE TABLE IF NOT EXISTS signal_sources (id SERIAL PRIMARY KEY, signal_id INTEGER REFERENCES report_signals(id) ON DELETE CASCADE, title TEXT, url TEXT UNIQUE);")
            conn.commit()

    def process_and_save(self):
        print("Processing and saving the final report...")
        report_id = self._save_to_db()
        if report_id:
            self._save_to_json(report_id)
            print("Report processing and saving complete.")

    def _save_to_db(self):
        summary = self.report_object['executive_summary']
        signals = self.report_object['signals']
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO daily_reports (report_date, summary) VALUES (%s, %s) ON CONFLICT (report_date) DO UPDATE SET summary = EXCLUDED.summary RETURNING id;", (self.report_date, summary))
                report_id = cursor.fetchone()[0]
                cursor.execute("DELETE FROM report_signals WHERE report_id = %s;", (report_id,))

                all_signals = signals['historical'] + signals['impact'] + signals['confidence']
                for signal in all_signals:
                    cursor.execute(
                        "INSERT INTO report_signals (report_id, signal_type, sector, direction, details) VALUES (%s, %s, %s, %s, %s) RETURNING id;",
                        (report_id, signal['type'], signal['sector'], signal['direction'], signal.get('details'))
                    )
                    signal_id = cursor.fetchone()[0]
                    # Save source articles
                    for source in signal.get('source_articles', []):
                        cursor.execute("INSERT INTO signal_sources (signal_id, title, url) VALUES (%s, %s, %s) ON CONFLICT (url) DO NOTHING;", (signal_id, source['title'], source['url']))
                    # Save predicted stocks
                    for stock in signal.get('predicted_stocks', []):
                        cursor.execute(
                            "INSERT INTO report_signals (report_id, signal_type, sector, stock_symbol, details) VALUES (%s, %s, %s, %s, %s);",
                            (report_id, 'STOCK_PREDICTION', signal['sector'], stock['symbol'], f"{stock['reason']} (Score: {stock['score']})")
                        )
                conn.commit()
            return report_id
        except Exception as e:
            print(f"Error saving report to DB: {e}")
            return None

    def _save_to_json(self, report_id):
        file_path = os.path.join(self.output_dir, f"report_{self.report_date}.json")
        output_data = {
            "report_id": report_id,
            "report_date": str(self.report_date),
            "generated_at_utc": datetime.utcnow().isoformat(),
            **self.report_object
        }
        with open(file_path, 'w') as f:
            json.dump(output_data, f, indent=4)
        print(f"Report saved to {file_path}")
