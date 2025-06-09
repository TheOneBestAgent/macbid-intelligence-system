#!/usr/bin/env python3
"""
🔥 MEGA LOT DISCOVERY - Maximum lot discovery using all possible techniques
"""

import asyncio
import json
import sqlite3
from datetime import datetime
import aiohttp
import ssl
import string
import itertools

class MegaLotDiscovery:
    def __init__(self):
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        self.discovered_lots = {}
        self.setup_database()
    
    def setup_database(self):
        """Setup mega discovery database."""
        self.db_path = 'mega_lot_discovery.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mega_lots (
                lot_id TEXT PRIMARY KEY,
                title TEXT,
                retail_price REAL,
                current_bid REAL,
                location TEXT,
                discovery_method TEXT,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("🗄️ Mega discovery database initialized")
    
    async def mega_search(self, session, params, max_pages=50):
        """Aggressive search with large limits."""
        all_lots = []
        
        # Try different page sizes
        for page_size in [1000, 500, 200]:
            for page in range(max_pages):
                search_params = params.copy()
                search_params.update({
                    'limit': page_size,
                    'offset': page * page_size
                })
                
                try:
                    param_str = '&'.join([f"{k}={v}" for k, v in search_params.items()])
                    url = f"https://api.macdiscount.com/search?{param_str}"
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            lots = data.get('hits', [])
                            
                            if not lots:
                                break
                                
                            all_lots.extend(lots)
                            
                            if len(lots) < page_size:
                                break
                        else:
                            break
                            
                    await asyncio.sleep(0.05)
                    
                except Exception:
                    continue
                
            if all_lots:
                break
        
        return all_lots
    
    async def mega_discovery_scan(self):
        """Run mega discovery."""
        print("🔥 MEGA LOT DISCOVERY - MAXIMUM DISCOVERY MODE")
        print("=" * 70)
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        # Mega search strategies
        strategies = [
            # High-limit empty searches
            ("High Limits", [
                {'limit': 5000},
                {'limit': 10000},
                {'q': '', 'limit': 5000},
                {'q': '*', 'limit': 5000},
            ]),
            
            # Deep pagination
            ("Deep Pagination", [
                {'offset': i * 1000, 'limit': 1000} for i in range(10)
            ]),
            
            # All characters
            ("All Characters", [
                {'q': char} for char in string.ascii_letters + string.digits
            ]),
            
            # Common terms
            ("Common Terms", [
                {'q': term} for term in [
                    'apple', 'samsung', 'sony', 'lg', 'hp', 'dell', 'microsoft',
                    'laptop', 'computer', 'phone', 'tablet', 'tv', 'monitor',
                    'headphones', 'speaker', 'watch', 'vacuum', 'appliance',
                    'furniture', 'kitchen', 'home', 'garden', 'electronics'
                ]
            ]),
            
            # Price ranges with sorts
            ("Price Sorts", [
                {'min_price': min_p, 'max_price': max_p, 'sort': sort_type, 'limit': 2000}
                for min_p, max_p in [(0, 100), (100, 500), (500, 1000), (1000, 5000)]
                for sort_type in ['newest', 'price_asc', 'price_desc']
            ]),
        ]
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context),
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as session:
            
            for strategy_name, search_configs in strategies:
                print(f"\n🎯 STRATEGY: {strategy_name.upper()}")
                print("-" * 50)
                
                strategy_new_lots = 0
                
                for i, params in enumerate(search_configs, 1):
                    try:
                        print(f"   [{i:3d}/{len(search_configs)}] {params}")
                        
                        lots = await self.mega_search(session, params)
                        new_lots = self.process_lots(lots, f"{strategy_name}_{i}")
                        strategy_new_lots += new_lots
                        
                        if new_lots > 0:
                            print(f"      ✅ Found {new_lots} NEW SC lots!")
                        
                        await asyncio.sleep(0.05)
                        
                    except Exception as e:
                        continue
                
                print(f"   📊 Strategy found {strategy_new_lots} new lots")
                print(f"   📊 Total discovered: {len(self.discovered_lots):,}")
        
        print(f"\n🎯 MEGA DISCOVERY COMPLETE")
        print(f"✅ Total unique lots discovered: {len(self.discovered_lots):,}")
        
        # Store and report
        if self.discovered_lots:
            for lot in self.discovered_lots.values():
                self.store_lot(lot)
            self.generate_report()
        
        return list(self.discovered_lots.values())
    
    def process_lots(self, lots, discovery_method):
        """Process lots and count new discoveries."""
        new_lots = 0
        
        for lot in lots:
            location = lot.get('auction_location', '')
            if any(sc_loc in location for sc_loc in self.sc_locations):
                lot_id = lot.get('id', lot.get('mac_lot_id', ''))
                if lot_id and lot_id not in self.discovered_lots:
                    lot['discovery_method'] = discovery_method
                    self.discovered_lots[lot_id] = lot
                    new_lots += 1
        
        return new_lots
    
    def store_lot(self, lot):
        """Store lot in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO mega_lots 
                (lot_id, title, retail_price, current_bid, location, discovery_method)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                lot.get('id', lot.get('mac_lot_id', '')),
                lot.get('auction_title', lot.get('title', '')),
                lot.get('discount', lot.get('retail_price', 0)),
                lot.get('current_bid', 0),
                lot.get('auction_location', ''),
                lot.get('discovery_method', 'unknown')
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Error storing lot: {e}")
        finally:
            conn.close()
    
    def generate_report(self):
        """Generate mega report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM mega_lots')
        total_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM mega_lots WHERE current_bid = 0')
        no_bid_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(retail_price) FROM mega_lots')
        total_retail_value = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT location, COUNT(*) as lot_count
            FROM mega_lots
            GROUP BY location
            ORDER BY lot_count DESC
        ''')
        warehouse_stats = cursor.fetchall()
        
        conn.close()
        
        print(f"""
🔥 MEGA LOT DISCOVERY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 MEGA DISCOVERY SUMMARY
Total Lots Discovered: {total_lots:,}
No Bid Opportunities: {no_bid_lots:,}
Total Retail Value: ${total_retail_value:,.2f}

🏭 WAREHOUSE BREAKDOWN""")
        
        for location, count in warehouse_stats:
            print(f"• {location}: {count:,} lots")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        print(f"\n📊 Database saved to: {self.db_path}")

async def main():
    scanner = MegaLotDiscovery()
    await scanner.mega_discovery_scan()

if __name__ == "__main__":
    asyncio.run(main()) 