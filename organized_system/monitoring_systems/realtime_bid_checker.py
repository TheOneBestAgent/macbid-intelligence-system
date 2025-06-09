#!/usr/bin/env python3
"""
Real-Time Bid Checker for South Carolina Lots
Verifies actual current bid status and activity
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import List, Dict, Any

class RealtimeBidChecker:
    def __init__(self):
        self.load_credentials()
        self.sc_locations = ['Rock Hill', 'Greenville', 'Spartanburg', 'Anderson']
        
        # Headers for API requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        # Add JWT token if available
        if self.jwt_token:
            self.auth_headers = self.headers.copy()
            self.auth_headers.update({
                'authorization': self.jwt_token,
                'origin': 'https://www.mac.bid',
                'referer': 'https://www.mac.bid/'
            })
        else:
            self.auth_headers = self.headers
    
    def load_credentials(self):
        """Load JWT token and customer ID."""
        self.jwt_token = None
        self.customer_id = None
        
        try:
            tokens_file = os.path.expanduser("~/.macbid_scraper/api_tokens.json")
            with open(tokens_file, 'r') as f:
                token_data = json.load(f)
                self.jwt_token = token_data.get('tokens', {}).get('authorization')
                self.customer_id = token_data.get('customer_id')
                
            if self.jwt_token:
                print(f"✅ Using JWT token: {self.jwt_token[:50]}...")
            if self.customer_id:
                print(f"✅ Customer ID: {self.customer_id}")
        except Exception as e:
            print(f"⚠️ Could not load credentials: {e}")
    
    async def get_detailed_lot_info(self, session: aiohttp.ClientSession, lot_id: str) -> Dict:
        """Get detailed information for a specific lot."""
        # Try to get more detailed info using search
        url = f"https://api.macdiscount.com/search?q={lot_id}&limit=1"
        
        try:
            async with session.get(url, headers=self.headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get('hits', [])
                    if hits:
                        return hits[0]
        except Exception as e:
            print(f"❌ Error getting lot {lot_id}: {e}")
        
        return {}
    
    async def check_current_bidding_status(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Check current bidding status for SC lots with real-time verification."""
        print("🔍 Checking Real-Time Bidding Status...")
        
        active_lots = []
        
        # Get lots from multiple search approaches
        search_terms = ['electronics', 'gaming', 'headphones', 'laptop']
        
        for term in search_terms:
            url = f"https://api.macdiscount.com/search?q={term}&limit=100"
            
            try:
                async with session.get(url, headers=self.headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        hits = data.get('hits', [])
                        
                        print(f"   📦 Checking {len(hits)} lots for '{term}'...")
                        
                        for item in hits:
                            # Filter for South Carolina
                            us_state = item.get('us_state', '')
                            auction_location = item.get('auction_location', '')
                            
                            is_sc = (us_state == 'South Carolina' or 
                                   any(sc_loc in auction_location for sc_loc in self.sc_locations))
                            
                            if is_sc:
                                # Get real-time status
                                lot_status = await self.analyze_lot_status(item)
                                if lot_status['is_active']:
                                    active_lots.append(lot_status)
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"❌ Error checking {term}: {e}")
        
        return active_lots
    
    async def analyze_lot_status(self, item: Dict) -> Dict:
        """Analyze the real-time status of a lot."""
        lot_id = item.get('lot_id', '')
        product_name = item.get('product_name', '')
        current_bid = float(item.get('current_bid', 0))
        retail_price = float(item.get('retail_price', 0))
        total_bids = item.get('total_bids', 0)
        unique_bidders = item.get('unique_bidders', 0)
        is_open = item.get('is_open', False)
        expected_close_date = item.get('expected_close_date', '')
        expected_closing_utc = item.get('expected_closing_utc', '')
        
        # Determine actual activity level
        activity_level = "Unknown"
        if total_bids == 0:
            activity_level = "No Bids Yet"
        elif total_bids < 5:
            activity_level = "Low Activity"
        elif total_bids < 15:
            activity_level = "Moderate Activity"
        else:
            activity_level = "High Activity"
        
        # Calculate time until close
        time_until_close = "Unknown"
        try:
            if expected_closing_utc:
                from datetime import datetime, timezone
                close_time = datetime.fromisoformat(expected_closing_utc.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                time_diff = close_time - now
                
                if time_diff.total_seconds() > 0:
                    hours = int(time_diff.total_seconds() // 3600)
                    minutes = int((time_diff.total_seconds() % 3600) // 60)
                    time_until_close = f"{hours}h {minutes}m"
                else:
                    time_until_close = "Closed"
        except:
            pass
        
        # Determine if this is an active opportunity
        is_active = (
            is_open and 
            retail_price > 0 and
            time_until_close != "Closed" and
            current_bid < retail_price * 0.7  # Still has potential for good deal
        )
        
        # Calculate current discount
        if retail_price > 0 and current_bid > 0:
            current_discount = ((retail_price - current_bid) / retail_price) * 100
        elif retail_price > 0:
            current_discount = 100  # No bids yet
        else:
            current_discount = 0
        
        return {
            'lot_id': lot_id,
            'product_name': product_name,
            'current_bid': current_bid,
            'retail_price': retail_price,
            'current_discount': current_discount,
            'total_bids': total_bids,
            'unique_bidders': unique_bidders,
            'activity_level': activity_level,
            'is_open': is_open,
            'time_until_close': time_until_close,
            'expected_close_date': expected_close_date,
            'location': item.get('auction_location', ''),
            'auction_number': item.get('auction_number', ''),
            'lot_number': item.get('lot_number', ''),
            'is_active': is_active,
            'condition': item.get('condition', ''),
            'category': item.get('category', ''),
            'is_shippable': item.get('is_shippable', False)
        }
    
    async def get_your_current_watchlist(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Get your current watchlist to see what you're already tracking."""
        if not self.customer_id or not self.jwt_token:
            return []
        
        watchlist_items = []
        url = f"https://api.macdiscount.com/auctions/customer/{self.customer_id}/active-auctions"
        
        try:
            async with session.get(url, headers=self.auth_headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    watchlist = data.get('watchlist', [])
                    
                    print(f"👀 You're currently watching {len(watchlist)} lots")
                    
                    for item in watchlist:
                        watchlist_items.append({
                            'lot_id': item.get('lot_id'),
                            'auction_number': item.get('auction_number'),
                            'lot_number': item.get('lot_number'),
                            'date_created': item.get('date_created')
                        })
        
        except Exception as e:
            print(f"❌ Error getting watchlist: {e}")
        
        return watchlist_items
    
    def display_active_lots(self, lots: List[Dict], watchlist: List[Dict] = None):
        """Display active lots with real-time status."""
        if not lots:
            print("❌ No active lots found in South Carolina")
            return
        
        # Create watchlist lookup
        watchlist_lot_ids = set()
        if watchlist:
            watchlist_lot_ids = {item['lot_id'] for item in watchlist if item.get('lot_id')}
        
        # Sort by activity level and discount
        activity_order = {"No Bids Yet": 0, "Low Activity": 1, "Moderate Activity": 2, "High Activity": 3}
        lots_sorted = sorted(lots, key=lambda x: (activity_order.get(x['activity_level'], 4), -x['current_discount']))
        
        print(f"\n🎯 ACTIVE SOUTH CAROLINA LOTS ({len(lots_sorted)} found):")
        print("=" * 100)
        
        for i, lot in enumerate(lots_sorted[:20], 1):  # Show top 20
            watching_indicator = "👀" if lot['lot_id'] in watchlist_lot_ids else "  "
            activity_emoji = {
                "No Bids Yet": "🟢",
                "Low Activity": "🟡", 
                "Moderate Activity": "🟠",
                "High Activity": "🔴"
            }.get(lot['activity_level'], "⚪")
            
            shipping_indicator = "📦" if lot['is_shippable'] else "🏪"
            
            print(f"{i:2d}. {watching_indicator} {activity_emoji} {shipping_indicator} {lot['product_name'][:55]}")
            print(f"    💰 Current: ${lot['current_bid']:.2f} | Retail: ${lot['retail_price']:.2f} | Discount: {lot['current_discount']:.1f}%")
            print(f"    🏢 {lot['location']} | ⏰ Closes in: {lot['time_until_close']}")
            print(f"    📊 {lot['activity_level']} - {lot['total_bids']} bids from {lot['unique_bidders']} bidders")
            print(f"    📋 Lot #{lot['lot_number']} in Auction #{lot['auction_number']} | {lot['condition']}")
            print()
    
    def display_summary_stats(self, lots: List[Dict]):
        """Display summary statistics."""
        if not lots:
            return
        
        # Activity breakdown
        activity_counts = {}
        for lot in lots:
            activity = lot['activity_level']
            activity_counts[activity] = activity_counts.get(activity, 0) + 1
        
        # Location breakdown
        location_counts = {}
        for lot in lots:
            location = lot['location']
            location_counts[location] = location_counts.get(location, 0) + 1
        
        # Discount ranges
        high_discount = len([l for l in lots if l['current_discount'] > 70])
        medium_discount = len([l for l in lots if 40 <= l['current_discount'] <= 70])
        low_discount = len([l for l in lots if l['current_discount'] < 40])
        
        print(f"\n📊 SUMMARY STATISTICS:")
        print("=" * 50)
        print(f"📦 Total Active Lots: {len(lots)}")
        print(f"\n🎯 Activity Levels:")
        for activity, count in activity_counts.items():
            print(f"   {activity}: {count} lots")
        
        print(f"\n🏢 Locations:")
        for location, count in location_counts.items():
            print(f"   {location}: {count} lots")
        
        print(f"\n💰 Discount Ranges:")
        print(f"   High (>70%): {high_discount} lots")
        print(f"   Medium (40-70%): {medium_discount} lots") 
        print(f"   Low (<40%): {low_discount} lots")
    
    async def run_realtime_check(self):
        """Run a real-time check of current bidding status."""
        print("🚀 Real-Time South Carolina Bid Status Check")
        print("=" * 60)
        print(f"⏰ Check started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            # Get current watchlist
            print("\n1. 👀 Checking Your Current Watchlist...")
            watchlist = await self.get_your_current_watchlist(session)
            
            # Check current bidding status
            print("\n2. 🔍 Checking Current Lot Status...")
            active_lots = await self.check_current_bidding_status(session)
            
            # Display results
            self.display_active_lots(active_lots, watchlist)
            self.display_summary_stats(active_lots)
            
            print(f"\n✅ Real-time check completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    checker = RealtimeBidChecker()
    await checker.run_realtime_check()

if __name__ == "__main__":
    asyncio.run(main()) 