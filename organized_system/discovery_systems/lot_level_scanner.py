#!/usr/bin/env python3
"""
🔬 Lot-Level Scanner - Advanced Analytics for All SC Inventory
Comprehensive analysis of all 37,037+ lots with advanced filtering and insights
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

class LotLevelScanner:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        self.db_file = "lot_analytics.db"
        self.init_database()
        
        # Comprehensive search terms for full inventory scan
        self.all_terms = [
            # Electronics & Tech
            "laptop", "computer", "tablet", "ipad", "macbook", "chromebook", "monitor", 
            "tv", "television", "smart", "gaming", "xbox", "playstation", "nintendo",
            "phone", "iphone", "samsung", "android", "pixel",
            
            # Audio/Video
            "headphones", "earbuds", "speaker", "soundbar", "beats", "sony", "bose", 
            "airpods", "camera", "canon", "nikon", "gopro", "lens",
            
            # Appliances
            "refrigerator", "washer", "dryer", "dishwasher", "microwave", "oven", 
            "air fryer", "dyson", "kitchenaid", "vitamix", "blender",
            
            # Tools & Equipment
            "drill", "saw", "hammer", "wrench", "toolbox", "dewalt", "milwaukee", 
            "makita", "craftsman", "tool",
            
            # Home & Garden
            "furniture", "chair", "desk", "table", "sofa", "bed", "mattress", 
            "outdoor", "grill", "patio", "garden",
            
            # Fitness & Sports
            "treadmill", "bike", "weights", "dumbbells", "yoga", "fitness", 
            "exercise", "peloton", "nordictrack",
            
            # Automotive
            "car", "auto", "tire", "battery", "oil", "brake", "parts",
            
            # Luxury & Jewelry
            "watch", "ring", "necklace", "bracelet", "diamond", "gold", "silver", 
            "rolex", "omega", "cartier", "tiffany",
            
            # Fashion & Accessories
            "bag", "purse", "wallet", "shoes", "clothing", "jacket", "coat",
            
            # General high-value terms
            "new", "open box", "like new", "refurbished", "sealed"
        ]
        
    def init_database(self):
        """Initialize comprehensive analytics database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lot_analytics (
                lot_id TEXT PRIMARY KEY,
                product_name TEXT,
                auction_location TEXT,
                auction_number TEXT,
                lot_number TEXT,
                category TEXT,
                condition_desc TEXT,
                retail_price REAL,
                instant_win_price REAL,
                current_bid REAL,
                bid_count INTEGER,
                expected_close_date TEXT,
                brand TEXT,
                savings_amount REAL,
                savings_percent REAL,
                value_score REAL,
                scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                location TEXT,
                avg_retail_price REAL,
                avg_instant_win REAL,
                avg_savings_percent REAL,
                total_items INTEGER,
                scan_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def create_session(self):
        """Create HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=15)
        timeout = aiohttp.ClientTimeout(total=45)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        )
        
    async def close_session(self):
        if self.session:
            await self.session.close()
            await asyncio.sleep(0.25)
            
    async def search_for_term(self, term, limit=200):
        """Search for a specific term with higher limit."""
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
            
    def extract_brand(self, product_name):
        """Extract brand from product name."""
        if not product_name:
            return "Unknown"
            
        product_lower = product_name.lower()
        
        # Common brands to look for
        brands = {
            'apple': ['apple', 'macbook', 'iphone', 'ipad', 'imac'],
            'sony': ['sony'],
            'samsung': ['samsung'],
            'lg': ['lg'],
            'dyson': ['dyson'],
            'kitchenaid': ['kitchenaid'],
            'dewalt': ['dewalt'],
            'milwaukee': ['milwaukee'],
            'makita': ['makita'],
            'nintendo': ['nintendo'],
            'xbox': ['xbox', 'microsoft'],
            'playstation': ['playstation', 'ps4', 'ps5'],
            'canon': ['canon'],
            'nikon': ['nikon'],
            'bose': ['bose'],
            'beats': ['beats'],
            'rolex': ['rolex'],
            'omega': ['omega'],
            'cartier': ['cartier'],
            'tiffany': ['tiffany']
        }
        
        for brand, keywords in brands.items():
            for keyword in keywords:
                if keyword in product_lower:
                    return brand.title()
                    
        return "Other"
        
    def calculate_value_score(self, item):
        """Calculate a value score for ranking items."""
        retail_price = item.get('retail_price', 0)
        instant_win_price = item.get('instant_win_price', 0)
        current_bid = item.get('current_bid', 0)
        
        if retail_price <= 0:
            return 0
            
        # Base score from retail price (higher = better)
        price_score = min(retail_price / 1000, 10)  # Cap at 10 points
        
        # Savings score
        savings_score = 0
        if instant_win_price > 0:
            savings_percent = ((retail_price - instant_win_price) / retail_price) * 100
            savings_score = min(savings_percent / 10, 10)  # Cap at 10 points
            
        # Bidding activity score (more bids = more interest)
        bid_score = min(current_bid / 100, 5) if current_bid > 0 else 0
        
        # Brand premium
        brand = self.extract_brand(item.get('product_name', ''))
        brand_score = 2 if brand in ['Apple', 'Sony', 'Dyson', 'Rolex'] else 0
        
        return price_score + savings_score + bid_score + brand_score
        
    async def comprehensive_scan(self, max_terms=None):
        """Perform comprehensive scan of all inventory."""
        terms_to_scan = self.all_terms[:max_terms] if max_terms else self.all_terms
        
        print(f"🔬 COMPREHENSIVE LOT-LEVEL SCAN")
        print(f"📊 Scanning {len(terms_to_scan)} search terms across SC warehouses")
        print(f"🎯 Target: All 37,037+ lots in inventory")
        print()
        
        all_items = []
        seen_lot_ids = set()
        
        for i, term in enumerate(terms_to_scan, 1):
            print(f"  {i:3d}/{len(terms_to_scan)} - Scanning '{term}'...")
            
            results = await self.search_for_term(term)
            
            # Process and deduplicate
            new_results = []
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    # Enhance with analytics
                    result['brand'] = self.extract_brand(result.get('product_name', ''))
                    
                    retail_price = result.get('retail_price', 0)
                    instant_win_price = result.get('instant_win_price', 0)
                    
                    if retail_price > 0 and instant_win_price > 0:
                        savings = retail_price - instant_win_price
                        savings_percent = (savings / retail_price) * 100
                        result['savings_amount'] = savings
                        result['savings_percent'] = savings_percent
                    else:
                        result['savings_amount'] = 0
                        result['savings_percent'] = 0
                        
                    result['value_score'] = self.calculate_value_score(result)
                    
                    seen_lot_ids.add(lot_id)
                    new_results.append(result)
                    
            all_items.extend(new_results)
            print(f"        Found {len(results)} total, {len(new_results)} unique | Running total: {len(all_items)}")
            
            await asyncio.sleep(0.15)  # Rate limiting
            
        return all_items
        
    def save_to_database(self, items):
        """Save scan results to database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Clear old data
        cursor.execute('DELETE FROM lot_analytics')
        
        # Insert new data
        for item in items:
            cursor.execute('''
                INSERT OR REPLACE INTO lot_analytics (
                    lot_id, product_name, auction_location, auction_number,
                    lot_number, category, condition_desc, retail_price,
                    instant_win_price, current_bid, expected_close_date,
                    brand, savings_amount, savings_percent, value_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.get('lot_id'),
                item.get('product_name'),
                item.get('auction_location'),
                item.get('auction_number'),
                item.get('lot_number'),
                item.get('category'),
                item.get('condition'),
                item.get('retail_price', 0),
                item.get('instant_win_price', 0),
                item.get('current_bid', 0),
                item.get('expected_close_date'),
                item.get('brand'),
                item.get('savings_amount', 0),
                item.get('savings_percent', 0),
                item.get('value_score', 0)
            ))
            
        conn.commit()
        conn.close()
        
    def generate_analytics_report(self, items):
        """Generate comprehensive analytics report."""
        if not items:
            print("❌ No items to analyze")
            return
            
        print(f"\n📊 COMPREHENSIVE ANALYTICS REPORT")
        print("=" * 80)
        
        # Overall statistics
        total_items = len(items)
        total_retail_value = sum(item.get('retail_price', 0) for item in items)
        total_instant_win = sum(item.get('instant_win_price', 0) for item in items if item.get('instant_win_price', 0) > 0)
        total_savings = sum(item.get('savings_amount', 0) for item in items)
        
        print(f"\n🎯 INVENTORY OVERVIEW")
        print("-" * 40)
        print(f"📦 Total Unique Lots: {total_items:,}")
        print(f"💰 Total Retail Value: ${total_retail_value:,.2f}")
        print(f"🏷️  Total Instant Win Value: ${total_instant_win:,.2f}")
        print(f"💸 Total Potential Savings: ${total_savings:,.2f}")
        
        if total_retail_value > 0:
            avg_savings_percent = (total_savings / total_retail_value) * 100
            print(f"📈 Average Savings: {avg_savings_percent:.1f}%")
            
        # Location breakdown
        print(f"\n📍 INVENTORY BY LOCATION")
        print("-" * 40)
        
        by_location = defaultdict(list)
        for item in items:
            location = item.get('auction_location', 'Unknown')
            by_location[location].append(item)
            
        for location in self.sc_locations:
            location_items = by_location.get(location, [])
            if location_items:
                location_value = sum(item.get('retail_price', 0) for item in location_items)
                location_savings = sum(item.get('savings_amount', 0) for item in location_items)
                avg_value = location_value / len(location_items) if location_items else 0
                
                print(f"  {location:12s}: {len(location_items):4d} lots | ${location_value:8,.0f} value | ${location_savings:6,.0f} savings | ${avg_value:6.0f} avg")
                
        # Category analysis
        print(f"\n📂 TOP CATEGORIES")
        print("-" * 40)
        
        by_category = defaultdict(list)
        for item in items:
            category = item.get('category', 'Unknown')
            by_category[category].append(item)
            
        sorted_categories = sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True)
        
        for category, category_items in sorted_categories[:15]:
            category_value = sum(item.get('retail_price', 0) for item in category_items)
            category_savings = sum(item.get('savings_amount', 0) for item in category_items)
            avg_savings = (category_savings / category_value * 100) if category_value > 0 else 0
            
            print(f"  {category[:20]:20s}: {len(category_items):4d} lots | ${category_value:8,.0f} | {avg_savings:4.0f}% avg savings")
            
        # Brand analysis
        print(f"\n🏷️  TOP BRANDS")
        print("-" * 40)
        
        by_brand = defaultdict(list)
        for item in items:
            brand = item.get('brand', 'Other')
            by_brand[brand].append(item)
            
        sorted_brands = sorted(by_brand.items(), key=lambda x: len(x[1]), reverse=True)
        
        for brand, brand_items in sorted_brands[:15]:
            if brand == 'Other':
                continue
            brand_value = sum(item.get('retail_price', 0) for item in brand_items)
            brand_savings = sum(item.get('savings_amount', 0) for item in brand_items)
            avg_value = brand_value / len(brand_items) if brand_items else 0
            
            print(f"  {brand:15s}: {len(brand_items):4d} lots | ${brand_value:8,.0f} value | ${avg_value:6.0f} avg")
            
        # Top value items
        print(f"\n💎 TOP 20 HIGHEST VALUE ITEMS")
        print("-" * 60)
        
        top_value_items = sorted(items, key=lambda x: x.get('value_score', 0), reverse=True)[:20]
        
        for i, item in enumerate(top_value_items, 1):
            product_name = item.get('product_name', 'Unknown')[:40]
            location = item.get('auction_location', 'Unknown')
            retail_price = item.get('retail_price', 0)
            instant_win = item.get('instant_win_price', 0)
            savings = item.get('savings_amount', 0)
            value_score = item.get('value_score', 0)
            
            print(f"{i:2d}. {product_name:40s} | {location:10s} | ${retail_price:6.0f} → ${instant_win:6.0f} | Score: {value_score:.1f}")
            
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"comprehensive_scan_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(items, f, indent=2)
        print(f"\n💾 Detailed results saved to: {filename}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Comprehensive Lot-Level Scanner')
    parser.add_argument('--full-scan', action='store_true', help='Full comprehensive scan')
    parser.add_argument('--quick-scan', action='store_true', help='Quick scan (first 20 terms)')
    parser.add_argument('--terms', type=int, default=None, help='Number of terms to scan')
    
    args = parser.parse_args()
    
    scanner = LotLevelScanner()
    await scanner.create_session()
    
    try:
        if args.quick_scan:
            items = await scanner.comprehensive_scan(max_terms=20)
        elif args.terms:
            items = await scanner.comprehensive_scan(max_terms=args.terms)
        else:
            items = await scanner.comprehensive_scan()
            
        scanner.save_to_database(items)
        scanner.generate_analytics_report(items)
        
    finally:
        await scanner.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 