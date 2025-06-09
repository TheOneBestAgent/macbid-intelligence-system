#!/usr/bin/env python3
"""
Debug NextJS API responses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_systems.nextjs_integration_system import NextJSIntegrationSystem
import requests

def debug_nextjs_api():
    """Debug what the NextJS API is actually returning"""
    print("🔍 DEBUGGING NEXTJS API RESPONSES")
    print("=" * 50)
    
    # Initialize system
    nextjs_system = NextJSIntegrationSystem()
    
    # Test lot ID
    test_lot_id = 35242923
    
    # Build URL
    url = f"https://www.mac.bid/_next/data/{nextjs_system.nextjs_build_id}/lot/mac_lot_{test_lot_id}.json"
    
    print(f"🔗 Testing URL: {url}")
    print(f"🍪 Cookies: {len(nextjs_system.session.cookies)} set")
    print(f"📄 Headers: {len(nextjs_system.session.headers)} set")
    
    try:
        response = nextjs_system.session.get(url, timeout=10)
        
        print(f"\n📡 RESPONSE DETAILS:")
        print(f"   Status Code: {response.status_code}")
        print(f"   Content Length: {len(response.content)} bytes")
        print(f"   Content Type: {response.headers.get('content-type', 'Unknown')}")
        
        if response.status_code == 200:
            print(f"   Raw Content (first 500 chars):")
            print(f"   {response.text[:500]}")
            
            if response.text.strip():
                try:
                    data = response.json()
                    print(f"   ✅ JSON parsed successfully")
                    print(f"   Top-level keys: {list(data.keys())}")
                    
                    if 'pageProps' in data:
                        print(f"   pageProps keys: {list(data['pageProps'].keys())}")
                        if 'activeLot' in data['pageProps']:
                            lot = data['pageProps']['activeLot']
                            print(f"   activeLot keys: {list(lot.keys())}")
                            print(f"   Product: {lot.get('product_name', 'Unknown')}")
                        else:
                            print(f"   ❌ No 'activeLot' in pageProps")
                    else:
                        print(f"   ❌ No 'pageProps' in response")
                        
                except Exception as e:
                    print(f"   ❌ JSON parsing failed: {e}")
            else:
                print(f"   ❌ Empty response body")
        else:
            print(f"   ❌ HTTP Error: {response.status_code}")
            print(f"   Response text: {response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
    
    # Try alternative URL formats
    print(f"\n🔄 TRYING ALTERNATIVE URL FORMATS:")
    
    alternative_urls = [
        f"https://www.mac.bid/_next/data/{nextjs_system.nextjs_build_id}/lot/{test_lot_id}.json",
        f"https://www.mac.bid/_next/data/{nextjs_system.nextjs_build_id}/lots/{test_lot_id}.json",
        f"https://www.mac.bid/_next/data/{nextjs_system.nextjs_build_id}/auction/lot/{test_lot_id}.json",
        f"https://www.mac.bid/api/lot/{test_lot_id}",
        f"https://www.mac.bid/api/lots/{test_lot_id}",
    ]
    
    for alt_url in alternative_urls:
        try:
            print(f"\n   Testing: {alt_url}")
            response = nextjs_system.session.get(alt_url, timeout=5)
            print(f"   Status: {response.status_code}, Length: {len(response.content)}")
            
            if response.status_code == 200 and len(response.content) > 10:
                print(f"   ✅ Potential success! Content preview:")
                print(f"   {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    # Check if we can access the lot page directly
    print(f"\n🌐 TESTING DIRECT LOT PAGE ACCESS:")
    lot_page_url = f"https://www.mac.bid/lot/mac_lot_{test_lot_id}"
    
    try:
        response = nextjs_system.session.get(lot_page_url, timeout=10)
        print(f"   Lot page status: {response.status_code}")
        print(f"   Content length: {len(response.content)}")
        
        if response.status_code == 200:
            # Look for NextJS data in the page
            if '_next/data' in response.text:
                print(f"   ✅ Found NextJS data references in page")
            else:
                print(f"   ❌ No NextJS data references found")
                
            # Look for build ID in the page
            if nextjs_system.nextjs_build_id in response.text:
                print(f"   ✅ Build ID {nextjs_system.nextjs_build_id} found in page")
            else:
                print(f"   ❌ Build ID not found - may be outdated")
                
    except Exception as e:
        print(f"   ❌ Failed to access lot page: {e}")

if __name__ == "__main__":
    debug_nextjs_api() 