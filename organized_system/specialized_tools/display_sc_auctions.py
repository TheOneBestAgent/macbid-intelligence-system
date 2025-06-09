#!/usr/bin/env python3
"""
📋 Display All SC Warehouse Auctions
Shows detailed information about all auctions in your 5 SC locations
"""

import json
from datetime import datetime
from collections import defaultdict

def load_auction_data():
    """Load the latest auction scan data."""
    try:
        with open('auction_scan_20250605_211113.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ No auction data found. Run the scanner first!")
        return []

def format_date(date_string):
    """Format ISO date string to readable format."""
    if not date_string:
        return "Unknown"
    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime('%m/%d %H:%M')
    except:
        return date_string

def display_all_auctions():
    """Display all auctions organized by location."""
    auctions = load_auction_data()
    
    if not auctions:
        return
        
    print("🏢 ALL AUCTIONS IN YOUR SC WAREHOUSES")
    print("=" * 80)
    print(f"📊 Total Auctions Found: {len(auctions)}")
    print()
    
    # Group by location
    by_location = defaultdict(list)
    for auction in auctions:
        location_id = auction.get('location_id')
        by_location[location_id].append(auction)
    
    # Location names mapping
    location_names = {
        17: "Spartanburg - A",
        20: "Greenville - N", 
        28: "Rock Hill - A",
        34: "Gastonia - A",
        36: "Anderson - B"
    }
    
    # Display by location
    for location_id in [17, 20, 28, 34, 36]:  # Your SC locations in order
        location_auctions = by_location.get(location_id, [])
        if not location_auctions:
            continue
            
        location_name = location_names.get(location_id, f"Location {location_id}")
        print(f"📍 {location_name} ({len(location_auctions)} auctions)")
        print("-" * 60)
        
        # Sort by closing date
        location_auctions.sort(key=lambda x: x.get('closing_date', ''))
        
        for i, auction in enumerate(location_auctions, 1):
            auction_number = auction.get('auction_number', 'Unknown')
            closing_date = format_date(auction.get('closing_date'))
            pickup_date = auction.get('pickup_date', 'Unknown')
            total_lots = auction.get('total_lots', 0)
            max_lot = auction.get('max_lot', 'Unknown')
            is_open = auction.get('is_open', 0)
            
            status = "🟢 OPEN" if is_open else "🔴 CLOSED"
            
            print(f"  {i:2d}. 📋 {auction_number}")
            print(f"      ⏰ Closes: {closing_date}")
            print(f"      📦 Pickup: {pickup_date}")
            print(f"      📊 {total_lots} lots (max: {max_lot})")
            print(f"      {status}")
            print()
            
        print()
    
    # Summary statistics
    print("📊 SUMMARY STATISTICS")
    print("=" * 40)
    
    total_lots = sum(auction.get('total_lots', 0) for auction in auctions)
    open_auctions = sum(1 for auction in auctions if auction.get('is_open', 0))
    
    print(f"🎯 Total Lots Available: {total_lots:,}")
    print(f"🟢 Open Auctions: {open_auctions}")
    print(f"🔴 Closed Auctions: {len(auctions) - open_auctions}")
    
    # Closing times analysis
    closing_times = defaultdict(int)
    for auction in auctions:
        closing_date = auction.get('closing_date', '')
        if closing_date:
            try:
                dt = datetime.fromisoformat(closing_date.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M')
                closing_times[time_str] += 1
            except:
                pass
                
    if closing_times:
        print(f"\n⏰ Closing Times:")
        for time, count in sorted(closing_times.items()):
            print(f"   {time}: {count} auctions")
    
    # Pickup dates
    pickup_dates = defaultdict(int)
    for auction in auctions:
        pickup_date = auction.get('pickup_date', 'Unknown')
        pickup_dates[pickup_date] += 1
        
    print(f"\n📦 Pickup Dates:")
    for date, count in sorted(pickup_dates.items()):
        print(f"   {date}: {count} auctions")

def search_auctions(keywords):
    """Search auctions for specific keywords."""
    auctions = load_auction_data()
    
    if not auctions:
        return
        
    print(f"🔍 SEARCHING FOR: {', '.join(keywords)}")
    print("=" * 60)
    
    matches = []
    for auction in auctions:
        # Search in auction number and any title/description fields
        searchable_text = ' '.join([
            auction.get('auction_number', '') or '',
            auction.get('title', '') or '',
            auction.get('description', '') or '',
            auction.get('external_folder_name', '') or '',
            auction.get('location_name', '') or ''
        ]).lower()
        
        if any(keyword.lower() in searchable_text for keyword in keywords):
            matches.append(auction)
    
    if matches:
        print(f"🎯 Found {len(matches)} matching auctions:")
        print()
        
        for match in matches:
            auction_number = match.get('auction_number', 'Unknown')
            location_name = match.get('location_name', 'Unknown Location')
            closing_date = format_date(match.get('closing_date'))
            total_lots = match.get('total_lots', 0)
            
            print(f"📋 {auction_number}")
            print(f"   📍 {location_name}")
            print(f"   ⏰ Closes: {closing_date}")
            print(f"   📊 {total_lots} lots")
            print()
    else:
        print("❌ No matches found")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Display SC Warehouse Auctions')
    parser.add_argument('--search', nargs='+', help='Search for specific keywords')
    parser.add_argument('--location', type=int, help='Show only specific location (17,20,28,34,36)')
    
    args = parser.parse_args()
    
    if args.search:
        search_auctions(args.search)
    elif args.location:
        # Filter and display single location
        auctions = load_auction_data()
        filtered = [a for a in auctions if a.get('location_id') == args.location]
        
        if filtered:
            print(f"📍 Location {args.location} Auctions ({len(filtered)} found)")
            print("=" * 50)
            for auction in filtered:
                auction_number = auction.get('auction_number', 'Unknown')
                closing_date = format_date(auction.get('closing_date'))
                total_lots = auction.get('total_lots', 0)
                print(f"📋 {auction_number} - {total_lots} lots - Closes: {closing_date}")
        else:
            print(f"❌ No auctions found for location {args.location}")
    else:
        display_all_auctions()

if __name__ == "__main__":
    main() 