#!/usr/bin/env python3
"""
📊 Price Analytics Tracker - Monitor Pricing Trends & Build Historical Database
Track closing prices, identify trends, and alert on unusual pricing patterns
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class PriceAnalyticsTracker:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        self.db_file = "price_analytics.db"
        self.init_database()
        
        # Product categories to track pricing for
        self.price_categories = {
            'Electronics': {
                'terms': ['laptop', 'macbook', 'iphone', 'ipad', 'samsung', 'tv', 'monitor'],
                'min_value': 200,
                'volatility_threshold': 0.3
            },
            'Audio Equipment': {
                'terms': ['headphones', 'speaker', 'soundbar', 'beats', 'bose', 'sony'],
                'min_value': 100,
                'volatility_threshold': 0.25
            },
            'Appliances': {
                'terms': ['refrigerator', 'washer', 'dryer', 'dishwasher', 'microwave'],
                'min_value': 300,
                'volatility_threshold': 0.2
            },
            'Tools': {
                'terms': ['dewalt', 'milwaukee', 'makita', 'drill', 'saw'],
                'min_value': 50,
                'volatility_threshold': 0.35
            },
            'Luxury Items': {
                'terms': ['rolex', 'omega', 'cartier', 'diamond', 'gold'],
                'min_value': 500,
                'volatility_threshold': 0.4
            },
            'Gaming': {
                'terms': ['xbox', 'playstation', 'nintendo', 'gaming'],
                'min_value': 150,
                'volatility_threshold': 0.25
            }
        }
        
    def init_database(self):
        """Initialize price analytics database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                product_name TEXT,
                category TEXT,
                auction_location TEXT,
                retail_price REAL,
                instant_win_price REAL,
                current_bid REAL,
                closing_date TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                price_change_percent REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                product_name TEXT,
                category TEXT,
                alert_type TEXT,
                current_discount REAL,
                expected_discount REAL,
                deviation_percent REAL,
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
                    
                    sc_hits = []
                    for hit in hits:
                        if hit.get('auction_location') in self.sc_locations:
                            sc_hits.append(hit)
                            
                    return sc_hits
                else:
                    return []
        except Exception as e:
            return []
            
    def categorize_product(self, product_name):
        """Categorize product based on name."""
        if not product_name:
            return "Unknown"
            
        product_lower = product_name.lower()
        
        for category, info in self.price_categories.items():
            for term in info['terms']:
                if term.lower() in product_lower:
                    return category
                    
        return "Other"
        
    async def collect_price_data(self):
        """Collect current price data across all categories."""
        print("📊 PRICE ANALYTICS TRACKER")
        print("🔍 Collecting price data across all categories...")
        print()
        
        all_items = []
        seen_lot_ids = set()
        
        for category, info in self.price_categories.items():
            print(f"📂 Analyzing {category}...")
            
            category_items = []
            for term in info['terms']:
                results = await self.search_for_term(term)
                
                for result in results:
                    lot_id = result.get('lot_id')
                    if lot_id and lot_id not in seen_lot_ids:
                        retail_price = result.get('retail_price', 0)
                        
                        if retail_price >= info['min_value']:
                            result['category'] = category
                            category_items.append(result)
                            seen_lot_ids.add(lot_id)
                            
                await asyncio.sleep(0.2)
                
            all_items.extend(category_items)
            print(f"   Found {len(category_items)} items in {category}")
            
        return all_items
        
    def analyze_price_trends(self, items):
        """Analyze price trends by category and location."""
        trends = {}
        
        by_category_location = defaultdict(list)
        for item in items:
            category = item.get('category', 'Unknown')
            location = item.get('auction_location', 'Unknown')
            key = f"{category}_{location}"
            by_category_location[key].append(item)
            
        for key, group_items in by_category_location.items():
            if len(group_items) < 3:
                continue
                
            category, location = key.split('_', 1)
            
            retail_prices = [item.get('retail_price', 0) for item in group_items if item.get('retail_price', 0) > 0]
            instant_win_prices = [item.get('instant_win_price', 0) for item in group_items if item.get('instant_win_price', 0) > 0]
            
            if retail_prices and instant_win_prices:
                avg_retail = statistics.mean(retail_prices)
                avg_instant_win = statistics.mean(instant_win_prices)
                
                discounts = []
                for item in group_items:
                    retail = item.get('retail_price', 0)
                    instant_win = item.get('instant_win_price', 0)
                    if retail > 0 and instant_win > 0:
                        discount = ((retail - instant_win) / retail) * 100
                        discounts.append(discount)
                        
                if discounts:
                    avg_discount = statistics.mean(discounts)
                    volatility = statistics.stdev(discounts) if len(discounts) > 1 else 0
                    
                    trend_direction = "STABLE"
                    if volatility > 20:
                        trend_direction = "VOLATILE"
                    elif avg_discount > 30:
                        trend_direction = "DECLINING"
                    elif avg_discount < 10:
                        trend_direction = "RISING"
                        
                    trends[key] = {
                        'category': category,
                        'location': location,
                        'avg_retail_price': avg_retail,
                        'avg_instant_win_price': avg_instant_win,
                        'avg_discount_percent': avg_discount,
                        'price_volatility': volatility,
                        'sample_size': len(group_items),
                        'trend_direction': trend_direction
                    }
                    
        return trends
        
    def generate_price_alerts(self, items, trends):
        """Generate price alerts for unusual patterns."""
        alerts = []
        
        for item in items:
            category = item.get('category', 'Unknown')
            location = item.get('auction_location', 'Unknown')
            trend_key = f"{category}_{location}"
            
            if trend_key in trends:
                trend = trends[trend_key]
                retail_price = item.get('retail_price', 0)
                instant_win_price = item.get('instant_win_price', 0)
                
                if retail_price > 0 and instant_win_price > 0:
                    discount_percent = ((retail_price - instant_win_price) / retail_price) * 100
                    expected_discount = trend['avg_discount_percent']
                    deviation = abs(discount_percent - expected_discount)
                    
                    if deviation > 25:
                        alert_type = "PRICE_ANOMALY_HIGH" if discount_percent > expected_discount else "PRICE_ANOMALY_LOW"
                        
                        alerts.append({
                            'lot_id': item.get('lot_id'),
                            'product_name': item.get('product_name'),
                            'category': category,
                            'alert_type': alert_type,
                            'current_discount': discount_percent,
                            'expected_discount': expected_discount,
                            'deviation_percent': deviation,
                            'message': f"Unusual pricing: {discount_percent:.1f}% discount vs expected {expected_discount:.1f}%"
                        })
                        
        return alerts
        
    def display_price_analytics_report(self, items, trends, alerts):
        """Display comprehensive price analytics report."""
        print(f"\n📊 PRICE ANALYTICS REPORT")
        print("=" * 80)
        
        if not items:
            print("❌ No price data collected")
            return
            
        print(f"📈 Analyzed {len(items)} items across {len(self.price_categories)} categories")
        print()
        
        total_retail_value = sum(item.get('retail_price', 0) for item in items)
        total_instant_win_value = sum(item.get('instant_win_price', 0) for item in items if item.get('instant_win_price', 0) > 0)
        overall_discount = ((total_retail_value - total_instant_win_value) / total_retail_value * 100) if total_retail_value > 0 else 0
        
        print(f"💰 MARKET OVERVIEW")
        print("-" * 40)
        print(f"📦 Total Items Analyzed: {len(items)}")
        print(f"💵 Total Retail Value: ${total_retail_value:,.2f}")
        print(f"🏷️  Total Instant Win Value: ${total_instant_win_value:,.2f}")
        print(f"📉 Overall Market Discount: {overall_discount:.1f}%")
        
        print(f"\n📂 CATEGORY PRICE TRENDS")
        print("-" * 60)
        
        for trend_key, trend in sorted(trends.items(), key=lambda x: x[1]['avg_discount_percent'], reverse=True):
            category = trend['category']
            location = trend['location']
            avg_discount = trend['avg_discount_percent']
            volatility = trend['price_volatility']
            direction = trend['trend_direction']
            sample_size = trend['sample_size']
            
            direction_icon = {"DECLINING": "📉", "RISING": "📈", "VOLATILE": "📊", "STABLE": "➡️"}.get(direction, "❓")
            
            print(f"{direction_icon} {category:15s} | {location:10s} | {avg_discount:5.1f}% avg discount | {volatility:4.1f}% volatility | {sample_size:2d} items")
            
        if alerts:
            print(f"\n🚨 PRICE ALERTS ({len(alerts)} anomalies detected)")
            print("-" * 70)
            
            for alert in alerts[:10]:
                product_name = alert['product_name'][:40] if alert['product_name'] else 'Unknown'
                current_discount = alert['current_discount']
                expected_discount = alert['expected_discount']
                deviation = alert['deviation_percent']
                
                alert_icon = "🔥" if "HIGH" in alert['alert_type'] else "❄️"
                
                print(f"{alert_icon} {product_name}...")
                print(f"     📊 {current_discount:.1f}% discount (expected {expected_discount:.1f}%) | Deviation: {deviation:.1f}%")
                print()
                
        print(f"\n💎 BEST DEALS BY CATEGORY")
        print("-" * 60)
        
        by_category = defaultdict(list)
        for item in items:
            category = item.get('category', 'Unknown')
            by_category[category].append(item)
            
        for category, category_items in by_category.items():
            deals = []
            for item in category_items:
                retail = item.get('retail_price', 0)
                instant_win = item.get('instant_win_price', 0)
                if retail > 0 and instant_win > 0:
                    discount = ((retail - instant_win) / retail) * 100
                    deals.append((item, discount))
                    
            if deals:
                deals.sort(key=lambda x: x[1], reverse=True)
                best_deal = deals[0]
                item, discount = best_deal
                
                product_name = item.get('product_name', 'Unknown')[:35]
                retail_price = item.get('retail_price', 0)
                instant_win = item.get('instant_win_price', 0)
                location = item.get('auction_location', 'Unknown')
                
                print(f"💎 {category:15s}: {discount:5.1f}% off | {product_name}... | ${retail_price} → ${instant_win} | {location}")
                
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"price_analytics_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'summary': {
                    'total_items': len(items),
                    'total_retail_value': total_retail_value,
                    'overall_discount': overall_discount
                },
                'trends': trends,
                'alerts': alerts
            }, f, indent=2)
            
        print(f"\n💾 Price analytics report saved to: {filename}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Price Analytics Tracker')
    parser.add_argument('--category', type=str, help='Analyze specific category only')
    parser.add_argument('--alerts-only', action='store_true', help='Show only price alerts')
    
    args = parser.parse_args()
    
    tracker = PriceAnalyticsTracker()
    await tracker.create_session()
    
    try:
        items = await tracker.collect_price_data()
        
        if args.category:
            items = [item for item in items if item.get('category', '').lower() == args.category.lower()]
            
        trends = tracker.analyze_price_trends(items)
        alerts = tracker.generate_price_alerts(items, trends)
        
        if args.alerts_only and alerts:
            print("🚨 PRICE ALERTS")
            for alert in alerts:
                print(f"• {alert['message']}")
        else:
            tracker.display_price_analytics_report(items, trends, alerts)
            
    finally:
        await tracker.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 