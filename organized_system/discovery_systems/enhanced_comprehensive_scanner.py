#!/usr/bin/env python3
"""
🔍 Enhanced Comprehensive Scanner - Find ALL lots across SC warehouses
Uses multiple discovery strategies to maximize lot discovery
"""

import asyncio
import json
import sqlite3
from datetime import datetime
import aiohttp
import ssl
from typing import List, Dict, Optional
import string

class EnhancedComprehensiveScanner:
    def __init__(self):
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        
        # Multiple discovery strategies
        self.discovery_strategies = {
            'brand_search': [
                'apple', 'samsung', 'sony', 'lg', 'dell', 'hp', 'lenovo', 'asus', 'acer',
                'microsoft', 'nintendo', 'xbox', 'playstation', 'bose', 'beats', 'jbl',
                'dyson', 'shark', 'bissell', 'dewalt', 'milwaukee', 'makita', 'ryobi',
                'craftsman', 'black+decker', 'bosch', 'canon', 'nikon', 'gopro',
                'fitbit', 'garmin', 'roku', 'amazon', 'google', 'nest', 'ring'
            ],
            'category_search': [
                'laptop', 'computer', 'tablet', 'phone', 'tv', 'monitor', 'camera',
                'headphones', 'speaker', 'watch', 'vacuum', 'appliance', 'tool',
                'drill', 'saw', 'gaming', 'console', 'furniture', 'kitchen',
                'home', 'garden', 'outdoor', 'fitness', 'sports', 'clothing',
                'shoes', 'bag', 'jewelry', 'electronics', 'audio', 'video'
            ],
            'condition_search': [
                'new', 'open box', 'refurbished', 'used', 'like new', 'excellent',
                'good', 'fair', 'damaged', 'parts', 'repair', 'clearance', 'sale'
            ],
            'price_range_search': [
                'under 50', 'under 100', 'under 200', 'under 500', 'under 1000',
                'over 100', 'over 200', 'over 500', 'over 1000', 'over 2000'
            ],
            'alphabet_search': list(string.ascii_lowercase),  # a, b, c, etc.
            'number_search': [str(i) for i in range(10)],  # 0, 1, 2, etc.
            'common_words': [
                'the', 'and', 'with', 'for', 'pro', 'plus', 'max', 'mini', 'air',
                'ultra', 'premium', 'deluxe', 'standard', 'basic', 'advanced',
                'wireless', 'bluetooth', 'smart', 'digital', 'portable', 'compact'
            ]
        }
        
        self.setup_database()
    
    def setup_database(self):
        """Setup enhanced scanning database."""
        self.db_path = 'enhanced_comprehensive_scan.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced lots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS all_lots (
                lot_id TEXT PRIMARY KEY,
                title TEXT,
                retail_price REAL,
                current_bid REAL,
                total_bids INTEGER,
                location TEXT,
                category TEXT,
                condition_name TEXT,
                discount_amount REAL,
                discount_percentage REAL,
                opportunity_score REAL,
                deal_rating TEXT,
                auction_id TEXT,
                auction_number TEXT,
                expected_close_date TEXT,
                image_url TEXT,
                discovery_strategy TEXT,
                scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Discovery tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovery_stats (
                strategy TEXT,
                search_term TEXT,
                lots_found INTEGER,
                sc_lots_found INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("📊 Enhanced scanning database initialized")
    
    async def discover_lots_by_strategy(self, strategy_name: str, search_terms: List[str]) -> List[Dict]:
        """Discover lots using a specific strategy."""
        all_lots = []
        unique_lots = {}
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        print(f"🔍 Strategy: {strategy_name.replace('_', ' ').title()}")
        print(f"   Searching {len(search_terms)} terms...")
        
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context),
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                
                for i, term in enumerate(search_terms, 1):
                    try:
                        # Try different search approaches
                        search_urls = [
                            f"https://api.macdiscount.com/search?q={term}&limit=200",
                            f"https://api.macdiscount.com/search?q={term}&sort=price_asc&limit=200",
                            f"https://api.macdiscount.com/search?q={term}&sort=price_desc&limit=200"
                        ]
                        
                        term_lots = 0
                        term_sc_lots = 0
                        
                        for url in search_urls:
                            try:
                                async with session.get(url) as response:
                                    if response.status == 200:
                                        data = await response.json()
                                        lot_data = data.get('hits', [])
                                        term_lots += len(lot_data)
                                        
                                        for lot in lot_data:
                                            # Filter for SC locations
                                            location = lot.get('auction_location', '')
                                            if any(sc_loc in location for sc_loc in self.sc_locations):
                                                lot_id = lot.get('id', lot.get('mac_lot_id', ''))
                                                if lot_id and lot_id not in unique_lots:
                                                    lot['discovery_strategy'] = strategy_name
                                                    lot['search_term'] = term
                                                    unique_lots[lot_id] = lot
                                                    all_lots.append(lot)
                                                    term_sc_lots += 1
                                
                                await asyncio.sleep(0.1)
                                
                            except Exception as e:
                                continue
                        
                        # Log discovery stats
                        conn = sqlite3.connect(self.db_path)
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO discovery_stats (strategy, search_term, lots_found, sc_lots_found)
                            VALUES (?, ?, ?, ?)
                        ''', (strategy_name, term, term_lots, term_sc_lots))
                        conn.commit()
                        conn.close()
                        
                        if i % 10 == 0:
                            progress = (i / len(search_terms)) * 100
                            print(f"   Progress: {progress:.1f}% ({i}/{len(search_terms)}) - Found {len(all_lots)} SC lots")
                        
                    except Exception as e:
                        print(f"   ❌ Error with term '{term}': {e}")
                        continue
                
                print(f"   ✅ {strategy_name}: {len(all_lots)} unique SC lots found")
                return all_lots
                
        except Exception as e:
            print(f"❌ Strategy error: {e}")
            return []
    
    async def run_enhanced_comprehensive_scan(self):
        """Run enhanced comprehensive scan using multiple strategies."""
        print("🚀 ENHANCED COMPREHENSIVE WAREHOUSE SCAN")
        print("=" * 60)
        print("Using multiple discovery strategies to maximize lot discovery")
        print()
        
        all_discovered_lots = []
        global_unique_lots = {}
        
        # Run each discovery strategy
        for strategy_name, search_terms in self.discovery_strategies.items():
            print(f"\n📡 DISCOVERY STRATEGY: {strategy_name.upper()}")
            print("-" * 50)
            
            strategy_lots = await self.discover_lots_by_strategy(strategy_name, search_terms)
            
            # Add to global collection (avoiding duplicates)
            new_lots = 0
            for lot in strategy_lots:
                lot_id = lot.get('id', lot.get('mac_lot_id', ''))
                if lot_id and lot_id not in global_unique_lots:
                    global_unique_lots[lot_id] = lot
                    all_discovered_lots.append(lot)
                    new_lots += 1
            
            print(f"   📦 New unique lots from this strategy: {new_lots}")
            print(f"   📊 Total unique lots so far: {len(all_discovered_lots)}")
        
        print(f"\n🎯 FINAL DISCOVERY RESULTS")
        print("=" * 30)
        print(f"✅ Total unique lots discovered: {len(all_discovered_lots)}")
        
        # Warehouse breakdown
        warehouse_counts = {}
        for lot in all_discovered_lots:
            location = lot.get('auction_location', 'Unknown')
            warehouse_counts[location] = warehouse_counts.get(location, 0) + 1
        
        print(f"\n🏭 WAREHOUSE BREAKDOWN:")
        for warehouse, count in sorted(warehouse_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"   • {warehouse}: {count:,} lots")
        
        # Strategy effectiveness
        print(f"\n📊 STRATEGY EFFECTIVENESS:")
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT strategy, SUM(sc_lots_found) as total_sc_lots
            FROM discovery_stats
            GROUP BY strategy
            ORDER BY total_sc_lots DESC
        ''')
        strategy_stats = cursor.fetchall()
        conn.close()
        
        for strategy, sc_lots in strategy_stats:
            print(f"   • {strategy.replace('_', ' ').title()}: {sc_lots:,} lots")
        
        # Store all lots
        if all_discovered_lots:
            print(f"\n💾 STORING {len(all_discovered_lots)} LOTS IN DATABASE")
            print("-" * 45)
            
            for i, lot in enumerate(all_discovered_lots, 1):
                self.store_lot_data(lot)
                
                if i % 500 == 0:
                    progress = (i / len(all_discovered_lots)) * 100
                    print(f"   Progress: {progress:.1f}% ({i:,}/{len(all_discovered_lots):,} lots stored)")
            
            print("✅ All lots stored successfully")
        
        # Generate summary report
        self.generate_enhanced_report()
        
        return all_discovered_lots
    
    def store_lot_data(self, lot: Dict):
        """Store lot data in enhanced database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            retail_price = lot.get('discount', lot.get('retail_price', 0))
            current_bid = lot.get('current_bid', 0)
            
            # Calculate metrics
            discount_amount = retail_price - current_bid if current_bid > 0 else retail_price
            discount_percentage = (discount_amount / retail_price * 100) if retail_price > 0 else 0
            
            # Opportunity score
            opportunity_score = min(discount_percentage / 100, 1.0)
            if current_bid == 0:
                opportunity_score *= 1.3
            opportunity_score = min(opportunity_score, 1.0)
            
            # Deal rating
            if discount_percentage >= 80:
                deal_rating = "EXCEPTIONAL"
            elif discount_percentage >= 60:
                deal_rating = "EXCELLENT"
            elif discount_percentage >= 40:
                deal_rating = "GOOD"
            else:
                deal_rating = "FAIR"
            
            cursor.execute('''
                INSERT OR REPLACE INTO all_lots 
                (lot_id, title, retail_price, current_bid, total_bids, location, category,
                 condition_name, discount_amount, discount_percentage, opportunity_score,
                 deal_rating, auction_id, auction_number, expected_close_date, image_url,
                 discovery_strategy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lot.get('id', lot.get('mac_lot_id', '')),
                lot.get('auction_title', lot.get('title', '')),
                retail_price,
                current_bid,
                lot.get('total_bids', 0),
                lot.get('auction_location', ''),
                lot.get('category', ''),
                lot.get('condition', ''),
                discount_amount,
                discount_percentage,
                opportunity_score,
                deal_rating,
                lot.get('auction_id', ''),
                lot.get('auction_number', ''),
                lot.get('expected_close_date', ''),
                lot.get('image_url', ''),
                lot.get('discovery_strategy', 'unknown')
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Error storing lot: {e}")
        finally:
            conn.close()
    
    def generate_enhanced_report(self):
        """Generate enhanced comprehensive report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Summary statistics
        cursor.execute('SELECT COUNT(*) FROM all_lots')
        total_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM all_lots WHERE current_bid = 0')
        no_bid_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(retail_price) FROM all_lots')
        total_retail_value = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(discount_percentage) FROM all_lots WHERE discount_percentage > 0')
        avg_discount = cursor.fetchone()[0] or 0
        
        # Top opportunities
        cursor.execute('''
            SELECT title, retail_price, current_bid, discount_percentage, 
                   opportunity_score, location, lot_id
            FROM all_lots
            WHERE opportunity_score > 0.8
            ORDER BY opportunity_score DESC, retail_price DESC
            LIMIT 20
        ''')
        top_opportunities = cursor.fetchall()
        
        conn.close()
        
        # Generate report
        report = f"""
🔍 ENHANCED COMPREHENSIVE WAREHOUSE SCAN REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 DISCOVERY SUMMARY
Total Lots Discovered: {total_lots:,}
No Bid Opportunities: {no_bid_lots:,}
Average Discount: {avg_discount:.1f}%
Total Retail Value: ${total_retail_value:,.2f}

🏆 TOP 20 OPPORTUNITIES
"""
        
        for i, (title, retail, current_bid, discount_pct, score, location, lot_id) in enumerate(top_opportunities, 1):
            clean_lot_id = lot_id.replace('mac_lot_', '')
            report += f"""
{i:2d}. {title[:60]}{'...' if len(title) > 60 else ''}
    Retail: ${retail:.2f} | Current Bid: ${current_bid:.2f} | Discount: {discount_pct:.1f}%
    Opportunity Score: {score:.3f} | Location: {location}
    🔗 Link: https://mac.bid/lot/{clean_lot_id}
"""
        
        # Save report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'enhanced_comprehensive_scan_{timestamp}.txt'
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Enhanced report saved to: {report_file}")
        print(f"📊 Database saved to: {self.db_path}")

async def main():
    """Main function."""
    scanner = EnhancedComprehensiveScanner()
    await scanner.run_enhanced_comprehensive_scan()

if __name__ == "__main__":
    asyncio.run(main()) 