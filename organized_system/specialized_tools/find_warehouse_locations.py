#!/usr/bin/env python3
"""
Find actual warehouse locations for mac.bid location IDs
"""

import asyncio
import aiohttp
import ssl
import json
from collections import defaultdict

async def explore_warehouse_locations():
    """Try to find actual warehouse location data."""
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        print("🗺️  Exploring mac.bid Warehouse Locations")
        print("=" * 60)
        
        # First, let's try some common API endpoints that might have location data
        location_endpoints = [
            "https://api.macdiscount.com/locations",
            "https://api.macdiscount.com/warehouses", 
            "https://api.macdiscount.com/sites",
            "https://api.macdiscount.com/pickup-locations",
            "https://api.macdiscount.com/facilities"
        ]
        
        print("🔍 Checking for location API endpoints...")
        for endpoint in location_endpoints:
            try:
                async with session.get(endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Found data at {endpoint}")
                        print(f"   Response keys: {list(data.keys()) if isinstance(data, dict) else 'List with ' + str(len(data)) + ' items'}")
                        
                        # Save the data for inspection
                        filename = endpoint.split('/')[-1] + '_data.json'
                        with open(filename, 'w') as f:
                            json.dump(data, f, indent=2, default=str)
                        print(f"   💾 Saved to: {filename}")
                        
                    elif response.status == 401:
                        print(f"🔒 {endpoint}: Requires authentication")
                    elif response.status == 404:
                        print(f"❌ {endpoint}: Not found")
                    else:
                        print(f"⚠️  {endpoint}: Status {response.status}")
            except Exception as e:
                print(f"❌ {endpoint}: Error - {str(e)[:50]}")
        
        print(f"\n🔍 Analyzing auction data for location clues...")
        
        # Collect detailed auction data to look for location hints
        location_data = defaultdict(list)
        sample_auctions = {}
        
        for page in range(1, 4):  # Check first 3 pages
            url = f"https://api.macdiscount.com/auctionsummary?pg={page}&ppg=20"
            
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        auctions = data.get('data', [])
                        
                        for auction in auctions:
                            location_id = auction.get('location_id')
                            if location_id is not None:
                                location_data[location_id].append(auction)
                                
                                # Keep one sample auction per location for analysis
                                if location_id not in sample_auctions:
                                    sample_auctions[location_id] = auction
                        
                        print(f"📄 Analyzed page {page}: {len(auctions)} auctions")
                        
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
        
        print(f"\n📊 Location Analysis Results:")
        print("-" * 50)
        
        # Look for location clues in auction data
        for location_id in sorted(location_data.keys()):
            auctions = location_data[location_id]
            sample = sample_auctions[location_id]
            
            print(f"\n📍 Location {location_id} ({len(auctions)} auctions):")
            
            # Look for location hints in various fields
            location_hints = []
            
            # Check auction number patterns (might contain location codes)
            auction_numbers = [a.get('auction_number', '') for a in auctions[:3]]
            if auction_numbers:
                print(f"   🔢 Sample auction numbers: {', '.join(auction_numbers)}")
                
                # Extract potential location codes from auction numbers
                codes = set()
                for num in auction_numbers:
                    if num:
                        # Look for letter patterns that might be location codes
                        parts = num.split('-')[0] if '-' in num else num
                        if len(parts) >= 2:
                            code = ''.join([c for c in parts if c.isalpha()])
                            if code:
                                codes.add(code)
                
                if codes:
                    print(f"   🏷️  Potential location codes: {', '.join(codes)}")
            
            # Check for any address or location fields
            location_fields = ['address', 'city', 'state', 'zip', 'location_name', 'warehouse', 'facility']
            for field in location_fields:
                if field in sample and sample[field]:
                    print(f"   📍 {field}: {sample[field]}")
            
            # Show all available fields for the first few locations
            if location_id <= 3:
                print(f"   📋 All fields: {list(sample.keys())}")
        
        # Try to get individual auction details (might have more location info)
        print(f"\n🔍 Checking individual auction details for location data...")
        
        # Pick a few sample auctions to get detailed info
        sample_auction_ids = []
        for location_id in sorted(location_data.keys())[:5]:  # First 5 locations
            if location_data[location_id]:
                auction_id = location_data[location_id][0].get('id')
                if auction_id:
                    sample_auction_ids.append((location_id, auction_id))
        
        for location_id, auction_id in sample_auction_ids:
            detail_url = f"https://api.macdiscount.com/auction/{auction_id}"
            try:
                async with session.get(detail_url) as response:
                    if response.status == 200:
                        detail_data = await response.json()
                        print(f"✅ Location {location_id} auction {auction_id} details:")
                        
                        # Look for location-specific fields
                        location_fields = ['pickup_address', 'warehouse_address', 'location_name', 
                                         'pickup_location', 'facility_address', 'site_address']
                        found_location_info = False
                        
                        for field in location_fields:
                            if field in detail_data and detail_data[field]:
                                print(f"   📍 {field}: {detail_data[field]}")
                                found_location_info = True
                        
                        if not found_location_info:
                            print(f"   📋 Available fields: {list(detail_data.keys())[:10]}...")
                        
                    elif response.status == 401:
                        print(f"🔒 Auction {auction_id}: Requires authentication")
                    else:
                        print(f"⚠️  Auction {auction_id}: Status {response.status}")
                        
            except Exception as e:
                print(f"❌ Error getting auction {auction_id} details: {str(e)[:50]}")
        
        # Save all location data for manual inspection
        with open('location_analysis.json', 'w') as f:
            # Convert defaultdict to regular dict for JSON serialization
            regular_dict = {str(k): v for k, v in location_data.items()}
            json.dump(regular_dict, f, indent=2, default=str)
        
        print(f"\n💾 Complete location analysis saved to: location_analysis.json")
        
        # Try to find location mapping from the main website
        print(f"\n🌐 Checking main website for location information...")
        
        website_urls = [
            "https://www.mac.bid/locations",
            "https://www.mac.bid/warehouses",
            "https://www.mac.bid/pickup-locations",
            "https://mac.bid/locations",
            "https://mac.bid/warehouses"
        ]
        
        for url in website_urls:
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        print(f"✅ Found page: {url}")
                        
                        # Save HTML for manual inspection
                        filename = url.split('/')[-1] + '_page.html'
                        with open(filename, 'w') as f:
                            f.write(content)
                        print(f"   💾 Saved HTML to: {filename}")
                        
                        # Look for location patterns in the HTML
                        if 'location' in content.lower() or 'warehouse' in content.lower():
                            print(f"   🎯 Contains location/warehouse information")
                        
                    else:
                        print(f"❌ {url}: Status {response.status}")
                        
            except Exception as e:
                print(f"❌ {url}: Error - {str(e)[:50]}")

async def main():
    await explore_warehouse_locations()

if __name__ == "__main__":
    asyncio.run(main()) 