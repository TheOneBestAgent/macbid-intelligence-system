#!/usr/bin/env python3
"""
Complete mac.bid Warehouse Locations Guide
Shows all warehouse locations with addresses, organized by region
"""

import json
import asyncio
import aiohttp
import ssl
from collections import defaultdict

# Load the locations data
def load_locations():
    """Load and organize warehouse location data."""
    try:
        with open('locations_data.json', 'r') as f:
            locations = json.load(f)
        return locations
    except FileNotFoundError:
        print("❌ locations_data.json not found. Run find_warehouse_locations.py first.")
        return []

def organize_by_state(locations):
    """Organize locations by state."""
    by_state = defaultdict(list)
    
    for loc in locations:
        city_state = loc.get('city_state', '')
        if ', ' in city_state:
            state = city_state.split(', ')[-1]
            by_state[state].append(loc)
    
    return dict(by_state)

def show_warehouse_guide():
    """Display comprehensive warehouse location guide."""
    locations = load_locations()
    
    if not locations:
        return
    
    print("🏢 Complete mac.bid Warehouse Locations Guide")
    print("=" * 70)
    
    # Organize by state
    by_state = organize_by_state(locations)
    
    # Show summary first
    print(f"📊 SUMMARY: {len(locations)} warehouse locations across {len(by_state)} states")
    print()
    
    # Show by state
    for state in sorted(by_state.keys()):
        state_locations = by_state[state]
        print(f"🏛️  {state} ({len(state_locations)} locations)")
        print("-" * 50)
        
        for loc in sorted(state_locations, key=lambda x: x['name']):
            location_id = loc['id']
            name = loc['name']
            address = loc['address']
            city_state = loc['city_state']
            zip_code = loc['zip_code']
            code = loc.get('code', 'N/A')
            
            print(f"📍 Location {location_id:2d}: {name}")
            print(f"   🏠 {address}")
            print(f"   📮 {city_state} {zip_code}")
            print(f"   🏷️  Code: {code}")
            
            # Show hours if available
            hours = loc.get('hours', '')
            if hours and 'Monday' in hours:
                # Clean up hours display
                clean_hours = hours.replace('<br>', ' | ').replace('<br/>', ' | ').replace('\r\n', ' ')
                clean_hours = clean_hours.split('<strong>')[0].strip()  # Remove license info
                if clean_hours:
                    print(f"   ⏰ {clean_hours}")
            
            # Show transfer destinations
            transfers = loc.get('transfer_destinations', '')
            if transfers:
                print(f"   🚚 Can transfer to locations: {transfers}")
            
            print()
        
        print()
    
    # Show most active locations
    print("🔥 MOST ACTIVE LOCATIONS (good for monitoring):")
    print("-" * 50)
    
    # These are based on our earlier analysis
    active_locations = [1, 13, 16, 20, 23, 25, 28, 85]
    
    for loc_id in active_locations:
        loc = next((l for l in locations if l['id'] == loc_id), None)
        if loc:
            print(f"📍 Location {loc_id:2d}: {loc['name']} - {loc['city_state']}")
    
    print()
    
    # Show regional groupings
    print("🗺️  REGIONAL GROUPINGS:")
    print("-" * 50)
    
    regions = {
        "Pennsylvania": ["Washington", "Butler", "Beaver Falls", "Pittsburgh", "Tarentum", "Uniontown"],
        "Ohio": ["Boardman", "Warren", "Akron", "Canton"],
        "South Carolina": ["Cowpens", "Greenville", "Rock Hill", "Gastonia", "Anderson"],
        "Texas": ["Schertz", "San Antonio"],
        "Arizona": ["Phoenix", "Mesa"],
        "Nevada": ["North Las Vegas", "Henderson"],
        "Tennessee": ["Jackson"],
        "Iowa": ["Davenport"],
        "West Virginia": ["Bridgeport"]
    }
    
    for region, cities in regions.items():
        region_locs = []
        for loc in locations:
            city = loc['city_state'].split(',')[0].strip()
            if city in cities:
                region_locs.append(loc)
        
        if region_locs:
            print(f"🏛️  {region}: {len(region_locs)} locations")
            for loc in sorted(region_locs, key=lambda x: x['name']):
                print(f"   📍 {loc['id']:2d}: {loc['name']} ({loc['city_state']})")
            print()

