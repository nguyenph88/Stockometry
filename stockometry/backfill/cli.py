"""
CLI Interface for Missing Reports Check

This module provides a simple menu-based interface for checking missing daily reports.
"""

import sys
import logging
from datetime import datetime, date
from typing import Optional

from .backfill_manager import BackfillManager
from .config import BackfillConfig, DEFAULT_BACKFILL_CONFIG

def setup_logging():
    """Setup basic logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def check_missing_reports(manager: BackfillManager):
    """Check for missing reports"""
    print("\n🔍 Checking for missing reports...")
    
    try:
        analysis = manager.check_missing_reports()
        
        print(f"\n📊 Check Results:")
        print(f"  Days checked: {analysis.total_days_checked}")
        print(f"  Reports expected: {analysis.total_reports_expected}")
        print(f"  Reports found: {analysis.total_reports_found}")
        print(f"  Coverage: {analysis.coverage_percentage:.1f}%")
        
        if analysis.missing_reports:
            print(f"\n❌ Missing Reports ({len(analysis.missing_reports)}):")
            print("┌────────────┬──────────┬─────────────────┐")
            print("│    Date    │   Time   │   Report Type   │")
            print("├────────────┼──────────┼─────────────────┤")
            
            # Group reports by date
            reports_by_date = {}
            for missing in analysis.missing_reports:
                date_str = missing.date.strftime("%Y-%m-%d")
                if date_str not in reports_by_date:
                    reports_by_date[date_str] = []
                reports_by_date[date_str].append(missing)
            
            # Print reports with separators only between dates
            date_keys = list(reports_by_date.keys())
            for i, date_str in enumerate(date_keys):
                date_reports = reports_by_date[date_str]
                for j, missing in enumerate(date_reports):
                    time_str = missing.expected_time.strftime("%H:%M")
                    type_str = missing.report_type.ljust(15)
                    print(f"│ {date_str} │  {time_str}   │ {type_str} │")
                
                # Add separator line between different dates (except after last date)
                if i < len(date_keys) - 1:
                    print("├────────────┼──────────┼─────────────────┤")
            
            print("└────────────┴──────────┴─────────────────┘")
        else:
            print("\n✅ All reports are present!")
            
    except Exception as e:
        print(f"❌ Error during check: {str(e)}")

def show_status(manager: BackfillManager):
    """Show system status"""
    print("\n📊 System Status:")
    
    try:
        status = manager.get_status()
        
        print(f"  Status: {status['status']}")
        print(f"  Daily reports: {status['capabilities']['daily_report_count']}")
        print(f"  Lookback days: {status['capabilities']['lookback_days']}")
        
        print(f"\n🗄️  Database:")
        print(f"  Environment: {status['database']['environment']}")
        print(f"  Active Database: {status['database']['active_database']}")
        print(f"  Host: {status['database']['host']}:{status['database']['port']}")
        
        print(f"\n📅 Current Schedule:")
        config = status['config']
        for i, time_str in enumerate(config['daily_report_times']):
            print(f"  {i+1}. {time_str}")
            
    except Exception as e:
        print(f"❌ Error getting status: {str(e)}")

def show_menu():
    """Display the main menu"""
    print("\n" + "="*50)
    print("📊 STOCKOMETRY MISSING REPORTS CHECK")
    print("="*50)
    print("1. Check Missing Reports")
    print("2. Show System Status")
    print("3. Exit")
    print("-"*50)

def main():
    """Main menu loop"""
    setup_logging()
    
    # Create manager with default config
    manager = BackfillManager()
    
    # Show database environment info at startup
    try:
        status = manager.get_status()
        print(f"\n🗄️  Connected to: {status['database']['environment'].upper()} environment")
        print(f"   Database: {status['database']['active_database']}")
        print(f"   Host: {status['database']['host']}:{status['database']['port']}")
    except Exception as e:
        print(f"⚠️  Warning: Could not verify database connection: {str(e)}")
    
    while True:
        show_menu()
        
        try:
            choice = input("Select an option (1-3): ").strip()
            
            if choice == '1':
                check_missing_reports(manager)
            elif choice == '2':
                show_status(manager)
            elif choice == '3':
                print("\n👋 Goodbye!")
                break
            else:
                print("❌ Please select a valid option (1-3)")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
        
        # Wait for user to continue
        input("\nPress Enter to continue...")

if __name__ == '__main__':
    main()
