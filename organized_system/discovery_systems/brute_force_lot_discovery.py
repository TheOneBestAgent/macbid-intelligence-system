#!/usr/bin/env python3
"""
🔥 Brute Force Lot Discovery - Find EVERY lot using API parameter exploration
Tests different API endpoints, parameters, and pagination to maximize discovery
"""

import asyncio
import json
import sqlite3
from datetime import datetime
import aiohttp
import ssl
from typing import List, Dict, Set
import time

class BruteForceLotDiscovery:
    def __init__(self):
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        self.discovered_lots = {}
        self.api_endpoints = [
            'https://api.macdiscount.com/search',
            'https://api.macdiscount.com/lots',
            'https://api.macdiscount.com/auctions',
            'https://api.macdiscount.com/products'
        ]
        
        # Different parameter combinations to test
        self.parameter_combinations = [
            {'limit': 500},
            {'limit': 1000},
            {'limit': 2000},
            {'offset': 0, 'limit': 500},
            {'offset': 500, 'limit': 500},
            {'offset': 1000, 'limit': 500},
            {'sort': 'newest', 'limit': 500},
            {'sort': 'price_asc', 'limit': 500},
            {'sort': 'price_desc', 'limit': 500},
            {'q': '', 'limit': 2000},
            {'q': '*', 'limit': 2000},
            {}  # Empty query
        ]
        
        self.setup_database()
    
    def setup_database(self):
        """Setup brute force discovery database."""
        self.db_path = 'brute_force_discovery.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovered_lots (
                lot_id TEXT PRIMARY KEY,
                title TEXT,
                retail_price REAL,
                current_bid REAL,
                total_bids INTEGER,
                location TEXT,
                category TEXT,
                condition_name TEXT,
                auction_id TEXT,
                auction_number TEXT,
                expected_close_date TEXT,
                image_url TEXT,
                discovery_method TEXT,
                api_endpoint TEXT,
                api_parameters TEXT,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_exploration_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT,
                parameters TEXT,
                response_status INTEGER,
                lots_found INTEGER,
                sc_lots_found INTEGER,
                new_lots_found INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("🗄️ Brute force discovery database initialized")
    
    async def test_api_params(self, session, params):
        """Test API with specific parameters."""
        try:
            param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
            url = f"https://api.macdiscount.com/search?{param_str}" if param_str else "https://api.macdiscount.com/search"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('hits', [])
                return []
        except:
            return []
    
    async def brute_force_discovery(self):
        """Run brute force discovery across all endpoints and parameters."""
        print("🔥 BRUTE FORCE LOT DISCOVERY")
        print("=" * 50)
        print("Testing all API endpoints and parameter combinations...")
        print()
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        total_combinations = len(self.api_endpoints) * len(self.parameter_combinations)
        current_combination = 0
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context),
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as session:
            
            for endpoint in self.api_endpoints:
                print(f"\n🎯 Testing endpoint: {endpoint}")
                print("-" * 40)
                
                for i, params in enumerate(self.parameter_combinations, 1):
                    current_combination += 1
                    progress = (current_combination / total_combinations) * 100
                    
                    print(f"[{i}/{len(self.parameter_combinations)}] Testing: {params}")
                    
                    lots = await self.test_api_params(session, params)
                    new_lots = 0
                    
                    for lot in lots:
                        location = lot.get('auction_location', '')
                        if any(sc_loc in location for sc_loc in self.sc_locations):
                            lot_id = lot.get('id', lot.get('mac_lot_id', ''))
                            if lot_id and lot_id not in self.discovered_lots:
                                self.discovered_lots[lot_id] = lot
                                lot['discovery_method'] = 'brute_force'
                                lot['api_endpoint'] = endpoint
                                lot['api_parameters'] = json.dumps(params)
                                new_lots += 1
                    
                    # Log the exploration
                    self.log_api_exploration(endpoint, params, 200, len(lots), len(self.sc_locations), new_lots)
                    
                    if new_lots > 0:
                        print(f"      ✅ Found {new_lots} NEW SC lots! (Total: {len(self.discovered_lots)})")
                    elif len(self.sc_locations) > 0:
                        print(f"      📦 Found {len(self.sc_locations)} SC lots (all previously discovered)")
                    
                    # Rate limiting
                    await asyncio.sleep(0.2)
        
        print(f"\n🎯 BRUTE FORCE DISCOVERY COMPLETE")
        print("=" * 35)
        print(f"✅ Total unique lots discovered: {len(self.discovered_lots):,}")
        
        # Store all discovered lots
        if self.discovered_lots:
            print(f"\n💾 Storing {len(self.discovered_lots):,} lots in database...")
            for lot in self.discovered_lots.values():
                self.store_discovered_lot(lot)
            print("✅ All lots stored successfully")
        
        # Generate comprehensive report
        self.generate_brute_force_report()
        
        return list(self.discovered_lots.values())
    
    def log_api_exploration(self, endpoint: str, params: Dict, status: int, 
                           total_lots: int, sc_lots: int, new_lots: int):
        """Log API exploration results."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_exploration_log 
            (endpoint, parameters, response_status, lots_found, sc_lots_found, new_lots_found)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (endpoint, json.dumps(params), status, total_lots, sc_lots, new_lots))
        
        conn.commit()
        conn.close()
    
    def store_discovered_lot(self, lot: Dict):
        """Store discovered lot in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO discovered_lots 
                (lot_id, title, retail_price, current_bid, total_bids, location, category,
                 condition_name, auction_id, auction_number, expected_close_date, image_url,
                 discovery_method, api_endpoint, api_parameters)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lot.get('id', lot.get('mac_lot_id', '')),
                lot.get('auction_title', lot.get('title', '')),
                lot.get('discount', lot.get('retail_price', 0)),
                lot.get('current_bid', 0),
                lot.get('total_bids', 0),
                lot.get('auction_location', ''),
                lot.get('category', ''),
                lot.get('condition', ''),
                lot.get('auction_id', ''),
                lot.get('auction_number', ''),
                lot.get('expected_close_date', ''),
                lot.get('image_url', ''),
                lot.get('discovery_method', 'brute_force'),
                lot.get('api_endpoint', ''),
                lot.get('api_parameters', '{}')
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Error storing lot: {e}")
        finally:
            conn.close()
    
    def generate_brute_force_report(self):
        """Generate comprehensive brute force discovery report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Summary statistics
        cursor.execute('SELECT COUNT(*) FROM discovered_lots')
        total_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM discovered_lots WHERE current_bid = 0')
        no_bid_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(retail_price) FROM discovered_lots')
        total_retail_value = cursor.fetchone()[0] or 0
        
        # Warehouse breakdown
        cursor.execute('''
            SELECT location, COUNT(*) as lot_count, SUM(retail_price) as total_value
            FROM discovered_lots
            GROUP BY location
            ORDER BY lot_count DESC
        ''')
        warehouse_stats = cursor.fetchall()
        
        # Most effective API combinations
        cursor.execute('''
            SELECT endpoint, parameters, SUM(new_lots_found) as total_new_lots
            FROM api_exploration_log
            WHERE new_lots_found > 0
            GROUP BY endpoint, parameters
            ORDER BY total_new_lots DESC
            LIMIT 10
        ''')
        effective_apis = cursor.fetchall()
        
        # Top opportunities
        cursor.execute('''
            SELECT title, retail_price, current_bid, location, lot_id
            FROM discovered_lots
            WHERE current_bid = 0 AND retail_price > 100
            ORDER BY retail_price DESC
            LIMIT 25
        ''')
        top_opportunities = cursor.fetchall()
        
        conn.close()
        
        # Generate report
        report = f"""
🔥 BRUTE FORCE LOT DISCOVERY REPORT
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
🎯 MOST EFFECTIVE API COMBINATIONS
"""
        
        for endpoint, params, new_lots in effective_apis:
            clean_endpoint = endpoint.split('/')[-1]
            clean_params = json.loads(params) if params != '{}' else 'no params'
            report += f"• {clean_endpoint} with {clean_params}: {new_lots} new lots\n"
        
        report += f"""
🏆 TOP 25 NO-BID OPPORTUNITIES
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
        report_file = f'brute_force_discovery_{timestamp}.txt'
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Report saved to: {report_file}")
        print(f"📊 Database saved to: {self.db_path}")

async def main():
    """Main function."""
    scanner = BruteForceLotDiscovery()
    await scanner.brute_force_discovery()

if __name__ == "__main__":
    asyncio.run(main()) 