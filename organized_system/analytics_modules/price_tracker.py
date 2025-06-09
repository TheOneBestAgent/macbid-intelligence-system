#!/usr/bin/env python3
"""
📊 Price Tracking & Analytics Scraper for mac.bid
Monitors closing prices, tracks trends, and identifies deals
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import sys

class PriceTracker:
    def __init__(self, db_path="price_tracker.db"):
        self.db_path = db_path
        self.session = None
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for price tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auctions (
                id INTEGER PRIMARY KEY,
                auction_number TEXT UNIQUE,
                title TEXT,
                location_id INTEGER,
                location_name TEXT,
                opening_date TEXT,
                closing_date TEXT,
                current_price REAL,
                starting_price REAL,
                final_price REAL,
                bid_count INTEGER,
                status TEXT,
                category TEXT,
                last_updated TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id INTEGER,
                price REAL,
                timestamp TEXT,
                FOREIGN KEY (auction_id) REFERENCES auctions (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                max_price REAL,
                location_ids TEXT,
                alert_type TEXT,
                created_date TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def create_session(self):
        """Create HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        
    async def close_session(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            await asyncio.sleep(0.1)
            
    async def fetch_auctions(self, pages=10):
        """Fetch auction data from API."""
        if not self.session:
            await self.create_session()
            
        all_auctions = []
        
        for page in range(1, pages + 1):
            url = f"https://api.macdiscount.com/auctionsummary?pg={page}&ppg=20"
            
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        auctions = data.get('data', [])
                        all_auctions.extend(auctions)
                        print(f"📄 Fetched page {page}: {len(auctions)} auctions")
                    else:
                        print(f"⚠️  Page {page}: Status {response.status}")
                        
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
                
        return all_auctions
        
    def save_auction_data(self, auctions):
        """Save auction data to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for auction in auctions:
            auction_id = auction.get('id')
            auction_number = auction.get('auction_number', '')
            title = auction.get('title', auction.get('external_folder_name', ''))
            location_id = auction.get('location_id')
            location_name = auction.get('location_name', '')
            opening_date = auction.get('opening_date', '')
            closing_date = auction.get('closing_date', '')
            
            # Extract pricing info (would need to be enhanced with actual bid data)
            current_price = 0.0  # Would come from bid API
            starting_price = 0.0  # Would come from auction details
            final_price = None if auction.get('is_active', True) else 0.0
            
            # Determine category from title
            category = self.categorize_auction(title)
            
            # Insert or update auction
            cursor.execute('''
                INSERT OR REPLACE INTO auctions 
                (id, auction_number, title, location_id, location_name, 
                 opening_date, closing_date, current_price, starting_price, 
                 final_price, category, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (auction_id, auction_number, title, location_id, location_name,
                  opening_date, closing_date, current_price, starting_price,
                  final_price, category, datetime.now().isoformat()))
                  
            # Add price history entry
            cursor.execute('''
                INSERT INTO price_history (auction_id, price, timestamp)
                VALUES (?, ?, ?)
            ''', (auction_id, current_price, datetime.now().isoformat()))
            
        conn.commit()
        conn.close()
        
    def categorize_auction(self, title):
        """Categorize auction based on title."""
        if not title:
            return "Unknown"
            
        title_lower = title.lower()
        
        categories = {
            "Electronics": ["iphone", "ipad", "laptop", "computer", "tv", "phone", "tablet", "electronics"],
            "Clothing": ["clothing", "apparel", "shirt", "pants", "dress", "shoes", "fashion"],
            "Home": ["furniture", "home", "kitchen", "appliance", "decor", "bedding"],
            "Tools": ["tools", "hardware", "drill", "saw", "equipment"],
            "Automotive": ["car", "auto", "vehicle", "parts", "tire", "engine"],
            "Sports": ["sports", "fitness", "exercise", "bike", "golf", "outdoor"],
            "Books": ["books", "media", "dvd", "cd", "games"],
            "Jewelry": ["jewelry", "watch", "ring", "necklace", "gold", "silver"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
                
        return "General"
        
    def analyze_price_trends(self, days=30):
        """Analyze price trends over specified days."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get price trends by category
        cursor.execute('''
            SELECT category, AVG(current_price) as avg_price, COUNT(*) as count,
                   MIN(current_price) as min_price, MAX(current_price) as max_price
            FROM auctions 
            WHERE last_updated > datetime('now', '-{} days')
            GROUP BY category
            ORDER BY count DESC
        '''.format(days))
        
        trends = cursor.fetchall()
        
        print(f"📊 Price Trends (Last {days} days)")
        print("=" * 60)
        
        for category, avg_price, count, min_price, max_price in trends:
            print(f"🏷️  {category}:")
            print(f"   📊 {count} auctions | Avg: ${avg_price:.2f} | Range: ${min_price:.2f}-${max_price:.2f}")
            
        # Get location-based trends
        cursor.execute('''
            SELECT location_name, AVG(current_price) as avg_price, COUNT(*) as count
            FROM auctions 
            WHERE last_updated > datetime('now', '-{} days') AND location_name != ''
            GROUP BY location_name
            ORDER BY count DESC
            LIMIT 10
        '''.format(days))
        
        location_trends = cursor.fetchall()
        
        print(f"\n📍 Top Locations by Activity:")
        print("-" * 40)
        
        for location, avg_price, count in location_trends:
            print(f"📍 {location}: {count} auctions (Avg: ${avg_price:.2f})")
            
        conn.close()
        
    def find_deals(self, threshold_percent=20):
        """Find potential deals based on price analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find auctions priced below category average
        cursor.execute('''
            WITH category_avg AS (
                SELECT category, AVG(current_price) as avg_price
                FROM auctions
                WHERE current_price > 0
                GROUP BY category
            )
            SELECT a.auction_number, a.title, a.current_price, a.category, 
                   ca.avg_price, a.closing_date, a.location_name
            FROM auctions a
            JOIN category_avg ca ON a.category = ca.category
            WHERE a.current_price > 0 
            AND a.current_price < (ca.avg_price * (1 - ? / 100.0))
            AND datetime(a.closing_date) > datetime('now')
            ORDER BY (ca.avg_price - a.current_price) DESC
            LIMIT 20
        ''', (threshold_percent,))
        
        deals = cursor.fetchall()
        
        print(f"🔥 Potential Deals ({threshold_percent}% below category average)")
        print("=" * 70)
        
        for auction_num, title, price, category, avg_price, closing, location in deals:
            savings = avg_price - price
            savings_percent = (savings / avg_price) * 100
            
            print(f"💰 {auction_num}: {title[:40]}...")
            print(f"   💵 ${price:.2f} (Category avg: ${avg_price:.2f}) - Save ${savings:.2f} ({savings_percent:.1f}%)")
            print(f"   📍 {location} | ⏰ Closes: {closing}")
            print()
            
        conn.close()
        
    def add_price_alert(self, keyword, max_price, location_ids=None, alert_type="keyword"):
        """Add a price alert."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        location_str = ','.join(map(str, location_ids)) if location_ids else ''
        
        cursor.execute('''
            INSERT INTO price_alerts (keyword, max_price, location_ids, alert_type, created_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (keyword, max_price, location_str, alert_type, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Alert added: '{keyword}' under ${max_price}")
        
    def check_alerts(self):
        """Check for triggered price alerts."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get active alerts
        cursor.execute('SELECT * FROM price_alerts WHERE is_active = 1')
        alerts = cursor.fetchall()
        
        triggered_alerts = []
        
        for alert in alerts:
            alert_id, keyword, max_price, location_ids, alert_type, created_date, is_active = alert
            
            # Build query based on alert type
            if alert_type == "keyword":
                query = '''
                    SELECT auction_number, title, current_price, location_name, closing_date
                    FROM auctions
                    WHERE title LIKE ? AND current_price <= ? AND current_price > 0
                    AND datetime(closing_date) > datetime('now')
                '''
                params = (f'%{keyword}%', max_price)
                
                if location_ids:
                    location_list = location_ids.split(',')
                    placeholders = ','.join(['?' for _ in location_list])
                    query += f' AND location_id IN ({placeholders})'
                    params = params + tuple(location_list)
                    
                cursor.execute(query, params)
                matches = cursor.fetchall()
                
                if matches:
                    triggered_alerts.append((alert, matches))
                    
        if triggered_alerts:
            print("🚨 PRICE ALERTS TRIGGERED!")
            print("=" * 50)
            
            for alert, matches in triggered_alerts:
                keyword, max_price = alert[1], alert[2]
                print(f"🔔 Alert: '{keyword}' under ${max_price}")
                
                for auction_num, title, price, location, closing in matches:
                    print(f"   💰 {auction_num}: {title[:40]}... - ${price} at {location}")
                    
                print()
                
        conn.close()
        return len(triggered_alerts)
        
    async def run_tracker(self, pages=5):
        """Run the price tracker."""
        print("📊 Starting Price Tracker")
        print("=" * 40)
        
        try:
            # Fetch latest auction data
            auctions = await self.fetch_auctions(pages)
            print(f"✅ Fetched {len(auctions)} auctions")
            
            # Save to database
            self.save_auction_data(auctions)
            print("✅ Saved auction data to database")
            
            # Analyze trends
            self.analyze_price_trends()
            
            # Find deals
            print()
            self.find_deals()
            
            # Check alerts
            print()
            alert_count = self.check_alerts()
            if alert_count == 0:
                print("✅ No price alerts triggered")
                
        finally:
            await self.close_session()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='mac.bid Price Tracker')
    parser.add_argument('--pages', type=int, default=5, help='Number of pages to scan')
    parser.add_argument('--add-alert', nargs=3, metavar=('KEYWORD', 'MAX_PRICE', 'LOCATIONS'),
                       help='Add price alert: keyword max_price location_ids')
    parser.add_argument('--trends', action='store_true', help='Show price trends only')
    parser.add_argument('--deals', action='store_true', help='Show deals only')
    parser.add_argument('--alerts', action='store_true', help='Check alerts only')
    
    args = parser.parse_args()
    
    tracker = PriceTracker()
    
    if args.add_alert:
        keyword, max_price, locations = args.add_alert
        location_ids = [int(x.strip()) for x in locations.split(',') if x.strip().isdigit()]
        tracker.add_price_alert(keyword, float(max_price), location_ids)
        
    elif args.trends:
        tracker.analyze_price_trends()
        
    elif args.deals:
        tracker.find_deals()
        
    elif args.alerts:
        tracker.check_alerts()
        
    else:
        asyncio.run(tracker.run_tracker(args.pages))

if __name__ == "__main__":
    main() 