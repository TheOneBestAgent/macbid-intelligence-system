#!/usr/bin/env python3
"""
🎧 Quick Headphone Finder for mac.bid
Searches current auctions for headphones in your SC locations
"""

import asyncio
import aiohttp
import ssl
import json
import re
from datetime import datetime

async def find_headphones(location_ids=None):
    """Find headphones in current auctions."""
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        print("🎧 Searching for Headphones in Your SC Locations")
        print("=" * 60)
        
        headphone_keywords = [
            'headphone', 'headphones', 'earphone', 'earphones', 'earbud', 'earbuds',
            'beats', 'airpods', 'sony', 'bose', 'sennheiser', 'audio-technica',
            'wireless headset', 'bluetooth headset', 'gaming headset'
        ]
        
        found_headphones = []
        
        # Search through multiple pages
        for page in range(1, 11):  # Check first 10 pages
            url = f"https://api.macdiscount.com/auctionsummary?pg={page}&ppg=20"
            
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        auctions = data.get('data', [])
                        
                        for auction in auctions:
                            title = auction.get('title', auction.get('external_folder_name', ''))
                            location_id = auction.get('location_id')
                            location_name = auction.get('location_name', '')
                            auction_number = auction.get('auction_number', '')
                            closing_date = auction.get('closing_date', '')
                            
                            # Filter by SC locations if specified
                            if location_ids and location_id not in location_ids:
                                continue
                                
                            # Check if title contains headphone keywords
                            if title and any(keyword.lower() in title.lower() for keyword in headphone_keywords):
                                found_headphones.append({
                                    'title': title,
                                    'auction_number': auction_number,
                                    'location_id': location_id,
                                    'location_name': location_name,
                                    'closing_date': closing_date
                                })
                                
                        print(f"📄 Searched page {page}: {len(auctions)} auctions")
                        
                    else:
                        print(f"⚠️  Page {page}: Status {response.status}")
                        
            except Exception as e:
                print(f"❌ Error on page {page}: {e}")
                
        # Display results
        if found_headphones:
            print(f"\n🎧 Found {len(found_headphones)} Headphone Auctions!")
            print("=" * 60)
            
            # Group by location
            by_location = {}
            for item in found_headphones:
                loc = item['location_name'] or f"Location {item['location_id']}"
                if loc not in by_location:
                    by_location[loc] = []
                by_location[loc].append(item)
                
            for location, items in by_location.items():
                print(f"\n📍 {location} ({len(items)} items):")
                print("-" * 40)
                
                for item in items:
                    print(f"🎧 {item['title']}")
                    print(f"   📋 Auction: {item['auction_number']}")
                    if item['closing_date']:
                        try:
                            closing_dt = datetime.fromisoformat(item['closing_date'].replace('Z', '+00:00'))
                            print(f"   ⏰ Closes: {closing_dt.strftime('%Y-%m-%d %H:%M')}")
                        except:
                            print(f"   ⏰ Closes: {item['closing_date']}")
                    print()
                    
        else:
            print("\n❌ No headphones found in current auctions")
            print("💡 Try checking again later or expanding your search locations")
            
        return found_headphones

async def main():
    # Your SC location IDs
    sc_locations = [17, 20, 28, 34, 36]
    
    print("🏛️  Searching in your SC locations:")
    print("   17: Spartanburg")
    print("   20: Greenville ⭐")
    print("   28: Rock Hill")
    print("   34: Gastonia ⭐")
    print("   36: Anderson")
    print()
    
    headphones = await find_headphones(sc_locations)
    
    if headphones:
        print(f"\n✅ Search complete! Found {len(headphones)} headphone auctions")
        print("💡 Tip: Set up alerts with: python3 price_tracker.py --add-alert 'headphones' 50 '17,20,28,34,36'")
    else:
        print("\n🔍 No headphones found right now, but your alert is active!")
        print("💡 You'll be notified when headphones under $100 appear")

if __name__ == "__main__":
    asyncio.run(main()) 