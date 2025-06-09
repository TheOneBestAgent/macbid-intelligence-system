#!/usr/bin/env python3
"""
💰 OPTIMIZED BID PRICE SCANNER
Ultra-fast bid monitoring system with authentication and smart filtering
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

class OptimizedBidScanner:
    def __init__(self):
        self.session = None
        self.authenticated = False
        self.customer_id = None
        
        # Performance settings
        self.max_concurrent = 50  # Process 50 lots simultaneously
        self.batch_size = 100     # Process in batches of 100
        self.rate_limit = 0.02    # 20ms between requests (very fast)
        
        self.setup_database()
    
    def setup_database(self):
        """Setup optimized bid tracking database."""
        self.db_path = 'optimized_bid_tracking.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main bid tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_tracking (
                lot_id TEXT PRIMARY KEY,
                title TEXT,
                retail_price REAL,
                current_bid REAL,
                previous_bid REAL,
                bid_count INTEGER,
                unique_bidders INTEGER,
                auction_location TEXT,
                expected_close_date TEXT,
                is_open INTEGER,
                priority_score REAL,
                last_checked TIMESTAMP,
                last_updated TIMESTAMP,
                check_frequency INTEGER DEFAULT 1,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bid history table for tracking changes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                old_bid REAL,
                new_bid REAL,
                bid_increase REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lot_id) REFERENCES bid_tracking (lot_id)
            )
        ''')
        
        # Performance index
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_priority_open 
            ON bid_tracking (priority_score DESC, is_open DESC, last_checked ASC)
        ''')
        
        conn.commit()
        conn.close()
        print("🗄️ Optimized bid tracking database initialized")
    
    async def authenticate_fast(self):
        """Fast authentication for bid monitoring."""
        print("🔐 FAST AUTHENTICATION")
        print("-" * 30)
        
        try:
            credentials_path = Path.home() / '.macbid_scraper' / 'credentials.json'
            
            if not credentials_path.exists():
                print("❌ No credentials found!")
                return False
            
            with open(credentials_path, 'r') as f:
                credentials = json.load(f)
            
            self.customer_id = credentials.get('customer_id')
            
            # Create high-performance session
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(
                ssl=ssl_context, 
                limit=100,           # High connection limit
                limit_per_host=50,   # High per-host limit
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive'
                }
            )
            
            print("✅ Fast session created")
            self.authenticated = True
            return True
            
        except Exception as e:
            print(f"❌ Auth error: {e}")
            return False
    
    def load_lots_for_monitoring(self, source_db=None):
        """Load lots from discovery database for monitoring."""
        print("📊 LOADING LOTS FOR MONITORING")
        print("-" * 40)
        
        # Try to load from the latest discovery database
        possible_sources = [
            source_db,
            'master_authenticated_lots.db',
            'typesense_paginated_all_lots.db',
            'enhanced_authenticated_lots.db',
            'typesense_all_lots.db'
        ]
        
        lots_loaded = []
        
        for db_path in possible_sources:
            if not db_path or not Path(db_path).exists():
                continue
            
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Try different table names
                table_names = ['authenticated_lots', 'paginated_lots', 'enhanced_lots', 'typesense_lots']
                
                for table_name in table_names:
                    try:
                        cursor.execute(f'''
                            SELECT lot_id, title, retail_price, current_bid, auction_location, 
                                   expected_close_date, is_open
                            FROM {table_name}
                            WHERE is_open = 1 AND retail_price > 50
                            ORDER BY retail_price DESC
                        ''')
                        
                        rows = cursor.fetchall()
                        if rows:
                            lots_loaded = [
                                {
                                    'lot_id': row[0],
                                    'title': row[1],
                                    'retail_price': row[2],
                                    'current_bid': row[3],
                                    'auction_location': row[4],
                                    'expected_close_date': row[5],
                                    'is_open': row[6]
                                }
                                for row in rows
                            ]
                            print(f"✅ Loaded {len(lots_loaded):,} lots from {db_path} ({table_name})")
                            break
                    except sqlite3.OperationalError:
                        continue
                
                conn.close()
                
                if lots_loaded:
                    break
                    
            except Exception as e:
                print(f"   ❌ Error loading from {db_path}: {e}")
                continue
        
        if not lots_loaded:
            print("❌ No lots found in any database!")
            return []
        
        # Calculate priority scores and filter
        high_priority_lots = []
        
        for lot in lots_loaded:
            retail_price = lot.get('retail_price', 0)
            current_bid = lot.get('current_bid', 0)
            
            # Priority scoring
            if retail_price > 0:
                discount_pct = ((retail_price - current_bid) / retail_price) * 100
                
                # High priority criteria
                priority_score = 0
                
                # Value-based scoring
                if retail_price > 1000:
                    priority_score += 3
                elif retail_price > 500:
                    priority_score += 2
                elif retail_price > 100:
                    priority_score += 1
                
                # Discount-based scoring
                if discount_pct > 90:
                    priority_score += 3
                elif discount_pct > 70:
                    priority_score += 2
                elif discount_pct > 50:
                    priority_score += 1
                
                # No bid bonus
                if current_bid == 0:
                    priority_score += 2
                
                lot['priority_score'] = priority_score
                
                # Only monitor high-priority lots for speed
                if priority_score >= 3:  # Minimum priority threshold
                    high_priority_lots.append(lot)
        
        # Sort by priority and limit for performance
        high_priority_lots.sort(key=lambda x: x['priority_score'], reverse=True)
        
        # Limit to top 5000 lots for optimal performance
        if len(high_priority_lots) > 5000:
            high_priority_lots = high_priority_lots[:5000]
            print(f"⚡ Limited to top 5,000 high-priority lots for optimal speed")
        
        print(f"🎯 Selected {len(high_priority_lots):,} high-priority lots for monitoring")
        
        # Store in tracking database
        self.store_lots_for_tracking(high_priority_lots)
        
        return high_priority_lots
    
    def store_lots_for_tracking(self, lots):
        """Store lots in tracking database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for lot in lots:
            cursor.execute('''
                INSERT OR REPLACE INTO bid_tracking 
                (lot_id, title, retail_price, current_bid, previous_bid, auction_location,
                 expected_close_date, is_open, priority_score, last_checked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lot['lot_id'],
                lot['title'],
                lot['retail_price'],
                lot['current_bid'],
                lot['current_bid'],  # previous_bid starts same as current
                lot['auction_location'],
                lot['expected_close_date'],
                lot['is_open'],
                lot['priority_score'],
                datetime.now().isoformat()
            ))
        
        conn.commit()
        conn.close()
    
    async def check_single_lot_bid(self, lot):
        """Ultra-fast single lot bid check."""
        try:
            lot_id = lot['lot_id']
            
            # Try multiple API endpoints for speed
            endpoints = [
                f"https://api.macdiscount.com/lots/{lot_id}",
                f"https://api.macdiscount.com/search?lot_id={lot_id}",
            ]
            
            for endpoint in endpoints:
                try:
                    async with self.session.get(endpoint) as response:
                        if response.status == 200:
                            data = await response.json()
                            
                            # Extract bid info
                            current_bid = data.get('current_bid', 0)
                            bid_count = data.get('total_bids', 0)
                            unique_bidders = data.get('unique_bidders', 0)
                            
                            # Check for changes
                            old_bid = lot.get('current_bid', 0)
                            
                            if current_bid != old_bid:
                                # Bid changed!
                                return {
                                    'lot_id': lot_id,
                                    'old_bid': old_bid,
                                    'new_bid': current_bid,
                                    'bid_count': bid_count,
                                    'unique_bidders': unique_bidders,
                                    'increase': current_bid - old_bid,
                                    'title': lot.get('title', ''),
                                    'retail_price': lot.get('retail_price', 0)
                                }
                            
                            return None  # No change
                            
                except asyncio.TimeoutError:
                    continue  # Try next endpoint
                except Exception:
                    continue  # Try next endpoint
            
            return None  # All endpoints failed
            
        except Exception:
            return None
    
    async def monitor_batch(self, lots_batch):
        """Monitor a batch of lots concurrently."""
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def check_with_semaphore(lot):
            async with semaphore:
                result = await self.check_single_lot_bid(lot)
                await asyncio.sleep(self.rate_limit)  # Rate limiting
                return result
        
        # Process batch concurrently
        tasks = [check_with_semaphore(lot) for lot in lots_batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        bid_changes = [
            result for result in results 
            if result is not None and not isinstance(result, Exception)
        ]
        
        return bid_changes
    
    def store_bid_changes(self, changes):
        """Store bid changes in database."""
        if not changes:
            return
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for change in changes:
            # Store in bid_changes table
            cursor.execute('''
                INSERT INTO bid_changes (lot_id, old_bid, new_bid, bid_increase)
                VALUES (?, ?, ?, ?)
            ''', (
                change['lot_id'],
                change['old_bid'],
                change['new_bid'],
                change['increase']
            ))
            
            # Update main tracking table
            cursor.execute('''
                UPDATE bid_tracking 
                SET current_bid = ?, previous_bid = ?, last_checked = ?, last_updated = ?
                WHERE lot_id = ?
            ''', (
                change['new_bid'],
                change['old_bid'],
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                change['lot_id']
            ))
        
        conn.commit()
        conn.close()
    
    def show_bid_changes(self, changes):
        """Display bid changes in real-time."""
        if not changes:
            return
        
        print(f"\n🔥 LIVE BID CHANGES DETECTED!")
        print("=" * 60)
        
        # Sort by bid increase (highest first)
        changes.sort(key=lambda x: x['increase'], reverse=True)
        
        for change in changes:
            title = change['title'][:50] + "..." if len(change['title']) > 50 else change['title']
            
            print(f"📈 {title}")
            print(f"   Old Bid: ${change['old_bid']:.2f} → New Bid: ${change['new_bid']:.2f}")
            print(f"   Increase: +${change['increase']:.2f} | Retail: ${change['retail_price']:.2f}")
            print(f"   🔗 https://mac.bid/lot/mac_lot_{change['lot_id']}")
            print()
    
    async def run_optimized_monitoring(self, source_db=None, duration_minutes=60):
        """Run optimized bid monitoring."""
        print("💰 OPTIMIZED BID PRICE SCANNER")
        print("=" * 60)
        print(f"⚡ Ultra-fast monitoring with {self.max_concurrent} concurrent checks")
        print(f"🎯 Duration: {duration_minutes} minutes")
        print()
        
        if not await self.authenticate_fast():
            print("❌ Authentication failed")
            return
        
        # Load lots for monitoring
        lots = self.load_lots_for_monitoring(source_db)
        if not lots:
            print("❌ No lots to monitor")
            return
        
        print(f"\n💰 STARTING OPTIMIZED BID MONITORING")
        print("-" * 50)
        print(f"📊 Monitoring {len(lots):,} high-priority lots")
        print(f"⚡ Batch size: {self.batch_size} | Concurrent: {self.max_concurrent}")
        print(f"🕒 Rate limit: {self.rate_limit*1000:.0f}ms between requests")
        print()
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        
        total_checks = 0
        total_changes = 0
        cycle = 1
        
        try:
            while time.time() < end_time:
                cycle_start = time.time()
                print(f"🔄 Monitoring Cycle {cycle}")
                print("-" * 30)
                
                # Process in batches
                cycle_changes = []
                
                for i in range(0, len(lots), self.batch_size):
                    batch = lots[i:i + self.batch_size]
                    batch_num = (i // self.batch_size) + 1
                    total_batches = (len(lots) + self.batch_size - 1) // self.batch_size
                    
                    print(f"   Batch {batch_num}/{total_batches} ({len(batch)} lots)...", end="")
                    
                    batch_changes = await self.monitor_batch(batch)
                    
                    if batch_changes:
                        cycle_changes.extend(batch_changes)
                        print(f" 🔥 {len(batch_changes)} changes!")
                    else:
                        print(" ✅ No changes")
                    
                    total_checks += len(batch)
                
                # Store and display changes
                if cycle_changes:
                    self.store_bid_changes(cycle_changes)
                    self.show_bid_changes(cycle_changes)
                    total_changes += len(cycle_changes)
                
                cycle_time = time.time() - cycle_start
                remaining_time = (end_time - time.time()) / 60
                
                print(f"\n📊 Cycle {cycle} Complete:")
                print(f"   ⏱️  Time: {cycle_time:.1f}s | Changes: {len(cycle_changes)} | Total Changes: {total_changes}")
                print(f"   📈 Checks/sec: {len(lots)/cycle_time:.1f} | Remaining: {remaining_time:.1f}min")
                print()
                
                cycle += 1
                
                # Brief pause between cycles
                await asyncio.sleep(2)
        
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        
        finally:
            total_time = time.time() - start_time
            
            print(f"\n💰 OPTIMIZED MONITORING COMPLETE")
            print("=" * 50)
            print(f"⏱️  Total Runtime: {total_time:.1f} seconds")
            print(f"🔄 Cycles Completed: {cycle - 1}")
            print(f"📊 Total Checks: {total_checks:,}")
            print(f"🔥 Total Changes: {total_changes}")
            print(f"📈 Average Speed: {total_checks/total_time:.1f} checks/second")
            print(f"💾 Database: {self.db_path}")
            
            if self.session:
                await self.session.close()

async def main():
    import sys
    
    # Command line arguments
    source_db = sys.argv[1] if len(sys.argv) > 1 else None
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 60
    
    scanner = OptimizedBidScanner()
    await scanner.run_optimized_monitoring(source_db, duration)

if __name__ == "__main__":
    asyncio.run(main()) 