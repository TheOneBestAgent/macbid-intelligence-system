#!/usr/bin/env python3
"""
🚀 TYPESENSE PAGINATED SCANNER
Gets ALL 37,705+ lots by paginating through the real Typesense API
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime
import math

class TypesensePaginatedScanner:
    def __init__(self):
        self.sc_locations = ['Anderson', 'Gastonia', 'Greenville', 'Rock Hill', 'Spartanburg']
        self.discovered_lots = {}
        self.seen_lot_ids = set()
        self.session = None
        
        # REAL TYPESENSE API (discovered by user)
        self.api_endpoint = "https://xczkhpt94lod37gqp.a1.typesense.net/multi_search"
        self.api_key = "jxX8RU6YVOkm9esgd9buaYjulIWv6N52"
        self.collection = "prod_macdiscount_alias"
        
        self.setup_database()
    
    def setup_database(self):
        """Setup paginated Typesense database."""
        self.db_path = 'typesense_paginated_all_lots.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS paginated_lots (
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
                upc TEXT,
                expected_close_date TEXT,
                is_open INTEGER,
                is_transferrable INTEGER,
                ranking_weight REAL,
                discount_amount REAL,
                discount_percentage REAL,
                opportunity_score REAL,
                deal_rating TEXT,
                page_number INTEGER,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("🗄️ Typesense paginated database initialized")
    
    async def create_session(self):
        """Create HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=20)
        timeout = aiohttp.ClientTimeout(total=60)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.6',
                'Content-Type': 'text/plain',
                'Origin': 'https://www.mac.bid',
                'Referer': 'https://www.mac.bid/',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'
            }
        )
    
    def calculate_scores(self, lot):
        """Calculate opportunity scores."""
        retail_price = lot.get('retail_price', 0)
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
    
    async def get_total_count(self):
        """Get the total number of results available."""
        try:
            # First request to get total count
            search_payload = {
                "query_by": "product_name,embedding,description,keywords,upc,inventory_id,auction_title",
                "exclude_fields": "description,keywords,bid_delta,embedding",
                "vector_query": "embedding:([], distance_threshold:0.18)",
                "drop_tokens_threshold": 0,
                "num_typos": "1,0,0,0,0,0,0",
                "use_cache": True,
                "sort_by": "ranking_weight:desc",
                "highlight_full_fields": "product_name,embedding,description,keywords,upc,inventory_id,auction_title",
                "collection": self.collection,
                "q": "*",
                "facet_by": "auction_location,category,condition,current_bid,expected_close_date,is_open,is_transferrable,retail_price",
                "filter_by": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1]",
                "max_facet_values": 20,
                "page": 1,
                "per_page": 1  # Just get 1 result to check total
            }
            
            payload = {"searches": [search_payload]}
            url = f"{self.api_endpoint}?x-typesense-api-key={self.api_key}"
            
            async with self.session.post(url, data=json.dumps(payload)) as response:
                if response.status == 200:
                    data = await response.json()
                    if "results" in data and len(data["results"]) > 0:
                        found = data["results"][0].get("found", 0)
                        return found
                    
            return 0
            
        except Exception as e:
            print(f"Error getting total count: {e}")
            return 0
    
    async def search_page(self, page_number, per_page=250):
        """Search a specific page."""
        try:
            search_payload = {
                "query_by": "product_name,embedding,description,keywords,upc,inventory_id,auction_title",
                "exclude_fields": "description,keywords,bid_delta,embedding",
                "vector_query": "embedding:([], distance_threshold:0.18)",
                "drop_tokens_threshold": 0,
                "num_typos": "1,0,0,0,0,0,0",
                "use_cache": True,
                "sort_by": "ranking_weight:desc",
                "highlight_full_fields": "product_name,embedding,description,keywords,upc,inventory_id,auction_title",
                "collection": self.collection,
                "q": "*",
                "facet_by": "auction_location,category,condition,current_bid,expected_close_date,is_open,is_transferrable,retail_price",
                "filter_by": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1]",
                "max_facet_values": 20,
                "page": page_number,
                "per_page": per_page
            }
            
            payload = {"searches": [search_payload]}
            url = f"{self.api_endpoint}?x-typesense-api-key={self.api_key}"
            
            async with self.session.post(url, data=json.dumps(payload)) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if "results" in data and len(data["results"]) > 0:
                        result = data["results"][0]
                        hits = result.get("hits", [])
                        found = result.get("found", 0)
                        
                        new_lots = 0
                        for hit in hits:
                            document = hit.get("document", {})
                            
                            # Get lot ID
                            lot_id = (document.get('id') or document.get('inventory_id') or 
                                     document.get('auction_id') or '')
                            
                            if lot_id and lot_id not in self.seen_lot_ids:
                                # Enhance with analytics
                                scores = self.calculate_scores(document)
                                document.update(scores)
                                document['page_number'] = page_number
                                
                                self.seen_lot_ids.add(lot_id)
                                self.discovered_lots[lot_id] = document
                                new_lots += 1
                        
                        return len(hits), new_lots, found
                    else:
                        return 0, 0, 0
                else:
                    print(f"      ❌ HTTP {response.status}")
                    return 0, 0, 0
                    
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return 0, 0, 0
    
    async def run_paginated_discovery(self):
        """Run paginated discovery to get ALL lots."""
        print("🚀 TYPESENSE PAGINATED SCANNER")
        print("=" * 80)
        print("Getting ALL 37,705+ lots by paginating through the real API")
        print()
        
        await self.create_session()
        
        # Get total count first
        print("🔍 Getting total count...")
        total_count = await self.get_total_count()
        print(f"📊 Total lots available: {total_count:,}")
        
        if total_count == 0:
            print("❌ No lots found or API error")
            return []
        
        # Calculate pages needed
        per_page = 250
        total_pages = math.ceil(total_count / per_page)
        print(f"📄 Pages to process: {total_pages:,} (at {per_page} per page)")
        print()
        
        print(f"🔍 PAGINATED DISCOVERY")
        print("-" * 70)
        
        total_api_hits = 0
        failed_pages = 0
        
        for page in range(1, total_pages + 1):
            print(f"   Page [{page:4d}/{total_pages}] Processing...")
            
            api_hits, new_lots, found = await self.search_page(page, per_page)
            total_api_hits += api_hits
            
            if new_lots > 0:
                print(f"      ✅ Found {new_lots} NEW lots! (Total: {len(self.discovered_lots):,})")
            elif api_hits == 0:
                failed_pages += 1
                print(f"      ❌ Failed to get results")
            else:
                print(f"      ℹ️  {api_hits} results, no new lots")
            
            # Progress updates every 50 pages
            if page % 50 == 0:
                progress = (page / total_pages) * 100
                print(f"      🚀 Progress: {progress:.1f}% - Total discovered: {len(self.discovered_lots):,}")
                print(f"      📈 Total API hits: {total_api_hits:,} | Failed pages: {failed_pages}")
                
                # Show current best opportunities
                if len(self.discovered_lots) > 0:
                    best_lots = sorted(self.discovered_lots.values(), 
                                     key=lambda x: x.get('retail_price', 0), reverse=True)[:3]
                    print(f"      🏆 Top opportunities so far:")
                    for j, lot in enumerate(best_lots, 1):
                        product_name = lot.get('product_name', 'Unknown')[:40]
                        retail = lot.get('retail_price', 0)
                        print(f"         {j}. {product_name}... - ${retail:.2f}")
                print()
            
            # Rate limiting - be respectful
            await asyncio.sleep(0.2)
        
        await self.session.close()
        
        print(f"\n🚀 PAGINATED DISCOVERY COMPLETE")
        print("=" * 60)
        print(f"✅ Total unique lots discovered: {len(self.discovered_lots):,}")
        print(f"📊 Total API responses processed: {total_api_hits:,}")
        print(f"❌ Failed pages: {failed_pages}")
        print(f"📄 Pages processed: {total_pages:,}")
        
        coverage = (len(self.discovered_lots) / total_count) * 100 if total_count > 0 else 0
        print(f"📈 Coverage: {coverage:.1f}% of available lots")
        
        if len(self.discovered_lots) > 30000:
            print(f"🎉 ULTIMATE SUCCESS! Discovered {len(self.discovered_lots):,} lots!")
        elif len(self.discovered_lots) > 20000:
            print(f"🚀 MASSIVE SUCCESS! Found {len(self.discovered_lots):,} lots!")
        elif len(self.discovered_lots) > 10000:
            print(f"✅ HUGE SUCCESS! Found {len(self.discovered_lots):,} lots!")
        else:
            print(f"✅ SUCCESS! Found {len(self.discovered_lots):,} lots!")
        
        # Store all lots
        if self.discovered_lots:
            print(f"\n💾 Storing {len(self.discovered_lots):,} lots in database...")
            batch_size = 1000
            stored = 0
            
            for i in range(0, len(self.discovered_lots), batch_size):
                batch = list(self.discovered_lots.values())[i:i+batch_size]
                for lot in batch:
                    self.store_lot(lot)
                    stored += 1
                
                if stored % 5000 == 0:
                    print(f"   📊 Stored {stored:,} lots...")
            
            print("✅ All lots stored successfully")
        
        # Generate comprehensive report
        self.generate_paginated_report()
        
        return list(self.discovered_lots.values())
    
    def store_lot(self, lot):
        """Store lot in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            lot_id = (lot.get('id') or lot.get('inventory_id') or 
                     lot.get('auction_id') or '')
            
            cursor.execute('''
                INSERT OR REPLACE INTO paginated_lots 
                (lot_id, title, product_name, retail_price, current_bid, auction_location,
                 category, condition_name, auction_id, inventory_id, upc, expected_close_date,
                 is_open, is_transferrable, ranking_weight, discount_amount, discount_percentage,
                 opportunity_score, deal_rating, page_number)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lot_id,
                lot.get('auction_title', ''),
                lot.get('product_name', ''),
                lot.get('retail_price', 0),
                lot.get('current_bid', 0),
                lot.get('auction_location', ''),
                lot.get('category', ''),
                lot.get('condition', ''),
                lot.get('auction_id', ''),
                lot.get('inventory_id', ''),
                lot.get('upc', ''),
                lot.get('expected_close_date', ''),
                lot.get('is_open', 0),
                lot.get('is_transferrable', 0),
                lot.get('ranking_weight', 0),
                lot.get('discount_amount', 0),
                lot.get('discount_percentage', 0),
                lot.get('opportunity_score', 0),
                lot.get('deal_rating', 'GOOD'),
                lot.get('page_number', 0)
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Error storing lot: {e}")
        finally:
            conn.close()
    
    def generate_paginated_report(self):
        """Generate paginated discovery report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM paginated_lots')
        total_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM paginated_lots WHERE current_bid = 0')
        no_bid_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(retail_price) FROM paginated_lots')
        total_retail_value = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(discount_percentage) FROM paginated_lots WHERE discount_percentage > 0')
        avg_discount = cursor.fetchone()[0] or 0
        
        # Warehouse breakdown
        cursor.execute('''
            SELECT auction_location, COUNT(*) as lot_count, SUM(retail_price) as total_value
            FROM paginated_lots
            GROUP BY auction_location
            ORDER BY lot_count DESC
        ''')
        warehouse_stats = cursor.fetchall()
        
        # Category breakdown
        cursor.execute('''
            SELECT category, COUNT(*) as lot_count
            FROM paginated_lots
            WHERE category IS NOT NULL AND category != ''
            GROUP BY category
            ORDER BY lot_count DESC
            LIMIT 20
        ''')
        category_stats = cursor.fetchall()
        
        # Top opportunities
        cursor.execute('''
            SELECT product_name, retail_price, current_bid, discount_percentage, 
                   opportunity_score, auction_location, lot_id
            FROM paginated_lots
            WHERE opportunity_score > 0.8
            ORDER BY retail_price DESC
            LIMIT 100
        ''')
        top_opportunities = cursor.fetchall()
        
        conn.close()
        
        print(f"""
🚀 PAGINATED TYPESENSE DISCOVERY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 COMPLETE DISCOVERY SUMMARY
Total Lots Discovered: {total_lots:,}
No Bid Opportunities: {no_bid_lots:,} ({(no_bid_lots/total_lots*100):.1f}%)
Average Discount: {avg_discount:.1f}%
Total Retail Value: ${total_retail_value:,.2f}

🏭 WAREHOUSE BREAKDOWN""")
        
        for location, count, value in warehouse_stats:
            print(f"• {location}: {count:,} lots (${value:,.2f} value)")
        
        print(f"""
📦 TOP 20 CATEGORIES""")
        
        for category, count in category_stats:
            print(f"• {category}: {count:,} lots")
        
        print(f"""
🏆 TOP 100 ULTIMATE OPPORTUNITIES""")
        
        for i, (product_name, retail, current_bid, discount_pct, score, location, lot_id) in enumerate(top_opportunities, 1):
            print(f"""
{i:3d}. {product_name[:60]}{'...' if len(product_name) > 60 else ''}
     Retail: ${retail:.2f} | Current Bid: ${current_bid:.2f} | Discount: {discount_pct:.1f}%
     Opportunity Score: {score:.3f} | Location: {location}
     🔗 Link: https://mac.bid/lot/{lot_id}""")
        
        print(f"\n📊 Database saved to: {self.db_path}")

async def main():
    scanner = TypesensePaginatedScanner()
    await scanner.run_paginated_discovery()

if __name__ == "__main__":
    asyncio.run(main()) 