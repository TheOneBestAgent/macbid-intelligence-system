#!/usr/bin/env python3
"""
💎 Deal Hunter - Find the Best Deals in SC Warehouses
Automatically finds high-value deals with significant savings
"""

import asyncio
import aiohttp
import ssl
import json
from datetime import datetime
from collections import defaultdict

class DealHunter:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        
        # High-value search terms for premium items
        self.premium_terms = [
            # Apple Products
            "macbook", "iphone", "ipad", "apple watch", "airpods", "imac",
            
            # High-End Electronics
            "sony", "samsung", "lg", "bose", "beats", "canon", "nikon",
            "nintendo", "xbox", "playstation", "gaming", "laptop", "tablet",
            
            # Luxury Items
            "rolex", "omega", "cartier", "tiffany", "diamond", "gold",
            "louis vuitton", "gucci", "prada", "coach",
            
            # High-Value Appliances
            "dyson", "kitchenaid", "vitamix", "breville", "weber",
            
            # Tools & Equipment
            "dewalt", "milwaukee", "makita", "snap-on", "craftsman",
            
            # Fitness Equipment
            "peloton", "nordictrack", "bowflex", "treadmill",
            
            # Audio/Video
            "tv", "monitor", "speaker", "soundbar", "receiver"
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
                    return []
        except Exception as e:
            return []
            
    async def hunt_deals(self, min_savings_percent=30, min_retail_value=100):
        """Hunt for the best deals."""
        print(f"🏹 DEAL HUNTER - Scanning for Premium Deals")
        print(f"📊 Criteria: {min_savings_percent}%+ savings, ${min_retail_value}+ retail value")
        print(f"🎯 Searching {len(self.premium_terms)} premium terms...")
        print()
        
        all_items = []
        seen_lot_ids = set()
        
        for i, term in enumerate(self.premium_terms, 1):
            print(f"  {i:2d}/{len(self.premium_terms)} - Scanning '{term}'...")
            
            results = await self.search_for_term(term)
            
            # Filter for good deals and deduplicate
            good_deals = []
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    retail_price = result.get('retail_price', 0)
                    instant_win_price = result.get('instant_win_price', 0)
                    
                    if retail_price >= min_retail_value and instant_win_price > 0:
                        savings = retail_price - instant_win_price
                        savings_percent = (savings / retail_price * 100)
                        
                        if savings_percent >= min_savings_percent:
                            result['savings'] = savings
                            result['savings_percent'] = savings_percent
                            good_deals.append(result)
                            seen_lot_ids.add(lot_id)
                            
            all_items.extend(good_deals)
            print(f"      Found {len(results)} items, {len(good_deals)} great deals")
            
            await asyncio.sleep(0.2)  # Rate limiting
            
        return all_items
        
    def display_deals(self, deals):
        """Display deals in organized format."""
        if not deals:
            print("❌ No deals found matching criteria")
            return
            
        # Sort by savings amount (highest first)
        deals.sort(key=lambda x: x.get('savings', 0), reverse=True)
        
        print(f"\n💎 FOUND {len(deals)} PREMIUM DEALS!")
        print("=" * 80)
        
        # Top 20 deals
        print(f"\n🏆 TOP 20 DEALS BY SAVINGS AMOUNT")
        print("-" * 60)
        
        for i, deal in enumerate(deals[:20], 1):
            product_name = deal.get('product_name', 'Unknown Product')
            location = deal.get('auction_location', 'Unknown')
            auction_number = deal.get('auction_number', 'Unknown')
            lot_number = deal.get('lot_number', 'Unknown')
            condition = deal.get('condition', 'Unknown')
            retail_price = deal.get('retail_price', 0)
            instant_win_price = deal.get('instant_win_price', 0)
            current_bid = deal.get('current_bid', 0)
            closing_date = deal.get('expected_close_date', 'Unknown')
            category = deal.get('category', 'Unknown')
            savings = deal.get('savings', 0)
            savings_percent = deal.get('savings_percent', 0)
            
            print(f"{i:2d}. 💰 SAVE ${savings:.0f} ({savings_percent:.0f}%)")
            print(f"    📦 {product_name[:55]}...")
            print(f"    📍 {location} | 📋 {auction_number} | Lot: {lot_number}")
            print(f"    💵 ${retail_price} → ${instant_win_price} | {condition}")
            print(f"    📂 {category} | ⏰ Closes: {closing_date}")
            if current_bid > 0:
                print(f"    🔥 Current Bid: ${current_bid}")
            print()
            
        # Group by location
        print(f"\n📍 DEALS BY LOCATION")
        print("-" * 40)
        
        by_location = defaultdict(list)
        for deal in deals:
            location = deal.get('auction_location', 'Unknown')
            by_location[location].append(deal)
            
        for location in self.sc_locations:
            location_deals = by_location.get(location, [])
            if location_deals:
                total_savings = sum(deal.get('savings', 0) for deal in location_deals)
                avg_savings_percent = sum(deal.get('savings_percent', 0) for deal in location_deals) / len(location_deals)
                print(f"  {location:12s}: {len(location_deals):2d} deals | ${total_savings:,.0f} total savings | {avg_savings_percent:.0f}% avg")
                
        # Category breakdown
        print(f"\n📂 DEALS BY CATEGORY")
        print("-" * 40)
        
        by_category = defaultdict(list)
        for deal in deals:
            category = deal.get('category', 'Unknown')
            by_category[category].append(deal)
            
        for category, category_deals in sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True):
            total_savings = sum(deal.get('savings', 0) for deal in category_deals)
            avg_savings_percent = sum(deal.get('savings_percent', 0) for deal in category_deals) / len(category_deals)
            print(f"  {category:20s}: {len(category_deals):2d} deals | ${total_savings:,.0f} savings | {avg_savings_percent:.0f}% avg")
            
        # Summary stats
        total_retail_value = sum(deal.get('retail_price', 0) for deal in deals)
        total_instant_win = sum(deal.get('instant_win_price', 0) for deal in deals)
        total_savings = sum(deal.get('savings', 0) for deal in deals)
        avg_savings_percent = sum(deal.get('savings_percent', 0) for deal in deals) / len(deals)
        
        print(f"\n📊 DEAL SUMMARY")
        print("=" * 40)
        print(f"💰 Total Retail Value: ${total_retail_value:,.2f}")
        print(f"🏷️  Total Instant Win: ${total_instant_win:,.2f}")
        print(f"💸 Total Savings: ${total_savings:,.2f}")
        print(f"📈 Average Savings: {avg_savings_percent:.1f}%")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"sc_premium_deals_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(deals, f, indent=2)
        print(f"\n💾 Detailed results saved to: {filename}")
        
    async def hunt_steals(self, min_savings_percent=50):
        """Hunt for absolute steals (50%+ off)."""
        print(f"🎯 STEAL HUNTER - Finding 50%+ Off Deals")
        return await self.hunt_deals(min_savings_percent=min_savings_percent, min_retail_value=50)
        
    async def hunt_luxury(self, min_retail_value=500):
        """Hunt for luxury items with any discount."""
        print(f"💎 LUXURY HUNTER - Finding High-Value Items")
        return await self.hunt_deals(min_savings_percent=10, min_retail_value=min_retail_value)

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SC Deal Hunter')
    parser.add_argument('--mode', choices=['deals', 'steals', 'luxury'], default='deals',
                       help='Hunt mode: deals (30%+ off), steals (50%+ off), luxury ($500+ items)')
    parser.add_argument('--min-savings', type=int, default=30,
                       help='Minimum savings percentage (default: 30)')
    parser.add_argument('--min-value', type=int, default=100,
                       help='Minimum retail value (default: $100)')
    
    args = parser.parse_args()
    
    hunter = DealHunter()
    await hunter.create_session()
    
    try:
        if args.mode == 'steals':
            deals = await hunter.hunt_steals()
        elif args.mode == 'luxury':
            deals = await hunter.hunt_luxury()
        else:
            deals = await hunter.hunt_deals(args.min_savings, args.min_value)
            
        hunter.display_deals(deals)
        
    finally:
        await hunter.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 