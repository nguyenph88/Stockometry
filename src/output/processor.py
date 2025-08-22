# src/output/processor.py
import json
import os
from datetime import datetime, timezone
from src.database import get_db_connection

class OutputProcessor:
    def __init__(self, report_object: dict, run_source: str = "SCHEDULED"):
        """
        Initialize the OutputProcessor with a report object and run source.
        
        Args:
            report_object (dict): The analysis report to process
            run_source (str): Source of the run - "ONDEMAND" or "SCHEDULED"
        """
        self.report_object = report_object
        self.report_date = datetime.now(timezone.utc).date()
        self.run_source = run_source.upper()  # Normalize to uppercase
        self._init_db_tables()

    def _init_db_tables(self):
        """Initialize database tables - now handled by init_db()"""
        # Tables are created by init_db() function
        # This method is kept for backward compatibility but does nothing
        pass

    def process_and_save(self):
        print(f"Processing and saving the final report (Source: {self.run_source})...")
        report_id = self._save_to_db()
        if report_id:
            print(f"Report processing and saving complete. Run source: {self.run_source}")
            return report_id
        return None

    def _save_to_db(self):
        executive_summary = self.report_object['executive_summary']
        signals = self.report_object['signals']
        generated_at = datetime.now(timezone.utc)
        
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if report already exists for this date
                cursor.execute("SELECT id FROM daily_reports WHERE report_date = %s;", (self.report_date,))
                existing_report = cursor.fetchone()
                
                if existing_report:
                    # Update existing report
                    cursor.execute("""
                        UPDATE daily_reports 
                        SET executive_summary = %s, run_source = %s, generated_at_utc = %s
                        WHERE report_date = %s
                        RETURNING id;
                    """, (executive_summary, self.run_source, generated_at, self.report_date))
                    report_id = cursor.fetchone()[0]
                else:
                    # Insert new report
                    cursor.execute("""
                        INSERT INTO daily_reports (report_date, executive_summary, run_source, generated_at_utc) 
                        VALUES (%s, %s, %s, %s) 
                        RETURNING id;
                    """, (self.report_date, executive_summary, self.run_source, generated_at))
                    report_id = cursor.fetchone()[0]
                
                # Clear existing signals for this report
                cursor.execute("DELETE FROM report_signals WHERE report_id = %s;", (report_id,))

                # Process all signal types
                all_signals = signals['historical'] + signals['impact'] + signals['confidence']
                
                for signal in all_signals:
                    # Insert signal
                    cursor.execute("""
                        INSERT INTO report_signals (report_id, signal_type, sector, direction, details) 
                        VALUES (%s, %s, %s, %s, %s) 
                        RETURNING id;
                    """, (report_id, signal['type'], signal['sector'], signal['direction'], signal.get('details')))
                    
                    signal_id = cursor.fetchone()[0]
                    
                    # Save source articles
                    for source in signal.get('source_articles', []):
                        cursor.execute("""
                            INSERT INTO signal_sources (signal_id, title, url) 
                            VALUES (%s, %s, %s) 
                            ON CONFLICT (signal_id, url) DO NOTHING;
                        """, (signal_id, source['title'], source['url']))
                    
                    # Save predicted stocks for confidence signals
                    for stock in signal.get('predicted_stocks', []):
                        cursor.execute("""
                            INSERT INTO predicted_stocks (signal_id, symbol, reason, url, score) 
                            VALUES (%s, %s, %s, %s, %s);
                        """, (signal_id, stock['symbol'], stock['reason'], stock.get('url'), stock.get('score')))
                
                conn.commit()
                return report_id
                
        except Exception as e:
            print(f"Error saving report to DB: {e}")
            return None

    def export_to_json(self, report_id: int = None, report_date: str = None):
        """
        Export report data to JSON format on demand.
        
        Args:
            report_id: Specific report ID to export
            report_date: Date string (YYYY-MM-DD) to export
            
        Returns:
            dict: Complete report data in JSON format
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                if report_id:
                    # Export specific report by ID
                    cursor.execute("""
                        SELECT id, report_date, executive_summary, run_source, generated_at_utc
                        FROM daily_reports WHERE id = %s
                    """, (report_id,))
                elif report_date:
                    # Export report by date
                    cursor.execute("""
                        SELECT id, report_date, executive_summary, run_source, generated_at_utc
                        FROM daily_reports WHERE report_date = %s
                    """, (report_date,))
                else:
                    # Export latest report
                    cursor.execute("""
                        SELECT id, report_date, executive_summary, run_source, generated_at_utc
                        FROM daily_reports ORDER BY generated_at_utc DESC LIMIT 1
                    """)
                
                report_row = cursor.fetchone()
                if not report_row:
                    return None
                
                report_id, report_date, executive_summary, run_source, generated_at_utc = report_row
                
                # Get all signals for this report
                cursor.execute("""
                    SELECT id, signal_type, sector, direction, details
                    FROM report_signals WHERE report_id = %s
                    ORDER BY signal_type, sector
                """, (report_id,))
                
                signals_data = {'historical': [], 'impact': [], 'confidence': []}
                
                for signal_row in cursor.fetchall():
                    signal_id, signal_type, sector, direction, details = signal_row
                    
                    # Get source articles for this signal
                    cursor.execute("""
                        SELECT title, url FROM signal_sources 
                        WHERE signal_id = %s ORDER BY title
                    """, (signal_id,))
                    source_articles = [{'title': title, 'url': url} for title, url in cursor.fetchall()]
                    
                    # Get predicted stocks for confidence signals
                    predicted_stocks = []
                    if signal_type == 'CONFIDENCE':
                        cursor.execute("""
                            SELECT symbol, reason, url, score FROM predicted_stocks 
                            WHERE signal_id = %s ORDER BY score DESC
                        """, (signal_id,))
                        predicted_stocks = [{'symbol': symbol, 'reason': reason, 'url': url, 'score': float(score) if score else None} 
                                         for symbol, reason, url, score in cursor.fetchall()]
                    
                    # Build signal object
                    signal_obj = {
                        'type': signal_type,
                        'sector': sector,
                        'direction': direction,
                        'source_articles': source_articles
                    }
                    
                    if details:
                        signal_obj['details'] = details
                    
                    if predicted_stocks:
                        signal_obj['predicted_stocks'] = predicted_stocks
                    
                    # Categorize by signal type
                    if signal_type == 'HISTORICAL':
                        signals_data['historical'].append(signal_obj)
                    elif signal_type == 'IMPACT':
                        signals_data['impact'].append(signal_obj)
                    elif signal_type == 'CONFIDENCE':
                        signals_data['confidence'].append(signal_obj)
                
                # Build complete report
                report_data = {
                    'report_id': report_id,
                    'report_date': str(report_date),
                    'generated_at_utc': generated_at_utc.isoformat(),
                    'run_source': run_source,
                    'executive_summary': executive_summary,
                    'signals': signals_data
                }
                
                return report_data
                
        except Exception as e:
            print(f"Error exporting report to JSON: {e}")
            return None

    def save_json_to_file(self, report_data: dict, output_dir: str = "exports"):
        """
        Save exported JSON data to a file (optional, for backup/download purposes).
        
        Args:
            report_data: Report data from export_to_json
            output_dir: Directory to save the file
            
        Returns:
            str: Path to saved file, or None if failed
        """
        if not report_data:
            return None
            
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            report_date = report_data['report_date']
            run_source = report_data['run_source'].lower()
            timestamp = datetime.now(timezone.utc).strftime("%H%M%S")
            
            filename = f"report_{report_date}_{timestamp}_{run_source}.json"
            file_path = os.path.join(output_dir, filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)
            
            print(f"JSON export saved to: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"Error saving JSON to file: {e}")
            return None
