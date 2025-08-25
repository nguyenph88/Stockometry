#!/usr/bin/env python3
"""Execute the SQL schema fix for daily_reports table"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'stockometry'))

from stockometry.database import get_db_connection

def fix_schema():
    """Fix the daily_reports table schema"""
    
    try:
        # Read the SQL file
        with open('fix_daily_reports_schema.sql', 'r') as f:
            sql_commands = f.read()
        
        print("🔧 Fixing daily_reports table schema...")
        print("="*60)
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Execute the SQL commands
            print("📝 Executing schema changes...")
            cursor.execute(sql_commands)
            
            # Commit the changes
            conn.commit()
            print("✅ Schema updated successfully!")
            
            # Verify the new schema
            print("\n🔍 Verifying new schema...")
            cursor.execute("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'daily_reports' 
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print("📊 New table structure:")
            for col in columns:
                col_name, data_type, nullable = col
                print(f"  {col_name}: {data_type} (nullable: {nullable})")
            
            # Check constraints
            cursor.execute("""
                SELECT constraint_name, constraint_type
                FROM information_schema.table_constraints 
                WHERE table_name = 'daily_reports';
            """)
            
            constraints = cursor.fetchall()
            print("\n🔒 Table constraints:")
            for constraint in constraints:
                name, constraint_type = constraint
                print(f"  {name}: {constraint_type}")
            
            cursor.close()
            
        print("\n🎉 Schema fix completed successfully!")
        print("📝 The table now supports multiple reports per day!")
        
    except Exception as e:
        print(f"❌ Schema fix failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = fix_schema()
    
    if success:
        print("\n🚀 Ready to test the backfill system again!")
    else:
        print("\n⚠️ Schema fix failed. Check the logs above.")