def show_location_picker():
    """Interactive location picker for monitoring."""
    locations = load_locations()
    
    if not locations:
        return
    
    print("🎯 Location Picker for Monitoring")
    print("=" * 40)
    print("Pick your preferred warehouse locations for monitoring:")
    print()
    
    by_state = organize_by_state(locations)
    
    for state in sorted(by_state.keys()):
        print(f"🏛️  {state}:")
        state_locations = by_state[state]
        
        for loc in sorted(state_locations, key=lambda x: x['name']):
            location_id = loc['id']
            name = loc['name']
            city = loc['city_state'].split(',')[0]
            print(f"   {location_id:2d}: {name} ({city})")
        print()
    
    print("💡 Usage Examples:")
    print("   # Pennsylvania locations only:")
    print("   python3 simple_monitor.py 1,6,12,13,15,16,23,25")
    print()
    print("   # Ohio locations only:")
    print("   python3 simple_monitor.py 16,18,19,44,85")
    print()
    print("   # Most active locations:")
    print("   python3 simple_monitor.py 1,13,16,20,23,25,28,85")
    print()
    print("   # Single state examples:")
    print("   python3 simple_monitor.py 17,20,28,34,35,36,38  # South Carolina")
    print("   python3 simple_monitor.py 49,50,51,60,61        # Texas")

async def check_current_activity():
    """Check which locations currently have active auctions."""
    print("🔍 Checking Current Auction Activity by Location")
    print("=" * 60)
    
    # Create SSL context
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=30)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        location_activity = defaultdict(int)
        
        # Check first 5 pages
        for page in range(1, 6):
            url = f"https://api.macdiscount.com/auctionsummary?pg={page}&ppg=20"
            
            try:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        auctions = data.get('data', [])
                        
                        for auction in auctions:
                            location_id = auction.get('location_id')
                            if location_id:
                                location_activity[location_id] += 1
                        
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
        
        # Load location names
        locations = load_locations()
        location_names = {loc['id']: loc['name'] for loc in locations}
        
        print("📊 Current Activity (Active Auctions by Location):")
        print("-" * 50)
        
        # Sort by activity level
        sorted_activity = sorted(location_activity.items(), key=lambda x: x[1], reverse=True)
        
        for location_id, count in sorted_activity:
            name = location_names.get(location_id, f"Location {location_id}")
            print(f"📍 {location_id:2d}: {name:<25} - {count:2d} active auctions")
        
        # Show recommendations
        print(f"\n🎯 RECOMMENDATIONS:")
        print("-" * 30)
        
        top_locations = [loc_id for loc_id, count in sorted_activity[:10] if count >= 2]
        if top_locations:
            location_list = ','.join(map(str, top_locations))
            print(f"🔥 Most active locations: {location_list}")
            print(f"   Command: python3 simple_monitor.py {location_list}")

def main():
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--picker':
            show_location_picker()
        elif sys.argv[1] == '--activity':
            asyncio.run(check_current_activity())
        elif sys.argv[1] == '--help':
            print("🏢 mac.bid Warehouse Locations Guide")
            print("\nUsage:")
            print("  python3 warehouse_locations_guide.py           # Show all locations")
            print("  python3 warehouse_locations_guide.py --picker  # Interactive picker")
            print("  python3 warehouse_locations_guide.py --activity # Check current activity")
            print("  python3 warehouse_locations_guide.py --help    # Show this help")
        else:
            print("❌ Unknown option. Use --help for usage info.")
    else:
        show_warehouse_guide()

if __name__ == "__main__":
    main() 