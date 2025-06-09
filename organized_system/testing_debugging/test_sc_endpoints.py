#!/usr/bin/env python3
"""
Quick test to check SC warehouse endpoints
"""

import asyncio
import aiohttp
import json
import os

async def test_sc_endpoints():
    """Test South Carolina warehouse endpoints."""
    
    # Load tokens
    tokens_file = os.path.expanduser("~/.macbid_scraper/api_tokens.json")
    try:
        with open(tokens_file, 'r') as f:
            token_data = json.load(f)
            jwt_token = token_data.get('tokens', {}).get('authorization')
    except:
        jwt_token = None
    
    # Use simple headers like the working personal monitor
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    # SC warehouse locations
    sc_locations = [17, 20, 28, 36, 38]
    sc_location_string = ",".join(map(str, sc_locations))
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        
        print("🔍 Testing SC Warehouse Endpoints")
        print("=" * 50)
        
        # Test 1: Combined SC locations
        print(f"\n1. Testing combined SC locations: {sc_location_string}")
        endpoint = f"https://api.macdiscount.com/auction/getAuctionItems?loc={sc_location_string}&pg=1&ppg=50"
        print(f"   URL: {endpoint}")
        
        try:
            async with session.get(endpoint, headers=headers, timeout=15) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    if data and isinstance(data, dict) and 'auctionItems' in data:
                        items = data['auctionItems']
                        print(f"   ✅ Found {len(items)} items")
                        if items:
                            print(f"   📦 Sample item: {items[0].get('productName', 'Unknown')[:50]}...")
                    else:
                        print(f"   ❌ Unexpected data format: {type(data)}")
                        print(f"   Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                else:
                    text = await response.text()
                    print(f"   ❌ Error response: {text[:200]}...")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 2: Individual SC locations
        print(f"\n2. Testing individual SC locations:")
        loc_names = {17: "Spartanburg", 20: "Greenville", 28: "Rock Hill", 36: "Anderson-B", 38: "Anderson-L"}
        
        for loc in sc_locations:
            print(f"\n   Testing {loc_names[loc]} (ID: {loc}):")
            endpoint = f"https://api.macdiscount.com/auction/getAuctionItems?loc={loc}&pg=1&ppg=20"
            print(f"   URL: {endpoint}")
            
            try:
                async with session.get(endpoint, headers=headers, timeout=15) as response:
                    print(f"   Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if data and isinstance(data, dict) and 'auctionItems' in data:
                            items = data['auctionItems']
                            print(f"   ✅ Found {len(items)} items")
                        else:
                            print(f"   ❌ No items or unexpected format")
                    else:
                        text = await response.text()
                        print(f"   ❌ Error: {text[:100]}...")
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        # Test 3: General auction endpoints
        print(f"\n3. Testing general auction endpoints:")
        
        general_endpoints = [
            "https://api.macdiscount.com/auction/getAuctionItems?pg=1&ppg=20",
            "https://api.macdiscount.com/auction/getAuctions?pg=1&ppg=20",
            "https://api.macdiscount.com/auction/search?q=&pg=1&ppg=20"
        ]
        
        for endpoint in general_endpoints:
            print(f"\n   Testing: {endpoint}")
            try:
                async with session.get(endpoint, headers=headers, timeout=15) as response:
                    print(f"   Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict):
                            if 'auctionItems' in data:
                                items = data['auctionItems']
                                print(f"   ✅ Found {len(items)} auction items")
                            elif 'data' in data:
                                items = data['data']
                                print(f"   ✅ Found {len(items)} data items")
                            else:
                                print(f"   📋 Keys: {list(data.keys())}")
                        elif isinstance(data, list):
                            print(f"   ✅ Found {len(data)} items in list")
                        else:
                            print(f"   ❓ Unexpected data type: {type(data)}")
                    else:
                        text = await response.text()
                        print(f"   ❌ Error: {text[:100]}...")
            except Exception as e:
                print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_sc_endpoints()) 