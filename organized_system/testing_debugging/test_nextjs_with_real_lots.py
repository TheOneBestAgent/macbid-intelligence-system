#!/usr/bin/env python3
"""
Test NextJS Integration with Real Lot IDs from Typesense
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_systems.nextjs_integration_system import NextJSIntegrationSystem
import re
import json

def test_nextjs_with_real_lots():
    """Test NextJS integration with real lot IDs from Typesense results"""
    print("🔍 TESTING NEXTJS WITH REAL LOT IDS")
    print("=" * 60)
    
    # Initialize system
    nextjs_system = NextJSIntegrationSystem()
    
    # Use the top lot IDs from our Typesense results
    test_lots = [
        (35242923, "Pallet of General Merchandise (REMOVAL)", 17986.38),
        (35684618, "General Merchandise 06-04 #2", 16562.34),
        (35739734, "General Merchandise 06-05", 14730.09),
        (35777466, "General Merchandise 06-05 #2", 14017.08),
        (35788222, "Pallet for Natasha, Kamille & Talia", 13626.62),
        (35813385, "General Merchandise 06-06", 12930.61),
        (35654485, "General Merchandise 06-04", 11949.51),
        (35610274, "General Merchandise 06-03 #3", 10091.89),
        (35451308, "Pallet of General Merchandise", 9831.69),
        (35451201, "Pallet of Broken Vacuums", 8900.17)
    ]
    
    print(f"🧪 Testing {len(test_lots)} high-value lots from Typesense results...")
    
    success_count = 0
    working_lots = []
    
    for i, (lot_id, product_name, retail_price) in enumerate(test_lots, 1):
        print(f"\n[{i}/{len(test_lots)}] Testing Lot {lot_id}")
        print(f"   Product: {product_name[:50]}...")
        print(f"   Retail: ${retail_price:,.2f}")
        
        # Test NextJS data extraction
        lot_page_url = f"https://www.mac.bid/lot/mac_lot_{lot_id}"
        
        try:
            response = nextjs_system.session.get(lot_page_url, timeout=15)
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check if lot ID is in page
                if str(lot_id) in html_content:
                    print(f"   ✅ Lot ID found in page")
                    
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
                                    print(f"      Time Remaining: {lot_data.get('time_remaining', 'N/A')}")
                                    
                                    # Check for active bidding
                                    if lot_data.get('total_bids', 0) > 0:
                                        print(f"      🔥 ACTIVE BIDDING DETECTED!")
                                    
                                    # This is our first working lot - perfect for integration testing
                                    if success_count == 1:
                                        print(f"   🌟 FIRST SUCCESS - Perfect for parallel discovery integration!")
                                        
                                else:
                                    print(f"   ❌ Empty or invalid lot data")
                                    if 'currentLot' in page_props:
                                        print(f"      currentLot type: {type(page_props['currentLot'])}")
                                        print(f"      currentLot content: {page_props['currentLot']}")
                            else:
                                print(f"   ❌ No pageProps in NextJS data")
                                print(f"      Available keys: {list(next_data.get('props', {}).keys())}")
                        except json.JSONDecodeError as e:
                            print(f"   ❌ Failed to parse NextJS JSON: {e}")
                    else:
                        print(f"   ❌ No __NEXT_DATA__ script found")
                else:
                    print(f"   ❌ Lot ID not found in page (may be inactive)")
            else:
                print(f"   ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   Success Rate: {success_count}/{len(test_lots)} ({success_count/len(test_lots)*100:.1f}%)")
    print(f"   Working Lots: {len(working_lots)}")
    
    if success_count > 0:
        print(f"\n🎉 NEXTJS INTEGRATION WORKING!")
        print(f"   ✅ Real-time bid data extraction successful")
        print(f"   ✅ Ready for parallel discovery integration")
        
        # Show integration format for the first working lot
        if working_lots:
            lot_id, lot_data = working_lots[0]
            print(f"\n🔧 INTEGRATION FORMAT EXAMPLE:")
            print(f"   Lot ID: {lot_id}")
            
            enhanced_lot = {
                'lot_id': lot_id,
                'product_name': lot_data.get('product_name', 'Unknown'),
                'retail_price': lot_data.get('retail_price', 0),
                'current_bid': lot_data.get('winning_bid_amount', 0),
                'total_bids': lot_data.get('total_bids', 0),
                'unique_bidders': lot_data.get('unique_bidders', 0),
                'is_open': lot_data.get('is_open', False),
                'time_remaining': lot_data.get('time_remaining', 'N/A'),
                'data_source': 'nextjs_enhanced',
                'has_realtime_data': True,
                'nextjs_timestamp': lot_data.get('nextjs_timestamp', 'N/A')
            }
            
            print(f"   📦 Enhanced lot format:")
            for key, value in enhanced_lot.items():
                print(f"      {key}: {value}")
                
        return True, working_lots
    else:
        print(f"\n❌ NEXTJS INTEGRATION FAILED")
        print(f"   All tested lots returned empty data")
        print(f"   This could mean:")
        print(f"   - Lots are inactive/closed")
        print(f"   - Authentication issues")
        print(f"   - NextJS structure changed")
        return False, []

if __name__ == "__main__":
    success, working_lots = test_nextjs_with_real_lots()
    
    if success:
        print(f"\n🚀 READY TO UPDATE PARALLEL DISCOVERY SYSTEM")
        print(f"   NextJS integration confirmed with {len(working_lots)} working lots")
        print(f"   Can now combine Typesense + NextJS for real-time bid data")
    else:
        print(f"\n🔧 DEBUGGING NEEDED")
        print(f"   NextJS integration requires further investigation") 