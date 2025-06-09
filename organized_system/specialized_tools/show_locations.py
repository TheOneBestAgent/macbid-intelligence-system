#!/usr/bin/env python3
"""
Show all available mac.bid warehouse locations
"""

import asyncio
import aiohttp
import ssl
from collections import Counter

async def show_locations():
    """Fetch and display all available warehouse locations."""
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        print("🏢 mac.bid Warehouse Locations")
        print("=" * 50)
        
        all_locations = Counter()
        
        # Check first 5 pages to get a good sample
        for page in range(1, 6):
            url = f"https://api.macdiscount.com/auctionsummary?pg={page}&ppg=20"
            
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        auctions = data.get('data', [])
                        
                        for auction in auctions:
                            location_id = auction.get('location_id')
                            if location_id is not None:
                                all_locations[location_id] += 1
                        
                        print(f"📄 Scanned page {page}: {len(auctions)} auctions")
                        
                    else:
                        print(f"❌ Page {page}: API returned status {response.status}")
                        
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
        
        print(f"\n📊 Found {len(all_locations)} unique warehouse locations:")
        print("-" * 50)
        
        # Sort by location ID
        for location_id in sorted(all_locations.keys()):
            count = all_locations[location_id]
            print(f"📍 Location {location_id:2d}: {count:2d} active auctions")
        
        print(f"\n💡 Usage Examples:")
        print(f"   # Monitor just a few locations:")
        print(f"   python3 simple_monitor.py 1,6,13,16,25")
        print(f"   ")
        print(f"   # Monitor single location:")
        print(f"   python3 simple_monitor.py 25")
        print(f"   ")
        print(f"   # Interactive setup:")
        print(f"   python3 simple_monitor.py")
        
        # Show top locations by activity
        print(f"\n🔥 Most Active Locations:")
        top_locations = all_locations.most_common(10)
        for location_id, count in top_locations:
            print(f"   📍 Location {location_id}: {count} auctions")

async def main():
    await show_locations()

if __name__ == "__main__":
    asyncio.run(main()) 