#!/usr/bin/env python3
"""
Export utility for Stockometry reports.
This script allows you to export reports from the database to JSON format on demand.
"""

import sys
import os
from datetime import datetime, timedelta
from src.output.processor import OutputProcessor

def export_latest_report():
    """Export the most recent report to JSON"""
    print("Exporting latest report...")
    
    processor = OutputProcessor({})  # Empty object for export only
    json_data = processor.export_to_json()
    
    if json_data:
        print(f"Latest report found: {json_data['report_date']} (ID: {json_data['report_id']})")
        
        # Save to exports directory
        file_path = processor.save_json_to_file(json_data, "exports")
        if file_path:
            print(f"Report exported to: {file_path}")
            return True
        else:
            print("Failed to save report to file")
            return False
    else:
        print("No reports found in database")
        return False

def export_report_by_date(date_str):
    """Export a specific report by date (YYYY-MM-DD)"""
    try:
        # Validate date format
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD")
        return False
    
    print(f"Exporting report for date: {date_str}")
    
    processor = OutputProcessor({})  # Empty object for export only
    json_data = processor.export_to_json(report_date=date_str)
    
    if json_data:
        print(f"Report found: {json_data['report_date']} (ID: {json_data['report_id']})")
        
        # Save to exports directory
        file_path = processor.save_json_to_file(json_data, "exports")
        if file_path:
            print(f"Report exported to: {file_path}")
            return True
        else:
            print("Failed to save report to file")
            return False
    else:
        print(f"No report found for date: {date_str}")
        return False

def export_report_by_id(report_id):
    """Export a specific report by ID"""
    try:
        report_id = int(report_id)
    except ValueError:
        print("Invalid report ID. Must be a number.")
        return False
    
    print(f"Exporting report with ID: {report_id}")
    
    processor = OutputProcessor({})  # Empty object for export only
    json_data = processor.export_to_json(report_id=report_id)
    
    if json_data:
        print(f"Report found: {json_data['report_date']} (ID: {json_data['report_id']})")
        
        # Save to exports directory
        file_path = processor.save_json_to_file(json_data, "exports")
        if file_path:
            print(f"Report exported to: {file_path}")
            return True
        else:
            print("Failed to save report to file")
            return False
    else:
        print(f"No report found with ID: {report_id}")
        return False

def list_available_reports():
    """List all available reports in the database"""
    print("Available reports in database:")
    print("-" * 50)
    
    try:
        from src.database import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, report_date, run_source, generated_at_utc, 
                       LENGTH(executive_summary) as summary_length
                FROM daily_reports 
                ORDER BY generated_at_utc DESC 
                LIMIT 20
            """)
            
            reports = cursor.fetchall()
            
            if not reports:
                print("No reports found in database")
                return
            
            print(f"{'ID':<5} {'Date':<12} {'Source':<12} {'Generated':<20} {'Summary':<10}")
            print("-" * 70)
            
            for report_id, report_date, run_source, generated_at, summary_length in reports:
                generated_str = generated_at.strftime("%Y-%m-%d %H:%M:%S")
                print(f"{report_id:<5} {report_date:<12} {run_source:<12} {generated_str:<20} {summary_length:<10}")
                
    except Exception as e:
        print(f"Error listing reports: {e}")

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("Stockometry Report Export Utility")
        print("=" * 40)
        print("Usage:")
        print("  python export_reports.py latest                    # Export latest report")
        print("  python export_reports.py date YYYY-MM-DD          # Export report by date")
        print("  python export_reports.py id <report_id>           # Export report by ID")
        print("  python export_reports.py list                     # List available reports")
        print("  python export_reports.py help                     # Show this help")
        return
    
    command = sys.argv[1].lower()
    
    if command == "latest":
        export_latest_report()
    
    elif command == "date" and len(sys.argv) > 2:
        export_report_by_date(sys.argv[2])
    
    elif command == "id" and len(sys.argv) > 2:
        export_report_by_id(sys.argv[2])
    
    elif command == "list":
        list_available_reports()
    
    elif command == "help":
        print("Stockometry Report Export Utility")
        print("=" * 40)
        print("Usage:")
        print("  python export_reports.py latest                    # Export latest report")
        print("  python export_reports.py date YYYY-MM-DD          # Export report by date")
        print("  python export_reports.py id <report_id>           # Export report by ID")
        print("  python export_reports.py list                     # List available reports")
        print("  python export_reports.py help                     # Show this help")
    
    else:
        print("Invalid command. Use 'python export_reports.py help' for usage information.")

if __name__ == "__main__":
    main()
