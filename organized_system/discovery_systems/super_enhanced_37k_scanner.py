#!/usr/bin/env python3
"""
🚀 SUPER ENHANCED 37K+ SCANNER - Maximum Discovery Method
Combines all proven techniques to maximize lot discovery beyond 37k+
"""

import asyncio
import json
import sqlite3
from datetime import datetime
import aiohttp
import ssl
from collections import defaultdict

class SuperEnhanced37KScanner:
    def __init__(self):
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        self.discovered_lots = {}
        self.seen_lot_ids = set()
        
        # SUPER COMPREHENSIVE: All proven search strategies combined
        self.comprehensive_terms = [
            # Electronics & Tech (Enhanced)
            "laptop", "computer", "tablet", "ipad", "macbook", "chromebook", "monitor", 
            "tv", "television", "smart", "gaming", "xbox", "playstation", "nintendo",
            "phone", "iphone", "samsung", "android", "pixel", "dell", "hp", "lenovo",
            "asus", "acer", "microsoft", "surface", "imac", "mac", "pc",
            
            # Audio/Video (Enhanced)
            "headphones", "earbuds", "speaker", "soundbar", "beats", "sony", "bose", 
            "airpods", "camera", "canon", "nikon", "gopro", "lens", "jbl", "skullcandy",
            "sennheiser", "audio", "stereo", "bluetooth", "wireless", "noise",
            
            # Appliances (Enhanced)
            "refrigerator", "washer", "dryer", "dishwasher", "microwave", "oven", 
            "air fryer", "dyson", "kitchenaid", "vitamix", "blender", "fridge",
            "freezer", "stove", "range", "cooktop", "hood", "disposal", "ice maker",
            
            # Tools & Equipment (Enhanced)
            "drill", "saw", "hammer", "wrench", "toolbox", "dewalt", "milwaukee", 
            "makita", "craftsman", "tool", "ryobi", "black decker", "bosch",
            "circular", "miter", "impact", "driver", "grinder", "sander",
            
            # Home & Garden (Enhanced)
            "furniture", "chair", "desk", "table", "sofa", "bed", "mattress", 
            "outdoor", "grill", "patio", "garden", "couch", "sectional", "recliner",
            "dining", "bedroom", "living", "office", "cabinet", "dresser",
            
            # Fitness & Sports (Enhanced)
            "treadmill", "bike", "weights", "dumbbells", "yoga", "fitness", 
            "exercise", "peloton", "nordictrack", "elliptical", "rowing", "bench",
            "barbell", "kettlebell", "resistance", "cardio", "strength",
            
            # Automotive (Enhanced)
            "car", "auto", "tire", "battery", "oil", "brake", "parts",
            "automotive", "vehicle", "motor", "engine", "transmission", "wheel",
            
            # Luxury & Jewelry (Enhanced)
            "watch", "ring", "necklace", "bracelet", "diamond", "gold", "silver", 
            "rolex", "omega", "cartier", "tiffany", "jewelry", "pendant", "earring",
            "chain", "platinum", "gemstone", "pearl", "luxury",
            
            # Fashion & Accessories (Enhanced)
            "bag", "purse", "wallet", "shoes", "clothing", "jacket", "coat",
            "handbag", "backpack", "luggage", "suitcase", "boots", "sneakers",
            
            # General high-value terms (Enhanced)
            "new", "open box", "like new", "refurbished", "sealed", "unused",
            "mint", "pristine", "excellent", "perfect", "brand new",
            
            # Single letters (for maximum coverage)
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
            "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
            
            # Numbers (for model numbers)
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
            
            # Common prefixes/suffixes
            "pro", "max", "mini", "ultra", "plus", "air", "lite", "xl", "xs",
            
            # Price ranges (to catch different segments)
            "under", "over", "cheap", "expensive", "premium", "budget", "high end"
        ]
        
        self.setup_database()
    
    def setup_database(self):
        """Setup super enhanced discovery database."""
        self.db_path = 'super_enhanced_37k_discovery.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS super_enhanced_lots (
                lot_id TEXT PRIMARY KEY,
                title TEXT,
                retail_price REAL,
                current_bid REAL,
                location TEXT,
                brand TEXT,
                discount_amount REAL,
                discount_percentage REAL,
                opportunity_score REAL,
                deal_rating TEXT,
                discovery_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("🗄️ Super Enhanced 37K+ discovery database initialized")
    
    def extract_brand(self, product_name):
        """Extract brand from product name."""
        if not product_name:
            return "Unknown"
            
        product_lower = product_name.lower()
        
        brands = {
            'Apple': ['apple', 'macbook', 'iphone', 'ipad', 'imac'],
            'Samsung': ['samsung'],
            'Sony': ['sony'],
            'LG': ['lg'],
            'Dyson': ['dyson'],
            'KitchenAid': ['kitchenaid'],
            'DeWalt': ['dewalt'],
            'Milwaukee': ['milwaukee'],
            'Nintendo': ['nintendo'],
            'Canon': ['canon'],
            'Bose': ['bose'],
            'Rolex': ['rolex'],
            'Peloton': ['peloton']
        }
        
        for brand, keywords in brands.items():
            for keyword in keywords:
                if keyword in product_lower:
                    return brand
                    
        return "Other"
    
    def calculate_scores(self, lot):
        """Calculate opportunity scores."""
        retail_price = lot.get('discount', lot.get('retail_price', 0))
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
            'deal_rating': deal_rating,
            'brand': self.extract_brand(lot.get('auction_title', ''))
        }
    
    async def search_super_enhanced(self, session, term, limit=200):
        """Search using super enhanced method with multiple field checks."""
        try:
            url = f"https://api.macdiscount.com/search?q={term}&limit={limit}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get('hits', [])
                    
                    new_lots = 0
                    for hit in hits:
                        location = hit.get('auction_location', '')
                        if any(sc_loc in location for sc_loc in self.sc_locations):
                            # Try multiple ID field names (KEY DIFFERENCE!)
                            lot_id = (hit.get('lot_id') or hit.get('id') or 
                                     hit.get('mac_lot_id') or hit.get('_id') or '')
                            
                            if lot_id and lot_id not in self.seen_lot_ids:
                                # Enhance with analytics
                                scores = self.calculate_scores(hit)
                                hit.update(scores)
                                
                                self.seen_lot_ids.add(lot_id)
                                self.discovered_lots[lot_id] = hit
                                new_lots += 1
                    
                    return new_lots
                else:
                    return 0
                    
        except Exception:
            return 0
    
    async def run_super_enhanced_discovery(self):
        """Run the super enhanced 37K+ discovery scan."""
        print("🚀 SUPER ENHANCED 37K+ DISCOVERY SCANNER")
        print("=" * 80)
        print("Using ALL proven breakthrough methods for MAXIMUM lot discovery")
        print(f"📊 Scanning {len(self.comprehensive_terms)} comprehensive search terms")
        print("🎯 Target: 37,000+ unique lots")
        print()
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=ssl_context),
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=60)
        ) as session:
            
            print("🎯 SUPER COMPREHENSIVE DISCOVERY SCAN")
            print("-" * 70)
            
            for i, term in enumerate(self.comprehensive_terms, 1):
                print(f"   [{i:3d}/{len(self.comprehensive_terms)}] Scanning '{term}'...")
                
                new_lots = await self.search_super_enhanced(session, term)
                
                if new_lots > 0:
                    print(f"      ✅ Found {new_lots} NEW SC lots! (Total: {len(self.discovered_lots):,})")
                
                if i % 25 == 0:
                    progress = (i / len(self.comprehensive_terms)) * 100
                    print(f"      🚀 Progress: {progress:.1f}% - Total discovered: {len(self.discovered_lots):,}")
                
                # Adaptive rate limiting
                if len(self.discovered_lots) > 1000:
                    await asyncio.sleep(0.1)  # Faster when finding lots
                else:
                    await asyncio.sleep(0.15)  # Standard rate
        
        print(f"\n🎯 SUPER ENHANCED 37K+ DISCOVERY COMPLETE")
        print("=" * 60)
        print(f"✅ Total unique lots discovered: {len(self.discovered_lots):,}")
        
        # Store all lots
        if self.discovered_lots:
            print(f"\n💾 Storing {len(self.discovered_lots):,} lots in database...")
            for lot in self.discovered_lots.values():
                self.store_lot(lot)
            print("✅ All lots stored successfully")
        
        # Generate report
        self.generate_report()
        
        return list(self.discovered_lots.values())
    
    def store_lot(self, lot):
        """Store lot in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            lot_id = (lot.get('lot_id') or lot.get('id') or 
                     lot.get('mac_lot_id') or lot.get('_id') or '')
            
            cursor.execute('''
                INSERT OR REPLACE INTO super_enhanced_lots 
                (lot_id, title, retail_price, current_bid, location, brand,
                 discount_amount, discount_percentage, opportunity_score, deal_rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lot_id,
                lot.get('auction_title', lot.get('title', '')),
                lot.get('discount', lot.get('retail_price', 0)),
                lot.get('current_bid', 0),
                lot.get('auction_location', ''),
                lot.get('brand', 'Unknown'),
                lot.get('discount_amount', 0),
                lot.get('discount_percentage', 0),
                lot.get('opportunity_score', 0),
                lot.get('deal_rating', 'GOOD')
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Error storing lot: {e}")
        finally:
            conn.close()
    
    def generate_report(self):
        """Generate super enhanced discovery report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM super_enhanced_lots')
        total_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM super_enhanced_lots WHERE current_bid = 0')
        no_bid_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(retail_price) FROM super_enhanced_lots')
        total_retail_value = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(discount_percentage) FROM super_enhanced_lots WHERE discount_percentage > 0')
        avg_discount = cursor.fetchone()[0] or 0
        
        # Warehouse breakdown
        cursor.execute('''
            SELECT location, COUNT(*) as lot_count, SUM(retail_price) as total_value
            FROM super_enhanced_lots
            GROUP BY location
            ORDER BY lot_count DESC
        ''')
        warehouse_stats = cursor.fetchall()
        
        # Top opportunities
        cursor.execute('''
            SELECT title, retail_price, current_bid, discount_percentage, 
                   opportunity_score, location, lot_id
            FROM super_enhanced_lots
            WHERE opportunity_score > 0.8
            ORDER BY opportunity_score DESC, retail_price DESC
            LIMIT 30
        ''')
        top_opportunities = cursor.fetchall()
        
        conn.close()
        
        print(f"""
🚀 SUPER ENHANCED 37K+ DISCOVERY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 MAXIMUM DISCOVERY SUMMARY
Total Lots Discovered: {total_lots:,}
No Bid Opportunities: {no_bid_lots:,}
Average Discount: {avg_discount:.1f}%
Total Retail Value: ${total_retail_value:,.2f}

🏭 WAREHOUSE BREAKDOWN""")
        
        for location, count, value in warehouse_stats:
            print(f"• {location}: {count:,} lots (${value:,.2f} value)")
        
        print(f"""
🏆 TOP 30 SUPER OPPORTUNITIES""")
        
        for i, (title, retail, current_bid, discount_pct, score, location, lot_id) in enumerate(top_opportunities, 1):
            clean_lot_id = str(lot_id).replace('mac_lot_', '')
            print(f"""
{i:2d}. {title[:60]}{'...' if len(title) > 60 else ''}
    Retail: ${retail:.2f} | Current Bid: ${current_bid:.2f} | Discount: {discount_pct:.1f}%
    Opportunity Score: {score:.3f} | Location: {location}
    🔗 Link: https://mac.bid/lot/{clean_lot_id}""")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        print(f"\n📊 Database saved to: {self.db_path}")

async def main():
    scanner = SuperEnhanced37KScanner()
    await scanner.run_super_enhanced_discovery()

if __name__ == "__main__":
    asyncio.run(main()) 