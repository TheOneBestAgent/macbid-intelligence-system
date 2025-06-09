#!/usr/bin/env python3
"""
📍 Location-Based Inventory Scraper for mac.bid
Tracks inventory by warehouse location and identifies regional patterns
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class LocationScraper:
    def __init__(self, db_path="location_inventory.db"):
        self.db_path = db_path
        self.session = None
        self.locations_data = {}
        self.init_database()
        self.load_locations()
        
    def init_database(self):
        """Initialize database for location tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS location_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER,
                location_name TEXT,
                city TEXT,
                state TEXT,
                auction_id INTEGER,
                auction_number TEXT,
                title TEXT,
                category TEXT,
                closing_date TEXT,
                estimated_value REAL,
                competition_level TEXT,
                recorded_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS location_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id INTEGER,
                location_name TEXT,
                total_items INTEGER,
                avg_value REAL,
                high_value_items INTEGER,
                categories_count INTEGER,
                last_updated TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS regional_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                state TEXT,
                category TEXT,
                avg_price REAL,
                item_count INTEGER,
                value_score REAL,
                last_calculated TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS route_optimizer (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route_name TEXT,
                location_ids TEXT,
                total_distance REAL,
                estimated_time REAL,
                high_value_items INTEGER,
                route_score REAL,
                created_date TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def load_locations(self):
        """Load location data from file."""
        try:
            with open('locations_data.json', 'r') as f:
                locations = json.load(f)
                for loc in locations:
                    self.locations_data[loc['id']] = {
                        'name': loc['name'],
                        'city': loc['city_state'].split(',')[0].strip(),
                        'state': loc['city_state'].split(',')[1].strip() if ',' in loc['city_state'] else '',
                        'address': loc['address'],
                        'zip_code': loc['zip_code']
                    }
        except FileNotFoundError:
            print("⚠️  locations_data.json not found. Run find_warehouse_locations.py first.")
            
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
            
    async def fetch_location_inventory(self, pages=20):
        """Fetch inventory data by location."""
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
        
    def categorize_item(self, title):
        """Categorize item based on title."""
        if not title:
            return "Unknown"
            
        title_lower = title.lower()
        
        categories = {
            "Electronics": ["iphone", "ipad", "laptop", "computer", "tv", "phone", "tablet", "gaming"],
            "Clothing": ["clothing", "apparel", "shirt", "pants", "dress", "shoes", "fashion"],
            "Home": ["furniture", "home", "kitchen", "appliance", "decor", "bedding"],
            "Tools": ["tools", "hardware", "drill", "saw", "equipment"],
            "Automotive": ["car", "auto", "vehicle", "parts", "tire"],
            "Sports": ["sports", "fitness", "exercise", "bike", "golf"],
            "Jewelry": ["jewelry", "watch", "ring", "necklace", "gold", "silver"],
            "Collectibles": ["collectible", "antique", "vintage", "art"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
                
        return "General"
        
    def estimate_item_value(self, title, category):
        """Estimate item value based on title and category."""
        if not title:
            return 10.0
            
        title_lower = title.lower()
        
        # Base values by category
        base_values = {
            "Electronics": 100,
            "Jewelry": 75,
            "Tools": 50,
            "Automotive": 60,
            "Sports": 40,
            "Home": 30,
            "Clothing": 25,
            "Collectibles": 80,
            "General": 20
        }
        
        base_value = base_values.get(category, 20)
        
        # Value multipliers
        multipliers = {
            "new": 2.0,
            "sealed": 1.8,
            "apple": 2.5,
            "samsung": 1.8,
            "nike": 1.5,
            "rolex": 5.0,
            "gold": 3.0,
            "diamond": 4.0,
            "vintage": 1.5,
            "antique": 2.0,
            "used": 0.6,
            "damaged": 0.3,
            "broken": 0.2
        }
        
        final_value = base_value
        
        for keyword, multiplier in multipliers.items():
            if keyword in title_lower:
                final_value *= multiplier
                break
                
        return min(final_value, 1000)  # Cap at $1000
        
    def save_location_inventory(self, auctions):
        """Save inventory data by location."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for auction in auctions:
            auction_id = auction.get('id')
            auction_number = auction.get('auction_number', '')
            title = auction.get('title', auction.get('external_folder_name', ''))
            location_id = auction.get('location_id')
            closing_date = auction.get('closing_date', '')
            
            if location_id in self.locations_data:
                location_info = self.locations_data[location_id]
                location_name = location_info['name']
                city = location_info['city']
                state = location_info['state']
            else:
                location_name = f"Location {location_id}"
                city = "Unknown"
                state = "Unknown"
                
            category = self.categorize_item(title)
            estimated_value = self.estimate_item_value(title, category)
            competition_level = "medium"  # Would be enhanced with bid data
            
            cursor.execute('''
                INSERT OR REPLACE INTO location_inventory
                (location_id, location_name, city, state, auction_id, auction_number,
                 title, category, closing_date, estimated_value, competition_level, recorded_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (location_id, location_name, city, state, auction_id, auction_number,
                  title, category, closing_date, estimated_value, competition_level,
                  datetime.now().isoformat()))
                  
        conn.commit()
        conn.close()
        
    def calculate_location_stats(self):
        """Calculate statistics for each location."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing stats
        cursor.execute('DELETE FROM location_stats')
        
        # Calculate stats for each location
        cursor.execute('SELECT DISTINCT location_id FROM location_inventory')
        location_ids = [row[0] for row in cursor.fetchall()]
        
        for location_id in location_ids:
            cursor.execute('''
                SELECT location_name, COUNT(*) as total_items, AVG(estimated_value) as avg_value,
                       SUM(CASE WHEN estimated_value > 100 THEN 1 ELSE 0 END) as high_value_items,
                       COUNT(DISTINCT category) as categories_count
                FROM location_inventory
                WHERE location_id = ?
            ''', (location_id,))
            
            result = cursor.fetchone()
            location_name, total_items, avg_value, high_value_items, categories_count = result
            
            cursor.execute('''
                INSERT INTO location_stats
                (location_id, location_name, total_items, avg_value, high_value_items,
                 categories_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (location_id, location_name, total_items, avg_value or 0, high_value_items,
                  categories_count, datetime.now().isoformat()))
                  
        conn.commit()
        conn.close()
        
    def analyze_regional_patterns(self):
        """Analyze patterns by state and region."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing patterns
        cursor.execute('DELETE FROM regional_patterns')
        
        # Calculate patterns by state and category
        cursor.execute('''
            SELECT state, category, AVG(estimated_value) as avg_price, COUNT(*) as item_count
            FROM location_inventory
            WHERE state != 'Unknown' AND category != 'Unknown'
            GROUP BY state, category
            HAVING COUNT(*) >= 3
        ''')
        
        patterns = cursor.fetchall()
        
        for state, category, avg_price, item_count in patterns:
            # Calculate value score (higher = better deals)
            value_score = 100 - min(avg_price / 10, 100)  # Inverse relationship with price
            
            cursor.execute('''
                INSERT INTO regional_patterns
                (state, category, avg_price, item_count, value_score, last_calculated)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (state, category, avg_price, item_count, value_score, datetime.now().isoformat()))
            
        conn.commit()
        conn.close()
        
    def show_top_locations(self, limit=10):
        """Show top locations by various metrics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🏆 Top Warehouse Locations")
        print("=" * 50)
        
        # By total inventory
        print("📦 Most Inventory:")
        cursor.execute('''
            SELECT location_name, total_items, avg_value, high_value_items
            FROM location_stats
            ORDER BY total_items DESC
            LIMIT ?
        ''', (limit,))
        
        for location_name, total_items, avg_value, high_value_items in cursor.fetchall():
            print(f"📍 {location_name}: {total_items} items (Avg: ${avg_value:.2f}, {high_value_items} high-value)")
            
        print(f"\n💎 Highest Value Items:")
        cursor.execute('''
            SELECT location_name, avg_value, high_value_items, total_items
            FROM location_stats
            WHERE total_items >= 5
            ORDER BY avg_value DESC
            LIMIT ?
        ''', (limit,))
        
        for location_name, avg_value, high_value_items, total_items in cursor.fetchall():
            high_value_percent = (high_value_items / total_items) * 100 if total_items > 0 else 0
            print(f"💰 {location_name}: ${avg_value:.2f} avg ({high_value_percent:.1f}% high-value)")
            
        conn.close()
        
    def show_regional_analysis(self):
        """Show regional pricing patterns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\n🗺️  Regional Analysis")
        print("=" * 40)
        
        # Best states for deals
        cursor.execute('''
            SELECT state, AVG(value_score) as avg_value_score, SUM(item_count) as total_items
            FROM regional_patterns
            GROUP BY state
            HAVING total_items >= 10
            ORDER BY avg_value_score DESC
        ''')
        
        print("🎯 Best States for Deals (Higher Score = Better):")
        for state, avg_score, total_items in cursor.fetchall():
            print(f"🏛️  {state}: Score {avg_score:.1f} ({total_items} items)")
            
        # Category analysis by region
        print(f"\n📊 Category Patterns by State:")
        cursor.execute('''
            SELECT state, category, avg_price, item_count
            FROM regional_patterns
            WHERE item_count >= 5
            ORDER BY state, avg_price ASC
        ''')
        
        current_state = None
        for state, category, avg_price, item_count in cursor.fetchall():
            if state != current_state:
                print(f"\n🏛️  {state}:")
                current_state = state
            print(f"   🏷️  {category}: ${avg_price:.2f} avg ({item_count} items)")
            
        conn.close()
        
    def find_best_pickup_routes(self, max_locations=5):
        """Find optimal pickup routes for high-value items."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"\n🚗 Optimal Pickup Routes")
        print("=" * 40)
        
        # Get locations with high-value items
        cursor.execute('''
            SELECT location_id, location_name, high_value_items, avg_value
            FROM location_stats
            WHERE high_value_items > 0
            ORDER BY (high_value_items * avg_value) DESC
            LIMIT ?
        ''', (max_locations * 2,))
        
        high_value_locations = cursor.fetchall()
        
        # Group by state for efficient routes
        state_groups = defaultdict(list)
        
        for location_id, location_name, high_value_items, avg_value in high_value_locations:
            if location_id in self.locations_data:
                state = self.locations_data[location_id]['state']
                state_groups[state].append({
                    'id': location_id,
                    'name': location_name,
                    'high_value_items': high_value_items,
                    'avg_value': avg_value,
                    'score': high_value_items * avg_value
                })
                
        # Show best routes by state
        for state, locations in state_groups.items():
            if len(locations) >= 2:
                locations.sort(key=lambda x: x['score'], reverse=True)
                top_locations = locations[:max_locations]
                
                total_score = sum(loc['score'] for loc in top_locations)
                total_high_value = sum(loc['high_value_items'] for loc in top_locations)
                
                print(f"🏛️  {state} Route (Score: {total_score:.0f}):")
                for loc in top_locations:
                    print(f"   📍 {loc['name']}: {loc['high_value_items']} high-value items (${loc['avg_value']:.2f} avg)")
                print(f"   🎯 Total: {total_high_value} high-value items")
                print()
                
        conn.close()
        
    def track_location_trends(self, days=7):
        """Track inventory trends over time."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print(f"\n📈 Location Trends (Last {days} days)")
        print("=" * 50)
        
        # Get recent activity
        cursor.execute('''
            SELECT location_name, COUNT(*) as recent_items, AVG(estimated_value) as recent_avg_value
            FROM location_inventory
            WHERE recorded_date > datetime('now', '-{} days')
            GROUP BY location_id, location_name
            ORDER BY recent_items DESC
            LIMIT 10
        '''.format(days))
        
        print("🔥 Most Active Locations Recently:")
        for location_name, recent_items, recent_avg_value in cursor.fetchall():
            print(f"📍 {location_name}: {recent_items} new items (${recent_avg_value:.2f} avg)")
            
        conn.close()
        
    async def run_location_analysis(self, pages=20):
        """Run complete location-based analysis."""
        print("📍 Starting Location-Based Inventory Analysis")
        print("=" * 60)
        
        try:
            # Fetch inventory data
            auctions = await self.fetch_location_inventory(pages)
            print(f"✅ Fetched {len(auctions)} auctions")
            
            # Save location inventory
            self.save_location_inventory(auctions)
            print("✅ Saved location inventory data")
            
            # Calculate statistics
            self.calculate_location_stats()
            print("✅ Calculated location statistics")
            
            # Analyze regional patterns
            self.analyze_regional_patterns()
            print("✅ Analyzed regional patterns")
            
            print()
            
            # Show analysis results
            self.show_top_locations()
            self.show_regional_analysis()
            self.find_best_pickup_routes()
            self.track_location_trends()
            
        finally:
            await self.close_session()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='mac.bid Location-Based Inventory Scraper')
    parser.add_argument('--pages', type=int, default=20, help='Number of pages to analyze')
    parser.add_argument('--top-locations', action='store_true', help='Show top locations only')
    parser.add_argument('--regional', action='store_true', help='Show regional analysis only')
    parser.add_argument('--routes', action='store_true', help='Show pickup routes only')
    parser.add_argument('--trends', action='store_true', help='Show location trends only')
    
    args = parser.parse_args()
    
    scraper = LocationScraper()
    
    if args.top_locations:
        scraper.show_top_locations()
    elif args.regional:
        scraper.show_regional_analysis()
    elif args.routes:
        scraper.find_best_pickup_routes()
    elif args.trends:
        scraper.track_location_trends()
    else:
        asyncio.run(scraper.run_location_analysis(args.pages))

if __name__ == "__main__":
    main() 