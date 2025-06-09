#!/usr/bin/env python3
"""
🎯 No-Bid Tracker - Find Valuable Items with Zero Bids
Identify high-value items that haven't received any bids yet
"""

import asyncio
import aiohttp
import ssl
import json
from datetime import datetime, timedelta
from collections import defaultdict

class NoBidTracker:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        
        # High-value search terms for items likely to have value
        self.value_terms = [
            # Premium electronics
            "macbook", "iphone", "ipad", "apple", "sony", "samsung", "lg",
            "nintendo", "xbox", "playstation", "gaming", "laptop", "tablet",
            "tv", "monitor", "camera", "canon", "nikon", "gopro",
            
            # Audio equipment
            "headphones", "speaker", "soundbar", "bose", "beats", "airpods",
            
            # Appliances
            "dyson", "kitchenaid", "vitamix", "refrigerator", "washer", "dryer",
            
            # Tools
            "dewalt", "milwaukee", "makita", "tool", "drill", "saw",
            
            # Luxury items
            "rolex", "omega", "cartier", "tiffany", "diamond", "gold", "watch",
            
            # Fitness
            "peloton", "nordictrack", "treadmill", "bike", "fitness",
            
            # General valuable conditions
            "new", "open box", "like new", "sealed", "refurbished"
        ]
        
    async def create_session(self):
        """Create HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=12)
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
            
    def calculate_opportunity_score(self, item):
        """Calculate opportunity score for no-bid items."""
        retail_price = item.get('retail_price', 0)
        instant_win_price = item.get('instant_win_price', 0)
        
        if retail_price <= 0:
            return 0
            
        # Base score from retail value
        value_score = min(retail_price / 200, 10)  # Cap at 10 points
        
        # Savings potential
        savings_score = 0
        if instant_win_price > 0:
            savings_percent = ((retail_price - instant_win_price) / retail_price) * 100
            savings_score = min(savings_percent / 10, 5)  # Cap at 5 points
            
        # Brand premium
        product_name = item.get('product_name', '').lower()
        brand_score = 0
        premium_brands = ['apple', 'sony', 'dyson', 'rolex', 'omega', 'nintendo', 'xbox', 'samsung']
        for brand in premium_brands:
            if brand in product_name:
                brand_score = 2
                break
                
        # Condition bonus
        condition = item.get('condition', '').lower()
        condition_score = 0
        if 'new' in condition or 'sealed' in condition:
            condition_score = 1
        elif 'like new' in condition:
            condition_score = 0.5
            
        return value_score + savings_score + brand_score + condition_score
        
    async def scan_no_bid_items(self, min_value=50):
        """Scan for items with no bids."""
        print(f"🎯 NO-BID TRACKER")
        print(f"💰 Minimum value: ${min_value}")
        print(f"🔍 Scanning {len(self.value_terms)} value terms...")
        print()
        
        all_items = []
        seen_lot_ids = set()
        
        for i, term in enumerate(self.value_terms, 1):
            print(f"  {i:2d}/{len(self.value_terms)} - Scanning '{term}'...")
            
            results = await self.search_for_term(term)
            
            # Filter for no-bid items
            no_bid_items = []
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    current_bid = result.get('current_bid', 0)
                    retail_price = result.get('retail_price', 0)
                    
                    # Must have no bids and meet minimum value
                    if current_bid == 0 and retail_price >= min_value:
                        # Calculate opportunity metrics
                        instant_win_price = result.get('instant_win_price', 0)
                        if instant_win_price > 0:
                            savings = retail_price - instant_win_price
                            savings_percent = (savings / retail_price) * 100
                            result['savings_amount'] = savings
                            result['savings_percent'] = savings_percent
                        else:
                            result['savings_amount'] = 0
                            result['savings_percent'] = 0
                            
                        result['opportunity_score'] = self.calculate_opportunity_score(result)
                        
                        no_bid_items.append(result)
                        seen_lot_ids.add(lot_id)
                        
            all_items.extend(no_bid_items)
            print(f"      Found {len(results)} items, {len(no_bid_items)} with no bids")
            
            await asyncio.sleep(0.2)  # Rate limiting
            
        return all_items
        
    def display_no_bid_report(self, items):
        """Display no-bid opportunities report."""
        if not items:
            print("❌ No no-bid opportunities found")
            return
            
        print(f"\n🎯 NO-BID OPPORTUNITIES REPORT")
        print("=" * 80)
        
        # Sort by opportunity score (highest first)
        items.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)
        
        print(f"🎉 Found {len(items)} items with NO BIDS!")
        print()
        
        # Top opportunities
        print(f"🏆 TOP 20 NO-BID OPPORTUNITIES")
        print("-" * 70)
        
        for i, item in enumerate(items[:20], 1):
            product_name = item.get('product_name', 'Unknown')[:45]
            location = item.get('auction_location', 'Unknown')
            retail_price = item.get('retail_price', 0)
            instant_win = item.get('instant_win_price', 0)
            savings = item.get('savings_amount', 0)
            savings_percent = item.get('savings_percent', 0)
            opportunity_score = item.get('opportunity_score', 0)
            closing_date = item.get('expected_close_date', 'Unknown')
            condition = item.get('condition', 'Unknown')
            
            print(f"{i:2d}. 🎯 Score: {opportunity_score:.1f}")
            print(f"     📦 {product_name}...")
            print(f"     💰 ${retail_price} → ${instant_win} | 💸 Save ${savings:.0f} ({savings_percent:.0f}%)")
            print(f"     📍 {location} | 📦 {condition} | ⏰ Closes: {closing_date}")
            print(f"     🎯 NO BIDS - PURE OPPORTUNITY!")
            print()
            
        # High-value no-bid items (>$500)
        high_value_items = [item for item in items if item.get('retail_price', 0) >= 500]
        if high_value_items:
            print(f"💎 HIGH-VALUE NO-BID ITEMS (${500}+)")
            print("-" * 60)
            
            for item in high_value_items[:10]:
                product_name = item.get('product_name', 'Unknown')[:40]
                retail_price = item.get('retail_price', 0)
                instant_win = item.get('instant_win_price', 0)
                location = item.get('auction_location', 'Unknown')
                
                print(f"💎 {product_name}... | ${retail_price} → ${instant_win} | {location}")
                
        # Ending soon no-bid items
        ending_soon_items = []
        for item in items:
            closing_date_str = item.get('expected_close_date', '')
            if closing_date_str and closing_date_str != 'Unknown':
                try:
                    if 'T' in closing_date_str:
                        closing_date = datetime.fromisoformat(closing_date_str.replace('Z', ''))
                    else:
                        closing_date = datetime.strptime(closing_date_str, '%Y-%m-%d')
                        
                    now = datetime.now()
                    hours_remaining = (closing_date - now).total_seconds() / 3600
                    
                    if 0 < hours_remaining <= 24:
                        item['hours_remaining'] = hours_remaining
                        ending_soon_items.append(item)
                except:
                    pass
                    
        if ending_soon_items:
            ending_soon_items.sort(key=lambda x: x.get('hours_remaining', 0))
            
            print(f"\n⏰ ENDING SOON - NO BIDS ({len(ending_soon_items)} items)")
            print("-" * 60)
            
            for item in ending_soon_items[:10]:
                product_name = item.get('product_name', 'Unknown')[:40]
                retail_price = item.get('retail_price', 0)
                instant_win = item.get('instant_win_price', 0)
                hours_remaining = item.get('hours_remaining', 0)
                location = item.get('auction_location', 'Unknown')
                
                print(f"⏰ {hours_remaining:.1f}h | {product_name}... | ${retail_price} → ${instant_win} | {location}")
                
        # Category breakdown
        print(f"\n📂 NO-BID ITEMS BY CATEGORY")
        print("-" * 40)
        
        by_category = defaultdict(list)
        for item in items:
            category = item.get('category', 'Unknown')
            by_category[category].append(item)
            
        sorted_categories = sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True)
        
        for category, category_items in sorted_categories[:10]:
            total_value = sum(item.get('retail_price', 0) for item in category_items)
            avg_value = total_value / len(category_items) if category_items else 0
            
            print(f"  {category[:20]:20s}: {len(category_items):3d} items | ${total_value:8,.0f} value | ${avg_value:6.0f} avg")
            
        # Location breakdown
        print(f"\n📍 NO-BID ITEMS BY LOCATION")
        print("-" * 40)
        
        by_location = defaultdict(list)
        for item in items:
            location = item.get('auction_location', 'Unknown')
            by_location[location].append(item)
            
        for location in self.sc_locations:
            location_items = by_location.get(location, [])
            if location_items:
                total_value = sum(item.get('retail_price', 0) for item in location_items)
                avg_opportunity = sum(item.get('opportunity_score', 0) for item in location_items) / len(location_items)
                high_value_count = len([item for item in location_items if item.get('retail_price', 0) >= 500])
                
                print(f"  {location:12s}: {len(location_items):3d} items | ${total_value:8,.0f} value | {avg_opportunity:.1f} avg score | {high_value_count} high-value")
                
        # Summary stats
        total_retail_value = sum(item.get('retail_price', 0) for item in items)
        total_instant_win = sum(item.get('instant_win_price', 0) for item in items if item.get('instant_win_price', 0) > 0)
        total_savings = sum(item.get('savings_amount', 0) for item in items)
        
        print(f"\n📊 NO-BID SUMMARY")
        print("-" * 40)
        print(f"🎯 Total No-Bid Items: {len(items)}")
        print(f"💰 Total Retail Value: ${total_retail_value:,.2f}")
        print(f"🏷️  Total Instant Win Value: ${total_instant_win:,.2f}")
        print(f"💸 Total Potential Savings: ${total_savings:,.2f}")
        
        if total_retail_value > 0:
            avg_savings_percent = (total_savings / total_retail_value) * 100
            print(f"📈 Average Savings Potential: {avg_savings_percent:.1f}%")
            
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"no_bid_opportunities_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(items, f, indent=2)
        print(f"\n💾 No-bid opportunities saved to: {filename}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='No-Bid Tracker')
    parser.add_argument('--min-value', type=int, default=50, help='Minimum retail value')
    parser.add_argument('--high-value-only', action='store_true', help='Show only items $500+')
    parser.add_argument('--ending-soon', action='store_true', help='Show only items ending within 24h')
    
    args = parser.parse_args()
    
    tracker = NoBidTracker()
    await tracker.create_session()
    
    try:
        items = await tracker.scan_no_bid_items(args.min_value)
        
        if args.high_value_only:
            items = [item for item in items if item.get('retail_price', 0) >= 500]
            
        if args.ending_soon:
            ending_soon_items = []
            for item in items:
                closing_date_str = item.get('expected_close_date', '')
                if closing_date_str and closing_date_str != 'Unknown':
                    try:
                        if 'T' in closing_date_str:
                            closing_date = datetime.fromisoformat(closing_date_str.replace('Z', ''))
                        else:
                            closing_date = datetime.strptime(closing_date_str, '%Y-%m-%d')
                            
                        now = datetime.now()
                        hours_remaining = (closing_date - now).total_seconds() / 3600
                        
                        if 0 < hours_remaining <= 24:
                            ending_soon_items.append(item)
                    except:
                        pass
            items = ending_soon_items
            
        tracker.display_no_bid_report(items)
        
    finally:
        await tracker.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 