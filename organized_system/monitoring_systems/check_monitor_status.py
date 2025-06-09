#!/usr/bin/env python3
"""
Check what auctions are currently being tracked
"""

import asyncio
import aiohttp
import json
import ssl
from datetime import datetime

async def fetch_current_auctions():
    """Fetch and display current auctions from mac.bid API."""
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        print("🔍 Fetching current auctions from mac.bid...")
        print("=" * 60)
        
        all_auctions = []
        
        # Check first 3 pages
        for page in range(1, 4):
            url = f"https://api.macdiscount.com/auctionsummary?pg={page}&ppg=20"
            
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        auctions = data.get('data', [])
                        
                        print(f"\n📄 PAGE {page} - {len(auctions)} auctions:")
                        print("-" * 40)
                        
                        for i, auction in enumerate(auctions, 1):
                            auction_id = auction.get('id', 'N/A')
                            auction_number = auction.get('auction_number', 'N/A')
                            title = auction.get('external_folder_name', 'No title')
                            closing_date = auction.get('closing_date', 'N/A')
                            location_id = auction.get('location_id', 'N/A')
                            
                            # Parse closing date for better display
                            try:
                                if closing_date != 'N/A':
                                    closing_dt = datetime.fromisoformat(closing_date.replace('Z', '+00:00'))
                                    closing_display = closing_dt.strftime('%m/%d %H:%M')
                                else:
                                    closing_display = 'N/A'
                            except:
                                closing_display = closing_date
                            
                            print(f"  {i:2d}. 🆔 {auction_id} | 🔢 {auction_number}")
                            print(f"      📝 {title}")
                            print(f"      📅 Closes: {closing_display} | 📍 Location: {location_id}")
                            
                            all_auctions.append(auction)
                        
                    else:
                        print(f"❌ Page {page}: API returned status {response.status}")
                        
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total auctions tracked: {len(all_auctions)}")
        
        # Show some statistics
        if all_auctions:
            locations = {}
            closing_soon = []
            
            for auction in all_auctions:
                # Count by location
                loc = auction.get('location_id', 'Unknown')
                locations[loc] = locations.get(loc, 0) + 1
                
                # Check if closing soon (within 24 hours)
                closing_date = auction.get('closing_date')
                if closing_date:
                    try:
                        closing_dt = datetime.fromisoformat(closing_date.replace('Z', '+00:00'))
                        hours_until_close = (closing_dt - datetime.now().replace(tzinfo=closing_dt.tzinfo)).total_seconds() / 3600
                        if 0 < hours_until_close < 24:
                            closing_soon.append({
                                'auction_number': auction.get('auction_number'),
                                'title': auction.get('external_folder_name', 'No title'),
                                'hours': hours_until_close
                            })
                    except:
                        pass
            
            print(f"\n📍 LOCATIONS:")
            for loc, count in sorted(locations.items()):
                print(f"   Location {loc}: {count} auctions")
            
            if closing_soon:
                print(f"\n⏰ CLOSING SOON (within 24 hours):")
                for auction in sorted(closing_soon, key=lambda x: x['hours']):
                    hours = auction['hours']
                    print(f"   🔥 {auction['auction_number']} - {auction['title'][:50]} ({hours:.1f}h)")
            
            # Save detailed data
            with open('current_auctions.json', 'w') as f:
                json.dump(all_auctions, f, indent=2, default=str)
            print(f"\n💾 Detailed data saved to: current_auctions.json")

async def main():
    await fetch_current_auctions()

if __name__ == "__main__":
    asyncio.run(main()) 