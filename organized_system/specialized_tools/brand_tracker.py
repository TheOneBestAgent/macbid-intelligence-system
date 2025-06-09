#!/usr/bin/env python3
"""
🏷️ Brand Tracker - Monitor Specific Premium Brands
Track Apple, Sony, Dyson, and other premium brands across SC warehouses
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

class BrandTracker:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        self.db_file = "brand_tracking.db"
        self.init_database()
        
        # Premium brands to track
        self.brands = {
            'Apple': {
                'terms': ['macbook', 'iphone', 'ipad', 'apple watch', 'airpods', 'imac', 'apple tv'],
                'priority': 'HIGH',
                'avg_value': 800
            },
            'Sony': {
                'terms': ['sony camera', 'sony headphones', 'sony tv', 'sony speaker', 'sony lens', 'playstation'],
                'priority': 'HIGH',
                'avg_value': 600
            },
            'Dyson': {
                'terms': ['dyson vacuum', 'dyson hair', 'dyson fan', 'dyson purifier'],
                'priority': 'HIGH',
                'avg_value': 500
            },
            'Samsung': {
                'terms': ['samsung tv', 'samsung phone', 'samsung tablet', 'samsung watch', 'samsung soundbar'],
                'priority': 'MEDIUM',
                'avg_value': 400
            },
            'Nintendo': {
                'terms': ['nintendo switch', 'nintendo console', 'nintendo game'],
                'priority': 'MEDIUM',
                'avg_value': 300
            },
            'Xbox': {
                'terms': ['xbox series', 'xbox one', 'xbox controller', 'xbox game'],
                'priority': 'MEDIUM',
                'avg_value': 350
            },
            'Canon': {
                'terms': ['canon camera', 'canon lens', 'canon printer'],
                'priority': 'MEDIUM',
                'avg_value': 450
            },
            'Nikon': {
                'terms': ['nikon camera', 'nikon lens'],
                'priority': 'MEDIUM',
                'avg_value': 500
            },
            'Bose': {
                'terms': ['bose headphones', 'bose speaker', 'bose soundbar'],
                'priority': 'MEDIUM',
                'avg_value': 300
            },
            'KitchenAid': {
                'terms': ['kitchenaid mixer', 'kitchenaid blender', 'kitchenaid'],
                'priority': 'LOW',
                'avg_value': 250
            },
            'DeWalt': {
                'terms': ['dewalt drill', 'dewalt saw', 'dewalt tool'],
                'priority': 'LOW',
                'avg_value': 200
            },
            'Milwaukee': {
                'terms': ['milwaukee tool', 'milwaukee drill', 'milwaukee saw'],
                'priority': 'LOW',
                'avg_value': 180
            }
        }
        
    def init_database(self):
        """Initialize brand tracking database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brand_inventory (
                lot_id TEXT PRIMARY KEY,
                brand TEXT,
                product_name TEXT,
                auction_location TEXT,
                auction_number TEXT,
                lot_number TEXT,
                category TEXT,
                condition_desc TEXT,
                retail_price REAL,
                instant_win_price REAL,
                current_bid REAL,
                expected_close_date TEXT,
                savings_amount REAL,
                savings_percent REAL,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brand_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT,
                lot_id TEXT,
                alert_type TEXT,
                message TEXT,
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
            
    async def track_brand(self, brand_name):
        """Track all items for a specific brand."""
        brand_info = self.brands.get(brand_name)
        if not brand_info:
            print(f"❌ Unknown brand: {brand_name}")
            return []
            
        print(f"🏷️ Tracking {brand_name} ({brand_info['priority']} priority)")
        print(f"📝 Search terms: {', '.join(brand_info['terms'])}")
        print()
        
        all_items = []
        seen_lot_ids = set()
        
        for i, term in enumerate(brand_info['terms'], 1):
            print(f"  {i:2d}/{len(brand_info['terms'])} - Searching '{term}'...")
            
            results = await self.search_for_term(term)
            
            # Process and deduplicate
            new_results = []
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    # Add brand info
                    result['brand'] = brand_name
                    
                    # Calculate savings
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
                        
                    seen_lot_ids.add(lot_id)
                    new_results.append(result)
                    
            all_items.extend(new_results)
            print(f"      Found {len(results)} total, {len(new_results)} new items")
            
            await asyncio.sleep(0.2)  # Rate limiting
            
        return all_items
        
    async def track_all_brands(self):
        """Track all premium brands."""
        print(f"🏷️ PREMIUM BRAND TRACKER")
        print(f"📊 Tracking {len(self.brands)} premium brands")
        print()
        
        all_brand_items = {}
        
        for brand_name in self.brands.keys():
            items = await self.track_brand(brand_name)
            all_brand_items[brand_name] = items
            print(f"✅ {brand_name}: {len(items)} items found")
            print()
            
        return all_brand_items
        
    def save_brand_data(self, brand_items):
        """Save brand tracking data to database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        for brand_name, items in brand_items.items():
            for item in items:
                # Check if item exists
                cursor.execute('SELECT lot_id FROM brand_inventory WHERE lot_id = ?', (item.get('lot_id'),))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing
                    cursor.execute('''
                        UPDATE brand_inventory SET
                            current_bid = ?, last_updated = CURRENT_TIMESTAMP
                        WHERE lot_id = ?
                    ''', (item.get('current_bid', 0), item.get('lot_id')))
                else:
                    # Insert new
                    cursor.execute('''
                        INSERT INTO brand_inventory (
                            lot_id, brand, product_name, auction_location,
                            auction_number, lot_number, category, condition_desc,
                            retail_price, instant_win_price, current_bid,
                            expected_close_date, savings_amount, savings_percent
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item.get('lot_id'),
                        brand_name,
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
                        item.get('savings_amount', 0),
                        item.get('savings_percent', 0)
                    ))
                    
                    # Create alert for high-value items
                    if item.get('retail_price', 0) >= self.brands[brand_name]['avg_value']:
                        alert_msg = f"High-value {brand_name} item: {item.get('product_name', '')[:50]} - ${item.get('retail_price', 0)}"
                        cursor.execute('''
                            INSERT INTO brand_alerts (brand, lot_id, alert_type, message)
                            VALUES (?, ?, ?, ?)
                        ''', (brand_name, item.get('lot_id'), 'HIGH_VALUE', alert_msg))
                        
        conn.commit()
        conn.close()
        
    def display_brand_report(self, brand_items):
        """Display comprehensive brand tracking report."""
        print(f"\n🏷️ BRAND TRACKING REPORT")
        print("=" * 80)
        
        # Overall summary
        total_items = sum(len(items) for items in brand_items.values())
        total_value = sum(sum(item.get('retail_price', 0) for item in items) for items in brand_items.values())
        
        print(f"\n📊 OVERVIEW")
        print("-" * 40)
        print(f"🏷️  Total Brands Tracked: {len(brand_items)}")
        print(f"📦 Total Items Found: {total_items}")
        print(f"💰 Total Retail Value: ${total_value:,.2f}")
        
        # Brand-by-brand breakdown
        print(f"\n🏷️ BRAND BREAKDOWN")
        print("-" * 60)
        
        for brand_name, items in sorted(brand_items.items(), key=lambda x: len(x[1]), reverse=True):
            if not items:
                continue
                
            brand_value = sum(item.get('retail_price', 0) for item in items)
            brand_savings = sum(item.get('savings_amount', 0) for item in items)
            avg_value = brand_value / len(items) if items else 0
            avg_savings = (brand_savings / brand_value * 100) if brand_value > 0 else 0
            
            priority = self.brands[brand_name]['priority']
            
            print(f"\n🏷️ {brand_name} ({priority} Priority)")
            print(f"   📦 Items: {len(items)} | 💰 Value: ${brand_value:,.0f} | 📈 Avg: ${avg_value:.0f} | 💸 Savings: {avg_savings:.0f}%")
            
            # Location breakdown for this brand
            by_location = defaultdict(list)
            for item in items:
                location = item.get('auction_location', 'Unknown')
                by_location[location].append(item)
                
            for location in self.sc_locations:
                location_items = by_location.get(location, [])
                if location_items:
                    print(f"      📍 {location}: {len(location_items)} items")
                    
            # Top items for this brand
            top_items = sorted(items, key=lambda x: x.get('retail_price', 0), reverse=True)[:3]
            for i, item in enumerate(top_items, 1):
                product_name = item.get('product_name', 'Unknown')[:40]
                retail_price = item.get('retail_price', 0)
                instant_win = item.get('instant_win_price', 0)
                location = item.get('auction_location', 'Unknown')
                
                print(f"      {i}. {product_name}... | ${retail_price} → ${instant_win} | {location}")
                
        # High-value alerts
        print(f"\n🚨 HIGH-VALUE ALERTS")
        print("-" * 40)
        
        high_value_items = []
        for brand_name, items in brand_items.items():
            brand_avg = self.brands[brand_name]['avg_value']
            for item in items:
                if item.get('retail_price', 0) >= brand_avg:
                    high_value_items.append((brand_name, item))
                    
        high_value_items.sort(key=lambda x: x[1].get('retail_price', 0), reverse=True)
        
        for i, (brand_name, item) in enumerate(high_value_items[:10], 1):
            product_name = item.get('product_name', 'Unknown')[:40]
            retail_price = item.get('retail_price', 0)
            instant_win = item.get('instant_win_price', 0)
            location = item.get('auction_location', 'Unknown')
            savings = item.get('savings_amount', 0)
            
            print(f"{i:2d}. 🏷️ {brand_name} | {product_name}...")
            print(f"     💰 ${retail_price} → ${instant_win} | 💸 Save ${savings:.0f} | 📍 {location}")
            
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"brand_tracking_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(brand_items, f, indent=2)
        print(f"\n💾 Brand tracking data saved to: {filename}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Premium Brand Tracker')
    parser.add_argument('--brand', type=str, help='Track specific brand')
    parser.add_argument('--all', action='store_true', help='Track all brands')
    parser.add_argument('--list-brands', action='store_true', help='List available brands')
    
    args = parser.parse_args()
    
    tracker = BrandTracker()
    
    if args.list_brands:
        print("🏷️ Available Brands to Track:")
        print("=" * 40)
        for brand, info in tracker.brands.items():
            print(f"{brand:12s} ({info['priority']:6s}): Avg ${info['avg_value']} | {len(info['terms'])} search terms")
        return
        
    await tracker.create_session()
    
    try:
        if args.brand:
            if args.brand in tracker.brands:
                items = await tracker.track_brand(args.brand)
                brand_items = {args.brand: items}
            else:
                print(f"❌ Unknown brand: {args.brand}")
                print(f"Available brands: {', '.join(tracker.brands.keys())}")
                return
        else:
            brand_items = await tracker.track_all_brands()
            
        tracker.save_brand_data(brand_items)
        tracker.display_brand_report(brand_items)
        
    finally:
        await tracker.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 