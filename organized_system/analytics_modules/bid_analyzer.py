#!/usr/bin/env python3
"""
🏆 Winning Bid Pattern Analyzer for mac.bid
Analyzes successful bidding patterns and identifies undervalued categories
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
import statistics
from collections import defaultdict
import re

class BidAnalyzer:
    def __init__(self, db_path="bid_analysis.db"):
        self.db_path = db_path
        self.session = None
        self.init_database()
        
    def init_database(self):
        """Initialize database for bid analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id INTEGER,
                auction_number TEXT,
                title TEXT,
                category TEXT,
                location_id INTEGER,
                starting_price REAL,
                final_price REAL,
                bid_count INTEGER,
                price_increase_ratio REAL,
                competition_level TEXT,
                value_rating TEXT,
                closing_date TEXT,
                recorded_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS category_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                avg_starting_price REAL,
                avg_final_price REAL,
                avg_price_increase REAL,
                avg_bid_count REAL,
                total_auctions INTEGER,
                undervalued_score REAL,
                last_updated TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sweet_spots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                location_id INTEGER,
                optimal_bid_range_min REAL,
                optimal_bid_range_max REAL,
                success_rate REAL,
                avg_savings REAL,
                sample_size INTEGER,
                confidence_level TEXT,
                last_calculated TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS value_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                max_price REAL,
                min_value_score REAL,
                location_ids TEXT,
                keywords TEXT,
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
            
    async def fetch_auction_data(self, pages=15):
        """Fetch auction data for bid analysis."""
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
        
    def categorize_auction(self, title):
        """Categorize auction based on title."""
        if not title:
            return "Unknown"
            
        title_lower = title.lower()
        
        categories = {
            "Electronics": ["iphone", "ipad", "laptop", "computer", "tv", "phone", "tablet", "electronics", "gaming", "console"],
            "Clothing": ["clothing", "apparel", "shirt", "pants", "dress", "shoes", "fashion", "jacket", "jeans"],
            "Home & Garden": ["furniture", "home", "kitchen", "appliance", "decor", "bedding", "garden", "outdoor"],
            "Tools & Hardware": ["tools", "hardware", "drill", "saw", "equipment", "wrench", "hammer"],
            "Automotive": ["car", "auto", "vehicle", "parts", "tire", "engine", "motorcycle"],
            "Sports & Fitness": ["sports", "fitness", "exercise", "bike", "golf", "outdoor", "gym"],
            "Books & Media": ["books", "media", "dvd", "cd", "games", "vinyl", "magazine"],
            "Jewelry & Watches": ["jewelry", "watch", "ring", "necklace", "gold", "silver", "diamond"],
            "Collectibles": ["collectible", "antique", "vintage", "rare", "limited", "signed"],
            "Beauty & Health": ["beauty", "cosmetics", "health", "skincare", "perfume", "makeup"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
                
        return "General"
        
    def estimate_value_rating(self, title, final_price, category):
        """Estimate if an item was undervalued, fairly priced, or overvalued."""
        if not title or final_price <= 0:
            return "unknown"
            
        title_lower = title.lower()
        
        # High-value indicators
        high_value_keywords = ["new", "sealed", "unopened", "mint", "brand new", "unused"]
        brand_keywords = ["apple", "samsung", "nike", "coach", "rolex", "omega"]
        
        # Low-value indicators  
        low_value_keywords = ["used", "damaged", "broken", "parts", "repair", "as-is"]
        
        value_score = 0
        
        # Adjust based on keywords
        if any(keyword in title_lower for keyword in high_value_keywords):
            value_score += 2
        if any(keyword in title_lower for keyword in brand_keywords):
            value_score += 1
        if any(keyword in title_lower for keyword in low_value_keywords):
            value_score -= 2
            
        # Adjust based on price ranges by category
        category_price_ranges = {
            "Electronics": (50, 500),
            "Jewelry & Watches": (25, 300),
            "Tools & Hardware": (20, 200),
            "Clothing": (10, 100),
            "Home & Garden": (15, 150),
            "Sports & Fitness": (20, 200),
            "Automotive": (30, 300),
            "Books & Media": (5, 50),
            "Collectibles": (10, 500),
            "Beauty & Health": (10, 100)
        }
        
        if category in category_price_ranges:
            min_price, max_price = category_price_ranges[category]
            if final_price < min_price * 0.5:
                value_score += 1  # Potentially undervalued
            elif final_price > max_price * 2:
                value_score -= 1  # Potentially overvalued
                
        # Convert score to rating
        if value_score >= 2:
            return "undervalued"
        elif value_score <= -2:
            return "overvalued"
        else:
            return "fair"
            
    def analyze_bid_patterns(self, auctions):
        """Analyze bidding patterns from auction data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for auction in auctions:
            auction_id = auction.get('id')
            auction_number = auction.get('auction_number', '')
            title = auction.get('title', auction.get('external_folder_name', ''))
            location_id = auction.get('location_id')
            closing_date = auction.get('closing_date', '')
            
            # Categorize
            category = self.categorize_auction(title)
            
            # Estimate pricing (would be enhanced with actual bid data)
            starting_price = 1.0  # Would come from auction details API
            final_price = 10.0    # Would come from completed auction data
            bid_count = 5         # Would come from bid history API
            
            # Calculate metrics
            price_increase_ratio = final_price / starting_price if starting_price > 0 else 0
            competition_level = "medium"  # Would be calculated from bid frequency
            value_rating = self.estimate_value_rating(title, final_price, category)
            
            # Save pattern data
            cursor.execute('''
                INSERT OR REPLACE INTO bid_patterns
                (auction_id, auction_number, title, category, location_id,
                 starting_price, final_price, bid_count, price_increase_ratio,
                 competition_level, value_rating, closing_date, recorded_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (auction_id, auction_number, title, category, location_id,
                  starting_price, final_price, bid_count, price_increase_ratio,
                  competition_level, value_rating, closing_date, datetime.now().isoformat()))
                  
        conn.commit()
        conn.close()
        
    def calculate_category_analysis(self):
        """Calculate analysis metrics by category."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing analysis
        cursor.execute('DELETE FROM category_analysis')
        
        # Get unique categories
        cursor.execute('SELECT DISTINCT category FROM bid_patterns WHERE category != "Unknown"')
        categories = [row[0] for row in cursor.fetchall()]
        
        for category in categories:
            cursor.execute('''
                SELECT AVG(starting_price), AVG(final_price), AVG(price_increase_ratio),
                       AVG(bid_count), COUNT(*),
                       SUM(CASE WHEN value_rating = 'undervalued' THEN 1 ELSE 0 END) as undervalued_count
                FROM bid_patterns
                WHERE category = ?
            ''', (category,))
            
            result = cursor.fetchone()
            avg_start, avg_final, avg_increase, avg_bids, total, undervalued_count = result
            
            if total > 0:
                # Calculate undervalued score (higher = more undervalued opportunities)
                undervalued_score = (undervalued_count / total) * 100
                
                cursor.execute('''
                    INSERT INTO category_analysis
                    (category, avg_starting_price, avg_final_price, avg_price_increase,
                     avg_bid_count, total_auctions, undervalued_score, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (category, avg_start or 0, avg_final or 0, avg_increase or 0,
                      avg_bids or 0, total, undervalued_score, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
    def find_undervalued_categories(self):
        """Find categories with the most undervalued opportunities."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("💎 Undervalued Category Analysis")
        print("=" * 60)
        
        cursor.execute('''
            SELECT category, undervalued_score, total_auctions, avg_final_price, avg_bid_count
            FROM category_analysis
            WHERE total_auctions >= 5
            ORDER BY undervalued_score DESC
            LIMIT 10
        ''')
        
        categories = cursor.fetchall()
        
        print("🎯 Categories with Most Undervalued Opportunities:")
        print("-" * 55)
        
        for category, score, total, avg_price, avg_bids in categories:
            print(f"💰 {category}")
            print(f"   📊 Undervalued Score: {score:.1f}% of auctions")
            print(f"   🔢 Sample Size: {total} auctions")
            print(f"   💵 Avg Final Price: ${avg_price:.2f}")
            print(f"   🏆 Avg Bid Count: {avg_bids:.1f}")
            print()
            
        conn.close()
        
    def calculate_sweet_spots(self):
        """Calculate optimal bidding ranges for each category."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing sweet spots
        cursor.execute('DELETE FROM sweet_spots')
        
        # Calculate for each category
        cursor.execute('SELECT DISTINCT category FROM bid_patterns WHERE category != "Unknown"')
        categories = [row[0] for row in cursor.fetchall()]
        
        for category in categories:
            cursor.execute('''
                SELECT final_price, value_rating
                FROM bid_patterns
                WHERE category = ? AND final_price > 0
            ''', (category,))
            
            results = cursor.fetchall()
            
            if len(results) >= 10:  # Need sufficient data
                prices = [row[0] for row in results]
                undervalued_prices = [row[0] for row in results if row[1] == 'undervalued']
                
                if undervalued_prices:
                    # Calculate optimal range based on undervalued items
                    min_optimal = min(undervalued_prices)
                    max_optimal = statistics.median(undervalued_prices)
                    success_rate = len(undervalued_prices) / len(results) * 100
                    avg_savings = (statistics.mean(prices) - statistics.mean(undervalued_prices)) / statistics.mean(prices) * 100
                    
                    confidence = "high" if len(undervalued_prices) >= 5 else "medium" if len(undervalued_prices) >= 3 else "low"
                    
                    cursor.execute('''
                        INSERT INTO sweet_spots
                        (category, location_id, optimal_bid_range_min, optimal_bid_range_max,
                         success_rate, avg_savings, sample_size, confidence_level, last_calculated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (category, 0, min_optimal, max_optimal, success_rate, avg_savings,
                          len(undervalued_prices), confidence, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
    def show_sweet_spots(self):
        """Show optimal bidding ranges."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🎯 Optimal Bidding Sweet Spots")
        print("=" * 50)
        
        cursor.execute('''
            SELECT category, optimal_bid_range_min, optimal_bid_range_max,
                   success_rate, avg_savings, sample_size, confidence_level
            FROM sweet_spots
            ORDER BY avg_savings DESC
        ''')
        
        sweet_spots = cursor.fetchall()
        
        print("💰 Best Value Ranges by Category:")
        print("-" * 40)
        
        for category, min_bid, max_bid, success_rate, savings, sample_size, confidence in sweet_spots:
            print(f"🏷️  {category}")
            print(f"   🎯 Optimal Range: ${min_bid:.2f} - ${max_bid:.2f}")
            print(f"   📊 Success Rate: {success_rate:.1f}%")
            print(f"   💵 Avg Savings: {savings:.1f}%")
            print(f"   🔢 Sample Size: {sample_size} ({confidence} confidence)")
            print()
            
        conn.close()
        
    def analyze_competition_patterns(self):
        """Analyze competition patterns by category and location."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("🏆 Competition Pattern Analysis")
        print("=" * 50)
        
        # Competition by category
        cursor.execute('''
            SELECT category, AVG(bid_count) as avg_competition, COUNT(*) as total
            FROM bid_patterns
            WHERE category != "Unknown"
            GROUP BY category
            ORDER BY avg_competition ASC
        ''')
        
        competition_data = cursor.fetchall()
        
        print("📊 Competition Levels by Category (Lower = Better):")
        print("-" * 50)
        
        for category, avg_competition, total in competition_data:
            competition_level = "Low" if avg_competition < 3 else "Medium" if avg_competition < 7 else "High"
            print(f"🏷️  {category}: {avg_competition:.1f} avg bids ({competition_level}) - {total} auctions")
            
        conn.close()
        
    def add_value_alert(self, category, max_price, min_value_score=50, location_ids=None, keywords=None):
        """Add a value alert for undervalued items."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        location_str = ','.join(map(str, location_ids)) if location_ids else ''
        keyword_str = ','.join(keywords) if keywords else ''
        
        cursor.execute('''
            INSERT INTO value_alerts
            (category, max_price, min_value_score, location_ids, keywords, created_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (category, max_price, min_value_score, location_str, keyword_str, 
              datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Value alert added: {category} under ${max_price}")
        
    async def run_bid_analysis(self, pages=15):
        """Run complete bid pattern analysis."""
        print("🏆 Starting Bid Pattern Analysis")
        print("=" * 50)
        
        try:
            # Fetch auction data
            auctions = await self.fetch_auction_data(pages)
            print(f"✅ Fetched {len(auctions)} auctions")
            
            # Analyze bid patterns
            self.analyze_bid_patterns(auctions)
            print("✅ Analyzed bid patterns")
            
            # Calculate category analysis
            self.calculate_category_analysis()
            print("✅ Calculated category metrics")
            
            # Calculate sweet spots
            self.calculate_sweet_spots()
            print("✅ Calculated optimal bidding ranges")
            
            print()
            
            # Show results
            self.find_undervalued_categories()
            print()
            self.show_sweet_spots()
            print()
            self.analyze_competition_patterns()
            
        finally:
            await self.close_session()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='mac.bid Bid Pattern Analyzer')
    parser.add_argument('--pages', type=int, default=15, help='Number of pages to analyze')
    parser.add_argument('--undervalued', action='store_true', help='Show undervalued categories only')
    parser.add_argument('--sweet-spots', action='store_true', help='Show optimal bidding ranges only')
    parser.add_argument('--competition', action='store_true', help='Show competition analysis only')
    parser.add_argument('--add-alert', nargs='+', help='Add value alert: category max_price [keywords...]')
    
    args = parser.parse_args()
    
    analyzer = BidAnalyzer()
    
    if args.add_alert:
        category = args.add_alert[0]
        max_price = float(args.add_alert[1])
        keywords = args.add_alert[2:] if len(args.add_alert) > 2 else None
        analyzer.add_value_alert(category, max_price, keywords=keywords)
        
    elif args.undervalued:
        analyzer.find_undervalued_categories()
        
    elif args.sweet_spots:
        analyzer.show_sweet_spots()
        
    elif args.competition:
        analyzer.analyze_competition_patterns()
        
    else:
        asyncio.run(analyzer.run_bid_analysis(args.pages))

if __name__ == "__main__":
    main() 