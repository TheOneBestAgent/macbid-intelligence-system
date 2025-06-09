#!/usr/bin/env python3
"""
🚨 New Arrival Monitor - Track Fresh Inventory in SC Warehouses
Monitor for newly added lots and get alerts for high-value items
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

class NewArrivalMonitor:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        self.db_file = "new_arrivals.db"
        self.init_database()
        
        # Categories to monitor for high-value items
        self.priority_terms = [
            "macbook", "iphone", "ipad", "apple", "sony", "samsung", "nintendo",
            "xbox", "playstation", "rolex", "omega", "dyson", "kitchenaid",
            "dewalt", "milwaukee", "canon", "nikon", "bose", "beats"
        ]
        
    def init_database(self):
        """Initialize SQLite database for tracking arrivals."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arrivals (
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
                expected_close_date TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_priority INTEGER DEFAULT 0,
                is_notified INTEGER DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                alert_type TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lot_id) REFERENCES arrivals (lot_id)
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
            
    async def scan_for_new_arrivals(self):
        """Scan for new arrivals across priority terms."""
        print(f"🔍 Scanning for new arrivals...")
        print(f"📝 Monitoring {len(self.priority_terms)} priority terms")
        print()
        
        all_items = []
        seen_lot_ids = set()
        
        for i, term in enumerate(self.priority_terms, 1):
            print(f"  {i:2d}/{len(self.priority_terms)} - Scanning '{term}'...")
            
            results = await self.search_for_term(term)
            
            # Deduplicate by lot_id
            new_results = []
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    seen_lot_ids.add(lot_id)
                    new_results.append(result)
                    
            all_items.extend(new_results)
            print(f"      Found {len(results)} total, {len(new_results)} unique items")
            
            await asyncio.sleep(0.2)  # Rate limiting
            
        return all_items
        
    def process_arrivals(self, items):
        """Process items and identify new arrivals."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        new_arrivals = []
        priority_arrivals = []
        
        for item in items:
            lot_id = item.get('lot_id')
            if not lot_id:
                continue
                
            # Check if we've seen this item before
            cursor.execute('SELECT lot_id FROM arrivals WHERE lot_id = ?', (lot_id,))
            existing = cursor.fetchone()
            
            if not existing:
                # New arrival!
                product_name = item.get('product_name', 'Unknown Product')
                auction_location = item.get('auction_location', 'Unknown')
                auction_number = item.get('auction_number', 'Unknown')
                lot_number = item.get('lot_number', 'Unknown')
                category = item.get('category', 'Unknown')
                condition = item.get('condition', 'Unknown')
                retail_price = item.get('retail_price', 0)
                instant_win_price = item.get('instant_win_price', 0)
                current_bid = item.get('current_bid', 0)
                closing_date = item.get('expected_close_date', 'Unknown')
                
                # Determine if this is a priority item
                is_priority = self.is_priority_item(item)
                
                # Insert into database
                cursor.execute('''
                    INSERT INTO arrivals (
                        lot_id, product_name, auction_location, auction_number,
                        lot_number, category, condition_desc, retail_price,
                        instant_win_price, current_bid, expected_close_date, is_priority
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lot_id, product_name, auction_location, auction_number,
                    lot_number, category, condition, retail_price,
                    instant_win_price, current_bid, closing_date, is_priority
                ))
                
                new_arrivals.append(item)
                
                if is_priority:
                    priority_arrivals.append(item)
                    
                    # Create alert
                    alert_message = f"Priority item: {product_name[:50]} - ${retail_price} in {auction_location}"
                    cursor.execute('''
                        INSERT INTO alerts (lot_id, alert_type, message)
                        VALUES (?, ?, ?)
                    ''', (lot_id, 'PRIORITY_ARRIVAL', alert_message))
                    
        conn.commit()
        conn.close()
        
        return new_arrivals, priority_arrivals
        
    def is_priority_item(self, item):
        """Determine if an item is high priority."""
        retail_price = item.get('retail_price', 0)
        instant_win_price = item.get('instant_win_price', 0)
        product_name = item.get('product_name', '').lower()
        
        # High retail value
        if retail_price >= 500:
            return True
            
        # Good savings
        if instant_win_price > 0 and retail_price > 0:
            savings_percent = ((retail_price - instant_win_price) / retail_price) * 100
            if savings_percent >= 40:
                return True
                
        # Premium brands
        premium_brands = ['apple', 'macbook', 'iphone', 'ipad', 'sony', 'samsung', 
                         'rolex', 'omega', 'dyson', 'kitchenaid', 'nintendo', 'xbox']
        
        for brand in premium_brands:
            if brand in product_name:
                return True
                
        return False
        
    def display_new_arrivals(self, new_arrivals, priority_arrivals):
        """Display new arrivals."""
        if not new_arrivals:
            print("✅ No new arrivals found")
            return
            
        print(f"\n🎉 FOUND {len(new_arrivals)} NEW ARRIVALS!")
        if priority_arrivals:
            print(f"🚨 {len(priority_arrivals)} HIGH PRIORITY ITEMS!")
        print("=" * 70)
        
        # Show priority arrivals first
        if priority_arrivals:
            print(f"\n🚨 HIGH PRIORITY NEW ARRIVALS")
            print("-" * 50)
            
            for i, item in enumerate(priority_arrivals[:10], 1):
                self.display_item(item, i, "🚨")
                
        # Show all new arrivals by location
        by_location = defaultdict(list)
        for item in new_arrivals:
            location = item.get('auction_location', 'Unknown')
            by_location[location].append(item)
            
        print(f"\n📍 ALL NEW ARRIVALS BY LOCATION")
        print("-" * 50)
        
        for location in self.sc_locations:
            location_items = by_location.get(location, [])
            if not location_items:
                continue
                
            print(f"\n📍 {location} ({len(location_items)} new items)")
            print("-" * 30)
            
            # Sort by retail price (highest first)
            location_items.sort(key=lambda x: x.get('retail_price', 0), reverse=True)
            
            for i, item in enumerate(location_items[:5], 1):  # Show top 5 per location
                self.display_item(item, i)
                
            if len(location_items) > 5:
                print(f"      ... and {len(location_items) - 5} more new items")
                print()
                
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"new_arrivals_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(new_arrivals, f, indent=2)
        print(f"\n💾 New arrivals saved to: {filename}")
        
    def display_item(self, item, index, prefix=""):
        """Display a single item."""
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
        
        print(f"  {prefix}{index:2d}. 📦 {product_name[:50]}...")
        print(f"      📋 {auction_number} | Lot: {lot_number} | {category}")
        print(f"      💰 ${retail_price}", end="")
        if instant_win_price:
            print(f" → ${instant_win_price}", end="")
            if savings > 0:
                print(f" (Save ${savings:.0f} - {savings_percent:.0f}%)")
            else:
                print()
        else:
            print()
        print(f"      📦 {condition} | ⏰ Closes: {closing_date}")
        if current_bid > 0:
            print(f"      🔥 Current Bid: ${current_bid}")
        print()
        
    def show_recent_alerts(self, hours=24):
        """Show recent alerts."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        cursor.execute('''
            SELECT alert_type, message, created_at
            FROM alerts
            WHERE created_at >= ?
            ORDER BY created_at DESC
        ''', (since,))
        
        alerts = cursor.fetchall()
        conn.close()
        
        if not alerts:
            print(f"📭 No alerts in the last {hours} hours")
            return
            
        print(f"\n🚨 RECENT ALERTS (Last {hours} hours)")
        print("=" * 50)
        
        for alert_type, message, created_at in alerts:
            print(f"⏰ {created_at}")
            print(f"🚨 {alert_type}: {message}")
            print()

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='New Arrival Monitor')
    parser.add_argument('--scan', action='store_true', help='Scan for new arrivals')
    parser.add_argument('--alerts', type=int, default=24, help='Show alerts from last N hours')
    parser.add_argument('--monitor', action='store_true', help='Continuous monitoring mode')
    
    args = parser.parse_args()
    
    monitor = NewArrivalMonitor()
    
    if args.monitor:
        print("🔄 Starting continuous monitoring mode...")
        print("Press Ctrl+C to stop")
        
        await monitor.create_session()
        
        try:
            while True:
                print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Scanning...")
                
                items = await monitor.scan_for_new_arrivals()
                new_arrivals, priority_arrivals = monitor.process_arrivals(items)
                
                if new_arrivals:
                    monitor.display_new_arrivals(new_arrivals, priority_arrivals)
                else:
                    print("✅ No new arrivals")
                    
                print(f"😴 Sleeping for 10 minutes...")
                await asyncio.sleep(600)  # 10 minutes
                
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
        finally:
            await monitor.close_session()
            
    elif args.scan:
        await monitor.create_session()
        
        try:
            items = await monitor.scan_for_new_arrivals()
            new_arrivals, priority_arrivals = monitor.process_arrivals(items)
            monitor.display_new_arrivals(new_arrivals, priority_arrivals)
        finally:
            await monitor.close_session()
            
    else:
        monitor.show_recent_alerts(args.alerts)

if __name__ == "__main__":
    asyncio.run(main()) 