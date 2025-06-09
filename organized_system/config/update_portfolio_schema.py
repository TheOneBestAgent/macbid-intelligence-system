#!/usr/bin/env python3
"""
🔧 Update Portfolio Database Schema
Add source column to support real data integration
"""

import sqlite3
import os

def update_portfolio_schema():
    """Update the portfolio database schema."""
    db_file = "portfolio_tracker.db"
    
    print("🔧 UPDATING PORTFOLIO DATABASE SCHEMA")
    print("=" * 50)
    
    if not os.path.exists(db_file):
        print("❌ Portfolio database not found!")
        return False
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    try:
        # Check if source column exists
        cursor.execute("PRAGMA table_info(bids)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Current columns: {columns}")
        
        if 'source' not in columns:
            print("➕ Adding 'source' column...")
            cursor.execute("ALTER TABLE bids ADD COLUMN source TEXT DEFAULT 'manual_entry'")
            print("✅ Source column added successfully!")
        else:
            print("✅ Source column already exists!")
        
        # Update existing records to have 'manual_entry' source
        cursor.execute("UPDATE bids SET source = 'manual_entry' WHERE source IS NULL")
        updated_rows = cursor.rowcount
        
        if updated_rows > 0:
            print(f"✅ Updated {updated_rows} existing records with 'manual_entry' source")
        
        conn.commit()
        
        # Show current data summary
        cursor.execute("SELECT COUNT(*), source FROM bids GROUP BY source")
        results = cursor.fetchall()
        
        print(f"\n📊 CURRENT DATA SUMMARY:")
        for count, source in results:
            print(f"   {source}: {count} items")
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating schema: {e}")
        return False
    
    finally:
        conn.close()

def main():
    """Main function."""
    print("🎯 PORTFOLIO DATABASE SCHEMA UPDATE")
    print("=" * 50)
    
    success = update_portfolio_schema()
    
    if success:
        print(f"\n🎉 SCHEMA UPDATE COMPLETE!")
        print("=" * 30)
        print("✅ Database ready for real data integration")
        print("✅ Run 'python3 integrate_real_data.py' again")
    else:
        print(f"\n❌ Schema update failed!")

if __name__ == "__main__":
    main() 