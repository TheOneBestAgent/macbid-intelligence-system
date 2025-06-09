#!/usr/bin/env python3
"""
🔍 Advanced Product Search Scraper for mac.bid
Leverages Typesense search API to find specific products and monitor inventory
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime
import re
from collections import defaultdict

class SearchScraper:
    def __init__(self, db_path="search_tracker.db"):
        self.db_path = db_path
        self.session = None
        self.search_base_url = "https://xczkhpt94lod37gqp.a1.typesense.net"
        self.init_database()
        
    def init_database(self):
        """Initialize database for search tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                filters TEXT,
                created_date TEXT,
                last_run TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_id INTEGER,
                product_id TEXT,
                title TEXT,
                description TEXT,
                upc TEXT,
                inventory_id TEXT,
                auction_title TEXT,
                price REAL,
                location_id INTEGER,
                found_date TEXT,
                FOREIGN KEY (query_id) REFERENCES search_queries (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT,
                title TEXT,
                upc TEXT,
                inventory_id TEXT,
                status TEXT,
                location_id INTEGER,
                first_seen TEXT,
                last_seen TEXT,
                times_seen INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brand_monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_name TEXT,
                keywords TEXT,
                min_price REAL,
                max_price REAL,
                location_ids TEXT,
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
            
    async def search_products(self, query, filters=None, per_page=50):
        """Search products using Typesense API."""
        if not self.session:
            await self.create_session()
            
        # Build search request
        search_requests = {
            "searches": [
                {
                    "collection": "products",
                    "q": query,
                    "query_by": "product_name,description,keywords,upc,inventory_id,auction_title",
                    "per_page": per_page,
                    "page": 1
                }
            ]
        }
        
        # Add filters if provided
        if filters:
            search_requests["searches"][0]["filter_by"] = filters
            
        url = f"{self.search_base_url}/multi_search"
        
        try:
            async with self.session.post(url, json=search_requests) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    if results:
                        hits = results[0].get("hits", [])
                        return [hit["document"] for hit in hits]
                else:
                    print(f"⚠️  Search API returned status {response.status}")
                    
        except Exception as e:
            print(f"❌ Search error: {e}")
            
        return []
        
    def save_search_query(self, query, filters=None):
        """Save a search query for monitoring."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO search_queries (query, filters, created_date, last_run)
            VALUES (?, ?, ?, ?)
        ''', (query, filters or '', datetime.now().isoformat(), datetime.now().isoformat()))
        
        query_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return query_id
        
    def save_search_results(self, query_id, results):
        """Save search results to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for result in results:
            product_id = result.get('id', '')
            title = result.get('product_name', '')
            description = result.get('description', '')
            upc = result.get('upc', '')
            inventory_id = result.get('inventory_id', '')
            auction_title = result.get('auction_title', '')
            price = result.get('price', 0.0)
            location_id = result.get('location_id', 0)
            
            cursor.execute('''
                INSERT INTO search_results 
                (query_id, product_id, title, description, upc, inventory_id, 
                 auction_title, price, location_id, found_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (query_id, product_id, title, description, upc, inventory_id,
                  auction_title, price, location_id, datetime.now().isoformat()))
                  
            # Update inventory tracking
            cursor.execute('''
                INSERT OR REPLACE INTO inventory_tracking
                (product_id, title, upc, inventory_id, status, location_id, 
                 first_seen, last_seen, times_seen)
                VALUES (?, ?, ?, ?, 'active', ?, 
                        COALESCE((SELECT first_seen FROM inventory_tracking WHERE product_id = ?), ?),
                        ?, 
                        COALESCE((SELECT times_seen FROM inventory_tracking WHERE product_id = ?) + 1, 1))
            ''', (product_id, title, upc, inventory_id, location_id, 
                  product_id, datetime.now().isoformat(),
                  datetime.now().isoformat(), product_id))
            
        conn.commit()
        conn.close()
        
    async def search_by_brand(self, brand, location_ids=None, price_range=None):
        """Search for products by brand."""
        print(f"🔍 Searching for {brand} products...")
        
        # Build search query
        query = f'"{brand}"'
        filters = []
        
        if location_ids:
            location_filter = " || ".join([f"location_id:{loc}" for loc in location_ids])
            filters.append(f"({location_filter})")
            
        if price_range:
            min_price, max_price = price_range
            filters.append(f"price:>={min_price} && price:<={max_price}")
            
        filter_str = " && ".join(filters) if filters else None
        
        results = await self.search_products(query, filter_str)
        
        print(f"✅ Found {len(results)} {brand} products")
        
        # Save query and results
        query_id = self.save_search_query(query, filter_str)
        self.save_search_results(query_id, results)
        
        return results
        
    async def search_by_keywords(self, keywords, location_ids=None):
        """Search for products by keywords."""
        print(f"🔍 Searching for: {', '.join(keywords)}")
        
        # Build search query
        query = " ".join(keywords)
        filters = []
        
        if location_ids:
            location_filter = " || ".join([f"location_id:{loc}" for loc in location_ids])
            filters.append(f"({location_filter})")
            
        filter_str = " && ".join(filters) if filters else None
        
        results = await self.search_products(query, filter_str)
        
        print(f"✅ Found {len(results)} matching products")
        
        # Save query and results
        query_id = self.save_search_query(query, filter_str)
        self.save_search_results(query_id, results)
        
        return results
        
    async def search_by_upc(self, upc_codes):
        """Search for products by UPC codes."""
        print(f"🔍 Searching for UPC codes: {', '.join(upc_codes)}")
        
        all_results = []
        
        for upc in upc_codes:
            query = f'upc:"{upc}"'
            results = await self.search_products(query)
            
            if results:
                print(f"✅ Found {len(results)} products for UPC {upc}")
                all_results.extend(results)
                
                # Save query and results
                query_id = self.save_search_query(query)
                self.save_search_results(query_id, results)
            else:
                print(f"❌ No products found for UPC {upc}")
                
        return all_results
        
    def add_brand_monitor(self, brand_name, keywords=None, price_range=None, location_ids=None):
        """Add a brand monitoring alert."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        keywords_str = ','.join(keywords) if keywords else ''
        location_str = ','.join(map(str, location_ids)) if location_ids else ''
        min_price = price_range[0] if price_range else 0
        max_price = price_range[1] if price_range else 999999
        
        cursor.execute('''
            INSERT INTO brand_monitoring 
            (brand_name, keywords, min_price, max_price, location_ids, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (brand_name, keywords_str, min_price, max_price, location_str, 
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Brand monitor added: {brand_name}")
        
    async def run_brand_monitors(self):
        """Run all active brand monitors."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM brand_monitoring WHERE is_active = 1')
        monitors = cursor.fetchall()
        
        print(f"🔍 Running {len(monitors)} brand monitors...")
        
        for monitor in monitors:
            monitor_id, brand_name, keywords, min_price, max_price, location_ids, created_date, is_active = monitor
            
            print(f"\n📱 Monitoring: {brand_name}")
            
            # Parse location IDs
            locations = [int(x.strip()) for x in location_ids.split(',') if x.strip().isdigit()] if location_ids else None
            
            # Search for brand
            results = await self.search_by_brand(
                brand_name, 
                location_ids=locations,
                price_range=(min_price, max_price) if max_price < 999999 else None
            )
            
            # Show results
            if results:
                print(f"🎯 Found {len(results)} {brand_name} products:")
                for result in results[:5]:  # Show first 5
                    title = result.get('product_name', 'Unknown')
                    price = result.get('price', 0)
                    location = result.get('location_id', 'Unknown')
                    print(f"   💰 {title[:50]}... - ${price} (Location {location})")
                    
                if len(results) > 5:
                    print(f"   ... and {len(results) - 5} more")
            else:
                print(f"❌ No {brand_name} products found")
                
        conn.close()
        
    def analyze_inventory_trends(self):
        """Analyze inventory trends and patterns."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("📊 Inventory Analysis")
        print("=" * 50)
        
        # Most frequently seen products
        cursor.execute('''
            SELECT title, times_seen, location_id, first_seen, last_seen
            FROM inventory_tracking
            ORDER BY times_seen DESC
            LIMIT 10
        ''')
        
        frequent_items = cursor.fetchall()
        
        print("🔄 Most Frequently Listed Items:")
        print("-" * 40)
        
        for title, times_seen, location_id, first_seen, last_seen in frequent_items:
            print(f"📦 {title[:40]}...")
            print(f"   🔢 Seen {times_seen} times | 📍 Location {location_id}")
            print(f"   📅 First: {first_seen[:10]} | Last: {last_seen[:10]}")
            print()
            
        # Location-based inventory
        cursor.execute('''
            SELECT location_id, COUNT(*) as item_count, AVG(times_seen) as avg_frequency
            FROM inventory_tracking
            GROUP BY location_id
            ORDER BY item_count DESC
            LIMIT 10
        ''')
        
        location_stats = cursor.fetchall()
        
        print("📍 Inventory by Location:")
        print("-" * 30)
        
        for location_id, item_count, avg_frequency in location_stats:
            print(f"📍 Location {location_id}: {item_count} unique items (Avg frequency: {avg_frequency:.1f})")
            
        conn.close()
        
    def show_search_history(self, limit=20):
        """Show recent search history."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT sq.query, sq.filters, sq.last_run, COUNT(sr.id) as result_count
            FROM search_queries sq
            LEFT JOIN search_results sr ON sq.id = sr.query_id
            GROUP BY sq.id
            ORDER BY sq.last_run DESC
            LIMIT ?
        ''', (limit,))
        
        history = cursor.fetchall()
        
        print("📜 Search History")
        print("=" * 40)
        
        for query, filters, last_run, result_count in history:
            print(f"🔍 '{query}'")
            if filters:
                print(f"   🎯 Filters: {filters}")
            print(f"   📅 {last_run[:19]} | 📊 {result_count} results")
            print()
            
        conn.close()
        
    async def run_search_scraper(self):
        """Main search scraper interface."""
        print("🔍 Advanced Product Search Scraper")
        print("=" * 50)
        
        try:
            # Run brand monitors
            await self.run_brand_monitors()
            
            print()
            
            # Show inventory analysis
            self.analyze_inventory_trends()
            
            print()
            
            # Show search history
            self.show_search_history(10)
            
        finally:
            await self.close_session()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='mac.bid Advanced Search Scraper')
    parser.add_argument('--brand', type=str, help='Search for specific brand')
    parser.add_argument('--keywords', nargs='+', help='Search by keywords')
    parser.add_argument('--upc', nargs='+', help='Search by UPC codes')
    parser.add_argument('--locations', type=str, help='Comma-separated location IDs')
    parser.add_argument('--price-range', nargs=2, type=float, metavar=('MIN', 'MAX'), 
                       help='Price range filter')
    parser.add_argument('--add-brand-monitor', nargs='+', 
                       help='Add brand monitor: brand_name [keywords...]')
    parser.add_argument('--run-monitors', action='store_true', help='Run all brand monitors')
    parser.add_argument('--inventory-analysis', action='store_true', help='Show inventory analysis')
    parser.add_argument('--search-history', action='store_true', help='Show search history')
    
    args = parser.parse_args()
    
    scraper = SearchScraper()
    
    # Parse location IDs
    location_ids = None
    if args.locations:
        location_ids = [int(x.strip()) for x in args.locations.split(',') if x.strip().isdigit()]
    
    if args.add_brand_monitor:
        brand_name = args.add_brand_monitor[0]
        keywords = args.add_brand_monitor[1:] if len(args.add_brand_monitor) > 1 else None
        scraper.add_brand_monitor(brand_name, keywords, args.price_range, location_ids)
        
    elif args.inventory_analysis:
        scraper.analyze_inventory_trends()
        
    elif args.search_history:
        scraper.show_search_history()
        
    elif args.run_monitors:
        asyncio.run(scraper.run_brand_monitors())
        
    elif args.brand:
        async def search_brand():
            results = await scraper.search_by_brand(args.brand, location_ids, args.price_range)
            for result in results:
                title = result.get('product_name', 'Unknown')
                price = result.get('price', 0)
                location = result.get('location_id', 'Unknown')
                print(f"💰 {title} - ${price} (Location {location})")
        asyncio.run(search_brand())
        
    elif args.keywords:
        async def search_keywords():
            results = await scraper.search_by_keywords(args.keywords, location_ids)
            for result in results:
                title = result.get('product_name', 'Unknown')
                price = result.get('price', 0)
                location = result.get('location_id', 'Unknown')
                print(f"💰 {title} - ${price} (Location {location})")
        asyncio.run(search_keywords())
        
    elif args.upc:
        async def search_upc():
            results = await scraper.search_by_upc(args.upc)
            for result in results:
                title = result.get('product_name', 'Unknown')
                upc = result.get('upc', 'Unknown')
                price = result.get('price', 0)
                location = result.get('location_id', 'Unknown')
                print(f"💰 {title} (UPC: {upc}) - ${price} (Location {location})")
        asyncio.run(search_upc())
        
    else:
        asyncio.run(scraper.run_search_scraper())

if __name__ == "__main__":
    main() 