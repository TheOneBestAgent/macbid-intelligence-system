#!/usr/bin/env python3
"""
API-Based South Carolina Auction Monitor
Uses working mac.bid API endpoints instead of browser scraping
"""

import asyncio
import aiohttp
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any
import time

class APIBasedSCMonitor:
    def __init__(self):
        self.setup_database()
        self.load_credentials()
        self.sc_locations = ['Rock Hill', 'Greenville', 'Spartanburg', 'Anderson']
        self.sc_location_ids = [17, 20, 28, 36, 38]  # SC warehouse IDs
        
        # Headers for API requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Add JWT token if available
        if self.jwt_token:
            self.auth_headers = self.headers.copy()
            self.auth_headers.update({
                'authorization': self.jwt_token,
                'origin': 'https://www.mac.bid',
                'referer': 'https://www.mac.bid/'
            })
        else:
            self.auth_headers = self.headers
    
    def setup_database(self):
        """Setup SQLite database for tracking opportunities."""
        self.db_path = "api_sc_monitor.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT UNIQUE,
                product_name TEXT,
                current_bid REAL,
                retail_price REAL,
                discount_percentage REAL,
                location TEXT,
                auction_id TEXT,
                auction_number TEXT,
                expected_close_date TEXT,
                is_turbo BOOLEAN,
                total_bids INTEGER,
                unique_bidders INTEGER,
                opportunity_score REAL,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'api'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                auction_number TEXT,
                lot_number TEXT,
                date_created TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_credentials(self):
        """Load JWT token and customer ID."""
        self.jwt_token = None
        self.customer_id = None
        
        try:
            tokens_file = os.path.expanduser("~/.macbid_scraper/api_tokens.json")
            with open(tokens_file, 'r') as f:
                token_data = json.load(f)
                self.jwt_token = token_data.get('tokens', {}).get('authorization')
                self.customer_id = token_data.get('customer_id')
                
            if self.jwt_token:
                print(f"✅ Loaded JWT token: {self.jwt_token[:50]}...")
            if self.customer_id:
                print(f"✅ Customer ID: {self.customer_id}")
        except Exception as e:
            print(f"⚠️ Could not load credentials: {e}")
    
    async def search_api_opportunities(self, session: aiohttp.ClientSession, search_terms: List[str]) -> List[Dict]:
        """Search for opportunities using the public search API."""
        opportunities = []
        
        for term in search_terms:
            for location in self.sc_locations:
                url = f"https://api.macdiscount.com/search?q={term}&location={location.replace(' ', '%20')}&limit=50"
                
                try:
                    async with session.get(url, headers=self.headers, timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            hits = data.get('hits', [])
                            
                            for item in hits:
                                # Calculate opportunity metrics
                                current_bid = float(item.get('current_bid', 0))
                                retail_price = float(item.get('retail_price', 0))
                                
                                if retail_price > 0:
                                    discount_percentage = ((retail_price - current_bid) / retail_price) * 100
                                else:
                                    discount_percentage = 0
                                
                                # Calculate opportunity score (similar to your 50% win rate strategy)
                                opportunity_score = self.calculate_opportunity_score(item, discount_percentage)
                                
                                # Filter for good opportunities (>40% discount, score >70)
                                if discount_percentage > 40 and opportunity_score > 70:
                                    opportunities.append({
                                        'lot_id': item.get('lot_id'),
                                        'product_name': item.get('product_name', ''),
                                        'current_bid': current_bid,
                                        'retail_price': retail_price,
                                        'discount_percentage': discount_percentage,
                                        'location': location,
                                        'auction_id': item.get('auction_id'),
                                        'auction_number': item.get('auction_number'),
                                        'expected_close_date': item.get('expected_close_date'),
                                        'is_turbo': item.get('is_turbo', False),
                                        'total_bids': item.get('total_bids', 0),
                                        'unique_bidders': item.get('unique_bidders', 0),
                                        'opportunity_score': opportunity_score,
                                        'source': f'search_api_{term}_{location}'
                                    })
                        
                        # Small delay to be respectful
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    print(f"❌ Error searching {term} in {location}: {e}")
        
        return opportunities
    
    async def get_auction_summary_opportunities(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Get opportunities from auction summary API."""
        opportunities = []
        
        # Check multiple pages
        for page in range(1, 6):  # Check first 5 pages
            url = f"https://api.macdiscount.com/auctionsummary?pg={page}&ppg=50"
            
            try:
                async with session.get(url, headers=self.headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('data', [])
                        
                        for auction in items:
                            # Check if this auction has SC locations
                            location_name = auction.get('location_name', '')
                            if any(sc_loc in location_name for sc_loc in self.sc_locations):
                                # This is a basic auction summary - we'd need to get lot details separately
                                # For now, just track the auction
                                opportunities.append({
                                    'auction_id': auction.get('id'),
                                    'auction_number': auction.get('auction_number'),
                                    'title': auction.get('title', ''),
                                    'location_name': location_name,
                                    'total_lots': auction.get('total_lots', 0),
                                    'closing_date': auction.get('closing_date'),
                                    'is_open': auction.get('is_open', False),
                                    'source': 'auction_summary_api'
                                })
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error getting auction summary page {page}: {e}")
        
        return opportunities
    
    async def get_turbo_opportunities(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Get opportunities from turbo clock auctions."""
        opportunities = []
        
        url = "https://api.macdiscount.com/turbo-clock-auctions"
        
        try:
            async with session.get(url, headers=self.headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for auction in data:
                        location_name = auction.get('location_name', '')
                        if any(sc_loc in location_name for sc_loc in self.sc_locations):
                            # Get items from turbo auction
                            items = auction.get('items', [])
                            
                            for item in items:
                                current_bid = float(item.get('current_bid', 0))
                                retail_price = float(item.get('retail_price', 0))
                                
                                if retail_price > 0:
                                    discount_percentage = ((retail_price - current_bid) / retail_price) * 100
                                    opportunity_score = self.calculate_opportunity_score(item, discount_percentage)
                                    
                                    if discount_percentage > 30:  # Lower threshold for turbo auctions
                                        opportunities.append({
                                            'lot_id': item.get('lot_id'),
                                            'product_name': item.get('product_name', ''),
                                            'current_bid': current_bid,
                                            'retail_price': retail_price,
                                            'discount_percentage': discount_percentage,
                                            'location': location_name,
                                            'auction_id': auction.get('id'),
                                            'auction_number': auction.get('auction_number'),
                                            'is_turbo': True,
                                            'opportunity_score': opportunity_score,
                                            'source': 'turbo_api'
                                        })
        
        except Exception as e:
            print(f"❌ Error getting turbo auctions: {e}")
        
        return opportunities
    
    async def get_personal_watchlist(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Get current watchlist items."""
        if not self.customer_id or not self.jwt_token:
            return []
        
        watchlist_items = []
        url = f"https://api.macdiscount.com/auctions/customer/{self.customer_id}/active-auctions"
        
        try:
            async with session.get(url, headers=self.auth_headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    watchlist = data.get('watchlist', [])
                    
                    for item in watchlist:
                        watchlist_items.append({
                            'lot_id': item.get('lot_id'),
                            'auction_number': item.get('auction_number'),
                            'lot_number': item.get('lot_number'),
                            'date_created': item.get('date_created')
                        })
        
        except Exception as e:
            print(f"❌ Error getting watchlist: {e}")
        
        return watchlist_items
    
    def calculate_opportunity_score(self, item: Dict, discount_percentage: float) -> float:
        """Calculate opportunity score based on your successful bidding patterns."""
        score = 0
        
        # Base score from discount percentage
        score += min(discount_percentage, 100)
        
        # Bonus for low bid count (easier to win)
        total_bids = item.get('total_bids', 0)
        if total_bids == 0:
            score += 20
        elif total_bids < 5:
            score += 15
        elif total_bids < 10:
            score += 10
        
        # Bonus for low unique bidders
        unique_bidders = item.get('unique_bidders', 0)
        if unique_bidders == 0:
            score += 15
        elif unique_bidders < 3:
            score += 10
        elif unique_bidders < 5:
            score += 5
        
        # Bonus for electronics (your successful category)
        product_name = item.get('product_name', '').lower()
        if any(term in product_name for term in ['headphone', 'gaming', 'processor', 'microphone', 'sony', 'steelseries']):
            score += 15
        
        # Penalty for very high retail prices (harder to get good deals)
        retail_price = float(item.get('retail_price', 0))
        if retail_price > 500:
            score -= 10
        elif retail_price > 200:
            score -= 5
        
        return min(score, 100)  # Cap at 100
    
    def save_opportunities(self, opportunities: List[Dict]):
        """Save opportunities to database."""
        if not opportunities:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for opp in opportunities:
            cursor.execute('''
                INSERT OR REPLACE INTO opportunities 
                (lot_id, product_name, current_bid, retail_price, discount_percentage, 
                 location, auction_id, auction_number, expected_close_date, is_turbo, 
                 total_bids, unique_bidders, opportunity_score, source, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                opp.get('lot_id'),
                opp.get('product_name'),
                opp.get('current_bid'),
                opp.get('retail_price'),
                opp.get('discount_percentage'),
                opp.get('location'),
                opp.get('auction_id'),
                opp.get('auction_number'),
                opp.get('expected_close_date'),
                opp.get('is_turbo', False),
                opp.get('total_bids'),
                opp.get('unique_bidders'),
                opp.get('opportunity_score'),
                opp.get('source'),
            ))
        
        conn.commit()
        conn.close()
        
        print(f"💾 Saved {len(opportunities)} opportunities to database")
    
    def save_watchlist(self, watchlist_items: List[Dict]):
        """Save watchlist items to database."""
        if not watchlist_items:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing watchlist
        cursor.execute('DELETE FROM watchlist_items')
        
        for item in watchlist_items:
            cursor.execute('''
                INSERT INTO watchlist_items (lot_id, auction_number, lot_number, date_created)
                VALUES (?, ?, ?, ?)
            ''', (
                item.get('lot_id'),
                item.get('auction_number'),
                item.get('lot_number'),
                item.get('date_created')
            ))
        
        conn.commit()
        conn.close()
        
        print(f"👀 Updated watchlist with {len(watchlist_items)} items")
    
    def display_top_opportunities(self, limit: int = 10):
        """Display top opportunities from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT product_name, current_bid, retail_price, discount_percentage, 
                   location, opportunity_score, total_bids, unique_bidders, source
            FROM opportunities 
            WHERE discount_percentage > 40
            ORDER BY opportunity_score DESC, discount_percentage DESC
            LIMIT ?
        ''', (limit,))
        
        opportunities = cursor.fetchall()
        conn.close()
        
        if opportunities:
            print(f"\n🎯 TOP {len(opportunities)} SOUTH CAROLINA OPPORTUNITIES:")
            print("=" * 80)
            
            for i, opp in enumerate(opportunities, 1):
                product, current_bid, retail, discount, location, score, bids, bidders, source = opp
                savings = retail - current_bid if retail and current_bid else 0
                
                print(f"{i:2d}. 📦 {product[:50]}")
                print(f"    💰 Current: ${current_bid:.2f} | Retail: ${retail:.2f} | Save: ${savings:.2f} ({discount:.1f}%)")
                print(f"    🏢 {location} | 🎯 Score: {score:.1f} | 👥 {bidders} bidders, {bids} bids")
                print(f"    📊 Source: {source}")
                print()
        else:
            print("❌ No high-value opportunities found")
    
    async def run_scan(self):
        """Run a complete scan using all working API endpoints."""
        print("🚀 Starting API-Based South Carolina Auction Scan")
        print("=" * 60)
        print(f"⏰ Scan started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            # 1. Search API opportunities
            print("\n1. 🔍 Scanning Search API...")
            search_terms = ['electronics', 'gaming', 'headphones', 'laptop', 'processor', 'microphone']
            search_opportunities = await self.search_api_opportunities(session, search_terms)
            print(f"   Found {len(search_opportunities)} search opportunities")
            
            # 2. Auction Summary opportunities
            print("\n2. 📊 Scanning Auction Summary API...")
            summary_opportunities = await self.get_auction_summary_opportunities(session)
            print(f"   Found {len(summary_opportunities)} auction summaries")
            
            # 3. Turbo auction opportunities
            print("\n3. ⚡ Scanning Turbo Clock Auctions...")
            turbo_opportunities = await self.get_turbo_opportunities(session)
            print(f"   Found {len(turbo_opportunities)} turbo opportunities")
            
            # 4. Personal watchlist
            print("\n4. 👀 Getting Personal Watchlist...")
            watchlist_items = await self.get_personal_watchlist(session)
            print(f"   Found {len(watchlist_items)} watchlist items")
            
            # Save all data
            all_opportunities = search_opportunities + turbo_opportunities
            if all_opportunities:
                self.save_opportunities(all_opportunities)
            
            if watchlist_items:
                self.save_watchlist(watchlist_items)
            
            # Display results
            self.display_top_opportunities()
            
            print(f"\n✅ Scan completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📊 Total opportunities found: {len(all_opportunities)}")
            print(f"💾 Database: {self.db_path}")

async def main():
    monitor = APIBasedSCMonitor()
    await monitor.run_scan()

if __name__ == "__main__":
    asyncio.run(main()) 