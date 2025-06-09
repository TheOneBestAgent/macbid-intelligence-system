#!/usr/bin/env python3
"""
🔐 AUTHENTICATED 37K+ DISCOVERY SCANNER
Logs in first to bypass API limitations and discover all available lots
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime
import os
from pathlib import Path

class Authenticated37KDiscoveryScanner:
    def __init__(self):
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        self.discovered_lots = {}
        self.seen_lot_ids = set()
        self.session = None
        self.authenticated = False
        
        # Load credentials from existing system
        self.credentials = self.load_stored_credentials()
        
        # Comprehensive search terms for authenticated access
        self.comprehensive_terms = [
            # Electronics & Tech
            "laptop", "computer", "tablet", "ipad", "macbook", "chromebook", "monitor", 
            "tv", "television", "smart", "gaming", "xbox", "playstation", "nintendo",
            "phone", "iphone", "samsung", "android", "pixel", "dell", "hp", "lenovo",
            "asus", "acer", "microsoft", "surface", "imac", "mac", "pc",
            
            # Audio/Video
            "headphones", "earbuds", "speaker", "soundbar", "beats", "sony", "bose", 
            "airpods", "camera", "canon", "nikon", "gopro", "lens", "jbl", "skullcandy",
            "sennheiser", "audio", "stereo", "bluetooth", "wireless", "noise",
            
            # Appliances
            "refrigerator", "washer", "dryer", "dishwasher", "microwave", "oven", 
            "air fryer", "dyson", "kitchenaid", "vitamix", "blender", "fridge",
            "freezer", "stove", "range", "cooktop", "hood", "disposal", "ice maker",
            
            # Tools & Equipment
            "drill", "saw", "hammer", "wrench", "toolbox", "dewalt", "milwaukee", 
            "makita", "craftsman", "tool", "ryobi", "black decker", "bosch",
            "circular", "miter", "impact", "driver", "grinder", "sander",
            
            # Home & Garden
            "furniture", "chair", "desk", "table", "sofa", "bed", "mattress", 
            "outdoor", "grill", "patio", "garden", "couch", "sectional", "recliner",
            "dining", "bedroom", "living", "office", "cabinet", "dresser",
            
            # Fitness & Sports
            "treadmill", "bike", "weights", "dumbbells", "yoga", "fitness", 
            "exercise", "peloton", "nordictrack", "elliptical", "rowing", "bench",
            "barbell", "kettlebell", "resistance", "cardio", "strength",
            
            # Automotive
            "car", "auto", "tire", "battery", "oil", "brake", "parts",
            "automotive", "vehicle", "motor", "engine", "transmission", "wheel",
            
            # Luxury & Jewelry
            "watch", "ring", "necklace", "bracelet", "diamond", "gold", "silver", 
            "rolex", "omega", "cartier", "tiffany", "jewelry", "pendant", "earring",
            "chain", "platinum", "gemstone", "pearl", "luxury",
            
            # Fashion & Accessories
            "bag", "purse", "wallet", "shoes", "clothing", "jacket", "coat",
            "handbag", "backpack", "luggage", "suitcase", "boots", "sneakers",
            
            # General high-value terms
            "new", "open box", "like new", "refurbished", "sealed", "unused",
            "mint", "pristine", "excellent", "perfect", "brand new",
            
            # Single letters for maximum coverage
            "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m",
            "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
            
            # Numbers
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
            
            # Common prefixes/suffixes
            "pro", "max", "mini", "ultra", "plus", "air", "lite", "xl", "xs",
            
            # Empty searches that might return everything
            "", " ", "*"
        ]
        
        self.setup_database()
    
    def load_stored_credentials(self):
        """Load credentials from the existing credential system."""
        try:
            config_file = Path.home() / '.macbid_scraper' / 'credentials.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    creds = json.load(f)
                    print(f"✅ Loaded stored credentials for: {creds.get('username', 'Unknown')}")
                    return creds
        except Exception as e:
            print(f"⚠️ Could not load stored credentials: {e}")
        
        # Fallback to environment variables
        email = os.getenv('MAC_BID_EMAIL')
        password = os.getenv('MAC_BID_PASSWORD')
        
        if email and password:
            print(f"✅ Using environment credentials for: {email}")
            return {'username': email, 'password': password}
        
        print("❌ No credentials found! Please run setup_personal_credentials.py first")
        return None
    
    def setup_database(self):
        """Setup authenticated discovery database."""
        self.db_path = 'authenticated_37k_discovery.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS authenticated_lots (
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
        print("🗄️ Authenticated 37K+ discovery database initialized")
    
    async def create_session(self):
        """Create authenticated HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=20)
        timeout = aiohttp.ClientTimeout(total=60)
        
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
    
    async def login(self):
        """Authenticate with Mac.bid to access full API."""
        if not self.credentials:
            print("❌ No credentials available for authentication")
            return False
        
        print("🔐 AUTHENTICATING WITH MAC.BID")
        print("-" * 40)
        print(f"📧 Using account: {self.credentials.get('username', 'Unknown')}")
        
        try:
            # First, get the login page to establish session
            login_url = "https://mac.bid/login"
            async with self.session.get(login_url) as response:
                if response.status == 200:
                    print("   ✅ Login page accessed successfully")
                else:
                    print(f"   ❌ Failed to access login page: {response.status}")
                    return False
            
            # Attempt login with credentials
            login_data = {
                'email': self.credentials['username'],
                'password': self.credentials['password'],
                'remember': 'on'
            }
            
            async with self.session.post(login_url, data=login_data) as response:
                if response.status == 200:
                    # Check if login was successful
                    response_text = await response.text()
                    if 'dashboard' in response_text.lower() or 'logout' in response_text.lower():
                        print("   ✅ Login successful!")
                        self.authenticated = True
                        return True
                    else:
                        print("   ⚠️ Login may have failed - checking API access...")
                        # Test API access
                        return await self.test_api_access()
                else:
                    print(f"   ❌ Login failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False
    
    async def test_api_access(self):
        """Test if we have authenticated API access."""
        try:
            url = "https://api.macdiscount.com/search?q=laptop&limit=500"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get('hits', [])
                    
                    if len(hits) > 20:  # More than unauthenticated limit
                        print(f"   ✅ Authenticated API access confirmed! ({len(hits)} results)")
                        self.authenticated = True
                        return True
                    else:
                        print(f"   ⚠️ Limited API access ({len(hits)} results)")
                        return False
                else:
                    print(f"   ❌ API test failed: HTTP {response.status}")
                    return False
        except Exception as e:
            print(f"   ❌ API test error: {e}")
            return False
    
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
            'deal_rating': deal_rating
        }
    
    async def search_authenticated(self, term, limit=1000):
        """Search using authenticated session with higher limits."""
        try:
            url = f"https://api.macdiscount.com/search?q={term}&limit={limit}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get('hits', [])
                    
                    new_lots = 0
                    for hit in hits:
                        location = hit.get('auction_location', '')
                        if any(sc_loc in location for sc_loc in self.sc_locations):
                            # Try multiple ID field names
                            lot_id = (hit.get('lot_id') or hit.get('id') or 
                                     hit.get('mac_lot_id') or hit.get('_id') or '')
                            
                            if lot_id and lot_id not in self.seen_lot_ids:
                                # Enhance with analytics
                                scores = self.calculate_scores(hit)
                                hit.update(scores)
                                
                                self.seen_lot_ids.add(lot_id)
                                self.discovered_lots[lot_id] = hit
                                new_lots += 1
                    
                    return len(hits), new_lots
                else:
                    return 0, 0
                    
        except Exception:
            return 0, 0
    
    async def run_authenticated_discovery(self):
        """Run authenticated 37K+ discovery scan."""
        print("🔐 AUTHENTICATED 37K+ DISCOVERY SCANNER")
        print("=" * 80)
        print("Logging in first to bypass API limitations and discover ALL lots")
        print()
        
        if not self.credentials:
            print("❌ No credentials available. Please run setup_personal_credentials.py first")
            return []
        
        await self.create_session()
        
        # Step 1: Authenticate
        if not await self.login():
            print("❌ Authentication failed. Proceeding with unauthenticated access...")
            print("   (Results will be limited)")
        
        print(f"\n🎯 {'AUTHENTICATED' if self.authenticated else 'UNAUTHENTICATED'} COMPREHENSIVE DISCOVERY")
        print("-" * 70)
        print(f"📊 Scanning {len(self.comprehensive_terms)} search terms")
        print()
        
        total_api_hits = 0
        
        for i, term in enumerate(self.comprehensive_terms, 1):
            print(f"   [{i:3d}/{len(self.comprehensive_terms)}] Scanning '{term}'...")
            
            api_hits, new_lots = await self.search_authenticated(term)
            total_api_hits += api_hits
            
            if new_lots > 0:
                print(f"      ✅ Found {new_lots} NEW SC lots! (Total: {len(self.discovered_lots):,})")
            
            if api_hits > 50:  # Show when we get good API responses
                print(f"      📊 API returned {api_hits} total results")
            
            if i % 25 == 0:
                progress = (i / len(self.comprehensive_terms)) * 100
                print(f"      🚀 Progress: {progress:.1f}% - Total discovered: {len(self.discovered_lots):,}")
                print(f"      📈 Total API hits so far: {total_api_hits:,}")
            
            # Adaptive rate limiting
            if self.authenticated:
                await asyncio.sleep(0.1)  # Faster for authenticated users
            else:
                await asyncio.sleep(0.2)  # Slower if not authenticated
        
        await self.session.close()
        
        print(f"\n🎯 {'AUTHENTICATED' if self.authenticated else 'UNAUTHENTICATED'} 37K+ DISCOVERY COMPLETE")
        print("=" * 60)
        print(f"✅ Total unique lots discovered: {len(self.discovered_lots):,}")
        print(f"📊 Total API responses processed: {total_api_hits:,}")
        
        if len(self.discovered_lots) > 1000:
            print(f"🎉 SUCCESS! Broke through the 1K barrier!")
        
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
                INSERT OR REPLACE INTO authenticated_lots 
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
        """Generate authenticated discovery report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM authenticated_lots')
        total_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM authenticated_lots WHERE current_bid = 0')
        no_bid_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(retail_price) FROM authenticated_lots')
        total_retail_value = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT AVG(discount_percentage) FROM authenticated_lots WHERE discount_percentage > 0')
        avg_discount = cursor.fetchone()[0] or 0
        
        # Warehouse breakdown
        cursor.execute('''
            SELECT location, COUNT(*) as lot_count, SUM(retail_price) as total_value
            FROM authenticated_lots
            GROUP BY location
            ORDER BY lot_count DESC
        ''')
        warehouse_stats = cursor.fetchall()
        
        # Top opportunities
        cursor.execute('''
            SELECT title, retail_price, current_bid, discount_percentage, 
                   opportunity_score, location, lot_id
            FROM authenticated_lots
            WHERE opportunity_score > 0.8
            ORDER BY opportunity_score DESC, retail_price DESC
            LIMIT 50
        ''')
        top_opportunities = cursor.fetchall()
        
        conn.close()
        
        print(f"""
