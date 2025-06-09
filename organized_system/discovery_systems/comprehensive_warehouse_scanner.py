#!/usr/bin/env python3
"""
🏭 Comprehensive Warehouse Scanner for Mac.bid
Searches ALL available products across 5 South Carolina warehouses to find the best deals
"""

import asyncio
import json
import sqlite3
from datetime import datetime
import aiohttp
import ssl
from typing import List, Dict, Optional

class ComprehensiveWarehouseScanner:
    def __init__(self):
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        
        # Comprehensive search terms covering all major categories
        self.search_categories = {
            'Electronics': [
                'laptop', 'computer', 'tablet', 'phone', 'smartphone', 'monitor', 'TV', 'television',
                'camera', 'drone', 'smartwatch', 'headphones', 'speaker', 'bluetooth', 'wireless',
                'gaming', 'console', 'xbox', 'playstation', 'nintendo', 'switch'
            ],
            'Apple Products': [
                'apple', 'iphone', 'ipad', 'macbook', 'imac', 'airpods', 'apple watch', 'mac'
            ],
            'Audio & Video': [
                'sony', 'bose', 'beats', 'jbl', 'samsung', 'lg', 'panasonic', 'canon', 'nikon'
            ],
            'Home & Garden': [
                'dyson', 'vacuum', 'appliance', 'kitchen', 'cookware', 'furniture', 'decor'
            ],
            'Tools & Equipment': [
                'dewalt', 'milwaukee', 'makita', 'ryobi', 'craftsman', 'tools', 'drill', 'saw'
            ],
            'Sports & Outdoors': [
                'bike', 'bicycle', 'fitness', 'exercise', 'outdoor', 'camping', 'sports'
            ],
            'Fashion & Accessories': [
                'watch', 'jewelry', 'bag', 'purse', 'clothing', 'shoes', 'accessories'
            ],
            'General': [
                'new', 'open box', 'refurbished', 'clearance', 'sale', 'deal'
            ]
        }
        
        self.setup_database()
    
    def setup_database(self):
        """Setup comprehensive scanning database."""
        self.db_path = 'comprehensive_warehouse_scan.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Comprehensive lots table
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
                expected_close_date TEXT,
                image_url TEXT,
                scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Best deals summary table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS best_deals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                deal_type TEXT,
                score REAL,
                reason TEXT,
                scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lot_id) REFERENCES all_lots (lot_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("📊 Comprehensive scanning database initialized")
    
    async def discover_all_lots(self) -> List[Dict]:
        """Discover ALL lots across all categories and warehouses."""
        all_lots = []
        unique_lots = {}
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        print("🔍 COMPREHENSIVE WAREHOUSE SCANNING")
        print("=" * 50)
        print(f"Searching across {len(self.sc_locations)} SC warehouses:")
        print(f"• {', '.join(self.sc_locations)}")
        print()
        
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context),
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                
                total_searches = sum(len(terms) for terms in self.search_categories.values())
                current_search = 0
                
                for category, search_terms in self.search_categories.items():
                    print(f"📦 Scanning {category}...")
                    category_lots = 0
                    
                    for term in search_terms:
                        current_search += 1
                        try:
                            url = f"https://api.macdiscount.com/search?q={term}&limit=100"
                            
                            async with session.get(url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    lot_data = data.get('hits', [])
                                    
                                    for lot in lot_data:
                                        # Filter for SC locations
                                        location = lot.get('auction_location', '')
                                        if any(sc_loc in location for sc_loc in self.sc_locations):
                                            lot_id = lot.get('id', lot.get('mac_lot_id', ''))
                                            if lot_id and lot_id not in unique_lots:
                                                lot['search_category'] = category
                                                unique_lots[lot_id] = lot
                                                all_lots.append(lot)
                                                category_lots += 1
                            
                            # Progress indicator
                            if current_search % 10 == 0:
                                progress = (current_search / total_searches) * 100
                                print(f"   Progress: {progress:.1f}% ({current_search}/{total_searches} searches)")
                            
                            await asyncio.sleep(0.2)  # Rate limiting
                            
                        except Exception as e:
                            print(f"   ❌ Error searching {term}: {e}")
                            continue
                    
                    print(f"   ✅ {category}: {category_lots} unique lots found")
                
                print(f"\n📦 TOTAL DISCOVERY RESULTS")
                print("-" * 30)
                print(f"✅ {len(all_lots)} unique lots found across all warehouses")
                
                # Warehouse breakdown
                warehouse_counts = {}
                for lot in all_lots:
                    location = lot.get('auction_location', 'Unknown')
                    warehouse_counts[location] = warehouse_counts.get(location, 0) + 1
                
                for warehouse, count in sorted(warehouse_counts.items()):
                    print(f"   • {warehouse}: {count} lots")
                
                return all_lots
                
        except Exception as e:
            print(f"❌ Discovery error: {e}")
            return []
    
    def calculate_deal_metrics(self, lot: Dict) -> Dict:
        """Calculate comprehensive deal metrics for a lot."""
        retail_price = lot.get('discount', lot.get('retail_price', 0))
        current_bid = lot.get('current_bid', 0)
        
        # Calculate discount metrics
        discount_amount = retail_price - current_bid if current_bid > 0 else retail_price
        discount_percentage = (discount_amount / retail_price * 100) if retail_price > 0 else 0
        
        # Deal rating based on discount percentage
        if discount_percentage >= 80:
            deal_rating = "EXCEPTIONAL"
        elif discount_percentage >= 60:
            deal_rating = "EXCELLENT"
        elif discount_percentage >= 40:
            deal_rating = "GOOD"
        elif discount_percentage >= 20:
            deal_rating = "FAIR"
        else:
            deal_rating = "POOR"
        
        # Opportunity score (0-1 scale)
        opportunity_score = min(discount_percentage / 100, 1.0)
        
        # Boost score for premium brands
        title = lot.get('auction_title', '').lower()
        premium_brands = ['apple', 'sony', 'samsung', 'nintendo', 'dyson', 'bose', 'dewalt', 'milwaukee']
        if any(brand in title for brand in premium_brands):
            opportunity_score *= 1.2
        
        # Boost score for no current bids
        if current_bid == 0:
            opportunity_score *= 1.3
        
        opportunity_score = min(opportunity_score, 1.0)
        
        return {
            'discount_amount': discount_amount,
            'discount_percentage': discount_percentage,
            'deal_rating': deal_rating,
            'opportunity_score': opportunity_score
        }
    
    def store_lot_data(self, lot: Dict, deal_metrics: Dict):
        """Store comprehensive lot data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO all_lots 
                (lot_id, title, retail_price, current_bid, total_bids, location, category,
                 condition_name, discount_amount, discount_percentage, opportunity_score,
                 deal_rating, auction_id, expected_close_date, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lot.get('id', lot.get('mac_lot_id', '')),
                lot.get('auction_title', lot.get('title', '')),
                lot.get('discount', lot.get('retail_price', 0)),
                lot.get('current_bid', 0),
                lot.get('total_bids', 0),
                lot.get('auction_location', ''),
                lot.get('search_category', 'Unknown'),
                lot.get('condition', ''),
                deal_metrics['discount_amount'],
                deal_metrics['discount_percentage'],
                deal_metrics['opportunity_score'],
                deal_metrics['deal_rating'],
                lot.get('auction_id', ''),
                lot.get('expected_close_date', ''),
                lot.get('image_url', '')
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Error storing lot data: {e}")
        finally:
            conn.close()
    
    def identify_best_deals(self):
        """Identify and categorize the best deals."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear previous best deals
        cursor.execute('DELETE FROM best_deals')
        
        # Top deals by opportunity score
        cursor.execute('''
            SELECT lot_id, opportunity_score FROM all_lots 
            WHERE opportunity_score > 0.8 
            ORDER BY opportunity_score DESC 
            LIMIT 20
        ''')
        top_opportunities = cursor.fetchall()
        
        for lot_id, score in top_opportunities:
            cursor.execute('''
                INSERT INTO best_deals (lot_id, deal_type, score, reason)
                VALUES (?, ?, ?, ?)
            ''', (lot_id, 'TOP_OPPORTUNITY', score, f'High opportunity score: {score:.3f}'))
        
        # No bid opportunities
        cursor.execute('''
            SELECT lot_id, retail_price FROM all_lots 
            WHERE current_bid = 0 AND retail_price > 100
            ORDER BY retail_price DESC 
            LIMIT 15
        ''')
        no_bid_opportunities = cursor.fetchall()
        
        for lot_id, retail_price in no_bid_opportunities:
            cursor.execute('''
                INSERT INTO best_deals (lot_id, deal_type, score, reason)
                VALUES (?, ?, ?, ?)
            ''', (lot_id, 'NO_BID_OPPORTUNITY', retail_price, f'No bids on ${retail_price:.2f} item'))
        
        # Exceptional discounts
        cursor.execute('''
            SELECT lot_id, discount_percentage FROM all_lots 
            WHERE discount_percentage >= 80 
            ORDER BY discount_percentage DESC 
            LIMIT 15
        ''')
        exceptional_discounts = cursor.fetchall()
        
        for lot_id, discount_pct in exceptional_discounts:
            cursor.execute('''
                INSERT INTO best_deals (lot_id, deal_type, score, reason)
                VALUES (?, ?, ?, ?)
            ''', (lot_id, 'EXCEPTIONAL_DISCOUNT', discount_pct, f'{discount_pct:.1f}% discount'))
        
        # Premium brand deals
        cursor.execute('''
            SELECT lot_id, opportunity_score FROM all_lots 
            WHERE (title LIKE '%Apple%' OR title LIKE '%Sony%' OR title LIKE '%Samsung%' 
                   OR title LIKE '%Nintendo%' OR title LIKE '%Dyson%' OR title LIKE '%Bose%')
            AND opportunity_score > 0.6
            ORDER BY opportunity_score DESC 
            LIMIT 15
        ''')
        premium_deals = cursor.fetchall()
        
        for lot_id, score in premium_deals:
            cursor.execute('''
                INSERT INTO best_deals (lot_id, deal_type, score, reason)
                VALUES (?, ?, ?, ?)
            ''', (lot_id, 'PREMIUM_BRAND_DEAL', score, f'Premium brand with {score:.3f} score'))
        
        conn.commit()
        conn.close()
    
    def generate_comprehensive_report(self) -> str:
        """Generate comprehensive warehouse scanning report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Summary statistics
        cursor.execute('SELECT COUNT(*) FROM all_lots')
        total_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM all_lots WHERE current_bid = 0')
        no_bid_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(discount_percentage) FROM all_lots WHERE discount_percentage > 0')
        avg_discount = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(retail_price) FROM all_lots')
        total_retail_value = cursor.fetchone()[0] or 0
        
        # Best deals by category
        cursor.execute('''
            SELECT bd.deal_type, COUNT(*) as count, AVG(bd.score) as avg_score
            FROM best_deals bd
            GROUP BY bd.deal_type
            ORDER BY count DESC
        ''')
        deal_categories = cursor.fetchall()
        
        # Top opportunities
        cursor.execute('''
            SELECT al.title, al.retail_price, al.current_bid, al.discount_percentage, 
                   al.opportunity_score, al.location, al.lot_id
            FROM all_lots al
            JOIN best_deals bd ON al.lot_id = bd.lot_id
            WHERE bd.deal_type = 'TOP_OPPORTUNITY'
            ORDER BY al.opportunity_score DESC
            LIMIT 10
        ''')
        top_opportunities = cursor.fetchall()
        
        # Warehouse breakdown
        cursor.execute('''
            SELECT location, COUNT(*) as count, AVG(discount_percentage) as avg_discount
            FROM all_lots
            GROUP BY location
            ORDER BY count DESC
        ''')
        warehouse_stats = cursor.fetchall()
        
        conn.close()
        
        # Generate report
        report = f"""
🏭 COMPREHENSIVE WAREHOUSE SCANNING REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 SUMMARY STATISTICS
Total Lots Discovered: {total_lots:,}
No Bid Opportunities: {no_bid_lots:,}
Average Discount: {avg_discount:.1f}%
Total Retail Value: ${total_retail_value:,.2f}

🏆 BEST DEAL CATEGORIES
"""
        
        for deal_type, count, avg_score in deal_categories:
            report += f"• {deal_type.replace('_', ' ').title()}: {count} deals (avg score: {avg_score:.3f})\n"
        
        report += f"""
🎯 TOP 10 OPPORTUNITIES
"""
        
        for i, (title, retail, current_bid, discount_pct, score, location, lot_id) in enumerate(top_opportunities, 1):
            clean_lot_id = lot_id.replace('mac_lot_', '')
            report += f"""
{i:2d}. {title[:50]}{'...' if len(title) > 50 else ''}
    Retail: ${retail:.2f} | Current Bid: ${current_bid:.2f} | Discount: {discount_pct:.1f}%
    Opportunity Score: {score:.3f} | Location: {location}
    🔗 Link: https://mac.bid/lot/{clean_lot_id}
"""
        
        report += f"""
🏭 WAREHOUSE BREAKDOWN
"""
        
        for location, count, avg_discount in warehouse_stats:
            report += f"• {location}: {count:,} lots (avg {avg_discount:.1f}% discount)\n"
        
        return report
    
    async def run_comprehensive_scan(self):
        """Run the complete comprehensive warehouse scan."""
        print("🚀 STARTING COMPREHENSIVE WAREHOUSE SCAN")
        print("=" * 60)
        
        # Step 1: Discover all lots
        all_lots = await self.discover_all_lots()
        
        if not all_lots:
            print("❌ No lots discovered")
            return
        
        # Step 2: Calculate deal metrics and store data
        print(f"\n💰 ANALYZING {len(all_lots)} LOTS FOR DEAL METRICS")
        print("-" * 45)
        
        for i, lot in enumerate(all_lots, 1):
            deal_metrics = self.calculate_deal_metrics(lot)
            self.store_lot_data(lot, deal_metrics)
            
            if i % 100 == 0:
                progress = (i / len(all_lots)) * 100
                print(f"   Progress: {progress:.1f}% ({i}/{len(all_lots)} lots analyzed)")
        
        print("✅ All lots analyzed and stored")
        
        # Step 3: Identify best deals
        print(f"\n🎯 IDENTIFYING BEST DEALS")
        print("-" * 25)
        self.identify_best_deals()
        print("✅ Best deals identified and categorized")
        
        # Step 4: Generate comprehensive report
        print(f"\n📊 GENERATING COMPREHENSIVE REPORT")
        print("-" * 35)
        report = self.generate_comprehensive_report()
        
        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'comprehensive_warehouse_scan_{timestamp}.txt'
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(report)
        print(f"\n📄 Report saved to: {report_file}")
        print(f"📊 Database saved to: {self.db_path}")
        
        return report

async def main():
    """Main function to run comprehensive warehouse scanning."""
    scanner = ComprehensiveWarehouseScanner()
    await scanner.run_comprehensive_scan()

if __name__ == "__main__":
    asyncio.run(main()) 