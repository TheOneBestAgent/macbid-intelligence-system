#!/usr/bin/env python3
"""
🎧 Comprehensive Headphone Search for SC Warehouses
Uses the search API to find all headphones and audio equipment
"""

import asyncio
import aiohttp
import ssl
import json
import time
from datetime import datetime
from collections import defaultdict

class HeadphoneSearcher:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        self.headphone_terms = [
            "headphones", "headphone", "earbuds", "earbud", "earphones", "earphone",
            "beats", "airpods", "sony", "bose", "sennheiser", "audio-technica",
            "skullcandy", "jbl", "plantronics", "jabra", "anker", "soundcore",
            "wireless headset", "bluetooth headset", "gaming headset", "noise cancelling"
        ]
        
    async def create_session(self):
        """Create HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        )
        
    async def close_session(self):
        if self.session:
            await self.session.close()
            await asyncio.sleep(0.25)
            
    async def search_for_term(self, term, limit=100):
        """Search for a specific term."""
        url = f"https://api.macdiscount.com/search?q={term}&limit={limit}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get('hits', [])
                    
                    # Filter to SC locations only
                    sc_hits = []
                    for hit in hits:
                        if hit.get('auction_location') in self.sc_locations:
                            sc_hits.append(hit)
                            
                    return sc_hits
                else:
                    print(f"⚠️  Search for '{term}': HTTP {response.status}")
                    return []
        except Exception as e:
            print(f"❌ Search for '{term}': {str(e)[:50]}...")
            return []
            
    async def comprehensive_headphone_search(self):
        """Search for all headphone-related terms."""
        print("🎧 Comprehensive Headphone Search - SC Warehouses")
        print("=" * 60)
        print("🔍 Searching for headphones, earbuds, and audio equipment")
        print("📍 Filtering to your 5 SC locations")
        print()
        
        all_headphones = []
        seen_lot_ids = set()
        
        # Search for each term
        for i, term in enumerate(self.headphone_terms, 1):
            print(f"🔍 {i:2d}/{len(self.headphone_terms)} - Searching for '{term}'...")
            
            results = await self.search_for_term(term)
            
            # Deduplicate by lot_id
            new_results = []
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    seen_lot_ids.add(lot_id)
                    new_results.append(result)
                    
            all_headphones.extend(new_results)
            print(f"    Found {len(results)} total, {len(new_results)} new items")
            
            await asyncio.sleep(0.3)  # Rate limiting
            
        print(f"\n✅ Search Complete!")
        print(f"🎧 Total unique headphones found: {len(all_headphones)}")
        
        if all_headphones:
            await self.display_headphone_results(all_headphones)
            
        return all_headphones
        
    async def display_headphone_results(self, headphones):
        """Display detailed headphone results."""
        print(f"\n🎉 FOUND {len(headphones)} HEADPHONES IN SC WAREHOUSES!")
        print("=" * 70)
        
        # Group by location
        by_location = defaultdict(list)
        for headphone in headphones:
            location = headphone.get('auction_location', 'Unknown')
            by_location[location].append(headphone)
            
        # Display by location
        for location in self.sc_locations:
            location_headphones = by_location.get(location, [])
            if not location_headphones:
                continue
                
            print(f"\n📍 {location} ({len(location_headphones)} items)")
            print("-" * 50)
            
            # Sort by retail price (highest first)
            location_headphones.sort(key=lambda x: x.get('retail_price', 0), reverse=True)
            
            for i, headphone in enumerate(location_headphones, 1):
                product_name = headphone.get('product_name', 'Unknown Product')
                auction_number = headphone.get('auction_number', 'Unknown')
                lot_number = headphone.get('lot_number', 'Unknown')
                condition = headphone.get('condition', 'Unknown')
                retail_price = headphone.get('retail_price', 0)
                instant_win_price = headphone.get('instant_win_price', 0)
                current_bid = headphone.get('current_bid', 0)
                closing_date = headphone.get('expected_close_date', 'Unknown')
                category = headphone.get('category', 'Unknown')
                
                # Calculate savings
                savings = retail_price - instant_win_price if instant_win_price else 0
                savings_percent = (savings / retail_price * 100) if retail_price > 0 else 0
                
                print(f"  {i:2d}. 🎧 {product_name}")
                print(f"      📋 Auction: {auction_number} | Lot: {lot_number}")
                print(f"      💰 Retail: ${retail_price} | Instant Win: ${instant_win_price}")
                if savings > 0:
                    print(f"      💸 Savings: ${savings:.2f} ({savings_percent:.1f}% off)")
                print(f"      📦 Condition: {condition} | Category: {category}")
                print(f"      ⏰ Closes: {closing_date}")
                if current_bid > 0:
                    print(f"      🔥 Current Bid: ${current_bid}")
                print()
                
        # Summary statistics
        print(f"\n📊 SUMMARY STATISTICS")
        print("=" * 40)
        
        total_retail_value = sum(h.get('retail_price', 0) for h in headphones)
        total_instant_win = sum(h.get('instant_win_price', 0) for h in headphones if h.get('instant_win_price'))
        total_savings = total_retail_value - total_instant_win
        
        print(f"💰 Total Retail Value: ${total_retail_value:,.2f}")
        print(f"🏷️  Total Instant Win: ${total_instant_win:,.2f}")
        print(f"💸 Total Potential Savings: ${total_savings:,.2f}")
        
        # Top brands
        brands = defaultdict(int)
        for headphone in headphones:
            product_name = headphone.get('product_name', '').lower()
            if 'sony' in product_name:
                brands['Sony'] += 1
            elif 'bose' in product_name:
                brands['Bose'] += 1
            elif 'beats' in product_name:
                brands['Beats'] += 1
            elif 'airpods' in product_name:
                brands['Apple AirPods'] += 1
            elif 'sennheiser' in product_name:
                brands['Sennheiser'] += 1
            elif 'jbl' in product_name:
                brands['JBL'] += 1
            elif 'skullcandy' in product_name:
                brands['Skullcandy'] += 1
            elif 'bowers' in product_name:
                brands['Bowers & Wilkins'] += 1
            elif 'sonos' in product_name:
                brands['Sonos'] += 1
            else:
                brands['Other'] += 1
                
        print(f"\n🏷️  Brands Found:")
        for brand, count in sorted(brands.items(), key=lambda x: x[1], reverse=True):
            print(f"   {brand}: {count} items")
            
        # Condition breakdown
        conditions = defaultdict(int)
        for headphone in headphones:
            condition = headphone.get('condition', 'Unknown')
            conditions[condition] += 1
            
        print(f"\n📦 Condition Breakdown:")
        for condition, count in sorted(conditions.items(), key=lambda x: x[1], reverse=True):
            print(f"   {condition}: {count} items")
            
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"sc_headphones_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(headphones, f, indent=2)
        print(f"\n💾 Detailed results saved to: {filename}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SC Headphone Search')
    parser.add_argument('--term', type=str, help='Search for specific term')
    parser.add_argument('--all', action='store_true', help='Search for all headphone terms')
    
    args = parser.parse_args()
    
    searcher = HeadphoneSearcher()
    await searcher.create_session()
    
    try:
        if args.term:
            results = await searcher.search_for_term(args.term)
            print(f"🔍 Found {len(results)} results for '{args.term}' in SC warehouses")
            if results:
                await searcher.display_headphone_results(results)
        else:
            await searcher.comprehensive_headphone_search()
            
    finally:
        await searcher.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 