🔐 {'AUTHENTICATED' if self.authenticated else 'UNAUTHENTICATED'} 37K+ DISCOVERY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 DISCOVERY SUMMARY
Total Lots Discovered: {total_lots:,}
No Bid Opportunities: {no_bid_lots:,}
Average Discount: {avg_discount:.1f}%
Total Retail Value: ${total_retail_value:,.2f}

🏭 WAREHOUSE BREAKDOWN""")
        
        for location, count, value in warehouse_stats:
            print(f"• {location}: {count:,} lots (${value:,.2f} value)")
        
        print(f"""
🏆 TOP 50 OPPORTUNITIES""")
        
        for i, (title, retail, current_bid, discount_pct, score, location, lot_id) in enumerate(top_opportunities, 1):
            clean_lot_id = str(lot_id).replace('mac_lot_', '')
            print(f"""
{i:2d}. {title[:60]}{'...' if len(title) > 60 else ''}
    Retail: ${retail:.2f} | Current Bid: ${current_bid:.2f} | Discount: {discount_pct:.1f}%
    Opportunity Score: {score:.3f} | Location: {location}
    🔗 Link: https://mac.bid/lot/{clean_lot_id}""")
        
        print(f"\n📊 Database saved to: {self.db_path}")

async def main():
    scanner = Authenticated37KDiscoveryScanner()
    await scanner.run_authenticated_discovery()

if __name__ == "__main__":
    asyncio.run(main()) 