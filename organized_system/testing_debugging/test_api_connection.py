#!/usr/bin/env python3
"""
Test API connectivity
"""

import asyncio
import aiohttp
import ssl

async def test_api():
    """Test basic API connectivity."""
    print("🔍 Testing Mac.bid API connectivity...")
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    test_urls = [
        "https://api.macdiscount.com/search?q=Apple&limit=10",
        "https://api.macdiscount.com/search?q=electronics&limit=10",
        "https://api.macdiscount.com/turbo-auctions?customer_id=2710619",
        "https://api.macdiscount.com/watchlist?customer_id=2710619"
    ]
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=ssl_context),
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=30)
    ) as session:
        
        for url in test_urls:
            try:
                print(f"\n📡 Testing: {url}")
                async with session.get(url) as response:
                    print(f"   Status: {response.status}")
                    if response.status == 200:
                        data = await response.json()
                        print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        if 'lots' in data:
                            print(f"   Lots found: {len(data['lots'])}")
                        elif 'auctions' in data:
                            print(f"   Auctions found: {len(data['auctions'])}")
                    else:
                        text = await response.text()
                        print(f"   Error: {text[:200]}")
                        
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(test_api()) 