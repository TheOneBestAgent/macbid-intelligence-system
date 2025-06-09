#!/usr/bin/env python3
"""
📊 TYPESENSE PROGRESS CHECKER
Quick script to check progress of the paginated scanner
"""

import sqlite3
import time
from datetime import datetime

def check_progress():
    try:
        conn = sqlite3.connect('typesense_paginated_all_lots.db')
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute('SELECT COUNT(*) FROM paginated_lots')
        total_lots = cursor.fetchone()[0]
        
        # Get no-bid count
        cursor.execute('SELECT COUNT(*) FROM paginated_lots WHERE current_bid = 0')
        no_bid_lots = cursor.fetchone()[0]
        
        # Get total retail value
        cursor.execute('SELECT SUM(retail_price) FROM paginated_lots WHERE retail_price > 0')
        total_value = cursor.fetchone()[0] or 0
        
        # Get latest timestamp
        cursor.execute('SELECT MAX(discovery_timestamp) FROM paginated_lots')
        latest_time = cursor.fetchone()[0]
        
        # Get location breakdown
        cursor.execute('''
            SELECT auction_location, COUNT(*) 
            FROM paginated_lots 
            WHERE auction_location IS NOT NULL 
            GROUP BY auction_location 
            ORDER BY COUNT(*) DESC
        ''')
        locations = cursor.fetchall()
        
        conn.close()
        
        print(f"🔍 TYPESENSE PAGINATED SCANNER PROGRESS")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"=" * 60)
        print(f"📊 Total Lots Discovered: {total_lots:,}")
        print(f"🎯 No-Bid Opportunities: {no_bid_lots:,}")
        print(f"💰 Total Retail Value: ${total_value:,.2f}")
        print(f"⏰ Latest Discovery: {latest_time}")
        print()
        
        if locations:
            print(f"📍 LOCATION BREAKDOWN:")
            for location, count in locations:
                print(f"   • {location}: {count:,} lots")
        
        print()
        
        # Progress towards 37,705
        target = 37705
        progress_pct = (total_lots / target) * 100 if target > 0 else 0
        print(f"🎯 Progress towards 37,705 target: {progress_pct:.1f}% ({total_lots:,}/{target:,})")
        
        if total_lots > 0:
            print(f"✅ Scanner is working! Found {total_lots:,} lots so far")
        else:
            print(f"⏳ Scanner starting up or no data yet...")
            
    except Exception as e:
        print(f"❌ Error checking progress: {e}")
        print("Database may not exist yet or scanner hasn't started")

if __name__ == "__main__":
    check_progress() 