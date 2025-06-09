#!/usr/bin/env python3
"""
Find Active Lots that Don't Close Today
"""

import sqlite3
import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_systems.nextjs_integration_system import NextJSIntegrationSystem
import re
import json

def find_active_lots_no_today():
    """Find active lots that don't close today"""
    print("🔍 FINDING ACTIVE LOTS (EXCLUDING TODAY'S CLOSURES)")
    print("=" * 60)
    
    # Connect to the Typesense database
    db_path = 'typesense_all_lots.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get today's date in various formats to filter out
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    today_alt = today.strftime('%m/%d/%Y')
    
    print(f"📅 Today's date: {today_str}")
    print(f"📊 Querying database for lots NOT closing today...")
    
    # Get lots that don't close today and are likely still active
    cursor.execute('''
        SELECT lot_id, product_name, retail_price, auction_location, current_bid, expected_close_date
        FROM typesense_lots 
        WHERE lot_id IS NOT NULL 
        AND (expected_close_date IS NULL 
             OR expected_close_date NOT LIKE '%2025-06-07%'
             OR expected_close_date NOT LIKE '%06/07/2025%'
             OR expected_close_date NOT LIKE '%6/7/2025%')
        ORDER BY CAST(REPLACE(lot_id, 'mac_lot_', '') AS INTEGER) DESC 
        LIMIT 30
    ''')
    
    recent_lots = cursor.fetchall()
    conn.close()
    
    if not recent_lots:
        print("❌ No lots found in database")
        return False
    
    print(f"✅ Found {len(recent_lots)} lots that don't close today")
    
    # Initialize NextJS system
    nextjs_system = NextJSIntegrationSystem()
    
    print(f"\n🧪 TESTING NEXTJS INTEGRATION WITH NON-TODAY LOTS")
    print("=" * 60)
    
    success_count = 0
    working_lots = []
    
    for i, (lot_id_raw, product_name, retail_price, location, current_bid, close_date) in enumerate(recent_lots[:15], 1):
        # Extract numeric lot ID from "mac_lot_XXXXX" format
        if lot_id_raw and lot_id_raw.startswith('mac_lot_'):
            lot_id = lot_id_raw.replace('mac_lot_', '')
        else:
            lot_id = str(lot_id_raw)
            
        print(f"\n[{i}/15] Testing Lot {lot_id}")
        print(f"   Product: {product_name[:50]}...")
        print(f"   Retail: ${retail_price:,.2f}")
        print(f"   Location: {location}")
        print(f"   Current Bid: ${current_bid:,.2f}")
        print(f"   Close Date: {close_date or 'Unknown'}")
        
        # Test NextJS data extraction
        lot_page_url = f"https://www.mac.bid/lot/mac_lot_{lot_id}"
        
        try:
            response = nextjs_system.session.get(lot_page_url, timeout=10)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check if lot ID is in page
                if str(lot_id) in html_content:
                    print(f"   ✅ Lot ID found in page - ACTIVE LOT!")
                    
                    # Extract NextJS data
                    next_data_pattern = r'<script id="__NEXT_DATA__" type="application/json">([^<]+)</script>'
                    next_data_match = re.search(next_data_pattern, html_content)
                    
                    if next_data_match:
                        try:
                            next_data = json.loads(next_data_match.group(1))
                            
                            if 'props' in next_data and 'pageProps' in next_data['props']:
                                page_props = next_data['props']['pageProps']
                                
                                # Check for lot data
                                lot_data = None
                                if 'activeLot' in page_props and page_props['activeLot']:
                                    lot_data = page_props['activeLot']
                                    print(f"   ✅ Found activeLot data!")
                                elif 'currentLot' in page_props and page_props['currentLot']:
                                    lot_data = page_props['currentLot']
                                    print(f"   ✅ Found currentLot data!")
                                
                                if lot_data and isinstance(lot_data, dict) and lot_data:
                                    # Check if lot closes today by examining the lot data
                                    lot_close_date = lot_data.get('expected_close_date', '')
                                    if today_str in str(lot_close_date) or today_alt in str(lot_close_date):
                                        print(f"   ⏰ SKIPPING - Lot closes today: {lot_close_date}")
                                        continue
                                    
                                    success_count += 1
                                    working_lots.append((lot_id, lot_data))
                                    
                                    print(f"   🎯 SUCCESS! Real-time data available:")
                                    print(f"      Product Name: {lot_data.get('product_name', 'N/A')}")
                                    print(f"      Retail Price: ${lot_data.get('retail_price', 0):,.2f}")
                                    print(f"      Current Bid: ${lot_data.get('winning_bid_amount', 0):,.2f}")
                                    print(f"      Total Bids: {lot_data.get('total_bids', 0)}")
                                    print(f"      Unique Bidders: {lot_data.get('unique_bidders', 0)}")
                                    print(f"      Is Open: {lot_data.get('is_open', False)}")
                                    print(f"      Close Date: {lot_data.get('expected_close_date', 'N/A')}")
                                    
                                    # Check for active bidding
                                    if lot_data.get('total_bids', 0) > 0:
                                        print(f"      🔥 ACTIVE BIDDING DETECTED!")
                                    
                                    # This is our first working lot - perfect for integration testing
                                    if success_count == 1:
                                        print(f"   🌟 FIRST SUCCESS - Perfect for parallel discovery integration!")
                                        return lot_id, lot_data  # Return immediately on first success
                                        
                                else:
                                    print(f"   ❌ Empty or invalid lot data")
                                    if 'currentLot' in page_props:
                                        print(f"      currentLot: {page_props['currentLot']}")
                                    if 'activeLot' in page_props:
                                        print(f"      activeLot: {page_props['activeLot']}")
                            else:
                                print(f"   ❌ No pageProps in NextJS data")
                        except json.JSONDecodeError as e:
                            print(f"   ❌ Failed to parse NextJS JSON: {e}")
                    else:
                        print(f"   ❌ No __NEXT_DATA__ script found")
                else:
                    print(f"   ❌ Lot ID not found in page (inactive)")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   Success Rate: {success_count}/15 ({success_count/15*100:.1f}%)")
    print(f"   Working Lots: {len(working_lots)}")
    
    if success_count > 0:
        print(f"\n🎉 NEXTJS INTEGRATION WORKING!")
        return True, working_lots
    else:
        print(f"\n❌ NO ACTIVE LOTS FOUND")
        print(f"   All tested lots appear to be inactive or close today")
        return False, []

if __name__ == "__main__":
    result = find_active_lots_no_today()
    
    if isinstance(result, tuple) and len(result) == 2:
        if isinstance(result[0], str):  # First success case (lot_id is string)
            lot_id, lot_data = result
            print(f"\n🚀 FOUND WORKING LOT!")
            print(f"   Lot ID: {lot_id}")
            print(f"   Product: {lot_data.get('product_name', 'Unknown')}")
            print(f"   NextJS integration confirmed!")
            print(f"   Ready to update parallel discovery system!")
        else:  # Multiple success case
            success, working_lots = result
            if success:
                print(f"\n🚀 NEXTJS INTEGRATION CONFIRMED!")
                print(f"   Found {len(working_lots)} working lots")
    else:
        print(f"\n❌ NO WORKING LOTS FOUND")
        print(f"   May need to wait for new auctions or check authentication") 