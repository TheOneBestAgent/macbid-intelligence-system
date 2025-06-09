#!/usr/bin/env python3
"""
Debug HTML parsing for NextJS data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_systems.nextjs_integration_system import NextJSIntegrationSystem
import re
import json

def debug_html_parsing():
    """Debug the HTML parsing process step by step"""
    print("🔍 DEBUGGING HTML PARSING FOR NEXTJS DATA")
    print("=" * 60)
    
    # Initialize system
    nextjs_system = NextJSIntegrationSystem()
    
    # Test lot ID
    test_lot_id = 35242923
    lot_page_url = f"https://www.mac.bid/lot/mac_lot_{test_lot_id}"
    
    print(f"🌐 Fetching page: {lot_page_url}")
    print(f"🍪 Cookies: {len(nextjs_system.session.cookies)} set")
    print(f"📄 Headers: {len(nextjs_system.session.headers)} set")
    
    try:
        response = nextjs_system.session.get(lot_page_url, timeout=15)
        
        print(f"\n📡 RESPONSE:")
        print(f"   Status: {response.status_code}")
        print(f"   Content Length: {len(response.content):,} bytes")
        print(f"   Content Type: {response.headers.get('content-type', 'Unknown')}")
        
        if response.status_code == 200:
            html_content = response.text
            
            # Check if we're getting the right page
            if "mac.bid" in html_content.lower():
                print(f"   ✅ Mac.bid page detected")
            else:
                print(f"   ❌ Not a Mac.bid page")
                
            # Look for NextJS indicators
            if "__NEXT_DATA__" in html_content:
                print(f"   ✅ __NEXT_DATA__ script found")
            else:
                print(f"   ❌ No __NEXT_DATA__ script found")
                
            # Look for lot-specific content
            if str(test_lot_id) in html_content:
                print(f"   ✅ Lot ID {test_lot_id} found in page")
            else:
                print(f"   ❌ Lot ID {test_lot_id} not found in page")
                
            # Extract __NEXT_DATA__ script
            print(f"\n🔍 EXTRACTING __NEXT_DATA__...")
            next_data_pattern = r'<script id="__NEXT_DATA__" type="application/json">([^<]+)</script>'
            next_data_match = re.search(next_data_pattern, html_content)
            
            if next_data_match:
                print(f"   ✅ __NEXT_DATA__ script extracted")
                next_data_json = next_data_match.group(1)
                print(f"   📏 JSON length: {len(next_data_json):,} characters")
                
                try:
                    next_data = json.loads(next_data_json)
                    print(f"   ✅ JSON parsed successfully")
                    print(f"   📋 Top-level keys: {list(next_data.keys())}")
                    
                    # Navigate through the structure
                    if 'props' in next_data:
                        props = next_data['props']
                        print(f"   📋 Props keys: {list(props.keys())}")
                        
                        if 'pageProps' in props:
                            page_props = props['pageProps']
                            print(f"   📋 PageProps keys: {list(page_props.keys())}")
                            print(f"   📋 PageProps types: {[(k, type(v).__name__) for k, v in page_props.items()]}")
                            
                            # Check each possible lot data location
                            for key in ['activeLot', 'currentLot', 'lot', 'lotData']:
                                if key in page_props:
                                    lot_data = page_props[key]
                                    print(f"   🎯 Found '{key}': {type(lot_data).__name__}")
                                    
                                    if isinstance(lot_data, dict):
                                        if lot_data:  # Non-empty dict
                                            print(f"      ✅ Non-empty dict with {len(lot_data)} keys")
                                            print(f"      📋 Keys: {list(lot_data.keys())[:10]}...")  # First 10 keys
                                            
                                            # Check for essential fields
                                            essential_fields = ['product_name', 'retail_price', 'winning_bid_amount', 'total_bids']
                                            for field in essential_fields:
                                                if field in lot_data:
                                                    print(f"      ✅ {field}: {lot_data[field]}")
                                                else:
                                                    print(f"      ❌ {field}: missing")
                                                    
                                            return lot_data
                                        else:
                                            print(f"      ❌ Empty dict")
                                    else:
                                        print(f"      ❌ Not a dict: {lot_data}")
                            
                            print(f"   ❌ No lot data found in any expected location")
                        else:
                            print(f"   ❌ No 'pageProps' in props")
                    else:
                        print(f"   ❌ No 'props' in __NEXT_DATA__")
                        
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON parsing failed: {e}")
                    print(f"   📄 First 200 chars: {next_data_json[:200]}")
            else:
                print(f"   ❌ No __NEXT_DATA__ script found")
                
                # Look for alternative data sources
                print(f"\n🔍 LOOKING FOR ALTERNATIVE DATA SOURCES...")
                
                # Look for inline JavaScript data
                js_patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({[^;]+});',
                    r'window\.lotData\s*=\s*({[^;]+});',
                    r'var\s+lotData\s*=\s*({[^;]+});'
                ]
                
                for pattern in js_patterns:
                    matches = re.findall(pattern, html_content)
                    if matches:
                        print(f"   ✅ Found JS data pattern: {pattern}")
                        for match in matches[:1]:  # Just first match
                            try:
                                data = json.loads(match)
                                print(f"      📋 Keys: {list(data.keys())}")
                            except:
                                print(f"      ❌ Failed to parse JS data")
                
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    return None

if __name__ == "__main__":
    result = debug_html_parsing()
    
    if result:
        print(f"\n🎉 SUCCESS! Found lot data")
        print(f"   NextJS integration should work")
    else:
        print(f"\n❌ FAILED! No lot data found")
        print(f"   NextJS integration needs different approach") 