#!/usr/bin/env python3
"""
Find active lots and test NextJS integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_systems.nextjs_integration_system import NextJSIntegrationSystem
import requests
import re
import json

def find_active_lots():
    """Find currently active lots using Typesense"""
    print("🔍 FINDING ACTIVE LOTS FROM TYPESENSE")
    print("=" * 50)
    
    # Initialize system
    nextjs_system = NextJSIntegrationSystem()
    
    # Get recent lots from Typesense
    print("📡 Querying Typesense for recent lots...")
    
    payload = {
        "searches": [
            {
                "collection": "lots",
                "q": "*",
                "query_by": "product_name,description",
                "sort_by": "lot_id:desc",  # Most recent lots first
                "per_page": 20,
                "page": 1
            }
        ]
    }
    
    try:
        response = requests.post(
            nextjs_system.typesense_url,
            headers={
                'X-TYPESENSE-API-KEY': nextjs_system.typesense_key,
                'Content-Type': 'application/json'
            },
            json=payload
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response keys: {list(data.keys())}")
            results = data.get('results', [])
            print(f"   Results count: {len(results)}")
            
            if results:
                print(f"   First result keys: {list(results[0].keys())}")
                if 'hits' in results[0]:
                    hits = results[0]['hits']
                    print(f"✅ Found {len(hits)} recent lots")
                    
                    # Test each lot with NextJS
                    print(f"\n🧪 TESTING NEXTJS INTEGRATION WITH RECENT LOTS")
                    print("=" * 60)
                    
                    success_count = 0
                    for i, hit in enumerate(hits[:5], 1):  # Test first 5 lots
                    doc = hit['document']
                    lot_id = doc.get('lot_id')
                    product_name = doc.get('product_name', 'Unknown')
                    retail_price = doc.get('retail_price', 0)
                    
                    print(f"\n[{i}/5] Testing Lot {lot_id}")
                    print(f"   Product: {product_name[:50]}...")
                    print(f"   Retail: ${retail_price:,.2f}")
                    
                    # Test NextJS data extraction
                    lot_page_url = f"https://www.mac.bid/lot/mac_lot_{lot_id}"
                    
                    try:
                        response = nextjs_system.session.get(lot_page_url, timeout=10)
                        
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
                                                print(f"   🎯 SUCCESS! Real-time data available:")
                                                print(f"      Current Bid: ${lot_data.get('winning_bid_amount', 0):,.2f}")
                                                print(f"      Total Bids: {lot_data.get('total_bids', 0)}")
                                                print(f"      Unique Bidders: {lot_data.get('unique_bidders', 0)}")
                                                print(f"      Is Open: {lot_data.get('is_open', False)}")
                                                
                                                # This is a working lot - save it for testing
                                                if success_count == 1:
                                                    print(f"   🌟 FIRST SUCCESS - Using this lot for integration testing")
                                                    return lot_id, lot_data
                                            else:
                                                print(f"   ❌ Empty or invalid lot data")
                                        else:
                                            print(f"   ❌ No pageProps in NextJS data")
                                    except json.JSONDecodeError:
                                        print(f"   ❌ Failed to parse NextJS JSON")
                                else:
                                    print(f"   ❌ No __NEXT_DATA__ script found")
                            else:
                                print(f"   ❌ Lot ID not found in page (may be inactive)")
                        else:
                            print(f"   ❌ HTTP {response.status_code}")
                            
                    except Exception as e:
                        print(f"   ❌ Exception: {e}")
                
                print(f"\n📊 RESULTS:")
                print(f"   Success Rate: {success_count}/5 ({success_count/5*100:.1f}%)")
                
                if success_count > 0:
                    print(f"   🎉 NextJS integration is working!")
                    return True
                else:
                    print(f"   ❌ No working lots found")
                    return False
                    
            else:
                print(f"❌ No lots found in Typesense")
                return False
        else:
            print(f"❌ Typesense error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

if __name__ == "__main__":
    result = find_active_lots()
    
    if result:
        if isinstance(result, tuple):
            lot_id, lot_data = result
            print(f"\n🚀 READY FOR PARALLEL DISCOVERY INTEGRATION")
            print(f"   Working lot ID: {lot_id}")
            print(f"   NextJS data extraction confirmed")
        else:
            print(f"\n✅ NEXTJS INTEGRATION CONFIRMED")
            print(f"   Multiple working lots found")
    else:
        print(f"\n❌ NEXTJS INTEGRATION FAILED")
        print(f"   Need to investigate further") 