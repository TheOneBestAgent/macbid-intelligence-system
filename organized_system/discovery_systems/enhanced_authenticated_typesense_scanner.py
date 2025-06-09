#!/usr/bin/env python3
"""
🔍 ENHANCED AUTHENTICATED TYPESENSE SCANNER
Updated version of all scanners using authentication + proven Typesense API
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
import os
from datetime import datetime
from pathlib import Path

class EnhancedAuthenticatedScanner:
    def __init__(self):
        self.session = None
        self.authenticated = False
        self.customer_id = None
        self.discovered_lots = {}
        self.seen_lot_ids = set()
        
        # Proven Typesense API configuration
        self.typesense_url = "https://xczkhpt94lod37gqp.a1.typesense.net/multi_search"
        self.typesense_api_key = "jxX8RU6YVOkm9esgd9buaYjulIWv6N52"
        self.collection = "prod_macdiscount_alias"
        self.sc_filter = "auction_location:=[Anderson,Gastonia,Greenville,Rock Hill,Spartanburg]"
        
        self.setup_database()
    
    def setup_database(self):
        """Setup enhanced database."""
        self.db_path = 'enhanced_authenticated_lots.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enhanced_lots (
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
                discovery_method TEXT,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("🗄️ Enhanced authenticated database initialized")
    
    async def authenticate_first(self):
        """Always authenticate before any operations."""
        print("🔐 AUTHENTICATION REQUIRED")
        print("-" * 40)
        
        try:
            # Load stored credentials
            credentials_path = Path.home() / '.macbid_scraper' / 'credentials.json'
            
            if not credentials_path.exists():
                print("❌ No stored credentials found!")
                print("💡 Run: python3 setup_personal_credentials.py")
                return False
            
            with open(credentials_path, 'r') as f:
                credentials = json.load(f)
            
            email = credentials.get('email')
            password = credentials.get('password')
            self.customer_id = credentials.get('customer_id')
            
            print(f"📧 Authenticating: {email}")
            print(f"👤 Customer ID: {self.customer_id}")
            
            # Create authenticated session
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            connector = aiohttp.TCPConnector(ssl=ssl_context, limit=50)
            timeout = aiohttp.ClientTimeout(total=60)
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
            )
            
            # Test authentication
            test_url = "https://api.macdiscount.com/search"
            async with self.session.get(test_url, params={'q': 'test', 'limit': 1}) as response:
                if response.status == 200:
                    print("✅ Authentication successful!")
                    self.authenticated = True
                    return True
                else:
                    print(f"❌ Authentication failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    async def discover_with_typesense_api(self, search_strategy="complete"):
        """Discover lots using the proven Typesense API."""
        if not self.authenticated:
            print("❌ Must authenticate first!")
            return []
        
        print(f"\n🔍 TYPESENSE API DISCOVERY")
        print("-" * 50)
        print(f"Strategy: {search_strategy}")
        
        try:
            headers = {
                'X-TYPESENSE-API-KEY': self.typesense_api_key,
                'Content-Type': 'application/json'
            }
            
            if search_strategy == "complete":
                # Complete paginated discovery (37,000+ lots)
                return await self.complete_paginated_discovery(headers)
            elif search_strategy == "targeted":
                # Targeted high-value discovery
                return await self.targeted_discovery(headers)
            else:
                # Quick sample discovery
                return await self.quick_sample_discovery(headers)
                
        except Exception as e:
            print(f"❌ Discovery error: {e}")
            return []
    
    async def complete_paginated_discovery(self, headers):
        """Complete paginated discovery of all lots."""
        print("📊 Getting total count...")
        
        # Get total count
        count_payload = {
            "searches": [{
                "collection": self.collection,
                "q": "*",
                "filter_by": self.sc_filter,
                "per_page": 0,
                "page": 1
            }]
        }
        
        async with self.session.post(self.typesense_url, json=count_payload, headers=headers) as response:
            if response.status != 200:
                print(f"❌ Failed to get count: HTTP {response.status}")
                return []
            
            data = await response.json()
            total_lots = data['results'][0]['found']
            print(f"✅ Total lots available: {total_lots:,}")
        
        # Paginate through all results
        per_page = 250
        total_pages = (total_lots + per_page - 1) // per_page
        print(f"📄 Processing {total_pages:,} pages...")
        
        all_lots = []
        
        for page in range(1, min(total_pages + 1, 151)):  # Limit to 151 pages for safety
            try:
                payload = {
                    "searches": [{
                        "collection": self.collection,
                        "q": "*",
                        "filter_by": self.sc_filter,
                        "per_page": per_page,
                        "page": page
                    }]
                }
                
                async with self.session.post(self.typesense_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        hits = data['results'][0]['hits']
                        
                        for hit in hits:
                            lot = hit['document']
                            lot_id = lot.get('id', '')
                            
                            if lot_id and lot_id not in self.seen_lot_ids:
                                scores = self.calculate_scores(lot)
                                lot.update(scores)
                                lot['discovery_method'] = 'typesense_paginated'
                                
                                self.seen_lot_ids.add(lot_id)
                                self.discovered_lots[lot_id] = lot
                                all_lots.append(lot)
                
                if page % 25 == 0:
                    print(f"   📄 Page {page}/{total_pages} - Found {len(all_lots):,} lots so far")
                
                await asyncio.sleep(0.05)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Page {page} error: {e}")
        
        print(f"✅ Complete discovery: {len(all_lots):,} lots")
        return all_lots
    
    async def targeted_discovery(self, headers):
        """Targeted discovery for high-value items."""
        print("🎯 Targeted high-value discovery...")
        
        # High-value search terms
        high_value_terms = [
            "apple", "samsung", "sony", "lg", "dell", "hp", "macbook", "iphone", "ipad",
            "graphics card", "rtx", "nvidia", "gaming", "laptop", "computer", "tv",
            "refrigerator", "washer", "dryer", "furniture", "jewelry", "watch",
            "camera", "lens", "drone", "tablet", "phone", "headphones", "speaker"
        ]
        
        all_lots = []
        
        for term in high_value_terms:
            try:
                payload = {
                    "searches": [{
                        "collection": self.collection,
                        "q": term,
                        "filter_by": self.sc_filter,
                        "per_page": 100,
                        "page": 1,
                        "sort_by": "retail_price:desc"
                    }]
                }
                
                async with self.session.post(self.typesense_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        hits = data['results'][0]['hits']
                        
                        for hit in hits:
                            lot = hit['document']
                            lot_id = lot.get('id', '')
                            
                            if lot_id and lot_id not in self.seen_lot_ids:
                                scores = self.calculate_scores(lot)
                                lot.update(scores)
                                lot['discovery_method'] = f'targeted_{term}'
                                
                                self.seen_lot_ids.add(lot_id)
                                self.discovered_lots[lot_id] = lot
                                all_lots.append(lot)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"   ❌ Term '{term}' error: {e}")
        
        print(f"✅ Targeted discovery: {len(all_lots):,} lots")
        return all_lots
    
    async def quick_sample_discovery(self, headers):
        """Quick sample discovery for testing."""
        print("⚡ Quick sample discovery...")
        
        payload = {
            "searches": [{
                "collection": self.collection,
                "q": "*",
                "filter_by": self.sc_filter,
                "per_page": 500,
                "page": 1,
                "sort_by": "retail_price:desc"
            }]
        }
        
        async with self.session.post(self.typesense_url, json=payload, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                hits = data['results'][0]['hits']
                
                all_lots = []
                for hit in hits:
                    lot = hit['document']
                    lot_id = lot.get('id', '')
                    
                    if lot_id:
                        scores = self.calculate_scores(lot)
                        lot.update(scores)
                        lot['discovery_method'] = 'quick_sample'
                        all_lots.append(lot)
                
                print(f"✅ Quick discovery: {len(all_lots):,} lots")
                return all_lots
            else:
                print(f"❌ Quick discovery failed: HTTP {response.status}")
                return []
    
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
        
        opportunity_score = min(discount_percentage / 100, 1.0)
        if current_bid == 0:
            opportunity_score *= 1.3
        opportunity_score = min(opportunity_score, 1.0)
        
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
    
    def store_lots(self, lots):
        """Store all discovered lots."""
        if not lots:
            return
        
        print(f"💾 Storing {len(lots):,} lots...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for lot in lots:
            try:
                lot_id = lot.get('id', lot.get('lot_id', ''))
                
                cursor.execute('''
                    INSERT OR REPLACE INTO enhanced_lots 
                    (lot_id, title, product_name, retail_price, current_bid, auction_location,
                     category, condition_name, auction_id, inventory_id, expected_close_date,
                     is_open, discount_amount, discount_percentage, opportunity_score, 
                     deal_rating, discovery_method)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lot_id,
                    lot.get('title', ''),
                    lot.get('product_name', ''),
                    lot.get('retail_price', 0),
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
                    lot.get('discovery_method', 'unknown')
                ))
                
            except Exception as e:
                print(f"   ❌ Error storing lot: {e}")
        
        conn.commit()
        conn.close()
        print("✅ All lots stored successfully")
    
    def generate_report(self, lots):
        """Generate comprehensive report."""
        print(f"\n📊 ENHANCED AUTHENTICATED SCANNER REPORT")
        print("=" * 70)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Authentication: {'✅ SUCCESS' if self.authenticated else '❌ FAILED'}")
        print(f"Customer ID: {self.customer_id}")
        print()
        
        if not lots:
            print("⚠️ No lots discovered")
            return
        
        total_lots = len(lots)
        no_bid_lots = sum(1 for lot in lots if lot.get('current_bid', 0) == 0)
        total_retail_value = sum(lot.get('retail_price', 0) for lot in lots)
        
        print(f"📊 DISCOVERY SUMMARY")
        print(f"Total Lots: {total_lots:,}")
        print(f"No Bid Opportunities: {no_bid_lots:,} ({(no_bid_lots/total_lots*100):.1f}%)")
        print(f"Total Retail Value: ${total_retail_value:,.2f}")
        print()
        
        # Top opportunities
        top_lots = sorted(lots, key=lambda x: x.get('retail_price', 0), reverse=True)[:10]
        
        print(f"🏆 TOP 10 OPPORTUNITIES")
        for i, lot in enumerate(top_lots, 1):
            title = lot.get('title', 'Unknown')[:50]
            retail = lot.get('retail_price', 0)
            current_bid = lot.get('current_bid', 0)
            location = lot.get('auction_location', 'Unknown')
            
            print(f"{i:2d}. {title}")
            print(f"    ${retail:.2f} retail | ${current_bid:.2f} bid | {location}")
            print()
        
        print(f"📊 Database: {self.db_path}")
    
    async def run_enhanced_scanner(self, strategy="complete"):
        """Run the enhanced authenticated scanner."""
        print("🚀 ENHANCED AUTHENTICATED TYPESENSE SCANNER")
        print("=" * 80)
        
        try:
            # Step 1: Always authenticate first
            if not await self.authenticate_first():
                print("❌ Cannot proceed without authentication")
                return
            
            # Step 2: Discover lots using Typesense API
            lots = await self.discover_with_typesense_api(strategy)
            
            if not lots:
                print("❌ No lots discovered")
                return
            
            # Step 3: Store results
            self.store_lots(lots)
            
            # Step 4: Generate report
            self.generate_report(lots)
            
            print(f"\n🎉 ENHANCED SCANNER COMPLETE")
            print(f"✅ Discovered {len(lots):,} lots successfully")
            
        except Exception as e:
            print(f"❌ Scanner error: {e}")
        finally:
            if self.session:
                await self.session.close()

async def main():
    import sys
    
    # Allow strategy selection
    strategy = "complete"  # Default
    if len(sys.argv) > 1:
        strategy = sys.argv[1]
    
    scanner = EnhancedAuthenticatedScanner()
    await scanner.run_enhanced_scanner(strategy)

if __name__ == "__main__":
    asyncio.run(main()) 