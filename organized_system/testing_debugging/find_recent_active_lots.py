#!/usr/bin/env python3
"""
Find Recent Active Lots from Typesense Database
"""

import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_systems.nextjs_integration_system import NextJSIntegrationSystem
import re
import json

def find_recent_active_lots():
    """Find recent lots from the database and test NextJS integration"""
    print("🔍 FINDING RECENT ACTIVE LOTS FROM DATABASE")
    print("=" * 60)
    
    # Connect to the Typesense database
    db_path = 'typesense_all_lots.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get the most recent lots (highest lot_id numbers)
    print("📊 Querying database for recent lots...")
    cursor.execute('''
        SELECT lot_id, product_name, retail_price, auction_location, current_bid
        FROM typesense_lots 
        WHERE lot_id IS NOT NULL 
        ORDER BY CAST(REPLACE(lot_id, 'mac_lot_', '') AS INTEGER) DESC 
        LIMIT 20
    ''')
    
    recent_lots = cursor.fetchall()
    conn.close()
    
    if not recent_lots:
        print("❌ No lots found in database")
        return False
    
    print(f"✅ Found {len(recent_lots)} recent lots")
    
    # Initialize NextJS system
    nextjs_system = NextJSIntegrationSystem()
    
    print(f"\n🧪 TESTING NEXTJS INTEGRATION WITH RECENT LOTS")
    print("=" * 60)
    
    success_count = 0
    working_lots = []
    
    for i, (lot_id_raw, product_name, retail_price, location, current_bid) in enumerate(recent_lots[:10], 1):
        # Extract numeric lot ID from "mac_lot_XXXXX" format
        if lot_id_raw.startswith('mac_lot_'):
            lot_id = lot_id_raw.replace('mac_lot_', '')
        else:
            lot_id = lot_id_raw
            
        print(f"\n[{i}/10] Testing Lot {lot_id}")
        print(f"   Product: {product_name[:50]}...")
        print(f"   Retail: ${retail_price:,.2f}")
        print(f"   Location: {location}")
        print(f"   Current Bid: ${current_bid:,.2f}")
        
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
                                    success_count += 1
                                    working_lots.append((lot_id, lot_data))
                                    
                                    print(f"   🎯 SUCCESS! Real-time data available:")
                                    print(f"      Product Name: {lot_data.get('product_name', 'N/A')}")
                                    print(f"      Retail Price: ${lot_data.get('retail_price', 0):,.2f}")
                                    print(f"      Current Bid: ${lot_data.get('winning_bid_amount', 0):,.2f}")
                                    print(f"      Total Bids: {lot_data.get('total_bids', 0)}")
                                    print(f"      Unique Bidders: {lot_data.get('unique_bidders', 0)}")
                                    print(f"      Is Open: {lot_data.get('is_open', False)}")
                                    
                                    # Check for active bidding
                                    if lot_data.get('total_bids', 0) > 0:
                                        print(f"      🔥 ACTIVE BIDDING DETECTED!")
                                    
                                    # This is our first working lot - perfect for integration testing
                                    if success_count == 1:
                                        print(f"   🌟 FIRST SUCCESS - Perfect for parallel discovery integration!")
                                        return lot_id, lot_data  # Return immediately on first success
                                        
                                else:
                                    print(f"   ❌ Empty or invalid lot data")
                                    print(f"      pageProps keys: {list(page_props.keys())}")
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
    print(f"   Success Rate: {success_count}/10 ({success_count/10*100:.1f}%)")
    print(f"   Working Lots: {len(working_lots)}")
    
    if success_count > 0:
        print(f"\n🎉 NEXTJS INTEGRATION WORKING!")
        return True, working_lots
    else:
        print(f"\n❌ NO ACTIVE LOTS FOUND")
        print(f"   All tested lots appear to be inactive")
        return False, []

if __name__ == "__main__":
    result = find_recent_active_lots()
    
    if isinstance(result, tuple) and len(result) == 2:
        if isinstance(result[0], int):  # First success case
            lot_id, lot_data = result
            print(f"\n🚀 FOUND WORKING LOT!")
            print(f"   Lot ID: {lot_id}")
            print(f"   Product: {lot_data.get('product_name', 'Unknown')}")
            print(f"   NextJS integration confirmed!")
        else:  # Multiple success case
            success, working_lots = result
            if success:
                print(f"\n🚀 NEXTJS INTEGRATION CONFIRMED!")
                print(f"   Found {len(working_lots)} working lots")
    else:
        print(f"\n❌ NO WORKING LOTS FOUND")
        print(f"   May need to wait for new auctions or check authentication") 