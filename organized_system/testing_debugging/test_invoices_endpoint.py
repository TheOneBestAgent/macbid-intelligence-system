#!/usr/bin/env python3
"""
🧪 Test Invoices Endpoint Access
Quick test to see if we can access the invoices endpoint
"""

import asyncio
import aiohttp
import json
import os

async def test_invoices_endpoint():
    """Test access to the invoices endpoint."""
    print("🧪 TESTING INVOICES ENDPOINT ACCESS")
    print("=" * 50)
    
    # Load credentials
    credentials_file = os.path.expanduser("~/.macbid_scraper/credentials.json")
    try:
        with open(credentials_file, 'r') as f:
            creds = json.load(f)
            customer_id = creds.get('customer_id')
            username = creds.get('username')
    except:
        print("❌ No credentials found!")
        return
    
    print(f"👤 Customer ID: {customer_id}")
    print(f"📧 Username: {username}")
    
    # Test endpoint
    url = f"https://api.macdiscount.com/user/{customer_id}/invoices-items?pg=1&ppg=30"
    print(f"\n🔍 Testing: {url}")
    
    # Try different authentication approaches
    test_cases = [
        {
            'name': 'No Authentication',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        },
        {
            'name': 'Basic Browser Headers',
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.mac.bid/',
                'Origin': 'https://www.mac.bid'
            }
        }
    ]
    
    connector = aiohttp.TCPConnector(ssl=False)
    session = aiohttp.ClientSession(connector=connector)
    
    try:
        for test_case in test_cases:
            print(f"\n🔍 Testing: {test_case['name']}")
            
            try:
                async with session.get(url, headers=test_case['headers'], timeout=10) as response:
                    print(f"   Status: {response.status}")
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            if data:
                                print(f"   ✅ SUCCESS! Got data")
                                if isinstance(data, list):
                                    print(f"   📊 Items: {len(data)}")
                                    if len(data) > 0:
                                        sample = data[0]
                                        if isinstance(sample, dict):
                                            print(f"   📋 Sample keys: {list(sample.keys())[:5]}")
                                elif isinstance(data, dict):
                                    print(f"   📋 Response keys: {list(data.keys())[:5]}")
                                
                                # Show first few items
                                print(f"   📄 Sample data: {str(data)[:200]}...")
                            else:
                                print(f"   ⚠️ Empty response")
                        except Exception as e:
                            text = await response.text()
                            print(f"   ⚠️ Invalid JSON: {text[:100]}...")
                    elif response.status == 401:
                        print(f"   ❌ Unauthorized - Need authentication")
                    elif response.status == 403:
                        print(f"   ❌ Forbidden - Access denied")
                    else:
                        text = await response.text()
                        print(f"   ⚠️ Response: {text[:100]}...")
            
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    finally:
        await session.close()
    
    print("\n💡 NEXT STEPS:")
    print("If you see 401/403 errors, you need to:")
    print("1. Open mac.bid in your browser")
    print("2. Log in to your account")
    print("3. Open Developer Tools (F12)")
    print("4. Go to Network tab")
    print("5. Navigate to a page that loads your invoice/bid data")
    print("6. Find the API call to this endpoint")
    print("7. Copy it as cURL and run capture_browser_tokens.py")

if __name__ == "__main__":
    asyncio.run(test_invoices_endpoint()) 