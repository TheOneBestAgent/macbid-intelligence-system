#!/usr/bin/env python3
"""
🔍 Test Personal Auction History Access
Test access to your personal mac.bid auction data using your customer ID
"""

import asyncio
import aiohttp
import ssl
import json
from pathlib import Path

async def test_personal_endpoints():
    """Test access to personal auction history endpoints."""
    print("🔍 Testing Personal Auction History Access")
    print("=" * 50)
    
    # Load credentials
    config_file = Path.home() / '.macbid_scraper' / 'credentials.json'
    with open(config_file, 'r') as f:
        creds = json.load(f)
    
    customer_id = creds.get('customer_id')
    print(f"📧 Account: {creds['username']}")
    print(f"🆔 Customer ID: {customer_id}")
    print()
    
    # Personal endpoints to test
    endpoints = {
        'Active Auctions': f'https://api.macdiscount.com/auctions/customer/{customer_id}/active-auctions',
        'Auction Alerts': f'https://api.macdiscount.com/auctions/customer/{customer_id}/auction-alerts',
        'User Alerts': f'https://api.macdiscount.com/user/{customer_id}/getAlertsAndKeywordsHitsForCustomer?loc=17,18&pg=1&ppg=25',
        'Customer Profile': f'https://api.macdiscount.com/customer/{customer_id}/profile',
        'Bidding History': f'https://api.macdiscount.com/customer/{customer_id}/bids',
        'Watchlist': f'https://api.macdiscount.com/customer/{customer_id}/watchlist'
    }
    
    # Setup HTTP session
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context, limit=10)
    timeout = aiohttp.ClientTimeout(total=30)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://mac.bid'
    }
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers=headers
    ) as session:
        
        print("🔍 Testing Personal Endpoints...")
        print("-" * 40)
        
        for name, url in endpoints.items():
            try:
                print(f"📡 Testing {name}...")
                async with session.get(url) as response:
                    status = response.status
                    
                    if status == 200:
                        try:
                            data = await response.json()
                            if isinstance(data, dict):
                                item_count = len(data.get('hits', data.get('data', data.get('items', []))))
                            elif isinstance(data, list):
                                item_count = len(data)
                            else:
                                item_count = "Unknown"
                            
                            print(f"   ✅ {name}: {item_count} items")
                            
                            # Show sample data structure
                            if isinstance(data, dict) and data:
                                keys = list(data.keys())[:5]
                                print(f"      📋 Keys: {keys}")
                            elif isinstance(data, list) and data:
                                if isinstance(data[0], dict):
                                    keys = list(data[0].keys())[:5]
                                    print(f"      📋 Item keys: {keys}")
                                    
                        except Exception as e:
                            print(f"   ✅ {name}: Response received (JSON parse error)")
                            
                    elif status == 401:
                        print(f"   🔒 {name}: Authentication required")
                    elif status == 403:
                        print(f"   ❌ {name}: Access forbidden")
                    elif status == 404:
                        print(f"   ⚠️ {name}: Endpoint not found")
                    else:
                        print(f"   ⚠️ {name}: Status {status}")
                        
            except Exception as e:
                print(f"   ❌ {name}: Error - {e}")
            
            await asyncio.sleep(0.5)  # Rate limiting
        
        print("\n🔍 Testing with Authentication...")
        print("-" * 40)
        
        # Try to get session cookies first
        try:
            from personal_unified_system import PersonalUnifiedSystem
            
            system = PersonalUnifiedSystem()
            await system.initialize_system(authenticate=True)
            
            if system.session_cookies:
                print(f"   ✅ Got {len(system.session_cookies)} session cookies")
                
                # Test with cookies
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout,
                    headers=headers,
                    cookies=system.session_cookies
                ) as auth_session:
                    
                    for name, url in list(endpoints.items())[:3]:  # Test first 3 with auth
                        try:
                            print(f"🔐 Testing {name} with auth...")
                            async with auth_session.get(url) as response:
                                status = response.status
                                
                                if status == 200:
                                    try:
                                        data = await response.json()
                                        if isinstance(data, dict):
                                            item_count = len(data.get('hits', data.get('data', data.get('items', []))))
                                        elif isinstance(data, list):
                                            item_count = len(data)
                                        else:
                                            item_count = "Unknown"
                                        
                                        print(f"   ✅ {name}: {item_count} items (authenticated)")
                                        
                                        # Save sample data for analysis
                                        if data:
                                            filename = f"personal_{name.lower().replace(' ', '_')}_sample.json"
                                            with open(filename, 'w') as f:
                                                json.dump(data, f, indent=2)
                                            print(f"      💾 Sample saved to {filename}")
                                            
                                    except Exception as e:
                                        print(f"   ✅ {name}: Response received (authenticated)")
                                        
                                else:
                                    print(f"   ⚠️ {name}: Status {status} (authenticated)")
                                    
                        except Exception as e:
                            print(f"   ❌ {name}: Error with auth - {e}")
                        
                        await asyncio.sleep(0.5)
            else:
                print("   ⚠️ No session cookies available")
                
        except Exception as e:
            print(f"   ❌ Authentication error: {e}")

if __name__ == "__main__":
    asyncio.run(test_personal_endpoints()) 