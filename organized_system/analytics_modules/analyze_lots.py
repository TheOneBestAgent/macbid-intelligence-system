#!/usr/bin/env python3
"""
📊 Analyze Total Lots in SC Warehouses
"""

import json

def analyze_lots():
    try:
        with open('enhanced_scan_20250605_211606.json', 'r') as f:
            auctions = json.load(f)
    except FileNotFoundError:
        print("❌ Enhanced scan file not found")
        return

    total_lots = sum(auction.get('total_lots', 0) for auction in auctions)
    print(f'📊 ANALYSIS RESULTS')
    print('=' * 40)
    print(f'Total auctions in SC warehouses: {len(auctions)}')
    print(f'Total LOTS in SC warehouses: {total_lots:,}')
    print()

    print('🏆 Top 10 auctions by lot count:')
    sorted_auctions = sorted(auctions, key=lambda x: x.get('total_lots', 0), reverse=True)
    for i, auction in enumerate(sorted_auctions[:10], 1):
        lots = auction.get('total_lots', 0)
        auction_num = auction.get('auction_number', 'Unknown')
        location = auction.get('location_id', 'Unknown')
        location_name = auction.get('location_name', f'Location {location}')
        print(f'  {i:2d}. {auction_num}: {lots:,} lots ({location_name})')

    print()
    print('📍 Lots by location:')
    by_location = {}
    for auction in auctions:
        location_id = auction.get('location_id')
        location_name = auction.get('location_name', f'Location {location_id}')
        lots = auction.get('total_lots', 0)
        
        if location_id not in by_location:
            by_location[location_id] = {'name': location_name, 'auctions': 0, 'lots': 0}
        
        by_location[location_id]['auctions'] += 1
        by_location[location_id]['lots'] += lots

    for location_id in [17, 20, 28, 34, 36]:
        if location_id in by_location:
            data = by_location[location_id]
            print(f'  Location {location_id} ({data["name"]}): {data["auctions"]} auctions, {data["lots"]:,} lots')

if __name__ == "__main__":
    analyze_lots() 