#!/usr/bin/env python3
"""
Simple Search API Monitor
Uses only the working Public Search API to monitor South Carolina lots
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import List, Dict

class SimpleSearchAPIMonitor:
    def __init__(self):
        self.sc_locations = ['Rock Hill', 'Greenville', 'Spartanburg', 'Anderson']
        
        # Simple headers for API requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
    
    async def search_lots(self, session: aiohttp.ClientSession, search_term: str, limit: int = 50) -> List[Dict]:
        """Search for lots using the working Public Search API."""
        url = f"https://api.macdiscount.com/search?q={search_term}&limit={limit}"
        
        try:
            async with session.get(url, headers=self.headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get('hits', [])
                    
                    # Filter for South Carolina lots
                    sc_lots = []
                    for item in hits:
                        us_state = item.get('us_state', '')
                        auction_location = item.get('auction_location', '')
                        
                        # Check if it's in South Carolina
                        is_sc = (us_state == 'South Carolina' or 
                               any(sc_loc in auction_location for sc_loc in self.sc_locations))
                        
                        if is_sc:
                            sc_lots.append(item)
                    
                    print(f"   📦 '{search_term}': {len(hits)} total, {len(sc_lots)} in SC")
                    return sc_lots
                else:
                    print(f"   ❌ Error {response.status} for '{search_term}'")
                    return []
        
        except Exception as e:
            print(f"   ❌ Exception for '{search_term}': {e}")
            return []
    
    async def search_by_location(self, session: aiohttp.ClientSession, location: str, limit: int = 30) -> List[Dict]:
        """Search for lots in a specific SC location."""
        url = f"https://api.macdiscount.com/search?q=&location={location.replace(' ', '%20')}&limit={limit}"
        
        try:
            async with session.get(url, headers=self.headers, timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get('hits', [])
                    print(f"   🏢 {location}: {len(hits)} lots")
                    return hits
                else:
                    print(f"   ❌ Error {response.status} for {location}")
                    return []
        
        except Exception as e:
            print(f"   ❌ Exception for {location}: {e}")
            return []
    
    def analyze_lot(self, lot: Dict) -> Dict:
        """Analyze a lot for opportunity scoring."""
        current_bid = float(lot.get('current_bid', 0))
        retail_price = float(lot.get('retail_price', 0))
        total_bids = lot.get('total_bids', 0)
        unique_bidders = lot.get('unique_bidders', 0)
        
        # Calculate discount
        if retail_price > 0:
            if current_bid > 0:
                discount = ((retail_price - current_bid) / retail_price) * 100
            else:
                discount = 100  # No bids yet
        else:
            discount = 0
        
        # Calculate opportunity score
        score = 0
        
        # Base score from discount
        score += min(discount, 100)
        
        # Bonus for no/low bids
        if total_bids == 0:
            score += 25
        elif total_bids < 5:
            score += 15
        elif total_bids < 10:
            score += 10
        
        # Bonus for few bidders
        if unique_bidders == 0:
            score += 20
        elif unique_bidders < 3:
            score += 15
        elif unique_bidders < 5:
            score += 10
        
        # Bonus for good categories (based on your success)
        product_name = lot.get('product_name', '').lower()
        if any(term in product_name for term in ['headphone', 'gaming', 'processor', 'microphone', 'sony']):
            score += 20
        elif any(term in product_name for term in ['electronics', 'laptop', 'monitor']):
            score += 10
        
        return {
            'lot_id': lot.get('lot_id'),
            'product_name': lot.get('product_name', ''),
            'current_bid': current_bid,
            'retail_price': retail_price,
            'discount': discount,
            'total_bids': total_bids,
            'unique_bidders': unique_bidders,
            'location': lot.get('auction_location', ''),
            'auction_number': lot.get('auction_number', ''),
            'lot_number': lot.get('lot_number', ''),
            'condition': lot.get('condition', ''),
            'is_open': lot.get('is_open', False),
            'is_shippable': lot.get('is_shippable', False),
            'expected_close_date': lot.get('expected_close_date', ''),
            'opportunity_score': min(score, 100)
        }
    
    def display_opportunities(self, opportunities: List[Dict]):
        """Display the best opportunities."""
        if not opportunities:
            print("❌ No opportunities found")
            return
        
        # Sort by opportunity score
        sorted_opps = sorted(opportunities, key=lambda x: x['opportunity_score'], reverse=True)
        
        print(f"\n🎯 TOP SOUTH CAROLINA OPPORTUNITIES ({len(sorted_opps)} found):")
        print("=" * 100)
        
        for i, opp in enumerate(sorted_opps[:20], 1):  # Show top 20
            current_bid = opp['current_bid']
            retail = opp['retail_price']
            discount = opp['discount']
            score = opp['opportunity_score']
            
            # Status indicators
            if current_bid == 0:
                status = "🟢 No Bids"
            elif opp['total_bids'] < 5:
                status = "🟡 Low Activity"
            elif opp['total_bids'] < 15:
                status = "🟠 Moderate"
            else:
                status = "🔴 High Activity"
            
            shipping = "📦" if opp['is_shippable'] else "🏪"
            
            print(f"{i:2d}. {status} {shipping} {opp['product_name'][:55]}")
            print(f"    💰 Current: ${current_bid:.2f} | Retail: ${retail:.2f} | Discount: {discount:.1f}%")
            print(f"    🏢 {opp['location']} | 🎯 Score: {score:.1f}")
            print(f"    📊 {opp['total_bids']} bids from {opp['unique_bidders']} bidders | Lot #{opp['lot_number']}")
            print(f"    📋 Auction #{opp['auction_number']} | {opp['condition']}")
            print()
    
    def display_summary(self, opportunities: List[Dict]):
        """Display summary statistics."""
        if not opportunities:
            return
        
        total = len(opportunities)
        no_bids = len([o for o in opportunities if o['current_bid'] == 0])
        high_discount = len([o for o in opportunities if o['discount'] > 70])
        shippable = len([o for o in opportunities if o['is_shippable']])
        
        # Location breakdown
        locations = {}
        for opp in opportunities:
            loc = opp['location']
            locations[loc] = locations.get(loc, 0) + 1
        
        print(f"\n📊 SUMMARY:")
        print("=" * 40)
        print(f"📦 Total Opportunities: {total}")
        print(f"🟢 No Bids Yet: {no_bids}")
        print(f"💎 High Discount (>70%): {high_discount}")
        print(f"📦 Shippable: {shippable}")
        print(f"\n🏢 By Location:")
        for loc, count in sorted(locations.items()):
            print(f"   {loc}: {count}")
    
    async def run_search_monitor(self):
        """Run the search API monitor."""
        print("🚀 Simple Search API Monitor")
        print("=" * 50)
        print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector) as session:
            
            all_lots = []
            
            # 1. Search by your successful categories
            print("\n1. 🔍 Searching by Categories...")
            search_terms = ['electronics', 'gaming', 'headphones', 'laptop', 'processor', 'microphone']
            
            for term in search_terms:
                lots = await self.search_lots(session, term, 50)
                all_lots.extend(lots)
                await asyncio.sleep(0.3)  # Be respectful
            
            # 2. Search by SC locations
            print("\n2. 🏢 Searching by SC Locations...")
            for location in self.sc_locations:
                lots = await self.search_by_location(session, location, 30)
                all_lots.extend(lots)
                await asyncio.sleep(0.3)
            
            # 3. Remove duplicates and analyze
            print("\n3. 📊 Analyzing Opportunities...")
            unique_lots = {}
            for lot in all_lots:
                lot_id = lot.get('lot_id')
                if lot_id and lot_id not in unique_lots:
                    unique_lots[lot_id] = lot
            
            print(f"   Found {len(unique_lots)} unique lots")
            
            # Analyze each lot
            opportunities = []
            for lot in unique_lots.values():
                analyzed = self.analyze_lot(lot)
                if analyzed['opportunity_score'] > 50:  # Only show decent opportunities
                    opportunities.append(analyzed)
            
            # 4. Display results
            self.display_opportunities(opportunities)
            self.display_summary(opportunities)
            
            print(f"\n✅ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    monitor = SimpleSearchAPIMonitor()
    await monitor.run_search_monitor()

if __name__ == "__main__":
    asyncio.run(main()) 