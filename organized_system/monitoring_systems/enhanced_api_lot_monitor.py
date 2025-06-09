#!/usr/bin/env python3
"""
Enhanced API-Based Lot Monitor for South Carolina
Checks individual lots within auctions, not just auction summaries
"""

import asyncio
import aiohttp
import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import List, Dict, Any
import time

class EnhancedAPILotMonitor:
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
        """Setup SQLite database for tracking lot opportunities."""
        self.db_path = "enhanced_api_lots.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lot_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT UNIQUE,
                product_name TEXT,
                current_bid REAL,
                retail_price REAL,
                instant_win_price REAL,
                discount_percentage REAL,
                instant_win_discount_percent REAL,
                location TEXT,
                us_state TEXT,
                auction_id TEXT,
                auction_number TEXT,
                lot_number TEXT,
                expected_close_date TEXT,
                expected_closing_utc TEXT,
                is_turbo BOOLEAN,
                is_open BOOLEAN,
                is_shippable BOOLEAN,
                total_bids INTEGER,
                unique_bidders INTEGER,
                category TEXT,
                condition TEXT,
                upc TEXT,
                opportunity_score REAL,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT DEFAULT 'api'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auction_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id TEXT UNIQUE,
                auction_number TEXT,
                title TEXT,
                location_name TEXT,
                total_lots INTEGER,
                closing_date TEXT,
                is_open BOOLEAN,
                is_active BOOLEAN,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    async def get_detailed_lots_from_search(self, session: aiohttp.ClientSession, search_terms: List[str]) -> List[Dict]:
        """Get detailed lot information using search API with higher limits."""
        lots = []
        
        for term in search_terms:
            # Search without location filter first to get more results
            url = f"https://api.macdiscount.com/search?q={term}&limit=100"
            
            try:
                async with session.get(url, headers=self.headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        hits = data.get('hits', [])
                        
                        print(f"   📦 Found {len(hits)} lots for '{term}'")
                        
                        for item in hits:
                            # Filter for South Carolina locations
                            us_state = item.get('us_state', '')
                            auction_location = item.get('auction_location', '')
                            
                            # Check if it's in South Carolina
                            is_sc = (us_state == 'South Carolina' or 
                                   any(sc_loc in auction_location for sc_loc in self.sc_locations))
                            
                            if is_sc:
                                # Calculate opportunity metrics
                                current_bid = float(item.get('current_bid', 0))
                                retail_price = float(item.get('retail_price', 0))
                                instant_win_price = float(item.get('instant_win_price', 0))
                                
                                if retail_price > 0:
                                    if current_bid > 0:
                                        discount_percentage = ((retail_price - current_bid) / retail_price) * 100
                                    else:
                                        discount_percentage = 100  # No bids yet
                                else:
                                    discount_percentage = 0
                                
                                # Calculate opportunity score
                                opportunity_score = self.calculate_lot_opportunity_score(item, discount_percentage)
                                
                                lots.append({
                                    'lot_id': item.get('lot_id'),
                                    'product_name': item.get('product_name', ''),
                                    'current_bid': current_bid,
                                    'retail_price': retail_price,
                                    'instant_win_price': instant_win_price,
                                    'discount_percentage': discount_percentage,
                                    'instant_win_discount_percent': item.get('instant_win_discount_percent', 0),
                                    'location': auction_location,
                                    'us_state': us_state,
                                    'auction_id': item.get('auction_id'),
                                    'auction_number': item.get('auction_number'),
                                    'lot_number': item.get('lot_number'),
                                    'expected_close_date': item.get('expected_close_date'),
                                    'expected_closing_utc': item.get('expected_closing_utc'),
                                    'is_turbo': item.get('is_turbo', False),
                                    'is_open': item.get('is_open', False),
                                    'is_shippable': item.get('is_shippable', False),
                                    'total_bids': item.get('total_bids', 0),
                                    'unique_bidders': item.get('unique_bidders', 0),
                                    'category': item.get('category', ''),
                                    'condition': item.get('condition', ''),
                                    'upc': item.get('upc', ''),
                                    'opportunity_score': opportunity_score,
                                    'source': f'search_lots_{term}'
                                })
                        
                        # Small delay to be respectful
                        await asyncio.sleep(0.5)
                        
            except Exception as e:
                print(f"❌ Error searching lots for {term}: {e}")
        
        return lots
    
    async def get_lots_from_location_search(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Get lots by searching each SC location specifically."""
        lots = []
        
        for location in self.sc_locations:
            # Search for all items in this location
            url = f"https://api.macdiscount.com/search?q=&location={location.replace(' ', '%20')}&limit=100"
            
            try:
                async with session.get(url, headers=self.headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        hits = data.get('hits', [])
                        
                        print(f"   🏢 Found {len(hits)} lots in {location}")
                        
                        for item in hits:
                            current_bid = float(item.get('current_bid', 0))
                            retail_price = float(item.get('retail_price', 0))
                            
                            if retail_price > 0:
                                if current_bid > 0:
                                    discount_percentage = ((retail_price - current_bid) / retail_price) * 100
                                else:
                                    discount_percentage = 100  # No bids yet
                                
                                opportunity_score = self.calculate_lot_opportunity_score(item, discount_percentage)
                                
                                lots.append({
                                    'lot_id': item.get('lot_id'),
                                    'product_name': item.get('product_name', ''),
                                    'current_bid': current_bid,
                                    'retail_price': retail_price,
                                    'instant_win_price': float(item.get('instant_win_price', 0)),
                                    'discount_percentage': discount_percentage,
                                    'instant_win_discount_percent': item.get('instant_win_discount_percent', 0),
                                    'location': location,
                                    'us_state': 'South Carolina',
                                    'auction_id': item.get('auction_id'),
                                    'auction_number': item.get('auction_number'),
                                    'lot_number': item.get('lot_number'),
                                    'expected_close_date': item.get('expected_close_date'),
                                    'expected_closing_utc': item.get('expected_closing_utc'),
                                    'is_turbo': item.get('is_turbo', False),
                                    'is_open': item.get('is_open', False),
                                    'is_shippable': item.get('is_shippable', False),
                                    'total_bids': item.get('total_bids', 0),
                                    'unique_bidders': item.get('unique_bidders', 0),
                                    'category': item.get('category', ''),
                                    'condition': item.get('condition', ''),
                                    'upc': item.get('upc', ''),
                                    'opportunity_score': opportunity_score,
                                    'source': f'location_search_{location}'
                                })
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error searching {location}: {e}")
        
        return lots
    
    async def get_turbo_lots(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Get individual lots from turbo clock auctions."""
        lots = []
        
        url = "https://api.macdiscount.com/turbo-clock-auctions"
        
        try:
            async with session.get(url, headers=self.headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for auction in data:
                        location_name = auction.get('location_name', '')
                        
                        # Check if this is a SC location
                        is_sc = any(sc_loc in location_name for sc_loc in self.sc_locations)
                        
                        if is_sc:
                            # Get individual items/lots from turbo auction
                            items = auction.get('items', [])
                            
                            print(f"   ⚡ Found {len(items)} turbo lots in {location_name}")
                            
                            for item in items:
                                current_bid = float(item.get('current_bid', 0))
                                retail_price = float(item.get('retail_price', 0))
                                
                                if retail_price > 0:
                                    if current_bid > 0:
                                        discount_percentage = ((retail_price - current_bid) / retail_price) * 100
                                    else:
                                        discount_percentage = 100
                                    
                                    opportunity_score = self.calculate_lot_opportunity_score(item, discount_percentage)
                                    
                                    lots.append({
                                        'lot_id': item.get('lot_id'),
                                        'product_name': item.get('product_name', ''),
                                        'current_bid': current_bid,
                                        'retail_price': retail_price,
                                        'instant_win_price': float(item.get('instant_win_price', 0)),
                                        'discount_percentage': discount_percentage,
                                        'location': location_name,
                                        'us_state': 'South Carolina',
                                        'auction_id': auction.get('id'),
                                        'auction_number': auction.get('auction_number'),
                                        'lot_number': item.get('lot_number'),
                                        'is_turbo': True,
                                        'is_open': item.get('is_open', False),
                                        'is_shippable': item.get('is_shippable', False),
                                        'total_bids': item.get('total_bids', 0),
                                        'unique_bidders': item.get('unique_bidders', 0),
                                        'category': item.get('category', ''),
                                        'condition': item.get('condition', ''),
                                        'opportunity_score': opportunity_score,
                                        'source': 'turbo_lots'
                                    })
        
        except Exception as e:
            print(f"❌ Error getting turbo lots: {e}")
        
        return lots
    
    def calculate_lot_opportunity_score(self, item: Dict, discount_percentage: float) -> float:
        """Calculate opportunity score for individual lots based on your successful patterns."""
        score = 0
        
        # Base score from discount percentage
        score += min(discount_percentage, 100)
        
        # Bonus for no bids yet (easier to win)
        total_bids = item.get('total_bids', 0)
        if total_bids == 0:
            score += 25  # Higher bonus for no bids
        elif total_bids < 3:
            score += 20
        elif total_bids < 5:
            score += 15
        elif total_bids < 10:
            score += 10
        
        # Bonus for low unique bidders
        unique_bidders = item.get('unique_bidders', 0)
        if unique_bidders == 0:
            score += 20
        elif unique_bidders < 2:
            score += 15
        elif unique_bidders < 3:
            score += 10
        elif unique_bidders < 5:
            score += 5
        
        # Bonus for your successful categories
        product_name = item.get('product_name', '').lower()
        if any(term in product_name for term in ['headphone', 'gaming', 'processor', 'microphone', 'sony', 'steelseries', 'amd', 'ryzen']):
            score += 20
        elif any(term in product_name for term in ['electronics', 'laptop', 'monitor', 'keyboard', 'mouse']):
            score += 10
        
        # Bonus for good condition
        condition = item.get('condition', '').lower()
        if 'new' in condition:
            score += 10
        elif 'open box' in condition:
            score += 5
        
        # Bonus for shippable items
        if item.get('is_shippable', False):
            score += 5
        
        # Penalty for very high retail prices (harder to get good deals)
        retail_price = float(item.get('retail_price', 0))
        if retail_price > 1000:
            score -= 15
        elif retail_price > 500:
            score -= 10
        elif retail_price > 200:
            score -= 5
        
        # Bonus for instant win opportunities
        instant_win_discount = item.get('instant_win_discount_percent', 0)
        if instant_win_discount > 50:
            score += 15
        elif instant_win_discount > 30:
            score += 10
        
        return min(score, 100)  # Cap at 100
    
    def save_lots(self, lots: List[Dict]):
        """Save lot opportunities to database."""
        if not lots:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for lot in lots:
            cursor.execute('''
                INSERT OR REPLACE INTO lot_opportunities 
                (lot_id, product_name, current_bid, retail_price, instant_win_price,
                 discount_percentage, instant_win_discount_percent, location, us_state,
                 auction_id, auction_number, lot_number, expected_close_date, expected_closing_utc,
                 is_turbo, is_open, is_shippable, total_bids, unique_bidders, category, condition,
                 upc, opportunity_score, source, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                lot.get('lot_id'),
                lot.get('product_name'),
                lot.get('current_bid'),
                lot.get('retail_price'),
                lot.get('instant_win_price'),
                lot.get('discount_percentage'),
                lot.get('instant_win_discount_percent'),
                lot.get('location'),
                lot.get('us_state'),
                lot.get('auction_id'),
                lot.get('auction_number'),
                lot.get('lot_number'),
                lot.get('expected_close_date'),
                lot.get('expected_closing_utc'),
                lot.get('is_turbo', False),
                lot.get('is_open', False),
                lot.get('is_shippable', False),
                lot.get('total_bids'),
                lot.get('unique_bidders'),
                lot.get('category'),
                lot.get('condition'),
                lot.get('upc'),
                lot.get('opportunity_score'),
                lot.get('source'),
            ))
        
        conn.commit()
        conn.close()
        
        print(f"💾 Saved {len(lots)} lot opportunities to database")
    
    def display_top_lot_opportunities(self, limit: int = 15):
        """Display top lot opportunities from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT product_name, current_bid, retail_price, discount_percentage, 
                   location, opportunity_score, total_bids, unique_bidders, 
                   lot_number, auction_number, is_turbo, is_open, condition, source
            FROM lot_opportunities 
            WHERE discount_percentage > 30
            ORDER BY opportunity_score DESC, discount_percentage DESC
            LIMIT ?
        ''', (limit,))
        
        opportunities = cursor.fetchall()
        conn.close()
        
        if opportunities:
            print(f"\n🎯 TOP {len(opportunities)} SOUTH CAROLINA LOT OPPORTUNITIES:")
            print("=" * 100)
            
            for i, opp in enumerate(opportunities, 1):
                (product, current_bid, retail, discount, location, score, 
                 bids, bidders, lot_num, auction_num, is_turbo, is_open, condition, source) = opp
                
                savings = retail - current_bid if retail and current_bid else retail
                turbo_indicator = "⚡" if is_turbo else "🔨"
                open_indicator = "🟢" if is_open else "🔴"
                
                print(f"{i:2d}. {turbo_indicator} {open_indicator} 📦 {product[:55]}")
                print(f"    💰 Current: ${current_bid:.2f} | Retail: ${retail:.2f} | Save: ${savings:.2f} ({discount:.1f}%)")
                print(f"    🏢 {location} | 🎯 Score: {score:.1f} | 👥 {bidders} bidders, {bids} bids")
                print(f"    📋 Lot #{lot_num} in Auction #{auction_num} | Condition: {condition}")
                print(f"    📊 Source: {source}")
                print()
        else:
            print("❌ No high-value lot opportunities found")
    
    def get_lot_statistics(self):
        """Display statistics about discovered lots."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total lots
        cursor.execute('SELECT COUNT(*) FROM lot_opportunities')
        total_lots = cursor.fetchone()[0]
        
        # Lots by location
        cursor.execute('SELECT location, COUNT(*) FROM lot_opportunities GROUP BY location ORDER BY COUNT(*) DESC')
        location_stats = cursor.fetchall()
        
        # Lots with no bids
        cursor.execute('SELECT COUNT(*) FROM lot_opportunities WHERE total_bids = 0')
        no_bid_lots = cursor.fetchone()[0]
        
        # High discount lots
        cursor.execute('SELECT COUNT(*) FROM lot_opportunities WHERE discount_percentage > 50')
        high_discount_lots = cursor.fetchone()[0]
        
        # Open lots
        cursor.execute('SELECT COUNT(*) FROM lot_opportunities WHERE is_open = 1')
        open_lots = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 LOT DISCOVERY STATISTICS:")
        print("=" * 50)
        print(f"📦 Total Lots Found: {total_lots}")
        print(f"🟢 Open for Bidding: {open_lots}")
        print(f"🎯 No Bids Yet: {no_bid_lots}")
        print(f"💎 High Discount (>50%): {high_discount_lots}")
        print(f"\n🏢 Lots by Location:")
        for location, count in location_stats:
            print(f"   {location}: {count} lots")
    
    async def run_comprehensive_lot_scan(self):
        """Run a comprehensive scan of individual lots using all working API endpoints."""
        print("🚀 Starting Comprehensive Lot-Level Scan")
        print("=" * 70)
        print(f"⏰ Scan started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            # 1. Search for lots by category
            print("\n1. 🔍 Scanning Lots by Search Terms...")
            search_terms = ['electronics', 'gaming', 'headphones', 'laptop', 'processor', 'microphone', 'monitor', 'keyboard']
            search_lots = await self.get_detailed_lots_from_search(session, search_terms)
            print(f"   Found {len(search_lots)} lots from search")
            
            # 2. Search for lots by location
            print("\n2. 🏢 Scanning Lots by SC Locations...")
            location_lots = await self.get_lots_from_location_search(session)
            print(f"   Found {len(location_lots)} lots from location search")
            
            # 3. Get turbo lots
            print("\n3. ⚡ Scanning Turbo Clock Lots...")
            turbo_lots = await self.get_turbo_lots(session)
            print(f"   Found {len(turbo_lots)} turbo lots")
            
            # Combine and deduplicate lots
            all_lots = search_lots + location_lots + turbo_lots
            unique_lots = {}
            for lot in all_lots:
                lot_id = lot.get('lot_id')
                if lot_id and lot_id not in unique_lots:
                    unique_lots[lot_id] = lot
            
            unique_lots_list = list(unique_lots.values())
            
            # Save all lots
            if unique_lots_list:
                self.save_lots(unique_lots_list)
            
            # Display results
            self.get_lot_statistics()
            self.display_top_lot_opportunities()
            
            print(f"\n✅ Comprehensive lot scan completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📊 Total unique lots found: {len(unique_lots_list)}")
            print(f"💾 Database: {self.db_path}")

async def main():
    monitor = EnhancedAPILotMonitor()
    await monitor.run_comprehensive_lot_scan()

if __name__ == "__main__":
    asyncio.run(main()) 