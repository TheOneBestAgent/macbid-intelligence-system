#!/usr/bin/env python3
"""
Extract NextJS information from Mac.bid pages
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_systems.nextjs_integration_system import NextJSIntegrationSystem
import re
import json

def extract_nextjs_info():
    """Extract NextJS build info and data from actual pages"""
    print("🔍 EXTRACTING NEXTJS INFORMATION FROM MAC.BID")
    print("=" * 60)
    
    # Initialize system
    nextjs_system = NextJSIntegrationSystem()
    
    # Test lot ID
    test_lot_id = 35242923
    lot_page_url = f"https://www.mac.bid/lot/mac_lot_{test_lot_id}"
    
    print(f"🌐 Accessing lot page: {lot_page_url}")
    
    try:
        response = nextjs_system.session.get(lot_page_url, timeout=15)
        
        if response.status_code == 200:
            html_content = response.text
            print(f"✅ Page loaded successfully ({len(html_content):,} chars)")
            
            # Extract build ID from the page
            print(f"\n🔍 SEARCHING FOR BUILD ID...")
            build_id_patterns = [
                r'"buildId":"([^"]+)"',
                r'/_next/static/([^/]+)/_buildManifest\.js',
                r'/_next/data/([^/]+)/',
                r'"buildId"\s*:\s*"([^"]+)"'
            ]
            
            found_build_ids = set()
            for pattern in build_id_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    found_build_ids.add(match)
                    print(f"   Found build ID: {match}")
            
            if found_build_ids:
                # Use the most common or first found build ID
                current_build_id = list(found_build_ids)[0]
                print(f"   ✅ Using build ID: {current_build_id}")
                
                if current_build_id != nextjs_system.nextjs_build_id:
                    print(f"   ⚠️  Build ID mismatch!")
                    print(f"   Current system: {nextjs_system.nextjs_build_id}")
                    print(f"   Found on page: {current_build_id}")
            else:
                print(f"   ❌ No build ID found in page")
                current_build_id = nextjs_system.nextjs_build_id
            
            # Look for NextJS data in the page
            print(f"\n🔍 SEARCHING FOR NEXTJS DATA...")
            
            # Look for __NEXT_DATA__ script
            next_data_pattern = r'<script id="__NEXT_DATA__" type="application/json">([^<]+)</script>'
            next_data_match = re.search(next_data_pattern, html_content)
            
            if next_data_match:
                print(f"   ✅ Found __NEXT_DATA__ script!")
                try:
                    next_data = json.loads(next_data_match.group(1))
                    print(f"   📋 Top-level keys: {list(next_data.keys())}")
                    
                    if 'props' in next_data:
                        props = next_data['props']
                        print(f"   📋 Props keys: {list(props.keys())}")
                        
                        if 'pageProps' in props:
                            page_props = props['pageProps']
                            print(f"   📋 PageProps keys: {list(page_props.keys())}")
                            
                            # Check for both 'activeLot' and 'currentLot'
                            lot_data = None
                            if 'activeLot' in page_props:
                                lot_data = page_props['activeLot']
                                print(f"   ✅ Found activeLot data!")
                            elif 'currentLot' in page_props:
                                lot_data = page_props['currentLot']
                                print(f"   ✅ Found currentLot data!")
                                print(f"   📋 CurrentLot type: {type(lot_data)}")
                                if isinstance(lot_data, dict):
                                    print(f"   📋 CurrentLot keys: {list(lot_data.keys())}")
                                else:
                                    print(f"   📋 CurrentLot value: {lot_data}")
                            
                            if lot_data and isinstance(lot_data, dict):
                                print(f"   📦 Product: {lot_data.get('product_name', 'Unknown')}")
                                print(f"   💰 Retail: ${lot_data.get('retail_price', 0):,.2f}")
                                print(f"   🔥 Current Bid: ${lot_data.get('winning_bid_amount', 0):,.2f}")
                                print(f"   👥 Bidders: {lot_data.get('unique_bidders', 0)}")
                                print(f"   🔓 Is Open: {lot_data.get('is_open', False)}")
                                
                                return lot_data, current_build_id
                            else:
                                print(f"   ❌ No valid lot data found (lot_data: {type(lot_data)})")
                        else:
                            print(f"   ❌ No 'pageProps' in props")
                    else:
                        print(f"   ❌ No 'props' in __NEXT_DATA__")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ Failed to parse __NEXT_DATA__: {e}")
            else:
                print(f"   ❌ No __NEXT_DATA__ script found")
            
            # Look for API endpoints in the page
            print(f"\n🔍 SEARCHING FOR API ENDPOINTS...")
            api_patterns = [
                r'/_next/data/[^"]+',
                r'/api/[^"]+',
                r'fetch\(["\']([^"\']+)["\']',
                r'axios\.get\(["\']([^"\']+)["\']'
            ]
            
            found_endpoints = set()
            for pattern in api_patterns:
                matches = re.findall(pattern, html_content)
                for match in matches:
                    if 'lot' in match.lower() or 'auction' in match.lower():
                        found_endpoints.add(match)
            
            if found_endpoints:
                print(f"   ✅ Found potential API endpoints:")
                for endpoint in sorted(found_endpoints):
                    print(f"   - {endpoint}")
            else:
                print(f"   ❌ No relevant API endpoints found")
                
        else:
            print(f"❌ Failed to load page: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error accessing page: {e}")
    
    return None, None

def test_extracted_data():
    """Test using the extracted data"""
    print(f"\n🧪 TESTING EXTRACTED DATA...")
    
    lot_data, build_id = extract_nextjs_info()
    
    if lot_data:
        print(f"✅ Successfully extracted lot data from page!")
        print(f"   This proves we can get real-time bid data")
        print(f"   We should modify the NextJS integration to parse HTML instead of API calls")
        
        # Test if we can use this data format
        enhanced_data = {
            'nextjs_current_bid': lot_data.get('winning_bid_amount', 0),
            'nextjs_total_bids': lot_data.get('total_bids', 0),
            'nextjs_unique_bidders': lot_data.get('unique_bidders', 0),
            'nextjs_is_open': lot_data.get('is_open', False),
            'nextjs_timestamp': '2025-06-07T19:15:00',
            'has_realtime_data': True,
            'data_source': 'nextjs_enhanced'
        }
        
        print(f"\n📊 ENHANCED DATA FORMAT:")
        for key, value in enhanced_data.items():
            print(f"   {key}: {value}")
            
        return True
    else:
        print(f"❌ Failed to extract lot data")
        return False

if __name__ == "__main__":
    success = test_extracted_data()
    
    if success:
        print(f"\n🎉 SOLUTION FOUND!")
        print(f"   Instead of using NextJS API endpoints, we should:")
        print(f"   1. Fetch the lot page HTML")
        print(f"   2. Extract __NEXT_DATA__ script content")
        print(f"   3. Parse the JSON to get real-time bid data")
        print(f"   4. This will give us the same data as the API")
    else:
        print(f"\n❌ SOLUTION NOT FOUND")
        print(f"   NextJS integration may not be possible with current approach") 