#!/usr/bin/env python3
"""
Test alternative mac.bid API endpoints to find working auction data sources
"""

import asyncio
import aiohttp
import json
import os

async def test_alternative_apis():
    """Test all alternative API endpoints we've discovered."""
    
    print("🔍 Testing Alternative mac.bid API Endpoints")
    print("=" * 60)
    
    # Load credentials and tokens
    credentials_file = os.path.expanduser("~/.macbid_scraper/credentials.json")
    tokens_file = os.path.expanduser("~/.macbid_scraper/api_tokens.json")
    
    # Basic headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }
    
    # Try to load session cookie
    try:
        with open(credentials_file, 'r') as f:
            creds = json.load(f)
            session_cookie = creds.get('session_cookie')
            customer_id = creds.get('customer_id')
            if session_cookie:
                headers['Cookie'] = f'ASP.NET_SessionId={session_cookie}'
                print(f"✅ Using session cookie: {session_cookie[:20]}...")
    except:
        print("⚠️ No session cookie found")
        customer_id = None
    
    # Try to load JWT token
    jwt_token = None
    try:
        with open(tokens_file, 'r') as f:
            token_data = json.load(f)
            jwt_token = token_data.get('tokens', {}).get('authorization')
            if jwt_token:
                print(f"✅ Using JWT token: {jwt_token[:50]}...")
            if not customer_id:
                customer_id = token_data.get('customer_id')
    except:
        print("⚠️ No JWT token found")
    
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        
        # Test 1: Public Search API
        print("\n1. 🔍 Testing Public Search API")
        search_endpoints = [
            "https://api.macdiscount.com/search?q=electronics&limit=20",
            "https://api.macdiscount.com/search?q=&limit=20",
            "https://api.macdiscount.com/search?q=laptop&limit=10"
        ]
        
        for endpoint in search_endpoints:
            print(f"   Testing: {endpoint}")
            try:
                async with session.get(endpoint, headers=headers, timeout=15) as response:
                    print(f"   Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            print(f"   ✅ SUCCESS! Found {len(data)} search results")
                            if data:
                                sample = data[0]
                                print(f"   📦 Sample: {sample.get('product_name', sample.get('title', 'Unknown'))[:50]}...")
                        elif isinstance(data, dict):
                            print(f"   📋 Response keys: {list(data.keys())}")
                    else:
                        text = await response.text()
                        print(f"   ❌ Error: {text[:100]}...")
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        # Test 2: Auction Summary API
        print("\n2. 📊 Testing Auction Summary API")
        summary_endpoints = [
            "https://api.macdiscount.com/auctionsummary?pg=1&ppg=20",
            "https://api.macdiscount.com/auctionsummary?pg=1&ppg=10"
        ]
        
        for endpoint in summary_endpoints:
            print(f"   Testing: {endpoint}")
            try:
                async with session.get(endpoint, headers=headers, timeout=15) as response:
                    print(f"   Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, dict):
                            if 'data' in data:
                                items = data['data']
                                print(f"   ✅ SUCCESS! Found {len(items)} auction summaries")
                                if items:
                                    sample = items[0]
                                    print(f"   📦 Sample: {sample.get('title', 'Unknown')[:50]}...")
                                    print(f"   🏢 Location: {sample.get('location', 'Unknown')}")
                            else:
                                print(f"   📋 Response keys: {list(data.keys())}")
                        elif isinstance(data, list):
                            print(f"   ✅ SUCCESS! Found {len(data)} auction summaries")
                    else:
                        text = await response.text()
                        print(f"   ❌ Error: {text[:100]}...")
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        # Test 3: Turbo Clock Auctions
        print("\n3. ⚡ Testing Turbo Clock Auctions API")
        turbo_endpoint = "https://api.macdiscount.com/turbo-clock-auctions"
        print(f"   Testing: {turbo_endpoint}")
        
        try:
            async with session.get(turbo_endpoint, headers=headers, timeout=15) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    if isinstance(data, list):
                        print(f"   ✅ SUCCESS! Found {len(data)} turbo auctions")
                    elif isinstance(data, dict):
                        print(f"   📋 Response keys: {list(data.keys())}")
                else:
                    text = await response.text()
                    print(f"   ❌ Error: {text[:100]}...")
        except Exception as e:
            print(f"   ❌ Exception: {e}")
        
        # Test 4: Personal APIs (if we have customer_id and JWT)
        if customer_id and jwt_token:
            print(f"\n4. 👤 Testing Personal APIs (Customer ID: {customer_id})")
            
            # Add JWT token to headers for personal endpoints
            auth_headers = headers.copy()
            auth_headers['authorization'] = jwt_token
            auth_headers['content-type'] = 'application/json'
            auth_headers['origin'] = 'https://www.mac.bid'
            auth_headers['referer'] = 'https://www.mac.bid/'
            
            personal_endpoints = [
                f"https://api.macdiscount.com/auctions/customer/{customer_id}/active-auctions",
                f"https://api.macdiscount.com/auctions/customer/{customer_id}/auction-alerts",
                f"https://api.macdiscount.com/user/{customer_id}/getAlertsAndKeywordsHitsForCustomer?loc=17,18&pg=1&ppg=25"
            ]
            
            for endpoint in personal_endpoints:
                endpoint_name = endpoint.split('/')[-1].split('?')[0]
                print(f"   Testing {endpoint_name}: {endpoint}")
                try:
                    async with session.get(endpoint, headers=auth_headers, timeout=15) as response:
                        print(f"   Status: {response.status}")
                        if response.status == 200:
                            data = await response.json()
                            if isinstance(data, list):
                                print(f"   ✅ SUCCESS! Found {len(data)} items")
                            elif isinstance(data, dict):
                                print(f"   📋 Response keys: {list(data.keys())}")
                        else:
                            text = await response.text()
                            print(f"   ❌ Error: {text[:100]}...")
                except Exception as e:
                    print(f"   ❌ Exception: {e}")
        else:
            print("\n4. ⚠️ Skipping Personal APIs (no customer_id or JWT token)")
        
        # Test 5: Alternative auction endpoints
        print("\n5. 🎯 Testing Alternative Auction Endpoints")
        alt_endpoints = [
            "https://api.macdiscount.com/auction/getAuctions?pg=1&ppg=20",
            "https://api.macdiscount.com/auction/search?q=&pg=1&ppg=20",
            "https://api.macdiscount.com/auction/getMyBids?pg=1&ppg=25"
        ]
        
        for endpoint in alt_endpoints:
            endpoint_name = endpoint.split('/')[-1].split('?')[0]
            print(f"   Testing {endpoint_name}: {endpoint}")
            
            # Try with different header combinations
            header_variants = [
                headers,  # Basic headers
                {**headers, 'authorization': jwt_token} if jwt_token else headers,  # With JWT
            ]
            
            success = False
            for i, test_headers in enumerate(header_variants):
                if success:
                    break
                try:
                    async with session.get(endpoint, headers=test_headers, timeout=15) as response:
                        print(f"   Status: {response.status} (headers variant {i+1})")
                        if response.status == 200:
                            data = await response.json()
                            if isinstance(data, dict) and 'auctionItems' in data:
                                items = data['auctionItems']
                                print(f"   ✅ SUCCESS! Found {len(items)} auction items")
                                success = True
                            elif isinstance(data, list):
                                print(f"   ✅ SUCCESS! Found {len(data)} items")
                                success = True
                            elif isinstance(data, dict):
                                print(f"   📋 Response keys: {list(data.keys())}")
                        else:
                            text = await response.text()
                            print(f"   ❌ Error: {text[:100]}...")
                except Exception as e:
                    print(f"   ❌ Exception: {e}")
            
            if not success:
                print(f"   ❌ All header variants failed for {endpoint_name}")
        
        # Test 6: Location-specific search
        print("\n6. 🏢 Testing Location-Specific Search")
        location_searches = [
            "https://api.macdiscount.com/search?q=&location=Rock%20Hill&limit=10",
            "https://api.macdiscount.com/search?q=&location=Greenville&limit=10",
            "https://api.macdiscount.com/search?q=electronics&location=Rock%20Hill&limit=10"
        ]
        
        for endpoint in location_searches:
            location = endpoint.split('location=')[1].split('&')[0].replace('%20', ' ')
            print(f"   Testing {location}: {endpoint}")
            try:
                async with session.get(endpoint, headers=headers, timeout=15) as response:
                    print(f"   Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            print(f"   ✅ SUCCESS! Found {len(data)} items for {location}")
                        elif isinstance(data, dict):
                            print(f"   📋 Response keys: {list(data.keys())}")
                    else:
                        text = await response.text()
                        print(f"   ❌ Error: {text[:100]}...")
            except Exception as e:
                print(f"   ❌ Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_alternative_apis()) 