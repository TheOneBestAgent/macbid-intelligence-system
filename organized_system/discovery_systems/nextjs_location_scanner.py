#!/usr/bin/env python3
"""
🔍 NEXT.JS LOCATION SCANNER
Uses the Next.js location endpoint to get lots by specific locations
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime

class NextJSLocationScanner:
    def __init__(self):
        self.sc_locations = {
            'anderson': {'aid': '48502', 'lid': '1649A'},
            'gastonia': {'aid': '48502', 'lid': '1649B'},
            'greenville': {'aid': '48502', 'lid': '1649C'},
            'rock-hill': {'aid': '48502', 'lid': '1649D'},
            'spartanburg': {'aid': '48502', 'lid': '1649E'}
        }
        
        self.discovered_lots = {}
        self.seen_lot_ids = set()
        self.session = None
        
        # Next.js endpoint pattern
        self.base_url = "https://www.mac.bid/_next/data/AslxUFb4wF5GgYRFXlpoC/locations"
        
        self.setup_database()
    
    def setup_database(self):
        """Setup Next.js location database."""
        self.db_path = 'nextjs_location_lots.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS nextjs_lots (
                lot_id TEXT PRIMARY KEY,
                title TEXT,
                product_name TEXT,
                retail_price REAL,
                current_bid REAL,
                auction_location TEXT,
                category TEXT,
                condition_name TEXT,
                auction_id TEXT,
                inventory_id TEXT,
                expected_close_date TEXT,
                is_open INTEGER,
                discount_amount REAL,
                discount_percentage REAL,
                opportunity_score REAL,
                deal_rating TEXT,
                source_location TEXT,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("🗄️ Next.js location database initialized")
    
    async def create_session(self):
        """Create HTTP session with proper cookies."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=20)
        timeout = aiohttp.ClientTimeout(total=60)
        
        # Use the cookies from your curl command
        cookies = {
            '__stripe_mid': 'b1219cc5-9a1f-4e9b-9b3b-ce16a3d90ba32b7fa4',
            'lat_lon': '{"lat":35.1293,"lon":-80.864}',
            'CookieConsent': 'true',
            'ab.storage.deviceId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3A6557c69b-3239-8d82-7b30-ec5862a4de57%7Ce%3Aundefined%7Cc%3A1747345668914%7Cl%3A1749216579283',
            'ab.storage.userId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3A2710619%7Ce%3Aundefined%7Cc%3A1749188938629%7Cl%3A1749216579283',
            'mp_78faade7af6b4f2ee5e1af36d8ac6232_mixpanel': '%7B%22distinct_id%22%3A%202710619%2C%22%24device_id%22%3A%20%22196d5eae0323e9-06ed80c653d2808-19525636-13c680-196d5eae0323e9%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22platform%22%3A%20%22website%22%2C%22selected_locations%22%3A%20%5B%0A%20%20%20%20%22Rock%20Hill%22%2C%0A%20%20%20%20%22Gastonia%22%0A%5D%2C%22%24user_id%22%3A%202710619%2C%22active_items%22%3A%20%5B%5D%2C%22mac_bucks_balance%22%3A%200%2C%22mac_bucks_gift_balance%22%3A%200%2C%22active_membership%22%3A%20%7B%22id%22%3A%20123339%2C%22date_created%22%3A%20%222025-05-29T18%3A11%3A59.000Z%22%2C%22membership_plan%22%3A%20%22STANDARD%22%2C%22customer_id%22%3A%202710619%2C%22bill_period%22%3A%20%22MONTHLY%22%2C%22bill_amount%22%3A%209.99%2C%22date_cancelled%22%3A%20null%2C%22external_id%22%3A%20%22sub_1RUFc8DhtPPAHVyel4iCCWV7%22%2C%22cancel_reason%22%3A%20null%2C%22stripe_customer_id%22%3A%20%22cus_S6Y0gK006usyW7%22%2C%22date_updated%22%3A%20null%7D%2C%22watchlist_count%22%3A%206%2C%22onboarding%22%3A%20true%7D',
            'ab.storage.sessionId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3A68bbd633-fcd4-4087-8e27-1e345191e246%7Ce%3A1749219874907%7Cc%3A1749216579282%7Cl%3A1749218074907',
            '__stripe_sid': 'f93c4078-c765-412b-9a2e-c773c20affff1d9236'
        }
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            cookies=cookies,
            headers={
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.6',
                'Priority': 'u=1, i',
                'Sec-Ch-Ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'Sec-Ch-Ua-Mobile': '?1',
                'Sec-Ch-Ua-Platform': '"Android"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Gpc': '1',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
                'X-Nextjs-Data': '1'
            }
        )
    
    def calculate_scores(self, lot):
        """Calculate opportunity scores."""
        retail_price = lot.get('retail_price', lot.get('discount', 0))
        current_bid = lot.get('current_bid', 0)
        
        if retail_price > 0:
            if current_bid > 0:
                discount_amount = retail_price - current_bid
                discount_percentage = (discount_amount / retail_price) * 100
            else:
                discount_amount = retail_price
                discount_percentage = 100.0
        else:
            discount_amount = 0
            discount_percentage = 0
        
        # Opportunity score
        opportunity_score = min(discount_percentage / 100, 1.0)
        if current_bid == 0:
            opportunity_score *= 1.3
        opportunity_score = min(opportunity_score, 1.0)
        
        # Deal rating
        if discount_percentage >= 90:
            deal_rating = "EXCEPTIONAL"
        elif discount_percentage >= 70:
            deal_rating = "EXCELLENT"
        elif discount_percentage >= 50:
            deal_rating = "VERY_GOOD"
        else:
            deal_rating = "GOOD"
        
        return {
            'discount_amount': discount_amount,
            'discount_percentage': discount_percentage,
            'opportunity_score': opportunity_score,
            'deal_rating': deal_rating
        }
    
    async def scan_location(self, location_name, location_params):
        """Scan a specific location."""
        try:
            url = f"{self.base_url}/{location_name}.json"
            params = {
                'aid': location_params['aid'],
                'lid': location_params['lid'],
                'loc': location_name
            }
            
            print(f"   🔍 Scanning {location_name.title()}...")
            print(f"      URL: {url}")
            print(f"      Params: {params}")
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Explore the data structure
                    print(f"      📊 Response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                    
                    # Try to find lots in various possible locations in the response
                    lots = []
                    if isinstance(data, dict):
                        # Check common locations for lot data
                        for key in ['pageProps', 'props', 'data', 'lots', 'auctions', 'items']:
                            if key in data:
                                sub_data = data[key]
                                if isinstance(sub_data, dict):
                                    # Look for arrays that might contain lots
                                    for sub_key in ['lots', 'auctions', 'items', 'data', 'results']:
                                        if sub_key in sub_data and isinstance(sub_data[sub_key], list):
                                            lots.extend(sub_data[sub_key])
                                elif isinstance(sub_data, list):
                                    lots.extend(sub_data)
                    
                    new_lots = 0
                    for lot in lots:
                        if isinstance(lot, dict):
                            # Get lot ID
                            lot_id = (lot.get('id') or lot.get('lot_id') or 
                                     lot.get('inventory_id') or lot.get('auction_id') or '')
                            
                            if lot_id and lot_id not in self.seen_lot_ids:
                                # Enhance with analytics
                                scores = self.calculate_scores(lot)
                                lot.update(scores)
                                lot['source_location'] = location_name
                                
                                self.seen_lot_ids.add(lot_id)
                                self.discovered_lots[lot_id] = lot
                                new_lots += 1
                    
                    print(f"      ✅ Found {len(lots)} total items, {new_lots} new lots")
                    
                    # If no lots found, show some sample data structure
                    if len(lots) == 0 and isinstance(data, dict):
                        print(f"      📋 Sample data structure:")
                        for key, value in list(data.items())[:3]:
                            if isinstance(value, (dict, list)):
                                print(f"         {key}: {type(value).__name__} with {len(value)} items")
                            else:
                                print(f"         {key}: {str(value)[:50]}...")
                    
                    return len(lots), new_lots
                    
                else:
                    print(f"      ❌ HTTP {response.status}")
                    if response.status == 404:
                        print(f"      💡 Endpoint might not exist or parameters incorrect")
                    return 0, 0
                    
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return 0, 0
    
    async def run_nextjs_discovery(self):
        """Run Next.js location discovery."""
        print("🔍 NEXT.JS LOCATION SCANNER")
        print("=" * 80)
        print("Using Next.js location endpoints to discover lots by location")
        print()
        
        await self.create_session()
        
        total_api_hits = 0
        
        print(f"🔍 LOCATION-BASED DISCOVERY")
        print("-" * 70)
        
        for location_name, location_params in self.sc_locations.items():
            api_hits, new_lots = await self.scan_location(location_name, location_params)
            total_api_hits += api_hits
            
            if new_lots > 0:
                print(f"      🎉 Total unique lots so far: {len(self.discovered_lots):,}")
            
            print()
            
            # Rate limiting
            await asyncio.sleep(1.0)
        
        await self.session.close()
        
        print(f"\n🔍 NEXT.JS LOCATION DISCOVERY COMPLETE")
        print("=" * 60)
        print(f"✅ Total unique lots discovered: {len(self.discovered_lots):,}")
        print(f"📊 Total API responses processed: {total_api_hits:,}")
        
        if len(self.discovered_lots) > 1000:
            print(f"🎉 SUCCESS! Discovered {len(self.discovered_lots):,} lots!")
        elif len(self.discovered_lots) > 100:
            print(f"✅ GOOD! Found {len(self.discovered_lots):,} lots!")
        else:
            print(f"ℹ️  Found {len(self.discovered_lots):,} lots (may need different approach)")
        
        # Store all lots
        if self.discovered_lots:
            print(f"\n💾 Storing {len(self.discovered_lots):,} lots in database...")
            for lot in self.discovered_lots.values():
                self.store_lot(lot)
            print("✅ All lots stored successfully")
        
        # Generate report
        self.generate_nextjs_report()
        
        return list(self.discovered_lots.values())
    
    def store_lot(self, lot):
        """Store lot in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            lot_id = (lot.get('id') or lot.get('lot_id') or 
                     lot.get('inventory_id') or lot.get('auction_id') or '')
            
            cursor.execute('''
                INSERT OR REPLACE INTO nextjs_lots 
                (lot_id, title, product_name, retail_price, current_bid, auction_location,
                 category, condition_name, auction_id, inventory_id, expected_close_date,
                 is_open, discount_amount, discount_percentage, opportunity_score, 
                 deal_rating, source_location)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lot_id,
                lot.get('title', lot.get('auction_title', '')),
                lot.get('product_name', ''),
                lot.get('retail_price', lot.get('discount', 0)),
                lot.get('current_bid', 0),
                lot.get('auction_location', ''),
                lot.get('category', ''),
                lot.get('condition', ''),
                lot.get('auction_id', ''),
                lot.get('inventory_id', ''),
                lot.get('expected_close_date', ''),
                lot.get('is_open', 0),
                lot.get('discount_amount', 0),
                lot.get('discount_percentage', 0),
                lot.get('opportunity_score', 0),
                lot.get('deal_rating', 'GOOD'),
                lot.get('source_location', '')
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Error storing lot: {e}")
        finally:
            conn.close()
    
    def generate_nextjs_report(self):
        """Generate Next.js discovery report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM nextjs_lots')
        total_lots = cursor.fetchone()[0]
        
        if total_lots > 0:
            cursor.execute('SELECT COUNT(*) FROM nextjs_lots WHERE current_bid = 0')
            no_bid_lots = cursor.fetchone()[0]
            
            cursor.execute('SELECT SUM(retail_price) FROM nextjs_lots')
            total_retail_value = cursor.fetchone()[0] or 0
            
            # Location breakdown
            cursor.execute('''
                SELECT source_location, COUNT(*) as lot_count
                FROM nextjs_lots
                GROUP BY source_location
                ORDER BY lot_count DESC
            ''')
            location_stats = cursor.fetchall()
            
            print(f"""
🔍 NEXT.JS LOCATION DISCOVERY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 DISCOVERY SUMMARY
Total Lots Discovered: {total_lots:,}
No Bid Opportunities: {no_bid_lots:,}
Total Retail Value: ${total_retail_value:,.2f}

📍 SOURCE LOCATION BREAKDOWN""")
            
            for location, count in location_stats:
                print(f"• {location}: {count:,} lots")
        else:
            print(f"""
🔍 NEXT.JS LOCATION DISCOVERY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 No lots discovered through Next.js endpoints
This suggests the endpoint structure may be different or require different parameters.""")
        
        conn.close()
        print(f"\n📊 Database saved to: {self.db_path}")

async def main():
    scanner = NextJSLocationScanner()
    await scanner.run_nextjs_discovery()

if __name__ == "__main__":
    asyncio.run(main()) 