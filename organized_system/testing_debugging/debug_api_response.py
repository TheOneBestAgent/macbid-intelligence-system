#!/usr/bin/env python3
"""
Debug API response structure
"""

import asyncio
import aiohttp
import ssl
import json

async def debug_api():
    """Debug API response structure."""
    print("🔍 Debugging Mac.bid API response structure...")
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    
    url = "https://api.macdiscount.com/search?q=Apple&limit=5"
    
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(ssl=ssl_context),
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=30)
    ) as session:
        
        try:
            print(f"\n📡 Testing: {url}")
            async with session.get(url) as response:
                print(f"   Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    print(f"\n📄 Full Response Structure:")
                    print(json.dumps(data, indent=2)[:2000])  # First 2000 chars
                    
                    if 'hits' in data:
                        hits = data['hits']
                        print(f"\n📦 Found {len(hits)} hits")
                        
                        if hits:
                            first_hit = hits[0]
                            print(f"\n🔍 First hit structure:")
                            print(json.dumps(first_hit, indent=2)[:1000])
                            
                            # Check for location info
                            location_fields = [k for k in first_hit.keys() if 'location' in k.lower()]
                            print(f"\n📍 Location fields: {location_fields}")
                            
                            for field in location_fields:
                                print(f"   {field}: {first_hit.get(field)}")
                                
                else:
                    text = await response.text()
                    print(f"   Error: {text}")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_api()) 