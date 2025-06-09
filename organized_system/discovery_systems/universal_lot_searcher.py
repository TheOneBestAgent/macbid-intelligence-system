#!/usr/bin/env python3
"""
🔍 Universal Lot Searcher for SC Warehouses
Search for ANY product type across all 37,037+ lots in your SC locations
"""

import asyncio
import aiohttp
import ssl
import json
import time
from datetime import datetime
from collections import defaultdict

class UniversalLotSearcher:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        
        # Predefined search categories
        self.search_categories = {
            "electronics": [
                "laptop", "computer", "tablet", "ipad", "macbook", "chromebook",
                "monitor", "tv", "television", "smart tv", "gaming", "xbox", "playstation", "nintendo"
            ],
            "phones": [
                "iphone", "samsung", "phone", "smartphone", "android", "pixel", "oneplus"
            ],
            "audio": [
                "headphones", "earbuds", "speaker", "soundbar", "beats", "sony", "bose", "airpods"
            ],
            "cameras": [
                "camera", "canon", "nikon", "sony", "gopro", "lens", "dslr", "mirrorless"
            ],
            "appliances": [
                "refrigerator", "washer", "dryer", "dishwasher", "microwave", "oven", "air fryer"
            ],
            "tools": [
                "drill", "saw", "hammer", "wrench", "toolbox", "dewalt", "milwaukee", "makita"
            ],
            "furniture": [
                "chair", "desk", "table", "sofa", "bed", "mattress", "dresser", "bookshelf"
            ],
            "fitness": [
                "treadmill", "bike", "weights", "dumbbells", "yoga", "fitness", "exercise"
            ],
            "automotive": [
                "car", "auto", "tire", "battery", "oil", "brake", "engine", "transmission"
            ],
            "jewelry": [
                "watch", "ring", "necklace", "bracelet", "diamond", "gold", "silver", "rolex"
            ]
        }
        
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
            
    async def search_category(self, category_name):
        """Search for all items in a category."""
        if category_name not in self.search_categories:
            print(f"❌ Unknown category: {category_name}")
            print(f"Available categories: {', '.join(self.search_categories.keys())}")
            return []
            
        terms = self.search_categories[category_name]
        print(f"🔍 Searching {category_name.upper()} category")
        print(f"📝 Search terms: {', '.join(terms)}")
        print()
        
        all_items = []
        seen_lot_ids = set()
        
        for i, term in enumerate(terms, 1):
            print(f"  {i:2d}/{len(terms)} - Searching '{term}'...")
            
            results = await self.search_for_term(term)
            
            # Deduplicate by lot_id
            new_results = []
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    seen_lot_ids.add(lot_id)
                    new_results.append(result)
                    
            all_items.extend(new_results)
            print(f"      Found {len(results)} total, {len(new_results)} new items")
            
            await asyncio.sleep(0.3)  # Rate limiting
            
        return all_items
        
    async def search_custom_terms(self, terms):
        """Search for custom list of terms."""
        print(f"🔍 Custom Search")
        print(f"📝 Search terms: {', '.join(terms)}")
        print()
        
        all_items = []
        seen_lot_ids = set()
        
        for i, term in enumerate(terms, 1):
            print(f"  {i:2d}/{len(terms)} - Searching '{term}'...")
            
            results = await self.search_for_term(term)
            
            # Deduplicate by lot_id
            new_results = []
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    seen_lot_ids.add(lot_id)
                    new_results.append(result)
                    
            all_items.extend(new_results)
            print(f"      Found {len(results)} total, {len(new_results)} new items")
            
            await asyncio.sleep(0.3)  # Rate limiting
            
        return all_items
        
    def display_results(self, items, category_name="Items"):
        """Display search results in organized format."""
        if not items:
            print(f"❌ No {category_name.lower()} found in SC warehouses")
            return
            
        print(f"\n🎉 FOUND {len(items)} {category_name.upper()} IN SC WAREHOUSES!")
        print("=" * 70)
        
        # Group by location
        by_location = defaultdict(list)
        for item in items:
            location = item.get('auction_location', 'Unknown')
            by_location[location].append(item)
            
        # Display by location
        for location in self.sc_locations:
            location_items = by_location.get(location, [])
            if not location_items:
                continue
                
            print(f"\n📍 {location} ({len(location_items)} items)")
            print("-" * 50)
            
            # Sort by retail price (highest first)
            location_items.sort(key=lambda x: x.get('retail_price', 0), reverse=True)
            
            for i, item in enumerate(location_items[:10], 1):  # Show top 10 per location
                product_name = item.get('product_name', 'Unknown Product')
                auction_number = item.get('auction_number', 'Unknown')
                lot_number = item.get('lot_number', 'Unknown')
                condition = item.get('condition', 'Unknown')
                retail_price = item.get('retail_price', 0)
                instant_win_price = item.get('instant_win_price', 0)
                current_bid = item.get('current_bid', 0)
                closing_date = item.get('expected_close_date', 'Unknown')
                category = item.get('category', 'Unknown')
                
                # Calculate savings
                savings = retail_price - instant_win_price if instant_win_price else 0
                savings_percent = (savings / retail_price * 100) if retail_price > 0 else 0
                
                print(f"  {i:2d}. 📦 {product_name[:50]}...")
                print(f"      📋 {auction_number} | Lot: {lot_number} | {category}")
                print(f"      💰 ${retail_price} → ${instant_win_price}", end="")
                if savings > 0:
                    print(f" (Save ${savings:.0f} - {savings_percent:.0f}%)")
                else:
                    print()
                print(f"      📦 {condition} | ⏰ Closes: {closing_date}")
                if current_bid > 0:
                    print(f"      🔥 Current Bid: ${current_bid}")
                print()
                
            if len(location_items) > 10:
                print(f"      ... and {len(location_items) - 10} more items")
                print()
                
        # Summary statistics
        self.display_summary_stats(items, category_name)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"sc_{category_name.lower().replace(' ', '_')}_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(items, f, indent=2)
        print(f"\n💾 Detailed results saved to: {filename}")
        
    def display_summary_stats(self, items, category_name):
        """Display summary statistics."""
        print(f"\n📊 {category_name.upper()} SUMMARY")
        print("=" * 40)
        
        total_retail_value = sum(item.get('retail_price', 0) for item in items)
        total_instant_win = sum(item.get('instant_win_price', 0) for item in items if item.get('instant_win_price'))
        total_savings = total_retail_value - total_instant_win
        
        print(f"💰 Total Retail Value: ${total_retail_value:,.2f}")
        if total_instant_win > 0:
            print(f"🏷️  Total Instant Win: ${total_instant_win:,.2f}")
            print(f"💸 Total Potential Savings: ${total_savings:,.2f}")
            
        # Top categories
        categories = defaultdict(int)
        for item in items:
            category = item.get('category', 'Unknown')
            categories[category] += 1
            
        print(f"\n📂 Top Categories:")
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   {category}: {count} items")
            
        # Condition breakdown
        conditions = defaultdict(int)
        for item in items:
            condition = item.get('condition', 'Unknown')
            conditions[condition] += 1
            
        print(f"\n📦 Condition Breakdown:")
        for condition, count in sorted(conditions.items(), key=lambda x: x[1], reverse=True):
            print(f"   {condition}: {count} items")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Universal SC Lot Searcher')
    parser.add_argument('--category', type=str, help='Search predefined category')
    parser.add_argument('--terms', nargs='+', help='Search custom terms')
    parser.add_argument('--list-categories', action='store_true', help='List available categories')
    
    args = parser.parse_args()
    
    searcher = UniversalLotSearcher()
    
    if args.list_categories:
        print("📂 Available Search Categories:")
        print("=" * 40)
        for category, terms in searcher.search_categories.items():
            print(f"{category:12s}: {', '.join(terms[:5])}{'...' if len(terms) > 5 else ''}")
        return
        
    await searcher.create_session()
    
    try:
        if args.category:
            items = await searcher.search_category(args.category)
            searcher.display_results(items, args.category)
        elif args.terms:
            items = await searcher.search_custom_terms(args.terms)
            searcher.display_results(items, "Custom Search")
        else:
            print("🔍 Universal SC Lot Searcher")
            print("=" * 40)
            print("Usage:")
            print("  --category CATEGORY    Search predefined category")
            print("  --terms TERM1 TERM2    Search custom terms")
            print("  --list-categories      Show available categories")
            print()
            print("Examples:")
            print("  python3 universal_lot_searcher.py --category electronics")
            print("  python3 universal_lot_searcher.py --terms 'macbook' 'iphone'")
            print("  python3 universal_lot_searcher.py --list-categories")
            
    finally:
        await searcher.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 