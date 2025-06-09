#!/usr/bin/env python3
"""
⏰ Ending Soon Monitor - Track High-Value Items Closing Soon
Monitor valuable items that are ending in the next few hours
"""

import asyncio
import aiohttp
import ssl
import json
from datetime import datetime, timedelta
from collections import defaultdict
import re

class EndingSoonMonitor:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        
        # High-value search terms
        self.priority_terms = [
            "macbook", "iphone", "ipad", "apple", "sony", "samsung", "nintendo",
            "xbox", "playstation", "dyson", "kitchenaid", "rolex", "omega",
            "canon", "nikon", "dewalt", "milwaukee", "tv", "camera", "laptop"
        ]
        
    async def create_session(self):
        """Create HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=10)
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
            
    async def search_for_term(self, term, limit=100):
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
            
    def parse_closing_date(self, date_str):
        """Parse closing date string to datetime."""
        if not date_str or date_str == 'Unknown':
            return None
            
        try:
            # Handle different date formats
            if 'T' in date_str:
                # ISO format: 2025-06-08T23:59:59
                return datetime.fromisoformat(date_str.replace('Z', ''))
            else:
                # Simple date format: 2025-06-08
                return datetime.strptime(date_str, '%Y-%m-%d')
        except:
            return None
            
    def calculate_urgency_score(self, item):
        """Calculate urgency score based on time remaining and value."""
        closing_date = self.parse_closing_date(item.get('expected_close_date'))
        if not closing_date:
            return 0
            
        now = datetime.now()
        time_remaining = closing_date - now
        hours_remaining = time_remaining.total_seconds() / 3600
        
        if hours_remaining <= 0:
            return 0  # Already ended
            
        # Base urgency score (higher = more urgent)
        if hours_remaining <= 2:
            urgency_base = 10
        elif hours_remaining <= 6:
            urgency_base = 8
        elif hours_remaining <= 12:
            urgency_base = 6
        elif hours_remaining <= 24:
            urgency_base = 4
        else:
            urgency_base = 2
            
        # Value multiplier
        retail_price = item.get('retail_price', 0)
        value_multiplier = min(retail_price / 500, 3)  # Cap at 3x
        
        # Bidding activity bonus
        current_bid = item.get('current_bid', 0)
        bid_bonus = 2 if current_bid == 0 else 1  # No bids = opportunity
        
        # Savings bonus
        instant_win_price = item.get('instant_win_price', 0)
        savings_bonus = 0
        if retail_price > 0 and instant_win_price > 0:
            savings_percent = ((retail_price - instant_win_price) / retail_price) * 100
            savings_bonus = min(savings_percent / 20, 2)  # Cap at 2 points
            
        return urgency_base * value_multiplier + bid_bonus + savings_bonus
        
    async def scan_ending_soon(self, max_hours=24, min_value=100):
        """Scan for items ending soon."""
        print(f"⏰ ENDING SOON MONITOR")
        print(f"🎯 Items ending within {max_hours} hours, min value ${min_value}")
        print(f"🔍 Scanning {len(self.priority_terms)} priority terms...")
        print()
        
        all_items = []
        seen_lot_ids = set()
        
        for i, term in enumerate(self.priority_terms, 1):
            print(f"  {i:2d}/{len(self.priority_terms)} - Scanning '{term}'...")
            
            results = await self.search_for_term(term)
            
            # Filter for ending soon items
            ending_soon = []
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    retail_price = result.get('retail_price', 0)
                    
                    if retail_price >= min_value:
                        closing_date = self.parse_closing_date(result.get('expected_close_date'))
                        
                        if closing_date:
                            now = datetime.now()
                            time_remaining = closing_date - now
                            hours_remaining = time_remaining.total_seconds() / 3600
                            
                            if 0 < hours_remaining <= max_hours:
                                result['hours_remaining'] = hours_remaining
                                result['urgency_score'] = self.calculate_urgency_score(result)
                                
                                # Calculate savings if available
                                instant_win_price = result.get('instant_win_price', 0)
                                if instant_win_price > 0:
                                    savings = retail_price - instant_win_price
                                    savings_percent = (savings / retail_price) * 100
                                    result['savings_amount'] = savings
                                    result['savings_percent'] = savings_percent
                                else:
                                    result['savings_amount'] = 0
                                    result['savings_percent'] = 0
                                    
                                ending_soon.append(result)
                                seen_lot_ids.add(lot_id)
                                
            all_items.extend(ending_soon)
            print(f"      Found {len(results)} items, {len(ending_soon)} ending soon")
            
            await asyncio.sleep(0.2)  # Rate limiting
            
        return all_items
        
    def display_ending_soon_report(self, items):
        """Display ending soon report."""
        if not items:
            print("❌ No items ending soon found")
            return
            
        print(f"\n⏰ ENDING SOON REPORT")
        print("=" * 80)
        
        # Sort by urgency score (highest first)
        items.sort(key=lambda x: x.get('urgency_score', 0), reverse=True)
        
        print(f"🎉 Found {len(items)} items ending soon")
        print()
        
        # Critical items (ending in 2 hours)
        critical_items = [item for item in items if item.get('hours_remaining', 0) <= 2]
        if critical_items:
            print(f"🚨 CRITICAL - ENDING IN 2 HOURS ({len(critical_items)} items)")
            print("-" * 60)
            
            for item in critical_items:
                self.display_item(item, "🚨")
                
        # Urgent items (ending in 6 hours)
        urgent_items = [item for item in items if 2 < item.get('hours_remaining', 0) <= 6]
        if urgent_items:
            print(f"⚠️  URGENT - ENDING IN 6 HOURS ({len(urgent_items)} items)")
            print("-" * 60)
            
            for item in urgent_items[:10]:  # Show top 10
                self.display_item(item, "⚠️ ")
                
        # Today items (ending in 24 hours)
        today_items = [item for item in items if 6 < item.get('hours_remaining', 0) <= 24]
        if today_items:
            print(f"📅 ENDING TODAY ({len(today_items)} items)")
            print("-" * 60)
            
            for item in today_items[:15]:  # Show top 15
                self.display_item(item, "📅")
                
        # Top opportunities by urgency score
        print(f"\n🎯 TOP 10 OPPORTUNITIES (by Urgency Score)")
        print("-" * 70)
        
        for i, item in enumerate(items[:10], 1):
            product_name = item.get('product_name', 'Unknown')[:45]
            location = item.get('auction_location', 'Unknown')
            retail_price = item.get('retail_price', 0)
            instant_win = item.get('instant_win_price', 0)
            current_bid = item.get('current_bid', 0)
            hours_remaining = item.get('hours_remaining', 0)
            urgency_score = item.get('urgency_score', 0)
            savings = item.get('savings_amount', 0)
            
            print(f"{i:2d}. 🎯 Urgency: {urgency_score:.1f} | ⏰ {hours_remaining:.1f}h left")
            print(f"     📦 {product_name}...")
            print(f"     💰 ${retail_price} → ${instant_win} | 💸 Save ${savings:.0f}")
            print(f"     📍 {location} | 🔥 Current Bid: ${current_bid}")
            print()
            
        # No-bid opportunities
        no_bid_items = [item for item in items if item.get('current_bid', 0) == 0]
        if no_bid_items:
            print(f"\n🎯 NO-BID OPPORTUNITIES ({len(no_bid_items)} items)")
            print("-" * 60)
            
            # Sort by value
            no_bid_items.sort(key=lambda x: x.get('retail_price', 0), reverse=True)
            
            for item in no_bid_items[:10]:
                product_name = item.get('product_name', 'Unknown')[:40]
                retail_price = item.get('retail_price', 0)
                instant_win = item.get('instant_win_price', 0)
                hours_remaining = item.get('hours_remaining', 0)
                location = item.get('auction_location', 'Unknown')
                
                print(f"🎯 {product_name}... | ${retail_price} → ${instant_win} | {hours_remaining:.1f}h | {location}")
                
        # Location breakdown
        print(f"\n📍 ENDING SOON BY LOCATION")
        print("-" * 40)
        
        by_location = defaultdict(list)
        for item in items:
            location = item.get('auction_location', 'Unknown')
            by_location[location].append(item)
            
        for location in self.sc_locations:
            location_items = by_location.get(location, [])
            if location_items:
                total_value = sum(item.get('retail_price', 0) for item in location_items)
                avg_hours = sum(item.get('hours_remaining', 0) for item in location_items) / len(location_items)
                no_bids = len([item for item in location_items if item.get('current_bid', 0) == 0])
                
                print(f"  {location:12s}: {len(location_items):2d} items | ${total_value:6,.0f} value | {avg_hours:4.1f}h avg | {no_bids} no bids")
                
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ending_soon_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(items, f, indent=2)
        print(f"\n💾 Ending soon data saved to: {filename}")
        
    def display_item(self, item, prefix=""):
        """Display a single item."""
        product_name = item.get('product_name', 'Unknown')[:45]
        location = item.get('auction_location', 'Unknown')
        retail_price = item.get('retail_price', 0)
        instant_win = item.get('instant_win_price', 0)
        current_bid = item.get('current_bid', 0)
        hours_remaining = item.get('hours_remaining', 0)
        savings = item.get('savings_amount', 0)
        auction_number = item.get('auction_number', 'Unknown')
        lot_number = item.get('lot_number', 'Unknown')
        
        print(f"{prefix} ⏰ {hours_remaining:.1f}h left")
        print(f"     📦 {product_name}...")
        print(f"     💰 ${retail_price} → ${instant_win} | 💸 Save ${savings:.0f}")
        print(f"     📍 {location} | 📋 {auction_number} | Lot: {lot_number}")
        if current_bid > 0:
            print(f"     🔥 Current Bid: ${current_bid}")
        else:
            print(f"     🎯 NO BIDS YET - OPPORTUNITY!")
        print()

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ending Soon Monitor')
    parser.add_argument('--hours', type=int, default=24, help='Max hours until closing')
    parser.add_argument('--min-value', type=int, default=100, help='Minimum retail value')
    parser.add_argument('--critical-only', action='store_true', help='Show only critical items (2h or less)')
    
    args = parser.parse_args()
    
    monitor = EndingSoonMonitor()
    await monitor.create_session()
    
    try:
        items = await monitor.scan_ending_soon(args.hours, args.min_value)
        
        if args.critical_only:
            items = [item for item in items if item.get('hours_remaining', 0) <= 2]
            
        monitor.display_ending_soon_report(items)
        
    finally:
        await monitor.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 