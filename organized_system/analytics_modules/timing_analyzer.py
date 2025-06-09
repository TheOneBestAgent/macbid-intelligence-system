#!/usr/bin/env python3
"""
⏰ Auction Timing Analyzer for mac.bid
Analyzes optimal bidding times and auction patterns
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
import statistics
from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd

class TimingAnalyzer:
    def __init__(self, db_path="timing_analysis.db"):
        self.db_path = db_path
        self.session = None
        self.init_database()
        
    def init_database(self):
        """Initialize database for timing analysis."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auction_timing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id INTEGER,
                auction_number TEXT,
                title TEXT,
                location_id INTEGER,
                opening_date TEXT,
                closing_date TEXT,
                duration_hours REAL,
                closing_hour INTEGER,
                closing_day_of_week INTEGER,
                final_price REAL,
                bid_count INTEGER,
                competition_level TEXT,
                recorded_date TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hourly_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hour INTEGER,
                day_of_week INTEGER,
                avg_final_price REAL,
                avg_bid_count REAL,
                auction_count INTEGER,
                competition_score REAL,
                last_updated TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS optimal_times (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                location_id INTEGER,
                best_hour INTEGER,
                best_day INTEGER,
                avg_savings_percent REAL,
                confidence_score REAL,
                sample_size INTEGER,
                last_calculated TEXT
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
            
    async def fetch_auction_data(self, pages=10):
        """Fetch auction data for timing analysis."""
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
        
    def analyze_auction_timing(self, auctions):
        """Analyze timing patterns from auction data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for auction in auctions:
            auction_id = auction.get('id')
            auction_number = auction.get('auction_number', '')
            title = auction.get('title', auction.get('external_folder_name', ''))
            location_id = auction.get('location_id')
            opening_date = auction.get('opening_date', '')
            closing_date = auction.get('closing_date', '')
            
            if not closing_date:
                continue
                
            try:
                # Parse dates
                closing_dt = datetime.fromisoformat(closing_date.replace('Z', '+00:00'))
                opening_dt = datetime.fromisoformat(opening_date.replace('Z', '+00:00')) if opening_date else None
                
                # Calculate duration
                duration_hours = 0
                if opening_dt:
                    duration_hours = (closing_dt - opening_dt).total_seconds() / 3600
                
                # Extract timing features
                closing_hour = closing_dt.hour
                closing_day_of_week = closing_dt.weekday()  # 0=Monday, 6=Sunday
                
                # Estimate competition level (would be enhanced with actual bid data)
                competition_level = self.estimate_competition(title, location_id)
                
                # Save timing data
                cursor.execute('''
                    INSERT OR REPLACE INTO auction_timing
                    (auction_id, auction_number, title, location_id, opening_date, 
                     closing_date, duration_hours, closing_hour, closing_day_of_week,
                     final_price, bid_count, competition_level, recorded_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (auction_id, auction_number, title, location_id, opening_date,
                      closing_date, duration_hours, closing_hour, closing_day_of_week,
                      0.0, 0, competition_level, datetime.now().isoformat()))
                      
            except Exception as e:
                print(f"⚠️  Error processing auction {auction_id}: {e}")
                
        conn.commit()
        conn.close()
        
    def estimate_competition(self, title, location_id):
        """Estimate competition level based on title and location."""
        if not title:
            return "medium"
            
        title_lower = title.lower()
        
        # High competition keywords
        high_comp = ["iphone", "ipad", "macbook", "laptop", "tv", "gaming", "gold", "jewelry"]
        # Low competition keywords  
        low_comp = ["clothing", "books", "dvd", "cd", "kitchen", "home"]
        
        if any(keyword in title_lower for keyword in high_comp):
            return "high"
        elif any(keyword in title_lower for keyword in low_comp):
            return "low"
        else:
            return "medium"
            
    def calculate_hourly_patterns(self):
        """Calculate bidding patterns by hour and day."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing patterns
        cursor.execute('DELETE FROM hourly_patterns')
        
        # Calculate patterns for each hour/day combination
        for day in range(7):  # 0-6 (Monday-Sunday)
            for hour in range(24):  # 0-23
                cursor.execute('''
                    SELECT AVG(final_price), AVG(bid_count), COUNT(*),
                           AVG(CASE WHEN competition_level = 'high' THEN 3
                                   WHEN competition_level = 'medium' THEN 2
                                   ELSE 1 END) as competition_score
                    FROM auction_timing
                    WHERE closing_hour = ? AND closing_day_of_week = ?
                ''', (hour, day))
                
                result = cursor.fetchone()
                avg_price, avg_bids, count, competition_score = result
                
                if count > 0:
                    cursor.execute('''
                        INSERT INTO hourly_patterns
                        (hour, day_of_week, avg_final_price, avg_bid_count, 
                         auction_count, competition_score, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (hour, day, avg_price or 0, avg_bids or 0, count,
                          competition_score or 2, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
    def find_optimal_bidding_times(self):
        """Find optimal bidding times with lowest competition."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("⏰ Optimal Bidding Times Analysis")
        print("=" * 60)
        
        # Find times with lowest competition
        cursor.execute('''
            SELECT hour, day_of_week, competition_score, auction_count, avg_final_price
            FROM hourly_patterns
            WHERE auction_count >= 3
            ORDER BY competition_score ASC, auction_count DESC
            LIMIT 10
        ''')
        
        optimal_times = cursor.fetchall()
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        print("🎯 Best Times to Bid (Lowest Competition):")
        print("-" * 50)
        
        for hour, day, comp_score, count, avg_price in optimal_times:
            day_name = days[day]
            time_str = f"{hour:02d}:00"
            
            print(f"📅 {day_name} at {time_str}")
            print(f"   📊 Competition Score: {comp_score:.2f}/3.0 (lower = better)")
            print(f"   🔢 Sample Size: {count} auctions")
            print(f"   💰 Avg Final Price: ${avg_price:.2f}")
            print()
            
        # Find times with highest competition (to avoid)
        cursor.execute('''
            SELECT hour, day_of_week, competition_score, auction_count, avg_final_price
            FROM hourly_patterns
            WHERE auction_count >= 3
            ORDER BY competition_score DESC, auction_count DESC
            LIMIT 5
        ''')
        
        busy_times = cursor.fetchall()
        
        print("🚫 Times to Avoid (Highest Competition):")
        print("-" * 40)
        
        for hour, day, comp_score, count, avg_price in busy_times:
            day_name = days[day]
            time_str = f"{hour:02d}:00"
            
            print(f"📅 {day_name} at {time_str} - Competition: {comp_score:.2f}/3.0")
            
        conn.close()
        
    def analyze_duration_patterns(self):
        """Analyze how auction duration affects final prices."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\n⏱️  Auction Duration Analysis")
        print("=" * 50)
        
        # Group by duration ranges
        duration_ranges = [
            (0, 24, "< 1 day"),
            (24, 72, "1-3 days"), 
            (72, 168, "3-7 days"),
            (168, 336, "1-2 weeks"),
            (336, 999999, "> 2 weeks")
        ]
        
        for min_hours, max_hours, label in duration_ranges:
            cursor.execute('''
                SELECT COUNT(*), AVG(final_price), AVG(bid_count)
                FROM auction_timing
                WHERE duration_hours >= ? AND duration_hours < ?
                AND final_price > 0
            ''', (min_hours, max_hours))
            
            result = cursor.fetchone()
            count, avg_price, avg_bids = result
            
            if count and count > 0:
                print(f"📊 {label}: {count} auctions")
                print(f"   💰 Avg Price: ${avg_price:.2f}")
                print(f"   🔢 Avg Bids: {avg_bids:.1f}")
                print()
                
        conn.close()
        
    def generate_timing_report(self):
        """Generate comprehensive timing analysis report."""
        print("📊 Comprehensive Timing Analysis Report")
        print("=" * 70)
        
        # Calculate patterns
        self.calculate_hourly_patterns()
        
        # Show optimal times
        self.find_optimal_bidding_times()
        
        # Show duration patterns
        self.analyze_duration_patterns()
        
        # Day of week analysis
        self.analyze_day_patterns()
        
    def analyze_day_patterns(self):
        """Analyze patterns by day of the week."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        print("\n📅 Day of Week Analysis")
        print("=" * 40)
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for day_num, day_name in enumerate(days):
            cursor.execute('''
                SELECT COUNT(*), AVG(competition_score), AVG(auction_count)
                FROM hourly_patterns
                WHERE day_of_week = ?
            ''', (day_num,))
            
            result = cursor.fetchone()
            count, avg_competition, avg_auctions = result
            
            if count and count > 0:
                print(f"📅 {day_name}:")
                print(f"   📊 Avg Competition: {avg_competition:.2f}/3.0")
                print(f"   🔢 Avg Auctions/Hour: {avg_auctions:.1f}")
                
                # Find best hour for this day
                cursor.execute('''
                    SELECT hour, competition_score
                    FROM hourly_patterns
                    WHERE day_of_week = ? AND auction_count >= 2
                    ORDER BY competition_score ASC
                    LIMIT 1
                ''', (day_num,))
                
                best_hour = cursor.fetchone()
                if best_hour:
                    hour, score = best_hour
                    print(f"   🎯 Best Hour: {hour:02d}:00 (Score: {score:.2f})")
                print()
                
        conn.close()
        
    async def run_timing_analysis(self, pages=10):
        """Run complete timing analysis."""
        print("⏰ Starting Auction Timing Analysis")
        print("=" * 50)
        
        try:
            # Fetch auction data
            auctions = await self.fetch_auction_data(pages)
            print(f"✅ Fetched {len(auctions)} auctions")
            
            # Analyze timing patterns
            self.analyze_auction_timing(auctions)
            print("✅ Analyzed timing patterns")
            
            # Generate comprehensive report
            print()
            self.generate_timing_report()
            
        finally:
            await self.close_session()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='mac.bid Auction Timing Analyzer')
    parser.add_argument('--pages', type=int, default=10, help='Number of pages to analyze')
    parser.add_argument('--report', action='store_true', help='Generate timing report only')
    parser.add_argument('--optimal-times', action='store_true', help='Show optimal bidding times')
    parser.add_argument('--day-analysis', action='store_true', help='Show day of week analysis')
    
    args = parser.parse_args()
    
    analyzer = TimingAnalyzer()
    
    if args.report:
        analyzer.generate_timing_report()
    elif args.optimal_times:
        analyzer.find_optimal_bidding_times()
    elif args.day_analysis:
        analyzer.analyze_day_patterns()
    else:
        asyncio.run(analyzer.run_timing_analysis(args.pages))

if __name__ == "__main__":
    main() 