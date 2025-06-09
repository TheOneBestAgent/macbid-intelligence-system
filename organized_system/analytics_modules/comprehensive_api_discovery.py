#!/usr/bin/env python3
"""
🔍 COMPREHENSIVE API DISCOVERY SCANNER
Find the API endpoint that returns ALL lots in SC locations without filtering
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime
from urllib.parse import urlencode

class ComprehensiveAPIDiscovery:
    def __init__(self):
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        self.discovered_lots = {}
        self.seen_lot_ids = set()
        self.session = None
        self.api_results = {}
        
        # Test different API endpoints and parameters
        self.api_endpoints = [
            # Main search API with different parameters
            "https://api.macdiscount.com/search",
            "https://api.macdiscount.com/lots",
            "https://api.macdiscount.com/auctions",
            "https://api.macdiscount.com/inventory",
            "https://api.macdiscount.com/products",
            "https://api.macdiscount.com/items",
            
            # Alternative domains/subdomains
            "https://mac.bid/api/search",
            "https://mac.bid/api/lots",
            "https://mac.bid/api/auctions",
            "https://www.mac.bid/api/search",
            "https://www.mac.bid/api/lots",
            
            # GraphQL endpoints
            "https://api.macdiscount.com/graphql",
            "https://mac.bid/graphql",
            
            # REST API variations
            "https://api.macdiscount.com/v1/search",
            "https://api.macdiscount.com/v2/search",
            "https://api.macdiscount.com/v1/lots",
            "https://api.macdiscount.com/v2/lots",
        ]
        
        # Different parameter combinations to test
        self.parameter_sets = [
            # No filters - get everything
            {},
            {"limit": 10000},
            {"limit": 5000},
            {"limit": 1000},
            {"per_page": 10000},
            {"per_page": 5000},
            {"size": 10000},
            {"size": 5000},
            
            # Location-based filters
            {"location": "South Carolina"},
            {"location": "SC"},
            {"state": "SC"},
            {"state": "South Carolina"},
            {"warehouse": "SC"},
            
            # Specific SC locations
            {"location": "Spartanburg"},
            {"location": "Greenville"},
            {"location": "Rock Hill"},
            {"location": "Gastonia"},
            {"location": "Anderson"},
            
            # Different query approaches
            {"q": ""},
            {"query": ""},
            {"search": ""},
            {"term": ""},
            {"keyword": ""},
            
            # Wildcard searches
            {"q": "*"},
            {"query": "*"},
            {"search": "*"},
            
            # Get all active auctions
            {"status": "active"},
            {"active": "true"},
            {"live": "true"},
            
            # Sort by different fields to get different results
            {"sort": "created_at"},
            {"sort": "updated_at"},
            {"sort": "auction_date"},
            {"sort": "lot_number"},
            {"order": "asc"},
            {"order": "desc"},
            
            # Pagination to get more results
            {"page": 1, "limit": 1000},
            {"page": 2, "limit": 1000},
            {"offset": 0, "limit": 1000},
            {"offset": 1000, "limit": 1000},
            
            # Combined approaches
            {"q": "*", "limit": 10000, "location": "SC"},
            {"query": "", "limit": 5000, "state": "South Carolina"},
            {"search": "*", "per_page": 1000, "active": "true"},
        ]
        
        self.setup_database()
    
    def setup_database(self):
        """Setup comprehensive API discovery database."""
        self.db_path = 'comprehensive_api_discovery.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint TEXT,
                parameters TEXT,
                status_code INTEGER,
                response_size INTEGER,
                lot_count INTEGER,
                sc_lot_count INTEGER,
                unique_lots_found INTEGER,
                test_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovered_lots (
                lot_id TEXT PRIMARY KEY,
                title TEXT,
                retail_price REAL,
                current_bid REAL,
                location TEXT,
                brand TEXT,
                discovery_endpoint TEXT,
                discovery_parameters TEXT,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("🗄️ Comprehensive API discovery database initialized")
    
    async def create_session(self):
        """Create HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=50)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
        )
    
    async def test_api_endpoint(self, endpoint, params):
        """Test a specific API endpoint with given parameters."""
        try:
            # Build URL with parameters
            if params:
                url = f"{endpoint}?{urlencode(params)}"
            else:
                url = endpoint
            
            async with self.session.get(url) as response:
                status_code = response.status
                
                if status_code == 200:
                    try:
                        data = await response.json()
                        response_size = len(str(data))
                        
                        # Try different ways to extract lots from response
                        lots = []
                        if isinstance(data, list):
                            lots = data
                        elif isinstance(data, dict):
                            # Try common field names for lot arrays
                            for field in ['hits', 'results', 'data', 'lots', 'auctions', 'items', 'products']:
                                if field in data and isinstance(data[field], list):
                                    lots = data[field]
                                    break
                        
                        lot_count = len(lots)
                        sc_lot_count = 0
                        unique_lots_found = 0
                        
                        # Count SC lots and track unique ones
                        for lot in lots:
                            location = lot.get('auction_location', lot.get('location', ''))
                            if any(sc_loc in location for sc_loc in self.sc_locations):
                                sc_lot_count += 1
                                
                                # Try to get lot ID
                                lot_id = (lot.get('lot_id') or lot.get('id') or 
                                         lot.get('mac_lot_id') or lot.get('_id') or '')
                                
                                if lot_id and lot_id not in self.seen_lot_ids:
                                    self.seen_lot_ids.add(lot_id)
                                    self.discovered_lots[lot_id] = {
                                        **lot,
                                        'discovery_endpoint': endpoint,
                                        'discovery_parameters': json.dumps(params)
                                    }
                                    unique_lots_found += 1
                        
                        # Store test result
                        self.store_api_test(endpoint, params, status_code, response_size, 
                                          lot_count, sc_lot_count, unique_lots_found)
                        
                        return {
                            'status': 'success',
                            'status_code': status_code,
                            'lot_count': lot_count,
                            'sc_lot_count': sc_lot_count,
                            'unique_lots_found': unique_lots_found,
                            'response_size': response_size
                        }
                        
                    except json.JSONDecodeError:
                        # Not JSON response
                        return {
                            'status': 'not_json',
                            'status_code': status_code,
                            'lot_count': 0,
                            'sc_lot_count': 0,
                            'unique_lots_found': 0
                        }
                else:
                    # Non-200 status
                    self.store_api_test(endpoint, params, status_code, 0, 0, 0, 0)
                    return {
                        'status': 'error',
                        'status_code': status_code,
                        'lot_count': 0,
                        'sc_lot_count': 0,
                        'unique_lots_found': 0
                    }
                    
        except Exception as e:
            # Connection error or timeout
            self.store_api_test(endpoint, params, 0, 0, 0, 0, 0)
            return {
                'status': 'exception',
                'error': str(e),
                'lot_count': 0,
                'sc_lot_count': 0,
                'unique_lots_found': 0
            }
    
    def store_api_test(self, endpoint, params, status_code, response_size, 
                      lot_count, sc_lot_count, unique_lots_found):
        """Store API test result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO api_tests 
                (endpoint, parameters, status_code, response_size, lot_count, 
                 sc_lot_count, unique_lots_found)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                endpoint,
                json.dumps(params),
                status_code,
                response_size,
                lot_count,
                sc_lot_count,
                unique_lots_found
            ))
            
            conn.commit()
        except Exception as e:
            print(f"   ❌ Error storing test result: {e}")
        finally:
            conn.close()
    
    def store_discovered_lot(self, lot):
        """Store discovered lot."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            lot_id = (lot.get('lot_id') or lot.get('id') or 
                     lot.get('mac_lot_id') or lot.get('_id') or '')
            
            cursor.execute('''
                INSERT OR REPLACE INTO discovered_lots 
                (lot_id, title, retail_price, current_bid, location, brand,
                 discovery_endpoint, discovery_parameters)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lot_id,
                lot.get('auction_title', lot.get('title', '')),
                lot.get('discount', lot.get('retail_price', 0)),
                lot.get('current_bid', 0),
                lot.get('auction_location', ''),
                lot.get('brand', 'Unknown'),
                lot.get('discovery_endpoint', ''),
                lot.get('discovery_parameters', '{}')
            ))
            
            conn.commit()
        except Exception as e:
            print(f"   ❌ Error storing lot: {e}")
        finally:
            conn.close()
    
    async def run_comprehensive_discovery(self):
        """Run comprehensive API discovery."""
        print("🔍 COMPREHENSIVE API DISCOVERY SCANNER")
        print("=" * 80)
        print("Testing ALL possible API endpoints to find the one that returns")
        print("ALL lots in South Carolina locations without filtering")
        print()
        
        await self.create_session()
        
        total_tests = len(self.api_endpoints) * len(self.parameter_sets)
        test_count = 0
        successful_tests = 0
        best_result = None
        
        print(f"🎯 TESTING {total_tests} API COMBINATIONS")
        print("-" * 60)
        
        for endpoint in self.api_endpoints:
            print(f"\n📡 Testing endpoint: {endpoint}")
            
            for params in self.parameter_sets:
                test_count += 1
                param_str = json.dumps(params) if params else "No parameters"
                
                print(f"   [{test_count:3d}/{total_tests}] {param_str[:50]}{'...' if len(param_str) > 50 else ''}")
                
                result = await self.test_api_endpoint(endpoint, params)
                
                if result['status'] == 'success':
                    successful_tests += 1
                    
                    if result['sc_lot_count'] > 0:
                        print(f"      ✅ SUCCESS! {result['sc_lot_count']} SC lots, {result['unique_lots_found']} new")
                        
                        # Track best result
                        if not best_result or result['sc_lot_count'] > best_result['result']['sc_lot_count']:
                            best_result = {
                                'endpoint': endpoint,
                                'params': params,
                                'result': result
                            }
                    
                    if result['lot_count'] > 100:  # Show promising results
                        print(f"      📊 {result['lot_count']} total lots returned")
                
                elif result['status'] == 'error':
                    if result['status_code'] == 404:
                        print(f"      ❌ 404 Not Found")
                    else:
                        print(f"      ❌ HTTP {result['status_code']}")
                
                # Rate limiting
                await asyncio.sleep(0.1)
                
                # Progress updates
                if test_count % 50 == 0:
                    progress = (test_count / total_tests) * 100
                    print(f"      🚀 Progress: {progress:.1f}% - Total unique lots: {len(self.discovered_lots):,}")
        
        await self.session.close()
        
        print(f"\n🎯 COMPREHENSIVE API DISCOVERY COMPLETE")
        print("=" * 60)
        print(f"✅ Total tests performed: {total_tests}")
        print(f"✅ Successful responses: {successful_tests}")
        print(f"✅ Total unique SC lots discovered: {len(self.discovered_lots):,}")
        
        # Store all discovered lots
        if self.discovered_lots:
            print(f"\n💾 Storing {len(self.discovered_lots):,} lots in database...")
            for lot in self.discovered_lots.values():
                self.store_discovered_lot(lot)
            print("✅ All lots stored successfully")
        
        # Show best result
        if best_result:
            print(f"\n🏆 BEST API ENDPOINT FOUND:")
            print(f"   Endpoint: {best_result['endpoint']}")
            print(f"   Parameters: {json.dumps(best_result['params'])}")
            print(f"   SC Lots Found: {best_result['result']['sc_lot_count']}")
            print(f"   Total Lots: {best_result['result']['lot_count']}")
        
        # Generate comprehensive report
        self.generate_discovery_report()
        
        return list(self.discovered_lots.values())
    
    def generate_discovery_report(self):
        """Generate comprehensive API discovery report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get test summary
        cursor.execute('''
            SELECT COUNT(*) as total_tests,
                   SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as successful_tests,
                   MAX(sc_lot_count) as max_sc_lots,
                   MAX(lot_count) as max_total_lots
            FROM api_tests
        ''')
        summary = cursor.fetchone()
        
        # Get top performing endpoints
        cursor.execute('''
            SELECT endpoint, parameters, sc_lot_count, lot_count, unique_lots_found
            FROM api_tests
            WHERE sc_lot_count > 0
            ORDER BY sc_lot_count DESC, lot_count DESC
            LIMIT 10
        ''')
        top_endpoints = cursor.fetchall()
        
        # Get discovered lots summary
        cursor.execute('SELECT COUNT(*) FROM discovered_lots')
        total_discovered = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT location, COUNT(*) as count
            FROM discovered_lots
            GROUP BY location
            ORDER BY count DESC
        ''')
        location_breakdown = cursor.fetchall()
        
        conn.close()
        
        print(f"""
🔍 COMPREHENSIVE API DISCOVERY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 TEST SUMMARY
Total API Tests: {summary[0]:,}
Successful Responses: {summary[1]:,}
Max SC Lots in Single Response: {summary[2]:,}
Max Total Lots in Single Response: {summary[3]:,}
Total Unique Lots Discovered: {total_discovered:,}

🏆 TOP PERFORMING ENDPOINTS""")
        
        for i, (endpoint, params, sc_lots, total_lots, unique) in enumerate(top_endpoints, 1):
            print(f"""
{i:2d}. {endpoint}
    Parameters: {params}
    SC Lots: {sc_lots:,} | Total Lots: {total_lots:,} | New Unique: {unique:,}""")
        
        print(f"""
🏭 LOCATION BREAKDOWN""")
        for location, count in location_breakdown:
            print(f"• {location}: {count:,} lots")
        
        print(f"\n📊 Database saved to: {self.db_path}")

async def main():
    scanner = ComprehensiveAPIDiscovery()
    await scanner.run_comprehensive_discovery()

if __name__ == "__main__":
    asyncio.run(main()) 