#!/usr/bin/env python3
"""
⌚ Luxury Watch Hunter - Find Premium Timepieces
Specialized tracker for Rolex, Omega, Cartier, and other luxury watches
"""

import asyncio
import aiohttp
import ssl
import json
from datetime import datetime
from collections import defaultdict

class LuxuryWatchHunter:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        
        # Luxury watch brands and their search terms
        self.watch_brands = {
            'Rolex': {
                'terms': ['rolex', 'rolex submariner', 'rolex datejust', 'rolex daytona', 'rolex gmt'],
                'tier': 'ULTRA_LUXURY',
                'avg_value': 8000,
                'keywords': ['submariner', 'datejust', 'daytona', 'gmt', 'oyster', 'perpetual']
            },
            'Omega': {
                'terms': ['omega', 'omega speedmaster', 'omega seamaster', 'omega constellation'],
                'tier': 'LUXURY',
                'avg_value': 3000,
                'keywords': ['speedmaster', 'seamaster', 'constellation', 'planet ocean', 'aqua terra']
            },
            'Cartier': {
                'terms': ['cartier', 'cartier tank', 'cartier santos', 'cartier ballon'],
                'tier': 'LUXURY',
                'avg_value': 4000,
                'keywords': ['tank', 'santos', 'ballon bleu', 'panthere', 'roadster']
            },
            'TAG Heuer': {
                'terms': ['tag heuer', 'tag heuer carrera', 'tag heuer formula'],
                'tier': 'PREMIUM',
                'avg_value': 1500,
                'keywords': ['carrera', 'formula', 'aquaracer', 'monaco', 'link']
            },
            'Breitling': {
                'terms': ['breitling', 'breitling navitimer', 'breitling superocean'],
                'tier': 'PREMIUM',
                'avg_value': 2500,
                'keywords': ['navitimer', 'superocean', 'avenger', 'chronomat']
            },
            'Patek Philippe': {
                'terms': ['patek philippe', 'patek'],
                'tier': 'ULTRA_LUXURY',
                'avg_value': 25000,
                'keywords': ['calatrava', 'nautilus', 'aquanaut', 'complications']
            },
            'Audemars Piguet': {
                'terms': ['audemars piguet', 'ap watch'],
                'tier': 'ULTRA_LUXURY',
                'avg_value': 20000,
                'keywords': ['royal oak', 'offshore', 'millenary']
            },
            'Tudor': {
                'terms': ['tudor', 'tudor black bay', 'tudor pelagos'],
                'tier': 'PREMIUM',
                'avg_value': 2000,
                'keywords': ['black bay', 'pelagos', 'ranger', 'heritage']
            },
            'Seiko': {
                'terms': ['seiko', 'seiko prospex', 'seiko presage', 'grand seiko'],
                'tier': 'ENTRY_LUXURY',
                'avg_value': 500,
                'keywords': ['prospex', 'presage', 'grand seiko', 'samurai', 'turtle']
            },
            'Citizen': {
                'terms': ['citizen', 'citizen eco drive', 'citizen promaster'],
                'tier': 'ENTRY_LUXURY',
                'avg_value': 300,
                'keywords': ['eco drive', 'promaster', 'satellite wave']
            }
        }
        
        # General watch terms
        self.general_watch_terms = [
            'watch', 'watches', 'timepiece', 'chronograph', 'automatic watch',
            'mechanical watch', 'luxury watch', 'swiss watch', 'diving watch'
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
            
    def identify_watch_brand(self, product_name):
        """Identify watch brand from product name."""
        if not product_name:
            return "Unknown"
            
        product_lower = product_name.lower()
        
        # Check for specific brands
        for brand, info in self.watch_brands.items():
            brand_lower = brand.lower()
            if brand_lower in product_lower:
                return brand
                
        # Check for general watch indicators
        watch_indicators = ['watch', 'timepiece', 'chronograph']
        for indicator in watch_indicators:
            if indicator in product_lower:
                return "Generic Watch"
                
        return "Unknown"
        
    def identify_watch_model(self, product_name, brand):
        """Identify specific watch model."""
        if not product_name or brand not in self.watch_brands:
            return "Unknown Model"
            
        product_lower = product_name.lower()
        brand_info = self.watch_brands[brand]
        
        for keyword in brand_info['keywords']:
            if keyword.lower() in product_lower:
                return keyword.title()
                
        return "Unknown Model"
        
    def calculate_watch_score(self, item):
        """Calculate luxury watch score."""
        retail_price = item.get('retail_price', 0)
        instant_win_price = item.get('instant_win_price', 0)
        current_bid = item.get('current_bid', 0)
        brand = item.get('watch_brand', 'Unknown')
        
        if retail_price <= 0:
            return 0
            
        # Base score from retail value
        value_score = min(retail_price / 1000, 15)  # Cap at 15 points
        
        # Brand tier bonus
        tier_bonus = 0
        if brand in self.watch_brands:
            tier = self.watch_brands[brand]['tier']
            if tier == 'ULTRA_LUXURY':
                tier_bonus = 10
            elif tier == 'LUXURY':
                tier_bonus = 7
            elif tier == 'PREMIUM':
                tier_bonus = 5
            elif tier == 'ENTRY_LUXURY':
                tier_bonus = 3
                
        # Savings bonus
        savings_bonus = 0
        if instant_win_price > 0:
            savings_percent = ((retail_price - instant_win_price) / retail_price) * 100
            savings_bonus = min(savings_percent / 10, 5)  # Cap at 5 points
            
        # Bidding activity (no bids = opportunity)
        bid_bonus = 3 if current_bid == 0 else 1
        
        # Condition bonus
        condition = item.get('condition', '').lower()
        condition_bonus = 0
        if 'new' in condition:
            condition_bonus = 2
        elif 'like new' in condition:
            condition_bonus = 1
            
        return value_score + tier_bonus + savings_bonus + bid_bonus + condition_bonus
        
    async def hunt_luxury_watches(self, min_value=200):
        """Hunt for luxury watches."""
        print(f"⌚ LUXURY WATCH HUNTER")
        print(f"💰 Minimum value: ${min_value}")
        print(f"🏷️ Tracking {len(self.watch_brands)} luxury brands")
        print()
        
        all_watches = []
        seen_lot_ids = set()
        
        # Search brand-specific terms
        for brand_name, brand_info in self.watch_brands.items():
            print(f"🏷️ Hunting {brand_name} ({brand_info['tier']})...")
            
            for term in brand_info['terms']:
                results = await self.search_for_term(term)
                
                for result in results:
                    lot_id = result.get('lot_id')
                    if lot_id and lot_id not in seen_lot_ids:
                        retail_price = result.get('retail_price', 0)
                        
                        if retail_price >= min_value:
                            # Enhance with watch-specific data
                            result['watch_brand'] = brand_name
                            result['watch_model'] = self.identify_watch_model(result.get('product_name', ''), brand_name)
                            result['brand_tier'] = brand_info['tier']
                            result['brand_avg_value'] = brand_info['avg_value']
                            
                            # Calculate savings
                            instant_win_price = result.get('instant_win_price', 0)
                            if instant_win_price > 0:
                                savings = retail_price - instant_win_price
                                savings_percent = (savings / retail_price) * 100
                                result['savings_amount'] = savings
                                result['savings_percent'] = savings_percent
                            else:
                                result['savings_amount'] = 0
                                result['savings_percent'] = 0
                                
                            result['watch_score'] = self.calculate_watch_score(result)
                            
                            all_watches.append(result)
                            seen_lot_ids.add(lot_id)
                            
                await asyncio.sleep(0.2)  # Rate limiting
                
        # Search general watch terms for unknown brands
        print(f"🔍 Searching general watch terms...")
        for term in self.general_watch_terms:
            results = await self.search_for_term(term)
            
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    retail_price = result.get('retail_price', 0)
                    
                    if retail_price >= min_value:
                        # Check if it's actually a watch
                        product_name = result.get('product_name', '').lower()
                        if any(indicator in product_name for indicator in ['watch', 'timepiece', 'chronograph']):
                            brand = self.identify_watch_brand(result.get('product_name', ''))
                            
                            result['watch_brand'] = brand
                            result['watch_model'] = "Unknown Model"
                            result['brand_tier'] = "UNKNOWN"
                            result['brand_avg_value'] = 0
                            
                            # Calculate savings
                            instant_win_price = result.get('instant_win_price', 0)
                            if instant_win_price > 0:
                                savings = retail_price - instant_win_price
                                savings_percent = (savings / retail_price) * 100
                                result['savings_amount'] = savings
                                result['savings_percent'] = savings_percent
                            else:
                                result['savings_amount'] = 0
                                result['savings_percent'] = 0
                                
                            result['watch_score'] = self.calculate_watch_score(result)
                            
                            all_watches.append(result)
                            seen_lot_ids.add(lot_id)
                            
            await asyncio.sleep(0.2)  # Rate limiting
            
        return all_watches
        
    def display_watch_report(self, watches):
        """Display luxury watch hunting report."""
        if not watches:
            print("❌ No luxury watches found")
            return
            
        print(f"\n⌚ LUXURY WATCH HUNTING REPORT")
        print("=" * 80)
        
        # Sort by watch score (highest first)
        watches.sort(key=lambda x: x.get('watch_score', 0), reverse=True)
        
        print(f"🎉 Found {len(watches)} luxury watches!")
        print()
        
        # Ultra luxury watches
        ultra_luxury = [w for w in watches if w.get('brand_tier') == 'ULTRA_LUXURY']
        if ultra_luxury:
            print(f"💎 ULTRA LUXURY WATCHES ({len(ultra_luxury)} found)")
            print("-" * 60)
            
            for watch in ultra_luxury:
                self.display_watch(watch, "💎")
                
        # Luxury watches
        luxury = [w for w in watches if w.get('brand_tier') == 'LUXURY']
        if luxury:
            print(f"🏆 LUXURY WATCHES ({len(luxury)} found)")
            print("-" * 60)
            
            for watch in luxury[:10]:  # Show top 10
                self.display_watch(watch, "🏆")
                
        # Premium watches
        premium = [w for w in watches if w.get('brand_tier') == 'PREMIUM']
        if premium:
            print(f"⭐ PREMIUM WATCHES ({len(premium)} found)")
            print("-" * 60)
            
            for watch in premium[:10]:  # Show top 10
                self.display_watch(watch, "⭐")
                
        # Top opportunities by score
        print(f"\n🎯 TOP 15 WATCH OPPORTUNITIES (by Score)")
        print("-" * 70)
        
        for i, watch in enumerate(watches[:15], 1):
            product_name = watch.get('product_name', 'Unknown')[:40]
            brand = watch.get('watch_brand', 'Unknown')
            model = watch.get('watch_model', 'Unknown')
            location = watch.get('auction_location', 'Unknown')
            retail_price = watch.get('retail_price', 0)
            instant_win = watch.get('instant_win_price', 0)
            current_bid = watch.get('current_bid', 0)
            watch_score = watch.get('watch_score', 0)
            savings = watch.get('savings_amount', 0)
            
            print(f"{i:2d}. ⌚ Score: {watch_score:.1f}")
            print(f"     🏷️ {brand} {model}")
            print(f"     📦 {product_name}...")
            print(f"     💰 ${retail_price} → ${instant_win} | 💸 Save ${savings:.0f}")
            print(f"     📍 {location} | 🔥 Current Bid: ${current_bid}")
            print()
            
        # No-bid luxury watches
        no_bid_watches = [w for w in watches if w.get('current_bid', 0) == 0]
        if no_bid_watches:
            print(f"🎯 NO-BID LUXURY WATCHES ({len(no_bid_watches)} opportunities)")
            print("-" * 60)
            
            # Sort by value
            no_bid_watches.sort(key=lambda x: x.get('retail_price', 0), reverse=True)
            
            for watch in no_bid_watches[:10]:
                brand = watch.get('watch_brand', 'Unknown')
                model = watch.get('watch_model', 'Unknown')
                retail_price = watch.get('retail_price', 0)
                instant_win = watch.get('instant_win_price', 0)
                location = watch.get('auction_location', 'Unknown')
                
                print(f"🎯 {brand} {model} | ${retail_price} → ${instant_win} | {location}")
                
        # Brand breakdown
        print(f"\n🏷️ WATCHES BY BRAND")
        print("-" * 40)
        
        by_brand = defaultdict(list)
        for watch in watches:
            brand = watch.get('watch_brand', 'Unknown')
            by_brand[brand].append(watch)
            
        sorted_brands = sorted(by_brand.items(), key=lambda x: len(x[1]), reverse=True)
        
        for brand, brand_watches in sorted_brands:
            total_value = sum(w.get('retail_price', 0) for w in brand_watches)
            avg_value = total_value / len(brand_watches) if brand_watches else 0
            tier = brand_watches[0].get('brand_tier', 'UNKNOWN') if brand_watches else 'UNKNOWN'
            no_bids = len([w for w in brand_watches if w.get('current_bid', 0) == 0])
            
            print(f"  {brand:15s} ({tier:12s}): {len(brand_watches):2d} watches | ${total_value:8,.0f} value | ${avg_value:6.0f} avg | {no_bids} no bids")
            
        # Location breakdown
        print(f"\n📍 WATCHES BY LOCATION")
        print("-" * 40)
        
        by_location = defaultdict(list)
        for watch in watches:
            location = watch.get('auction_location', 'Unknown')
            by_location[location].append(watch)
            
        for location in self.sc_locations:
            location_watches = by_location.get(location, [])
            if location_watches:
                total_value = sum(w.get('retail_price', 0) for w in location_watches)
                avg_score = sum(w.get('watch_score', 0) for w in location_watches) / len(location_watches)
                luxury_count = len([w for w in location_watches if w.get('brand_tier') in ['ULTRA_LUXURY', 'LUXURY']])
                
                print(f"  {location:12s}: {len(location_watches):2d} watches | ${total_value:8,.0f} value | {avg_score:.1f} avg score | {luxury_count} luxury")
                
        # Summary stats
        total_retail_value = sum(w.get('retail_price', 0) for w in watches)
        total_instant_win = sum(w.get('instant_win_price', 0) for w in watches if w.get('instant_win_price', 0) > 0)
        total_savings = sum(w.get('savings_amount', 0) for w in watches)
        
        print(f"\n📊 LUXURY WATCH SUMMARY")
        print("-" * 40)
        print(f"⌚ Total Watches Found: {len(watches)}")
        print(f"💰 Total Retail Value: ${total_retail_value:,.2f}")
        print(f"🏷️  Total Instant Win Value: ${total_instant_win:,.2f}")
        print(f"💸 Total Potential Savings: ${total_savings:,.2f}")
        
        if total_retail_value > 0:
            avg_savings_percent = (total_savings / total_retail_value) * 100
            print(f"📈 Average Savings: {avg_savings_percent:.1f}%")
            
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"luxury_watches_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(watches, f, indent=2)
        print(f"\n💾 Luxury watch data saved to: {filename}")
        
    def display_watch(self, watch, prefix=""):
        """Display a single watch."""
        product_name = watch.get('product_name', 'Unknown')[:45]
        brand = watch.get('watch_brand', 'Unknown')
        model = watch.get('watch_model', 'Unknown')
        location = watch.get('auction_location', 'Unknown')
        retail_price = watch.get('retail_price', 0)
        instant_win = watch.get('instant_win_price', 0)
        current_bid = watch.get('current_bid', 0)
        savings = watch.get('savings_amount', 0)
        condition = watch.get('condition', 'Unknown')
        closing_date = watch.get('expected_close_date', 'Unknown')
        
        print(f"{prefix} {brand} {model}")
        print(f"     📦 {product_name}...")
        print(f"     💰 ${retail_price} → ${instant_win} | 💸 Save ${savings:.0f}")
        print(f"     📍 {location} | 📦 {condition} | ⏰ Closes: {closing_date}")
        if current_bid > 0:
            print(f"     🔥 Current Bid: ${current_bid}")
        else:
            print(f"     🎯 NO BIDS - OPPORTUNITY!")
        print()

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Luxury Watch Hunter')
    parser.add_argument('--min-value', type=int, default=200, help='Minimum retail value')
    parser.add_argument('--brand', type=str, help='Hunt specific brand only')
    parser.add_argument('--luxury-only', action='store_true', help='Show only luxury tier and above')
    parser.add_argument('--no-bids-only', action='store_true', help='Show only items with no bids')
    
    args = parser.parse_args()
    
    hunter = LuxuryWatchHunter()
    
    if args.brand and args.brand not in hunter.watch_brands:
        print(f"❌ Unknown brand: {args.brand}")
        print(f"Available brands: {', '.join(hunter.watch_brands.keys())}")
        return
        
    await hunter.create_session()
    
    try:
        watches = await hunter.hunt_luxury_watches(args.min_value)
        
        if args.brand:
            watches = [w for w in watches if w.get('watch_brand') == args.brand]
            
        if args.luxury_only:
            watches = [w for w in watches if w.get('brand_tier') in ['ULTRA_LUXURY', 'LUXURY']]
            
        if args.no_bids_only:
            watches = [w for w in watches if w.get('current_bid', 0) == 0]
            
        hunter.display_watch_report(watches)
        
    finally:
        await hunter.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 