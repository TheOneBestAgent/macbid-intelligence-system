#!/usr/bin/env python3
"""
Test the exact same endpoint that was working in personal_realtime_monitor.py
"""

import asyncio
import aiohttp
import json
import os

async def test_original_endpoint():
    """Test the exact endpoint from personal_realtime_monitor.py"""
    
    print("🔍 Testing Original Working Endpoint")
    print("=" * 50)
    
    # Use the exact same headers as personal_realtime_monitor
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    # Load session cookie if available
    credentials_file = os.path.expanduser("~/.macbid_scraper/credentials.json")
    try:
        with open(credentials_file, 'r') as f:
            creds = json.load(f)
            session_cookie = creds.get('session_cookie')
            if session_cookie:
                headers['Cookie'] = f'ASP.NET_SessionId={session_cookie}'
                print(f"✅ Using session cookie: {session_cookie[:20]}...")
    except:
        print("⚠️ No session cookie found")
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        
        # Test 1: Exact same endpoint from personal_realtime_monitor
        print("\n1. Testing exact original endpoint (loc=17,18):")
        url = "https://api.macdiscount.com/auction/getAuctionItems?loc=17,18&pg=1&ppg=50"
        print(f"   URL: {url}")
        
        try:
            async with session.get(url, headers=headers, timeout=15) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    if data and 'auctionItems' in data:
                        items = data['auctionItems']
                        print(f"   ✅ SUCCESS! Found {len(items)} auction items")
                        if items:
                            sample = items[0]
                            print(f"   📦 Sample: {sample.get('productName', 'Unknown')[:50]}...")
                            print(f"   💰 Price: ${sample.get('retailPrice', 0)}")
                            print(f"   🏢 Location: {sample.get('locationId', 'Unknown')}")
                    else:
                        print(f"   ❌ No auctionItems in response")
                        print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                else:
                    text = await response.text()
                    print(f"   ❌ Error: {text[:200]}...")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 2: Try just SC locations one by one
        print("\n2. Testing individual SC locations:")
        sc_locations = [17, 20, 28, 36, 38]
        loc_names = {17: "Spartanburg", 20: "Greenville", 28: "Rock Hill", 36: "Anderson-B", 38: "Anderson-L"}
        
        for loc in sc_locations:
            url = f"https://api.macdiscount.com/auction/getAuctionItems?loc={loc}&pg=1&ppg=20"
            print(f"\n   {loc_names[loc]} (ID: {loc}):")
            print(f"   URL: {url}")
            
            try:
                async with session.get(url, headers=headers, timeout=15) as response:
                    print(f"   Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if data and 'auctionItems' in data:
                            items = data['auctionItems']
                            print(f"   ✅ Found {len(items)} items")
                        else:
                            print(f"   ❌ No items or unexpected format")
                    else:
                        text = await response.text()
                        print(f"   ❌ Error: {text[:100]}...")
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        # Test 3: Try pairs of SC locations
        print("\n3. Testing pairs of SC locations:")
        location_pairs = [
            (17, 20, "Spartanburg + Greenville"),
            (28, 36, "Rock Hill + Anderson-B"),
            (17, 28, "Spartanburg + Rock Hill")
        ]
        
        for loc1, loc2, name in location_pairs:
            url = f"https://api.macdiscount.com/auction/getAuctionItems?loc={loc1},{loc2}&pg=1&ppg=20"
            print(f"\n   {name}:")
            print(f"   URL: {url}")
            
            try:
                async with session.get(url, headers=headers, timeout=15) as response:
                    print(f"   Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if data and 'auctionItems' in data:
                            items = data['auctionItems']
                            print(f"   ✅ Found {len(items)} items")
                        else:
                            print(f"   ❌ No items")
                    else:
                        text = await response.text()
                        print(f"   ❌ Error: {text[:100]}...")
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        # Test 4: Try without location filter
        print("\n4. Testing without location filter:")
        url = "https://api.macdiscount.com/auction/getAuctionItems?pg=1&ppg=20"
        print(f"   URL: {url}")
        
        try:
            async with session.get(url, headers=headers, timeout=15) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    if data and 'auctionItems' in data:
                        items = data['auctionItems']
                        print(f"   ✅ Found {len(items)} items from all locations")
                        if items:
                            # Show location distribution
                            locations = {}
                            for item in items:
                                loc_id = item.get('locationId', 'Unknown')
                                locations[loc_id] = locations.get(loc_id, 0) + 1
                            print(f"   📊 Location distribution: {locations}")
                    else:
                        print(f"   ❌ No items")
                else:
                    text = await response.text()
                    print(f"   ❌ Error: {text[:100]}...")
        except Exception as e:
            print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_original_endpoint()) 