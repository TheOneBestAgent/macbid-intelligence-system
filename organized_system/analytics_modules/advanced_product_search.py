#!/usr/bin/env python3
"""
🔍 Advanced Product Search Scraper - Monitor Specific Brands, Models & Keywords
Search for specific products, track inventory levels, and alert when items appear
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import re

class AdvancedProductSearch:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        self.db_file = "product_search.db"
        self.init_database()
        
        # Premium brands to monitor
        self.premium_brands = {
            'Apple': {
                'models': ['iphone 15', 'iphone 14', 'macbook pro', 'macbook air', 'ipad pro', 'airpods pro', 'apple watch'],
                'keywords': ['apple', 'iphone', 'macbook', 'ipad', 'airpods'],
                'min_value': 300,
                'priority': 'HIGH'
            },
            'Sony': {
                'models': ['wh-1000xm5', 'wh-1000xm4', 'playstation 5', 'ps5', 'a7r', 'fx6'],
                'keywords': ['sony', 'playstation', 'ps5', 'wh-1000'],
                'min_value': 200,
                'priority': 'HIGH'
            },
            'Samsung': {
                'models': ['galaxy s24', 'galaxy s23', 'galaxy tab', 'qled', 'neo qled'],
                'keywords': ['samsung', 'galaxy', 'qled'],
                'min_value': 250,
                'priority': 'HIGH'
            },
            'Nintendo': {
                'models': ['switch oled', 'switch lite', 'nintendo switch'],
                'keywords': ['nintendo', 'switch'],
                'min_value': 150,
                'priority': 'MEDIUM'
            },
            'Dyson': {
                'models': ['v15', 'v12', 'v11', 'airwrap', 'supersonic'],
                'keywords': ['dyson'],
                'min_value': 200,
                'priority': 'HIGH'
            },
            'Bose': {
                'models': ['quietcomfort', 'soundlink', 'wave'],
                'keywords': ['bose'],
                'min_value': 100,
                'priority': 'MEDIUM'
            },
            'DeWalt': {
                'models': ['20v max', 'flexvolt', 'atomic'],
                'keywords': ['dewalt'],
                'min_value': 50,
                'priority': 'MEDIUM'
            },
            'Milwaukee': {
                'models': ['m18', 'm12', 'fuel'],
                'keywords': ['milwaukee'],
                'min_value': 50,
                'priority': 'MEDIUM'
            }
        }
        
        # Rare/valuable item patterns
        self.rare_patterns = [
            r'limited edition',
            r'collector',
            r'vintage',
            r'rare',
            r'first edition',
            r'prototype',
            r'signed',
            r'autographed'
        ]
        
    def init_database(self):
        """Initialize product search database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Product inventory tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT UNIQUE,
                product_name TEXT,
                brand TEXT,
                model TEXT,
                upc TEXT,
                auction_location TEXT,
                retail_price REAL,
                instant_win_price REAL,
                current_bid REAL,
                discount_percent REAL,
                rarity_score INTEGER,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'ACTIVE'
            )
        ''')
        
        # Search alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                product_name TEXT,
                brand TEXT,
                alert_type TEXT,
                trigger_keyword TEXT,
                retail_price REAL,
                instant_win_price REAL,
                discount_percent REAL,
                rarity_score INTEGER,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Brand monitoring
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brand_monitors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT,
                keyword TEXT,
                min_value REAL,
                max_value REAL,
                min_discount REAL,
                location_filter TEXT,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # UPC tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS upc_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upc TEXT,
                product_name TEXT,
                brand TEXT,
                model TEXT,
                target_price REAL,
                alert_threshold REAL,
                times_seen INTEGER DEFAULT 0,
                last_seen TIMESTAMP,
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
            
    async def search_for_term(self, term, limit=200):
        """Search for a specific term."""
        url = f"https://api.macdiscount.com/search?q={term}&limit={limit}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get('hits', [])
                    
                    sc_hits = []
                    for hit in hits:
                        if hit.get('auction_location') in self.sc_locations:
                            sc_hits.append(hit)
                            
                    return sc_hits
                else:
                    return []
        except Exception as e:
            return []
            
    def extract_brand_model(self, product_name):
        """Extract brand and model from product name."""
        if not product_name:
            return None, None
            
        product_lower = product_name.lower()
        
        # Check for known brands
        for brand, info in self.premium_brands.items():
            for keyword in info['keywords']:
                if keyword.lower() in product_lower:
                    # Try to extract model
                    for model in info['models']:
                        if model.lower() in product_lower:
                            return brand, model
                    return brand, None
                    
        return None, None
        
    def calculate_rarity_score(self, product_name, retail_price, instant_win_price):
        """Calculate rarity score based on various factors."""
        if not product_name:
            return 0
            
        score = 0
        product_lower = product_name.lower()
        
        # Check for rare patterns
        for pattern in self.rare_patterns:
            if re.search(pattern, product_lower):
                score += 30
                
        # High-value items get points
        if retail_price > 1000:
            score += 20
        elif retail_price > 500:
            score += 10
            
        # High discount percentage
        if retail_price > 0 and instant_win_price > 0:
            discount = ((retail_price - instant_win_price) / retail_price) * 100
            if discount > 50:
                score += 25
            elif discount > 30:
                score += 15
                
        # Brand premium
        brand, _ = self.extract_brand_model(product_name)
        if brand in ['Apple', 'Sony', 'Dyson']:
            score += 15
        elif brand in ['Samsung', 'Bose', 'Nintendo']:
            score += 10
            
        return min(score, 100)  # Cap at 100
        
    def detect_valuable_items(self, items):
        """Detect potentially valuable or rare items."""
        valuable_items = []
        
        for item in items:
            product_name = item.get('product_name', '')
            retail_price = item.get('retail_price', 0)
            instant_win_price = item.get('instant_win_price', 0)
            
            rarity_score = self.calculate_rarity_score(product_name, retail_price, instant_win_price)
            
            # High-value threshold
            if rarity_score >= 40 or retail_price >= 500:
                brand, model = self.extract_brand_model(product_name)
                
                discount_percent = 0
                if retail_price > 0 and instant_win_price > 0:
                    discount_percent = ((retail_price - instant_win_price) / retail_price) * 100
                    
                valuable_items.append({
                    'item': item,
                    'brand': brand,
                    'model': model,
                    'rarity_score': rarity_score,
                    'discount_percent': discount_percent
                })
                
        return valuable_items
        
    async def monitor_premium_brands(self):
        """Monitor all premium brands for new items."""
        print("🔍 ADVANCED PRODUCT SEARCH")
        print("🏷️  Monitoring premium brands and rare items...")
        print()
        
        all_items = []
        seen_lot_ids = set()
        
        for brand, info in self.premium_brands.items():
            print(f"🔎 Searching {brand} products...")
            
            brand_items = []
            
            # Search by brand keywords
            for keyword in info['keywords']:
                results = await self.search_for_term(keyword)
                
                for result in results:
                    lot_id = result.get('lot_id')
                    if lot_id and lot_id not in seen_lot_ids:
                        retail_price = result.get('retail_price', 0)
                        
                        if retail_price >= info['min_value']:
                            # Enhance with brand/model info
                            detected_brand, detected_model = self.extract_brand_model(result.get('product_name', ''))
                            result['detected_brand'] = detected_brand or brand
                            result['detected_model'] = detected_model
                            result['priority'] = info['priority']
                            result['rarity_score'] = self.calculate_rarity_score(
                                result.get('product_name', ''),
                                retail_price,
                                result.get('instant_win_price', 0)
                            )
                            
                            brand_items.append(result)
                            seen_lot_ids.add(lot_id)
                            
                await asyncio.sleep(0.15)
                
            all_items.extend(brand_items)
            print(f"   Found {len(brand_items)} {brand} items")
            
        return all_items
        
    def save_inventory_data(self, items):
        """Save inventory data to database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        for item in items:
            retail_price = item.get('retail_price', 0)
            instant_win_price = item.get('instant_win_price', 0)
            
            discount_percent = 0
            if retail_price > 0 and instant_win_price > 0:
                discount_percent = ((retail_price - instant_win_price) / retail_price) * 100
                
            cursor.execute('''
                INSERT OR REPLACE INTO product_inventory (
                    lot_id, product_name, brand, model, auction_location,
                    retail_price, instant_win_price, current_bid,
                    discount_percent, rarity_score, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                item.get('lot_id'),
                item.get('product_name'),
                item.get('detected_brand'),
                item.get('detected_model'),
                item.get('auction_location'),
                retail_price,
                instant_win_price,
                item.get('current_bid', 0),
                discount_percent,
                item.get('rarity_score', 0)
            ))
            
        conn.commit()
        conn.close()
        
    def generate_search_alerts(self, items):
        """Generate alerts for valuable finds."""
        alerts = []
        
        for item in items:
            product_name = item.get('product_name', '')
            retail_price = item.get('retail_price', 0)
            instant_win_price = item.get('instant_win_price', 0)
            rarity_score = item.get('rarity_score', 0)
            brand = item.get('detected_brand')
            priority = item.get('priority', 'MEDIUM')
            
            discount_percent = 0
            if retail_price > 0 and instant_win_price > 0:
                discount_percent = ((retail_price - instant_win_price) / retail_price) * 100
                
            # High-priority brand alert
            if priority == 'HIGH' and discount_percent > 25:
                alerts.append({
                    'lot_id': item.get('lot_id'),
                    'product_name': product_name,
                    'brand': brand,
                    'alert_type': 'HIGH_PRIORITY_BRAND',
                    'trigger_keyword': brand,
                    'retail_price': retail_price,
                    'instant_win_price': instant_win_price,
                    'discount_percent': discount_percent,
                    'rarity_score': rarity_score,
                    'message': f"High-priority {brand} item with {discount_percent:.1f}% discount"
                })
                
            # Rare item alert
            if rarity_score >= 50:
                alerts.append({
                    'lot_id': item.get('lot_id'),
                    'product_name': product_name,
                    'brand': brand,
                    'alert_type': 'RARE_ITEM',
                    'trigger_keyword': 'rarity',
                    'retail_price': retail_price,
                    'instant_win_price': instant_win_price,
                    'discount_percent': discount_percent,
                    'rarity_score': rarity_score,
                    'message': f"Rare item detected (score: {rarity_score})"
                })
                
            # High-value item alert
            if retail_price >= 1000 and discount_percent > 20:
                alerts.append({
                    'lot_id': item.get('lot_id'),
                    'product_name': product_name,
                    'brand': brand,
                    'alert_type': 'HIGH_VALUE',
                    'trigger_keyword': 'high_value',
                    'retail_price': retail_price,
                    'instant_win_price': instant_win_price,
                    'discount_percent': discount_percent,
                    'rarity_score': rarity_score,
                    'message': f"High-value item (${retail_price}) with {discount_percent:.1f}% discount"
                })
                
        return alerts
        
    def display_search_report(self, items, alerts):
        """Display comprehensive search report."""
        print(f"\n🔍 ADVANCED PRODUCT SEARCH REPORT")
        print("=" * 80)
        
        if not items:
            print("❌ No premium products found")
            return
            
        print(f"🎯 Found {len(items)} premium products across {len(self.premium_brands)} brands")
        print()
        
        # Brand breakdown
        by_brand = defaultdict(list)
        total_retail_value = 0
        total_instant_win_value = 0
        
        for item in items:
            brand = item.get('detected_brand', 'Unknown')
            by_brand[brand].append(item)
            total_retail_value += item.get('retail_price', 0)
            total_instant_win_value += item.get('instant_win_price', 0)
            
        print(f"💰 INVENTORY OVERVIEW")
        print("-" * 50)
        print(f"📦 Total Premium Items: {len(items)}")
        print(f"💵 Total Retail Value: ${total_retail_value:,.2f}")
        print(f"🏷️  Total Instant Win Value: ${total_instant_win_value:,.2f}")
        
        overall_discount = ((total_retail_value - total_instant_win_value) / total_retail_value * 100) if total_retail_value > 0 else 0
        print(f"📉 Average Discount: {overall_discount:.1f}%")
        
        print(f"\n🏷️  BRAND INVENTORY")
        print("-" * 60)
        
        for brand, brand_items in sorted(by_brand.items(), key=lambda x: len(x[1]), reverse=True):
            if brand == 'Unknown':
                continue
                
            brand_retail = sum(item.get('retail_price', 0) for item in brand_items)
            brand_instant_win = sum(item.get('instant_win_price', 0) for item in brand_items)
            brand_discount = ((brand_retail - brand_instant_win) / brand_retail * 100) if brand_retail > 0 else 0
            
            # Get priority
            priority = self.premium_brands.get(brand, {}).get('priority', 'MEDIUM')
            priority_icon = {"HIGH": "🔥", "MEDIUM": "⭐", "LOW": "📦"}.get(priority, "📦")
            
            print(f"{priority_icon} {brand:12s} | {len(brand_items):2d} items | ${brand_retail:8,.0f} retail | {brand_discount:5.1f}% avg discount")
            
        # Location breakdown
        print(f"\n📍 LOCATION BREAKDOWN")
        print("-" * 50)
        
        by_location = defaultdict(list)
        for item in items:
            location = item.get('auction_location', 'Unknown')
            by_location[location].append(item)
            
        for location, location_items in sorted(by_location.items(), key=lambda x: len(x[1]), reverse=True):
            location_retail = sum(item.get('retail_price', 0) for item in location_items)
            print(f"📍 {location:12s}: {len(location_items):2d} items | ${location_retail:8,.0f} retail value")
            
        # Alerts
        if alerts:
            print(f"\n🚨 SEARCH ALERTS ({len(alerts)} high-priority items)")
            print("-" * 70)
            
            for alert in alerts[:15]:
                product_name = alert['product_name'][:45] if alert['product_name'] else 'Unknown'
                alert_type = alert['alert_type']
                retail_price = alert['retail_price']
                instant_win_price = alert['instant_win_price']
                discount = alert['discount_percent']
                rarity = alert['rarity_score']
                
                alert_icons = {
                    'HIGH_PRIORITY_BRAND': '🔥',
                    'RARE_ITEM': '💎',
                    'HIGH_VALUE': '💰'
                }
                icon = alert_icons.get(alert_type, '⚠️')
                
                print(f"{icon} {product_name}...")
                print(f"     💵 ${retail_price} → ${instant_win_price} ({discount:.1f}% off) | Rarity: {rarity}")
                print()
                
        # Top finds by category
        print(f"\n💎 TOP FINDS BY RARITY")
        print("-" * 60)
        
        # Sort by rarity score
        top_items = sorted(items, key=lambda x: x.get('rarity_score', 0), reverse=True)[:10]
        
        for i, item in enumerate(top_items, 1):
            product_name = item.get('product_name', 'Unknown')[:40]
            brand = item.get('detected_brand', 'Unknown')
            retail_price = item.get('retail_price', 0)
            instant_win_price = item.get('instant_win_price', 0)
            rarity_score = item.get('rarity_score', 0)
            location = item.get('auction_location', 'Unknown')
            
            discount = ((retail_price - instant_win_price) / retail_price * 100) if retail_price > 0 else 0
            
            print(f"{i:2d}. 💎 {product_name}...")
            print(f"     🏷️  {brand} | ${retail_price} → ${instant_win_price} ({discount:.1f}% off)")
            print(f"     ⭐ Rarity: {rarity_score} | 📍 {location}")
            print()
            
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"product_search_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'summary': {
                    'total_items': len(items),
                    'total_retail_value': total_retail_value,
                    'total_instant_win_value': total_instant_win_value,
                    'overall_discount': overall_discount
                },
                'by_brand': {brand: len(items) for brand, items in by_brand.items()},
                'by_location': {loc: len(items) for loc, items in by_location.items()},
                'alerts': alerts,
                'top_items': top_items[:20]
            }, f, indent=2)
            
        print(f"💾 Product search report saved to: {filename}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Advanced Product Search')
    parser.add_argument('--brand', type=str, help='Search specific brand only')
    parser.add_argument('--min-value', type=int, default=0, help='Minimum retail value')
    parser.add_argument('--alerts-only', action='store_true', help='Show only alerts')
    parser.add_argument('--rare-only', action='store_true', help='Show only rare items (rarity >= 50)')
    
    args = parser.parse_args()
    
    searcher = AdvancedProductSearch()
    await searcher.create_session()
    
    try:
        items = await searcher.monitor_premium_brands()
        
        # Apply filters
        if args.brand:
            items = [item for item in items if item.get('detected_brand', '').lower() == args.brand.lower()]
            
        if args.min_value:
            items = [item for item in items if item.get('retail_price', 0) >= args.min_value]
            
        if args.rare_only:
            items = [item for item in items if item.get('rarity_score', 0) >= 50]
            
        searcher.save_inventory_data(items)
        alerts = searcher.generate_search_alerts(items)
        
        if args.alerts_only and alerts:
            print("🚨 PRODUCT SEARCH ALERTS")
            for alert in alerts:
                print(f"• {alert['message']}")
        else:
            searcher.display_search_report(items, alerts)
            
    finally:
        await searcher.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 