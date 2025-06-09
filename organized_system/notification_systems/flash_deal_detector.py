#!/usr/bin/env python3
"""
⚡ Flash Deal Detector - Find Massive Discounts That Just Appeared
Detect items with huge savings that recently became available
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict

class FlashDealDetector:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        self.db_file = "flash_deals.db"
        self.init_database()
        
        # Search terms for high-value items likely to have flash deals
        self.flash_terms = [
            # High-value electronics
            "macbook", "iphone", "ipad", "samsung tv", "sony camera", "nintendo switch",
            "xbox", "playstation", "dyson", "kitchenaid", "canon", "nikon",
            
            # Luxury items
            "rolex", "omega", "cartier", "tiffany", "diamond", "gold",
            
            # High-end appliances
            "refrigerator", "washer", "dryer", "dishwasher", "vitamix",
            
            # Premium tools
            "dewalt", "milwaukee", "makita", "snap-on",
            
            # Fitness equipment
            "peloton", "nordictrack", "treadmill",
            
            # General high-value terms
            "open box", "like new", "refurbished", "clearance"
        ]
        
    def init_database(self):
        """Initialize flash deals database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flash_deals (
                lot_id TEXT PRIMARY KEY,
                product_name TEXT,
                auction_location TEXT,
                auction_number TEXT,
                lot_number TEXT,
                category TEXT,
                condition_desc TEXT,
                retail_price REAL,
                instant_win_price REAL,
                current_bid REAL,
                expected_close_date TEXT,
                savings_amount REAL,
                savings_percent REAL,
                flash_score REAL,
                first_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flash_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                alert_type TEXT,
                message TEXT,
                savings_amount REAL,
                savings_percent REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def create_session(self):
        """Create HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=12)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        )
        
    async def close_session(self):
        if self.session:
            await self.session.close()
            await asyncio.sleep(0.25)
            
    async def search_for_term(self, term, limit=150):
        """Search for a specific term."""
        url = f"https://api.macdiscount.com/search?q={term}&limit={limit}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get('hits', [])
                    
                    # Filter to SC locations only
                    sc_hits = []
                    for hit in hits:
                        if hit.get('auction_location') in self.sc_locations:
                            sc_hits.append(hit)
                            
                    return sc_hits
                else:
                    return []
        except Exception as e:
            return []
            
    def calculate_flash_score(self, item):
        """Calculate flash deal score based on savings and value."""
        retail_price = item.get('retail_price', 0)
        instant_win_price = item.get('instant_win_price', 0)
        current_bid = item.get('current_bid', 0)
        
        if retail_price <= 0 or instant_win_price <= 0:
            return 0
            
        savings_amount = retail_price - instant_win_price
        savings_percent = (savings_amount / retail_price) * 100
        
        # Base score from savings percentage
        savings_score = min(savings_percent / 10, 10)  # Cap at 10
        
        # Value multiplier (higher value = higher score)
        value_multiplier = min(retail_price / 500, 5)  # Cap at 5x
        
        # Urgency bonus (no current bids = higher score)
        urgency_bonus = 2 if current_bid == 0 else 0
        
        # Premium brand bonus
        product_name = item.get('product_name', '').lower()
        brand_bonus = 0
        premium_brands = ['apple', 'sony', 'dyson', 'rolex', 'omega', 'nintendo', 'xbox']
        for brand in premium_brands:
            if brand in product_name:
                brand_bonus = 1
                break
                
        return savings_score * value_multiplier + urgency_bonus + brand_bonus
        
    async def scan_for_flash_deals(self, min_savings_percent=40, min_retail_value=100):
        """Scan for flash deals with high savings."""
        print(f"⚡ FLASH DEAL DETECTOR")
        print(f"🎯 Criteria: {min_savings_percent}%+ savings, ${min_retail_value}+ retail value")
        print(f"🔍 Scanning {len(self.flash_terms)} high-value terms...")
        print()
        
        all_deals = []
        seen_lot_ids = set()
        
        for i, term in enumerate(self.flash_terms, 1):
            print(f"  {i:2d}/{len(self.flash_terms)} - Scanning '{term}'...")
            
            results = await self.search_for_term(term)
            
            # Filter for flash deals
            flash_deals = []
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    retail_price = result.get('retail_price', 0)
                    instant_win_price = result.get('instant_win_price', 0)
                    
                    if retail_price >= min_retail_value and instant_win_price > 0:
                        savings = retail_price - instant_win_price
                        savings_percent = (savings / retail_price) * 100
                        
                        if savings_percent >= min_savings_percent:
                            result['savings_amount'] = savings
                            result['savings_percent'] = savings_percent
                            result['flash_score'] = self.calculate_flash_score(result)
                            
                            flash_deals.append(result)
                            seen_lot_ids.add(lot_id)
                            
            all_deals.extend(flash_deals)
            print(f"      Found {len(results)} items, {len(flash_deals)} flash deals")
            
            await asyncio.sleep(0.2)  # Rate limiting
            
        return all_deals
        
    def process_flash_deals(self, deals):
        """Process deals and identify truly new flash deals."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        new_flash_deals = []
        updated_deals = []
        
        for deal in deals:
            lot_id = deal.get('lot_id')
            if not lot_id:
                continue
                
            # Check if we've seen this deal before
            cursor.execute('SELECT lot_id, savings_percent FROM flash_deals WHERE lot_id = ?', (lot_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing deal
                cursor.execute('''
                    UPDATE flash_deals SET
                        current_bid = ?, last_seen = CURRENT_TIMESTAMP
                    WHERE lot_id = ?
                ''', (deal.get('current_bid', 0), lot_id))
                updated_deals.append(deal)
            else:
                # New flash deal!
                cursor.execute('''
                    INSERT INTO flash_deals (
                        lot_id, product_name, auction_location, auction_number,
                        lot_number, category, condition_desc, retail_price,
                        instant_win_price, current_bid, expected_close_date,
                        savings_amount, savings_percent, flash_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    lot_id,
                    deal.get('product_name'),
                    deal.get('auction_location'),
                    deal.get('auction_number'),
                    deal.get('lot_number'),
                    deal.get('category'),
                    deal.get('condition'),
                    deal.get('retail_price', 0),
                    deal.get('instant_win_price', 0),
                    deal.get('current_bid', 0),
                    deal.get('expected_close_date'),
                    deal.get('savings_amount', 0),
                    deal.get('savings_percent', 0),
                    deal.get('flash_score', 0)
                ))
                
                new_flash_deals.append(deal)
                
                # Create alert for high-score deals
                if deal.get('flash_score', 0) >= 15:
                    alert_msg = f"MEGA FLASH DEAL: {deal.get('product_name', '')[:50]} - Save ${deal.get('savings_amount', 0):.0f} ({deal.get('savings_percent', 0):.0f}%)"
                    cursor.execute('''
                        INSERT INTO flash_alerts (lot_id, alert_type, message, savings_amount, savings_percent)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (lot_id, 'MEGA_FLASH', alert_msg, deal.get('savings_amount', 0), deal.get('savings_percent', 0)))
                elif deal.get('flash_score', 0) >= 10:
                    alert_msg = f"Flash Deal: {deal.get('product_name', '')[:50]} - Save ${deal.get('savings_amount', 0):.0f} ({deal.get('savings_percent', 0):.0f}%)"
                    cursor.execute('''
                        INSERT INTO flash_alerts (lot_id, alert_type, message, savings_amount, savings_percent)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (lot_id, 'FLASH_DEAL', alert_msg, deal.get('savings_amount', 0), deal.get('savings_percent', 0)))
                    
        conn.commit()
        conn.close()
        
        return new_flash_deals, updated_deals
        
    def display_flash_deals(self, new_deals, all_deals):
        """Display flash deals report."""
        print(f"\n⚡ FLASH DEAL REPORT")
        print("=" * 80)
        
        if not all_deals:
            print("❌ No flash deals found")
            return
            
        print(f"🎉 Found {len(all_deals)} total flash deals")
        if new_deals:
            print(f"🆕 {len(new_deals)} NEW flash deals detected!")
        print()
        
        # Sort by flash score (highest first)
        all_deals.sort(key=lambda x: x.get('flash_score', 0), reverse=True)
        
        # Top flash deals
        print(f"⚡ TOP 15 FLASH DEALS (by Flash Score)")
        print("-" * 70)
        
        for i, deal in enumerate(all_deals[:15], 1):
            product_name = deal.get('product_name', 'Unknown')[:45]
            location = deal.get('auction_location', 'Unknown')
            retail_price = deal.get('retail_price', 0)
            instant_win = deal.get('instant_win_price', 0)
            savings = deal.get('savings_amount', 0)
            savings_percent = deal.get('savings_percent', 0)
            flash_score = deal.get('flash_score', 0)
            current_bid = deal.get('current_bid', 0)
            closing_date = deal.get('expected_close_date', 'Unknown')
            
            is_new = "🆕" if deal in new_deals else "   "
            
            print(f"{i:2d}. {is_new} ⚡ Score: {flash_score:.1f}")
            print(f"     📦 {product_name}...")
            print(f"     💰 ${retail_price} → ${instant_win} | 💸 Save ${savings:.0f} ({savings_percent:.0f}%)")
            print(f"     📍 {location} | ⏰ Closes: {closing_date}")
            if current_bid > 0:
                print(f"     🔥 Current Bid: ${current_bid}")
            print()
            
        # Mega deals (score >= 15)
        mega_deals = [deal for deal in all_deals if deal.get('flash_score', 0) >= 15]
        if mega_deals:
            print(f"🚨 MEGA FLASH DEALS (Score 15+)")
            print("-" * 50)
            
            for deal in mega_deals:
                product_name = deal.get('product_name', 'Unknown')[:40]
                savings = deal.get('savings_amount', 0)
                savings_percent = deal.get('savings_percent', 0)
                location = deal.get('auction_location', 'Unknown')
                
                print(f"🚨 {product_name}... | Save ${savings:.0f} ({savings_percent:.0f}%) | {location}")
                
        # Location breakdown
        print(f"\n📍 FLASH DEALS BY LOCATION")
        print("-" * 40)
        
        by_location = defaultdict(list)
        for deal in all_deals:
            location = deal.get('auction_location', 'Unknown')
            by_location[location].append(deal)
            
        for location in self.sc_locations:
            location_deals = by_location.get(location, [])
            if location_deals:
                total_savings = sum(deal.get('savings_amount', 0) for deal in location_deals)
                avg_score = sum(deal.get('flash_score', 0) for deal in location_deals) / len(location_deals)
                
                print(f"  {location:12s}: {len(location_deals):2d} deals | ${total_savings:6,.0f} savings | {avg_score:.1f} avg score")
                
        # Summary stats
        total_retail = sum(deal.get('retail_price', 0) for deal in all_deals)
        total_instant_win = sum(deal.get('instant_win_price', 0) for deal in all_deals)
        total_savings = sum(deal.get('savings_amount', 0) for deal in all_deals)
        avg_savings_percent = sum(deal.get('savings_percent', 0) for deal in all_deals) / len(all_deals)
        
        print(f"\n📊 FLASH DEAL SUMMARY")
        print("-" * 40)
        print(f"💰 Total Retail Value: ${total_retail:,.2f}")
        print(f"🏷️  Total Instant Win: ${total_instant_win:,.2f}")
        print(f"💸 Total Savings: ${total_savings:,.2f}")
        print(f"📈 Average Savings: {avg_savings_percent:.1f}%")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"flash_deals_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(all_deals, f, indent=2)
        print(f"\n💾 Flash deals saved to: {filename}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Flash Deal Detector')
    parser.add_argument('--min-savings', type=int, default=40, help='Minimum savings percentage')
    parser.add_argument('--min-value', type=int, default=100, help='Minimum retail value')
    parser.add_argument('--mega-only', action='store_true', help='Show only mega deals (score 15+)')
    
    args = parser.parse_args()
    
    detector = FlashDealDetector()
    await detector.create_session()
    
    try:
        deals = await detector.scan_for_flash_deals(args.min_savings, args.min_value)
        new_deals, updated_deals = detector.process_flash_deals(deals)
        
        if args.mega_only:
            deals = [deal for deal in deals if deal.get('flash_score', 0) >= 15]
            new_deals = [deal for deal in new_deals if deal.get('flash_score', 0) >= 15]
            
        detector.display_flash_deals(new_deals, deals)
        
    finally:
        await detector.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 