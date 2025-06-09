#!/usr/bin/env python3
"""
Next.js Integration System for Mac.bid
Combines Typesense discovery with detailed Next.js lot analysis
"""

import requests
import json
import sqlite3
from datetime import datetime
import os
import sys
import asyncio
import aiohttp
import time
from urllib.parse import urlparse, parse_qs

class NextJSIntegrationSystem:
    def __init__(self):
        self.session = requests.Session()
        self.db_path = "databases/nextjs_integration.db"
        self.setup_database()
        
        # Typesense API configuration
        self.typesense_url = "https://xczkhpt94lod37gqp.a1.typesense.net/multi_search"
        self.typesense_key = "jxX8RU6YVOkm9esgd9buaYjulIWv6N52"
        
        # Next.js configuration
        self.nextjs_build_id = "AslxUFb4wF5GgYRFXlpoC"
        
        # Set up session headers for Next.js
        self.session.headers.update({
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.6',
            'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'x-nextjs-data': '1'
        })
        
        # Initialize authentication (use cookies for now)
        self.authenticated = True  # Assume cookies work
        self.set_cookies()
        
    def setup_database(self):
        """Setup comprehensive database"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced lot details with both Typesense and Next.js data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enhanced_lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER UNIQUE,
                auction_id INTEGER,
                lot_number TEXT,
                product_name TEXT,
                title TEXT,
                description TEXT,
                retail_price REAL,
                instant_win_price REAL,
                current_bid REAL,
                total_bids INTEGER,
                unique_bidders INTEGER,
                condition_name TEXT,
                warehouse_location TEXT,
                dimensions TEXT,
                upc TEXT,
                model TEXT,
                brand TEXT,
                category TEXT,
                is_tested INTEGER,
                tested_note TEXT,
                damaged_note TEXT,
                is_partial INTEGER,
                partial_note TEXT,
                expected_close_date TEXT,
                is_open INTEGER,
                is_transferrable INTEGER,
                buyers_assurance_cost REAL,
                image_url TEXT,
                deal_score REAL,
                discount_percentage REAL,
                value_rating TEXT,
                opportunity_score REAL,
                risk_factors TEXT,
                recommendation TEXT,
                data_source TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Discovery queue for lots to analyze
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discovery_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                auction_id INTEGER,
                lot_id TEXT,
                lot_number TEXT,
                product_name TEXT,
                status TEXT DEFAULT 'PENDING',
                priority INTEGER DEFAULT 1,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Analysis results summary
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                total_discovered INTEGER,
                total_analyzed INTEGER,
                strong_buy_count INTEGER,
                buy_count INTEGER,
                consider_count INTEGER,
                avoid_count INTEGER,
                avg_deal_score REAL,
                avg_discount REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def set_cookies(self):
        """Set authentication cookies"""
        cookies = {
            '__stripe_mid': 'b1219cc5-9a1f-4e9b-9b3b-ce16a3d90ba32b7fa4',
            'CookieConsent': 'true',
            'ab.storage.deviceId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3A6557c69b-3239-8d82-7b30-ec5862a4de57%7Ce%3Aundefined%7Cc%3A1747345668914%7Cl%3A1749267987617',
            'ab.storage.userId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3A2710619%7Ce%3Aundefined%7Cc%3A1749188938629%7Cl%3A1749267987617',
            '__stripe_sid': '82edccd6-9b05-4a36-a118-e155bd9212b7ec69fb',
            'mp_78faade7af6b4f2ee5e1af36d8ac6232_mixpanel': '%7B%22distinct_id%22%3A%202710619%2C%22%24device_id%22%3A%20%22196d5eae0323e9-06ed80c653d2808-19525636-13c680-196d5eae0323e9%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22platform%22%3A%20%22website%22%2C%22selected_locations%22%3A%20%5B%0A%20%20%20%20%22Rock%20Hill%22%2C%0A%20%20%20%20%22Gastonia%22%0A%5D%2C%22%24user_id%22%3A%202710619%2C%22active_items%22%3A%20%5B%0A%20%20%20%20%7B%22id%22%3A%2046608657%2C%22invoice_id%22%3A%2018714030%2C%22box_size%22%3A%20%22large%22%2C%22warehouse_location%22%3A%20%22ANL-D-BIN-55%22%2C%22removal_container%22%3A%20null%2C%22product_name%22%3A%20%22KOKISO%20metal%20%22%2C%22status%22%3A%20%22PENDING-TRANSFER%22%2C%22boxes%22%3A%201%2C%22note%22%3A%20null%2C%22current_location_id%22%3A%2038%2C%22allow_transfers%22%3A%201%2C%22allow_shipping%22%3A%200%2C%22is_turbo%22%3A%200%2C%22free_transfers%22%3A%200%2C%22auction_number%22%3A%20%22ANL2506-05-A2%22%2C%22auction_abandon_date%22%3A%20%222025-06-10T18%3A00%3A00.000Z%22%2C%22abandon_date%22%3A%20null%2C%22lot_number%22%3A%20%221726Z%22%2C%22lot_id%22%3A%2035490378%2C%22has_buyer_assurance%22%3A%200%2C%22item_price%22%3A%205.67%2C%22cover_image%22%3A%20%22https%3A%2F%2Fm.media-amazon.com%2Fimages%2FI%2F71fm%2BEdRyKL.jpg%22%2C%22grand_total%22%3A%205.67%2C%22date_paid%22%3A%20%222025-06-06T09%3A20%3A50.000Z%22%2C%22transfer_id%22%3A%206229971%2C%22start_location_code%22%3A%20%22ANL%22%2C%22dest_location_code%22%3A%20%22RHA%22%2C%22start_location_id%22%3A%2038%2C%22dest_location_id%22%3A%2028%2C%22grouping_id%22%3A%20%2218714030_200_35872237%22%2C%22auction_lot_deadline%22%3A%20null%7D%0A%5D%2C%22mac_bucks_balance%22%3A%200%2C%22mac_bucks_gift_balance%22%3A%200%2C%22active_membership%22%3A%20%7B%22id%22%3A%20123339%2C%22date_created%22%3A%20%222025-05-29T18%3A11%3A59.000Z%22%2C%22membership_plan%22%3A%20%22STANDARD%22%2C%22customer_id%22%3A%202710619%2C%22bill_period%22%3A%20%22MONTHLY%22%2C%22bill_amount%22%3A%209.99%2C%22date_cancelled%22%3A%20null%2C%22external_id%22%3A%20%22sub_1RUFc8DhtPPAHVyel4iCCWV7%22%2C%22cancel_reason%22%3A%20null%2C%22stripe_customer_id%22%3A%20%22cus_S6Y0gK006usyW7%22%2C%22date_updated%22%3A%20null%7D%2C%22watchlist_count%22%3A%207%2C%22onboarding%22%3A%20true%7D',
            'ab.storage.sessionId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3Aa18c4004-ac5d-06ae-84af-39127b94f2a6%7Ce%3A1749269831396%7Cc%3A1749267987616%7Cl%3A1749268031396'
        }
        
        self.session.cookies.update(cookies)
    
    async def setup_authentication(self):
        """Setup authentication using the centralized auth system"""
        try:
            # Import the authentication system
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from core_systems.authentication_manager import require_authentication, get_authenticated_headers
            
            # Get authenticated session (async)
            auth_manager = await require_authentication()
            authenticated_headers = get_authenticated_headers()
            
            # Update session with authenticated headers
            self.session.headers.update(authenticated_headers)
            
            self.authenticated = True
            print("✅ NextJS system authenticated successfully")
            
        except Exception as e:
            print(f"⚠️  NextJS authentication failed: {e}")
            print("   Continuing with cookie-based authentication")
            self.authenticated = False
            # Fall back to cookie-based auth
            self.set_cookies()
    
    def discover_lots_typesense(self, max_pages=5, target_brands=None):
        """Discover lots using Typesense API"""
        print(f"🔍 DISCOVERING LOTS via Typesense API (max {max_pages} pages)")
        
        if target_brands is None:
            target_brands = ["Apple", "Sony", "Samsung", "Nintendo", "Dyson", "Bose", "DeWalt", "Milwaukee"]
        
        discovered_lots = []
        
        for page in range(1, max_pages + 1):
            print(f"📄 Page {page}/{max_pages}")
            
            # Build search query for premium brands
            brand_filter = " || ".join([f'product_name:*{brand}*' for brand in target_brands])
            
            payload = {
                "searches": [
                    {
                        "collection": "lots",
                        "q": "*",
                        "query_by": "product_name,description",
                        "filter_by": f"auction_location:=[Anderson,Gastonia,Greenville,Rock Hill,Spartanburg] && ({brand_filter})",
                        "sort_by": "retail_price:desc",
                        "per_page": 250,
                        "page": page
                    }
                ]
            }
            
            try:
                response = requests.post(
                    self.typesense_url,
                    headers={
                        'X-TYPESENSE-API-KEY': self.typesense_key,
                        'Content-Type': 'application/json'
                    },
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    if results and 'hits' in results[0]:
                        hits = results[0]['hits']
                        print(f"  ✅ Found {len(hits)} lots")
                        
                        for hit in hits:
                            doc = hit['document']
                            lot_info = {
                                'auction_id': doc.get('auction_id'),
                                'lot_id': doc.get('lot_id'),
                                'lot_number': doc.get('lot_number'),
                                'product_name': doc.get('product_name'),
                                'retail_price': doc.get('retail_price', 0),
                                'brand': self.extract_brand(doc.get('product_name', '')),
                                'category': doc.get('category', 'Unknown')
                            }
                            discovered_lots.append(lot_info)
                        
                        if len(hits) < 250:
                            print(f"  📋 Reached end of results")
                            break
                    else:
                        print(f"  ❌ No results on page {page}")
                        break
                else:
                    print(f"  ❌ Error: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"  ❌ Exception: {e}")
                break
        
        print(f"🎯 DISCOVERY COMPLETE: {len(discovered_lots)} lots found")
        return discovered_lots
    
    def extract_brand(self, product_name):
        """Extract brand from product name"""
        brands = ["Apple", "Sony", "Samsung", "Nintendo", "Dyson", "Bose", "DeWalt", "Milwaukee", "ECOVACS"]
        product_upper = product_name.upper()
        
        for brand in brands:
            if brand.upper() in product_upper:
                return brand
        
        return "Unknown"
    
    def queue_lots_for_analysis(self, discovered_lots):
        """Queue discovered lots for detailed analysis"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        queued_count = 0
        for lot in discovered_lots:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO discovery_queue 
                    (auction_id, lot_id, lot_number, product_name, priority)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    lot['auction_id'],
                    lot['lot_id'],
                    lot['lot_number'],
                    lot['product_name'],
                    self.calculate_priority(lot)
                ))
                queued_count += 1
            except Exception as e:
                print(f"Error queuing lot {lot.get('lot_number')}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"📋 QUEUED: {queued_count} lots for detailed analysis")
        return queued_count
    
    def calculate_priority(self, lot):
        """Calculate analysis priority (1=highest, 5=lowest)"""
        retail_price = lot.get('retail_price', 0)
        brand = lot.get('brand', 'Unknown')
        
        # High-value items get priority
        if retail_price >= 1000:
            priority = 1
        elif retail_price >= 500:
            priority = 2
        elif retail_price >= 200:
            priority = 3
        elif retail_price >= 100:
            priority = 4
        else:
            priority = 5
        
        # Premium brands get boost
        premium_brands = ["Apple", "Sony", "Samsung", "Nintendo", "Dyson"]
        if brand in premium_brands:
            priority = max(1, priority - 1)
        
        return priority
    
    def fetch_nextjs_lot_data(self, auction_id, lot_id):
        """Fetch detailed lot data from Next.js by parsing HTML page"""
        import re
        import json
        
        # Fetch the lot page HTML
        lot_page_url = f"https://www.mac.bid/lot/mac_lot_{lot_id}"
        
        try:
            response = self.session.get(lot_page_url, timeout=15)
            if response.status_code == 200:
                html_content = response.text
                
                # Extract __NEXT_DATA__ script content
                next_data_pattern = r'<script id="__NEXT_DATA__" type="application/json">([^<]+)</script>'
                next_data_match = re.search(next_data_pattern, html_content)
                
                if next_data_match:
                    try:
                        next_data = json.loads(next_data_match.group(1))
                        
                        # Navigate to lot data
                        if 'props' in next_data and 'pageProps' in next_data['props']:
                            page_props = next_data['props']['pageProps']
                            
                            # Check for both 'activeLot' and 'currentLot'
                            lot_data = None
                            if 'activeLot' in page_props and page_props['activeLot']:
                                lot_data = page_props['activeLot']
                            elif 'currentLot' in page_props and page_props['currentLot']:
                                lot_data = page_props['currentLot']
                            
                            if lot_data and isinstance(lot_data, dict) and lot_data:
                                # Add NextJS-specific fields for tracking
                                lot_data['nextjs_current_bid'] = lot_data.get('winning_bid_amount', 0)
                                lot_data['nextjs_total_bids'] = lot_data.get('total_bids', 0)
                                lot_data['nextjs_unique_bidders'] = lot_data.get('unique_bidders', 0)
                                lot_data['nextjs_is_open'] = lot_data.get('is_open', False)
                                lot_data['nextjs_timestamp'] = datetime.now().isoformat()
                                return lot_data
                            
                    except json.JSONDecodeError as e:
                        print(f"Error parsing NextJS data for lot {lot_id}: {e}")
                        return None
                        
            return None
            
        except Exception as e:
            print(f"Error fetching Next.js data for lot {lot_id}: {e}")
            return None
    
    def analyze_lot_value(self, lot_data):
        """Analyze lot value and generate recommendations"""
        retail_price = lot_data.get('retail_price', 0)
        instant_win_price = lot_data.get('instant_win_price', 0)
        
        # Calculate discount
        if retail_price > 0 and instant_win_price > 0:
            discount_percentage = ((retail_price - instant_win_price) / retail_price) * 100
        else:
            discount_percentage = 0
        
        # Calculate deal score
        deal_score = min(discount_percentage, 100)
        
        # Value rating
        if discount_percentage >= 70:
            value_rating = "EXCELLENT"
        elif discount_percentage >= 50:
            value_rating = "VERY_GOOD"
        elif discount_percentage >= 30:
            value_rating = "GOOD"
        elif discount_percentage >= 15:
            value_rating = "FAIR"
        else:
            value_rating = "POOR"
        
        # Risk assessment
        risk_factors = []
        description = lot_data.get('description', '').lower()
        
        if lot_data.get('damaged_note'):
            risk_factors.append("DAMAGED")
        if lot_data.get('is_partial'):
            risk_factors.append("PARTIAL")
        if not lot_data.get('is_tested'):
            risk_factors.append("UNTESTED")
        if any(word in description for word in ['dirty', 'damaged', 'broken']):
            risk_factors.append("CONDITION_ISSUES")
        if any(word in description for word in ['moisture', 'water', 'wet']):
            risk_factors.append("MOISTURE_DAMAGE")
        
        # Competition analysis
        unique_bidders = lot_data.get('unique_bidders', 0)
        competition_factor = max(0, 100 - (unique_bidders * 15))
        
        # Opportunity score
        opportunity_score = (deal_score + competition_factor) / 2
        
        # Final recommendation
        if opportunity_score >= 80 and len(risk_factors) <= 1:
            recommendation = "STRONG_BUY"
        elif opportunity_score >= 60 and len(risk_factors) <= 2:
            recommendation = "BUY"
        elif opportunity_score >= 40:
            recommendation = "CONSIDER"
        else:
            recommendation = "AVOID"
        
        return {
            'deal_score': deal_score,
            'discount_percentage': discount_percentage,
            'value_rating': value_rating,
            'opportunity_score': opportunity_score,
            'risk_factors': ', '.join(risk_factors),
            'recommendation': recommendation
        }
    
    def process_analysis_queue(self, max_lots=50):
        """Process queued lots for detailed analysis"""
        print(f"🔬 PROCESSING ANALYSIS QUEUE (max {max_lots} lots)")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get pending lots ordered by priority
        cursor.execute('''
            SELECT auction_id, lot_id, lot_number, product_name 
            FROM discovery_queue 
            WHERE status = 'PENDING' 
            ORDER BY priority ASC, timestamp ASC 
            LIMIT ?
        ''', (max_lots,))
        
        pending_lots = cursor.fetchall()
        conn.close()
        
        if not pending_lots:
            print("📭 No lots in queue for analysis")
            return
        
        print(f"📋 Processing {len(pending_lots)} lots...")
        
        analyzed_count = 0
        recommendations = {'STRONG_BUY': 0, 'BUY': 0, 'CONSIDER': 0, 'AVOID': 0}
        
        for auction_id, lot_id, lot_number, product_name in pending_lots:
            print(f"\n🔍 Analyzing Lot {lot_number} ({product_name[:50]}...)")
            
            # Fetch detailed data
            nextjs_data = self.fetch_nextjs_lot_data(auction_id, lot_id)
            
            if nextjs_data and 'pageProps' in nextjs_data:
                active_lot = nextjs_data['pageProps'].get('activeLot', {})
                
                if active_lot:
                    # Analyze the lot
                    analytics = self.analyze_lot_value(active_lot)
                    
                    # Save to database
                    self.save_enhanced_lot_data(active_lot, analytics)
                    
                    # Update queue status
                    self.update_queue_status(auction_id, lot_id, 'COMPLETED')
                    
                    # Track recommendations
                    recommendations[analytics['recommendation']] += 1
                    analyzed_count += 1
                    
                    # Display summary
                    print(f"  💰 ${active_lot.get('retail_price', 0):,.0f} → ${active_lot.get('instant_win_price', 0):,.0f}")
                    print(f"  💎 Deal Score: {analytics['deal_score']:.1f}/100")
                    print(f"  🎯 Recommendation: {analytics['recommendation']}")
                    
                    if analytics['risk_factors']:
                        print(f"  ⚠️  Risks: {analytics['risk_factors']}")
                else:
                    print(f"  ❌ No active lot data found")
                    self.update_queue_status(auction_id, lot_id, 'NO_DATA')
            else:
                print(f"  ❌ Failed to fetch Next.js data")
                self.update_queue_status(auction_id, lot_id, 'FAILED')
            
            # Rate limiting
            time.sleep(0.5)
        
        print(f"\n{'='*60}")
        print("ANALYSIS COMPLETE")
        print(f"{'='*60}")
        print(f"📊 Analyzed: {analyzed_count} lots")
        print(f"🎯 Recommendations:")
        for rec, count in recommendations.items():
            print(f"  {rec}: {count} lots")
        
        return analyzed_count, recommendations
    
    def save_enhanced_lot_data(self, lot_data, analytics):
        """Save comprehensive lot data with analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO enhanced_lots 
            (lot_id, auction_id, lot_number, product_name, title, description,
             retail_price, instant_win_price, current_bid, total_bids, unique_bidders,
             condition_name, warehouse_location, dimensions, upc, model, brand,
             is_tested, tested_note, damaged_note, is_partial, partial_note,
             expected_close_date, is_open, is_transferrable, buyers_assurance_cost,
             image_url, deal_score, discount_percentage, value_rating,
             opportunity_score, risk_factors, recommendation, data_source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lot_data.get('id'),
            lot_data.get('auction_id'),
            lot_data.get('lot_number'),
            lot_data.get('product_name'),
            lot_data.get('title'),
            lot_data.get('description'),
            lot_data.get('retail_price'),
            lot_data.get('instant_win_price'),
            lot_data.get('winning_bid_amount'),
            lot_data.get('total_bids'),
            lot_data.get('unique_bidders'),
            lot_data.get('condition_name'),
            lot_data.get('warehouse_location'),
            lot_data.get('dimensions'),
            lot_data.get('upc'),
            lot_data.get('model'),
            self.extract_brand(lot_data.get('product_name', '')),
            lot_data.get('is_tested'),
            lot_data.get('tested_note'),
            lot_data.get('damaged_note'),
            lot_data.get('is_partial'),
            lot_data.get('partial_note'),
            lot_data.get('expected_close_date'),
            lot_data.get('is_open'),
            lot_data.get('is_transferrable'),
            lot_data.get('buyers_assurance_cost'),
            lot_data.get('image_url'),
            analytics['deal_score'],
            analytics['discount_percentage'],
            analytics['value_rating'],
            analytics['opportunity_score'],
            analytics['risk_factors'],
            analytics['recommendation'],
            'NEXTJS_API'
        ))
        
        conn.commit()
        conn.close()
    
    def update_queue_status(self, auction_id, lot_id, status):
        """Update queue item status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE discovery_queue 
            SET status = ? 
            WHERE auction_id = ? AND lot_id = ?
        ''', (status, auction_id, lot_id))
        
        conn.commit()
        conn.close()
    
    def generate_opportunities_report(self):
        """Generate comprehensive opportunities report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get top opportunities
        cursor.execute('''
            SELECT product_name, lot_number, retail_price, instant_win_price,
                   deal_score, opportunity_score, recommendation, risk_factors,
                   warehouse_location, expected_close_date
            FROM enhanced_lots 
            WHERE recommendation IN ('STRONG_BUY', 'BUY')
            ORDER BY opportunity_score DESC
            LIMIT 20
        ''')
        
        opportunities = cursor.fetchall()
        
        # Get summary stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_lots,
                AVG(deal_score) as avg_deal_score,
                AVG(discount_percentage) as avg_discount,
                SUM(CASE WHEN recommendation = 'STRONG_BUY' THEN 1 ELSE 0 END) as strong_buy,
                SUM(CASE WHEN recommendation = 'BUY' THEN 1 ELSE 0 END) as buy,
                SUM(CASE WHEN recommendation = 'CONSIDER' THEN 1 ELSE 0 END) as consider,
                SUM(CASE WHEN recommendation = 'AVOID' THEN 1 ELSE 0 END) as avoid
            FROM enhanced_lots
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        
        print(f"\n{'='*80}")
        print("🎯 TOP OPPORTUNITIES REPORT")
        print(f"{'='*80}")
        
        if stats[0] > 0:
            print(f"📊 SUMMARY:")
            print(f"  Total Lots Analyzed: {stats[0]}")
            print(f"  Average Deal Score: {stats[1]:.1f}/100")
            print(f"  Average Discount: {stats[2]:.1f}%")
            print(f"  Strong Buy: {stats[3]} | Buy: {stats[4]} | Consider: {stats[5]} | Avoid: {stats[6]}")
            
            if opportunities:
                print(f"\n🏆 TOP OPPORTUNITIES:")
                print(f"{'='*80}")
                
                for i, opp in enumerate(opportunities, 1):
                    product_name, lot_number, retail_price, instant_win_price, deal_score, opportunity_score, recommendation, risk_factors, warehouse_location, expected_close_date = opp
                    
                    print(f"\n{i:2d}. {product_name[:60]}")
                    print(f"    🏷️  Lot: {lot_number} | 📍 {warehouse_location}")
                    print(f"    💰 ${retail_price:,.0f} → ${instant_win_price:,.0f} ({deal_score:.1f}% off)")
                    print(f"    🎯 Score: {opportunity_score:.1f}/100 | 🎯 {recommendation}")
                    if risk_factors:
                        print(f"    ⚠️  Risks: {risk_factors}")
                    print(f"    ⏰ Closes: {expected_close_date}")
            else:
                print(f"\n📭 No strong opportunities found")
        else:
            print(f"📭 No lots analyzed yet")
        
        return opportunities
    
    def run_complete_analysis(self, max_discovery_pages=3, max_analysis_lots=25):
        """Run complete discovery and analysis pipeline"""
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        print(f"🚀 STARTING COMPLETE ANALYSIS SESSION: {session_id}")
        print(f"{'='*80}")
        
        # Step 1: Discover lots
        discovered_lots = self.discover_lots_typesense(max_pages=max_discovery_pages)
        
        if not discovered_lots:
            print("❌ No lots discovered. Exiting.")
            return
        
        # Step 2: Queue for analysis
        queued_count = self.queue_lots_for_analysis(discovered_lots)
        
        # Step 3: Process analysis queue
        analyzed_count, recommendations = self.process_analysis_queue(max_lots=max_analysis_lots)
        
        # Step 4: Generate opportunities report
        opportunities = self.generate_opportunities_report()
        
        # Step 5: Save session summary
        self.save_session_summary(session_id, len(discovered_lots), analyzed_count, recommendations)
        
        print(f"\n🎉 ANALYSIS SESSION COMPLETE: {session_id}")
        print(f"📊 Discovered: {len(discovered_lots)} | Analyzed: {analyzed_count}")
        print(f"🗄️  Database: {self.db_path}")
        
        return {
            'session_id': session_id,
            'discovered_count': len(discovered_lots),
            'analyzed_count': analyzed_count,
            'recommendations': recommendations,
            'opportunities': opportunities
        }
    
    def save_session_summary(self, session_id, discovered, analyzed, recommendations):
        """Save session summary to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO analysis_summary 
            (session_id, total_discovered, total_analyzed, strong_buy_count,
             buy_count, consider_count, avoid_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            discovered,
            analyzed,
            recommendations.get('STRONG_BUY', 0),
            recommendations.get('BUY', 0),
            recommendations.get('CONSIDER', 0),
            recommendations.get('AVOID', 0)
        ))
        
        conn.commit()
        conn.close()

def main():
    """Main function"""
    print("=== NEXT.JS INTEGRATION SYSTEM ===")
    
    system = NextJSIntegrationSystem()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "discover":
            # Just discovery
            lots = system.discover_lots_typesense(max_pages=2)
            system.queue_lots_for_analysis(lots)
        elif sys.argv[1] == "analyze":
            # Just analysis
            system.process_analysis_queue(max_lots=10)
        elif sys.argv[1] == "report":
            # Just report
            system.generate_opportunities_report()
        else:
            # Complete analysis
            system.run_complete_analysis(max_discovery_pages=2, max_analysis_lots=15)
    else:
        # Default: complete analysis
        system.run_complete_analysis(max_discovery_pages=2, max_analysis_lots=15)

if __name__ == "__main__":
    main() 