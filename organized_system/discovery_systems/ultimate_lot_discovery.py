#!/usr/bin/env python3
"""
🚀 Ultimate Lot Discovery - Exhaustive search using pagination and all possible patterns
"""

import asyncio
import json
import sqlite3
from datetime import datetime
import aiohttp
import ssl
import string
import itertools

class UltimateLotDiscovery:
    def __init__(self):
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        self.discovered_lots = {}
        self.setup_database()
    
    def setup_database(self):
        """Setup ultimate discovery database."""
        self.db_path = 'ultimate_lot_discovery.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ultimate_lots (
                lot_id TEXT PRIMARY KEY,
                title TEXT,
                retail_price REAL,
                current_bid REAL,
                location TEXT,
                category TEXT,
                condition_name TEXT,
                auction_id TEXT,
                discovery_method TEXT,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("🗄️ Ultimate discovery database initialized")
    
    async def paginated_search(self, session, base_params, max_pages=20):
        """Search with pagination to get all results."""
        all_lots = []
        page_size = 200
        
        for page in range(max_pages):
            params = base_params.copy()
            params.update({
                'limit': page_size,
                'offset': page * page_size
            })
            
            try:
                param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
                url = f"https://api.macdiscount.com/search?{param_str}"
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        lots = data.get('hits', [])
                        
                        if not lots:  # No more results
                            break
                            
                        all_lots.extend(lots)
                        print(f"      Page {page + 1}: {len(lots)} lots (Total: {len(all_lots)})")
                        
                        if len(lots) < page_size:  # Last page
                            break
                    else:
                        break
                        
                await asyncio.sleep(0.1)
                
            except Exception as e:
                break
        
        return all_lots
    
    async def exhaustive_search_patterns(self):
        """Try exhaustive search patterns."""
        print("🚀 ULTIMATE LOT DISCOVERY - EXHAUSTIVE SEARCH")
        print("=" * 60)
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        search_strategies = [
            # 1. Empty/wildcard searches with pagination
            ("Empty Search", {}),
            ("Wildcard Search", {'q': '*'}),
            ("Space Search", {'q': ' '}),
            
            # 2. Single character searches
            ("Single Letters", [{'q': letter} for letter in string.ascii_lowercase]),
            ("Single Numbers", [{'q': str(i)} for i in range(10)]),
            
            # 3. Two character combinations
            ("Two Letter Combos", [{'q': a + b} for a, b in itertools.product(string.ascii_lowercase[:5], repeat=2)]),
            
            # 4. Common prefixes/suffixes
            ("Prefixes", [{'q': prefix} for prefix in ['mac', 'apple', 'samsung', 'sony', 'lg', 'hp', 'dell']]),
            ("Suffixes", [{'q': suffix} for suffix in ['pro', 'max', 'mini', 'air', 'plus', 'ultra']]),
            
            # 5. Price-based searches
            ("Price Ranges", [
                {'min_price': 0, 'max_price': 50},
                {'min_price': 50, 'max_price': 100},
                {'min_price': 100, 'max_price': 200},
                {'min_price': 200, 'max_price': 500},
                {'min_price': 500, 'max_price': 1000},
                {'min_price': 1000, 'max_price': 2000},
                {'min_price': 2000}
            ]),
            
            # 6. Sort variations
            ("Sort Methods", [
                {'sort': 'newest'},
                {'sort': 'oldest'},
                {'sort': 'price_asc'},
                {'sort': 'price_desc'},
                {'sort': 'ending_soon'},
                {'sort': 'popular'}
            ]),
            
            # 7. Category searches
            ("Categories", [{'category': cat} for cat in [
                'electronics', 'computers', 'appliances', 'tools', 'furniture',
                'automotive', 'sports', 'home', 'garden', 'clothing', 'jewelry'
            ]]),
            
            # 8. Condition searches
            ("Conditions", [{'condition': cond} for cond in [
                'new', 'used', 'refurbished', 'open_box', 'damaged', 'parts'
            ]]),
            
            # 9. Location-specific searches
            ("Locations", [{'location': loc.lower().replace(' ', '_')} for loc in self.sc_locations]),
        ]
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context),
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            for strategy_name, search_params in search_strategies:
                print(f"\n🎯 STRATEGY: {strategy_name.upper()}")
                print("-" * 50)
                
                if isinstance(search_params, list):
                    # Multiple parameter sets
                    for i, params in enumerate(search_params, 1):
                        print(f"   [{i}/{len(search_params)}] Testing: {params}")
                        
                        lots = await self.paginated_search(session, params, max_pages=10)
                        new_lots = self.process_lots(lots, f"{strategy_name}_{i}")
                        
                        if new_lots > 0:
                            print(f"      ✅ Found {new_lots} NEW SC lots!")
                        
                        if i % 5 == 0:
                            print(f"      Progress: {(i/len(search_params)*100):.1f}% - Total discovered: {len(self.discovered_lots)}")
                        
                        await asyncio.sleep(0.1)
                else:
                    # Single parameter set
                    print(f"   Testing: {search_params}")
                    lots = await self.paginated_search(session, search_params, max_pages=50)
                    new_lots = self.process_lots(lots, strategy_name)
                    
                    if new_lots > 0:
                        print(f"   ✅ Found {new_lots} NEW SC lots!")
                
                print(f"   📊 Total unique lots discovered so far: {len(self.discovered_lots)}")
        
        print(f"\n🎯 ULTIMATE DISCOVERY COMPLETE")
        print("=" * 35)
        print(f"✅ Total unique lots discovered: {len(self.discovered_lots):,}")
        
        # Store all lots
        if self.discovered_lots:
            print(f"\n💾 Storing {len(self.discovered_lots):,} lots...")
            for lot in self.discovered_lots.values():
                self.store_lot(lot)
            print("✅ All lots stored successfully")
        
        # Generate report
        self.generate_ultimate_report()
        
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
                INSERT OR REPLACE INTO ultimate_lots 
                (lot_id, title, retail_price, current_bid, location, category,
                 condition_name, auction_id, discovery_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lot.get('id', lot.get('mac_lot_id', '')),
                lot.get('auction_title', lot.get('title', '')),
                lot.get('discount', lot.get('retail_price', 0)),
                lot.get('current_bid', 0),
                lot.get('auction_location', ''),
                lot.get('category', ''),
                lot.get('condition', ''),
                lot.get('auction_id', ''),
                lot.get('discovery_method', 'unknown')
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Error storing lot: {e}")
        finally:
            conn.close()
    
    def generate_ultimate_report(self):
        """Generate ultimate discovery report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Summary statistics
        cursor.execute('SELECT COUNT(*) FROM ultimate_lots')
        total_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ultimate_lots WHERE current_bid = 0')
        no_bid_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(retail_price) FROM ultimate_lots')
        total_retail_value = cursor.fetchone()[0] or 0
        
        # Warehouse breakdown
        cursor.execute('''
            SELECT location, COUNT(*) as lot_count, SUM(retail_price) as total_value
            FROM ultimate_lots
            GROUP BY location
            ORDER BY lot_count DESC
        ''')
        warehouse_stats = cursor.fetchall()
        
        # Discovery method effectiveness
        cursor.execute('''
            SELECT discovery_method, COUNT(*) as lot_count
            FROM ultimate_lots
            GROUP BY discovery_method
            ORDER BY lot_count DESC
            LIMIT 10
        ''')
        method_stats = cursor.fetchall()
        
        # Top opportunities
        cursor.execute('''
            SELECT title, retail_price, current_bid, location, lot_id
            FROM ultimate_lots
            WHERE current_bid = 0 AND retail_price > 500
            ORDER BY retail_price DESC
            LIMIT 30
        ''')
        top_opportunities = cursor.fetchall()
        
        conn.close()
        
        # Generate report
        report = f"""
🚀 ULTIMATE LOT DISCOVERY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 DISCOVERY SUMMARY
Total Lots Discovered: {total_lots:,}
No Bid Opportunities: {no_bid_lots:,}
Total Retail Value: ${total_retail_value:,.2f}

🏭 WAREHOUSE BREAKDOWN
"""
        
        for location, count, value in warehouse_stats:
            report += f"• {location}: {count:,} lots (${value:,.2f} retail value)\n"
        
        report += f"""
🎯 MOST EFFECTIVE DISCOVERY METHODS
"""
        
        for method, count in method_stats:
            report += f"• {method}: {count:,} lots\n"
        
        report += f"""
🏆 TOP 30 HIGH-VALUE NO-BID OPPORTUNITIES
"""
        
        for i, (title, retail, current_bid, location, lot_id) in enumerate(top_opportunities, 1):
            clean_lot_id = lot_id.replace('mac_lot_', '')
            report += f"""
{i:2d}. {title[:60]}{'...' if len(title) > 60 else ''}
    Retail: ${retail:.2f} | Current Bid: ${current_bid:.2f} | Location: {location}
    🔗 Link: https://mac.bid/lot/{clean_lot_id}
"""
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'ultimate_lot_discovery_{timestamp}.txt'
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Report saved to: {report_file}")
        print(f"📊 Database saved to: {self.db_path}")

async def main():
    scanner = UltimateLotDiscovery()
    await scanner.exhaustive_search_patterns()

if __name__ == "__main__":
    asyncio.run(main()) 