#!/usr/bin/env python3
"""
🚀 TYPESENSE ALL LOTS SCANNER
Uses the REAL Mac.bid API (Typesense) discovered by user to get ALL lots
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime

class TypesenseAllLotsScanner:
    def __init__(self):
        self.sc_locations = ['Anderson', 'Gastonia', 'Greenville', 'Rock Hill', 'Spartanburg']
        self.discovered_lots = {}
        self.seen_lot_ids = set()
        self.session = None
        
        # REAL TYPESENSE API (discovered by user)
        self.api_endpoint = "https://xczkhpt94lod37gqp.a1.typesense.net/multi_search"
        self.api_key = "jxX8RU6YVOkm9esgd9buaYjulIWv6N52"
        self.collection = "prod_macdiscount_alias"
        
        # Search strategies to get ALL lots
        self.search_strategies = [
            # 1. Get all open lots in SC locations (base query)
            {
                "name": "All Open SC Lots",
                "query": "*",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1]",
                "per_page": 250  # Try higher limit
            },
            
            # 2. Get all lots (open and closed) in SC locations
            {
                "name": "All SC Lots (Open + Closed)",
                "query": "*",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`]",
                "per_page": 250
            },
            
            # 3. Individual location searches for maximum coverage
            {
                "name": "Anderson Only",
                "query": "*",
                "filter": "auction_location:=[`Anderson`] && is_open:=[1]",
                "per_page": 250
            },
            {
                "name": "Gastonia Only", 
                "query": "*",
                "filter": "auction_location:=[`Gastonia`] && is_open:=[1]",
                "per_page": 250
            },
            {
                "name": "Greenville Only",
                "query": "*",
                "filter": "auction_location:=[`Greenville`] && is_open:=[1]",
                "per_page": 250
            },
            {
                "name": "Rock Hill Only",
                "query": "*",
                "filter": "auction_location:=[`Rock Hill`] && is_open:=[1]",
                "per_page": 250
            },
            {
                "name": "Spartanburg Only",
                "query": "*",
                "filter": "auction_location:=[`Spartanburg`] && is_open:=[1]",
                "per_page": 250
            },
            
            # 4. Category-based searches to ensure we get everything
            {
                "name": "Electronics Category",
                "query": "electronics OR computer OR laptop OR phone OR tablet",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1]",
                "per_page": 250
            },
            {
                "name": "Appliances Category",
                "query": "appliance OR refrigerator OR washer OR dryer OR microwave",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1]",
                "per_page": 250
            },
            {
                "name": "Tools Category",
                "query": "tool OR drill OR saw OR hammer OR wrench",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1]",
                "per_page": 250
            },
            {
                "name": "Furniture Category",
                "query": "furniture OR chair OR table OR sofa OR bed",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1]",
                "per_page": 250
            },
            
            # 5. Price range searches to catch different segments
            {
                "name": "High Value Items ($1000+)",
                "query": "*",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1] && retail_price:>=1000",
                "per_page": 250
            },
            {
                "name": "Medium Value Items ($100-$999)",
                "query": "*",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1] && retail_price:>=100 && retail_price:<1000",
                "per_page": 250
            },
            {
                "name": "Low Value Items (<$100)",
                "query": "*",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1] && retail_price:<100",
                "per_page": 250
            },
            
            # 6. No bid opportunities
            {
                "name": "No Bid Items",
                "query": "*",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1] && current_bid:=0",
                "per_page": 250
            },
            
            # 7. Different sort orders to get different results
            {
                "name": "Newest First",
                "query": "*",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1]",
                "per_page": 250,
                "sort_by": "expected_close_date:desc"
            },
            {
                "name": "Oldest First", 
                "query": "*",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1]",
                "per_page": 250,
                "sort_by": "expected_close_date:asc"
            },
            {
                "name": "Highest Value First",
                "query": "*",
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1]",
                "per_page": 250,
                "sort_by": "retail_price:desc"
            },
            {
                "name": "Lowest Value First",
                "query": "*", 
                "filter": "auction_location:=[`Anderson`,`Gastonia`,`Greenville`,`Rock Hill`,`Spartanburg`] && is_open:=[1]",
                "per_page": 250,
                "sort_by": "retail_price:asc"
            }
        ]
        
        self.setup_database()
    
    def setup_database(self):
        """Setup Typesense discovery database."""
        self.db_path = 'typesense_all_lots.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS typesense_lots (
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
                search_strategy TEXT,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("🗄️ Typesense all lots database initialized")
    
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
    
    async def search_with_strategy(self, strategy):
        """Search using a specific strategy - CHECK ALL PAGES."""
        total_api_hits = 0
        total_new_lots = 0
        page = 1
        max_pages = 50  # Safety limit to prevent infinite loops
        
        try:
            while page <= max_pages:
                # Build the search payload for current page
                search_payload = {
                    "query_by": "product_name,embedding,description,keywords,upc,inventory_id,auction_title",
                    "exclude_fields": "description,keywords,bid_delta,embedding",
                    "vector_query": "embedding:([], distance_threshold:0.18)",
                    "drop_tokens_threshold": 0,
                    "num_typos": "1,0,0,0,0,0,0",
                    "use_cache": True,
                    "highlight_full_fields": "product_name,embedding,description,keywords,upc,inventory_id,auction_title",
                    "collection": self.collection,
                    "q": strategy["query"],
                    "facet_by": "auction_location,category,condition,current_bid,expected_close_date,is_open,is_transferrable,retail_price",
                    "filter_by": strategy["filter"],
                    "max_facet_values": 20,
                    "page": page,
                    "per_page": strategy["per_page"]
                }
                
                # Add sort if specified
                if "sort_by" in strategy:
                    search_payload["sort_by"] = strategy["sort_by"]
                else:
                    search_payload["sort_by"] = "ranking_weight:desc"
                
                # Create multi-search payload
                payload = {
                    "searches": [search_payload]
                }
                
                url = f"{self.api_endpoint}?x-typesense-api-key={self.api_key}"
                
                async with self.session.post(url, data=json.dumps(payload)) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if "results" in data and len(data["results"]) > 0:
                            hits = data["results"][0].get("hits", [])
                            
                            # If no hits on this page, we've reached the end
                            if not hits:
                                break
                            
                            page_new_lots = 0
                            for hit in hits:
                                document = hit.get("document", {})
                                
                                # Get lot ID
                                lot_id = (document.get('id') or document.get('inventory_id') or 
                                         document.get('auction_id') or '')
                                
                                if lot_id and lot_id not in self.seen_lot_ids:
                                    # Enhance with analytics
                                    scores = self.calculate_scores(document)
                                    document.update(scores)
                                    document['search_strategy'] = strategy['name']
                                    
                                    self.seen_lot_ids.add(lot_id)
                                    self.discovered_lots[lot_id] = document
                                    page_new_lots += 1
                            
                            total_api_hits += len(hits)
                            total_new_lots += page_new_lots
                            
                            # Show progress for multi-page strategies
                            if page > 1:
                                print(f"         Page {page}: {len(hits)} hits, {page_new_lots} new lots")
                            
                            # If we got fewer results than per_page, we've reached the end
                            if len(hits) < strategy["per_page"]:
                                break
                                
                            page += 1
                            
                            # Rate limiting between pages
                            await asyncio.sleep(0.5)
                            
                        else:
                            break
                    else:
                        print(f"      ❌ HTTP {response.status} on page {page}")
                        break
            
            if page > 2:
                print(f"      📄 Searched {page-1} pages total")
                        
            return total_api_hits, total_new_lots
                    
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return total_api_hits, total_new_lots
    
    async def run_typesense_discovery(self):
        """Run Typesense all lots discovery."""
        print("🚀 TYPESENSE ALL LOTS SCANNER")
        print("=" * 80)
        print("Using the REAL Mac.bid API (Typesense) to discover ALL lots")
        print(f"API Endpoint: {self.api_endpoint}")
        print(f"Collection: {self.collection}")
        print(f"Strategies: {len(self.search_strategies)}")
        print()
        
        await self.create_session()
        
        total_api_hits = 0
        
        print(f"🔍 TYPESENSE COMPREHENSIVE SEARCH")
        print("-" * 70)
        
        for i, strategy in enumerate(self.search_strategies, 1):
            print(f"   [{i:2d}/{len(self.search_strategies)}] {strategy['name']}...")
            print(f"      Query: '{strategy['query']}'")
            print(f"      Filter: {strategy['filter'][:80]}{'...' if len(strategy['filter']) > 80 else ''}")
            
            api_hits, new_lots = await self.search_with_strategy(strategy)
            total_api_hits += api_hits
            
            if new_lots > 0:
                print(f"      ✅ Found {new_lots} NEW lots! (Total: {len(self.discovered_lots):,})")
            
            if api_hits > 0:
                print(f"      📊 API returned {api_hits} total results")
            
            # Show progress
            if len(self.discovered_lots) > 0:
                best_lot = max(self.discovered_lots.values(), 
                              key=lambda x: x.get('retail_price', 0))
                print(f"      🏆 Best find so far: {best_lot.get('product_name', 'Unknown')[:40]} - ${best_lot.get('retail_price', 0):.2f}")
            
            print()
            
            # Rate limiting
            await asyncio.sleep(1.0)  # Be respectful to their API
        
        await self.session.close()
        
        print(f"\n🚀 TYPESENSE ALL LOTS DISCOVERY COMPLETE")
        print("=" * 60)
        print(f"✅ Total unique lots discovered: {len(self.discovered_lots):,}")
        print(f"📊 Total API responses processed: {total_api_hits:,}")
        
        if len(self.discovered_lots) > 1000:
            print(f"🎉 MASSIVE SUCCESS! Discovered {len(self.discovered_lots):,} lots!")
        elif len(self.discovered_lots) > 500:
            print(f"🚀 HUGE SUCCESS! Found {len(self.discovered_lots):,} lots!")
        elif len(self.discovered_lots) > 300:
            print(f"✅ GREAT SUCCESS! Found {len(self.discovered_lots):,} lots!")
        else:
            print(f"✅ SUCCESS! Found {len(self.discovered_lots):,} lots!")
        
        # Store all lots
        if self.discovered_lots:
            print(f"\n💾 Storing {len(self.discovered_lots):,} lots in database...")
            for lot in self.discovered_lots.values():
                self.store_lot(lot)
            print("✅ All lots stored successfully")
        
        # Generate comprehensive report
        self.generate_typesense_report()
        
        return list(self.discovered_lots.values())
    
    def store_lot(self, lot):
        """Store lot in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            lot_id = (lot.get('id') or lot.get('inventory_id') or 
                     lot.get('auction_id') or '')
            
            cursor.execute('''
                INSERT OR REPLACE INTO typesense_lots 
                (lot_id, title, product_name, retail_price, current_bid, auction_location,
                 category, condition_name, auction_id, inventory_id, upc, expected_close_date,
                 is_open, is_transferrable, ranking_weight, discount_amount, discount_percentage,
                 opportunity_score, deal_rating, search_strategy)
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
                lot.get('search_strategy', '')
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Error storing lot: {e}")
        finally:
            conn.close()
    
    def generate_typesense_report(self):
        """Generate Typesense discovery report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM typesense_lots')
        total_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM typesense_lots WHERE current_bid = 0')
        no_bid_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(retail_price) FROM typesense_lots')
        total_retail_value = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(discount_percentage) FROM typesense_lots WHERE discount_percentage > 0')
        avg_discount = cursor.fetchone()[0] or 0
        
        # Warehouse breakdown
        cursor.execute('''
            SELECT auction_location, COUNT(*) as lot_count, SUM(retail_price) as total_value
            FROM typesense_lots
            GROUP BY auction_location
            ORDER BY lot_count DESC
        ''')
        warehouse_stats = cursor.fetchall()
        
        # Strategy effectiveness
        cursor.execute('''
            SELECT search_strategy, COUNT(*) as discoveries
            FROM typesense_lots
            GROUP BY search_strategy
            ORDER BY discoveries DESC
        ''')
        strategy_stats = cursor.fetchall()
        
        # Top opportunities
        cursor.execute('''
            SELECT product_name, retail_price, current_bid, discount_percentage, 
                   opportunity_score, auction_location, lot_id
            FROM typesense_lots
            WHERE opportunity_score > 0.8
            ORDER BY opportunity_score DESC, retail_price DESC
            LIMIT 50
        ''')
        top_opportunities = cursor.fetchall()
        
        conn.close()
        
        print(f"""
🚀 TYPESENSE ALL LOTS DISCOVERY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 TYPESENSE DISCOVERY SUMMARY
Total Lots Discovered: {total_lots:,}
No Bid Opportunities: {no_bid_lots:,} ({(no_bid_lots/total_lots*100):.1f}%)
Average Discount: {avg_discount:.1f}%
Total Retail Value: ${total_retail_value:,.2f}

🏭 WAREHOUSE BREAKDOWN""")
        
        for location, count, value in warehouse_stats:
            print(f"• {location}: {count:,} lots (${value:,.2f} value)")
        
        print(f"""
🎯 STRATEGY EFFECTIVENESS""")
        
        for strategy, discoveries in strategy_stats:
            print(f"• {strategy}: {discoveries:,} lots discovered")
        
        print(f"""
🏆 TOP 50 TYPESENSE OPPORTUNITIES""")
        
        for i, (product_name, retail, current_bid, discount_pct, score, location, lot_id) in enumerate(top_opportunities, 1):
            print(f"""
{i:2d}. {product_name[:60]}{'...' if len(product_name) > 60 else ''}
    Retail: ${retail:.2f} | Current Bid: ${current_bid:.2f} | Discount: {discount_pct:.1f}%
    Opportunity Score: {score:.3f} | Location: {location}
    🔗 Link: https://mac.bid/lot/{lot_id}""")
        
        print(f"\n📊 Database saved to: {self.db_path}")

async def main():
    scanner = TypesenseAllLotsScanner()
    await scanner.run_typesense_discovery()

if __name__ == "__main__":
    asyncio.run(main()) 