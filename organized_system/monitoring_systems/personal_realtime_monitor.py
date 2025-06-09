#!/usr/bin/env python3
"""
🎯 Personal Real-time Monitor - Your Personalized Auction Assistant
Monitors auctions and provides personalized recommendations based on YOUR bidding history
"""

import asyncio
import aiohttp
import json
import sqlite3
from datetime import datetime
from personalized_analytics import PersonalizedAnalytics
import os

class PersonalRealtimeMonitor:
    def __init__(self):
        self.analytics = PersonalizedAnalytics()
        self.session = None
        self.credentials_file = os.path.expanduser("~/.macbid_scraper/credentials.json")
        self.load_credentials()
        
    def load_credentials(self):
        """Load stored credentials."""
        try:
            with open(self.credentials_file, 'r') as f:
                creds = json.load(f)
                self.username = creds.get('username')
                self.session_cookie = creds.get('session_cookie')
                self.customer_id = creds.get('customer_id')
        except:
            print("❌ No credentials found. Run setup_personal_credentials.py first!")
            exit(1)
    
    async def get_current_auctions(self):
        """Get current auctions with your session."""
        if not self.session:
            connector = aiohttp.TCPConnector(ssl=False)
            self.session = aiohttp.ClientSession(connector=connector)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Cookie': f'ASP.NET_SessionId={self.session_cookie}' if self.session_cookie else ''
        }
        
        try:
            # Get current auctions
            url = "https://api.macdiscount.com/auction/getAuctionItems?loc=17,18&pg=1&ppg=50"
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('auctionItems', [])
        except Exception as e:
            print(f"❌ Error fetching auctions: {e}")
        
        return []
    
    def analyze_item_for_you(self, item):
        """Analyze an auction item specifically for your bidding patterns."""
        # Extract item details
        product_name = item.get('productName', '')
        brand = self.extract_brand(product_name)
        category = self.categorize_item(product_name)
        retail_price = float(item.get('retailPrice', 0))
        instant_win = float(item.get('instantWinPrice', 0))
        current_bid = float(item.get('currentBid', 0))
        lot_id = item.get('lotNumber', '')
        
        # Create item dict for analysis
        item_dict = {
            'product_name': product_name,
            'brand': brand,
            'category': category,
            'retail_price': retail_price,
            'instant_win_price': instant_win,
            'current_bid': current_bid,
            'lot_id': lot_id
        }
        
        # Get your personal recommendation
        try:
            personal_stats = self.analytics.analyze_personal_patterns()
            if not personal_stats:
                return None
                
            # Calculate your success rates for this item
            category_success = personal_stats['category_stats'].get(category, {})
            category_win_rate = category_success.get('wins', 0) / category_success.get('total', 1) * 100 if category_success.get('total', 0) > 0 else 50
            
            brand_success = personal_stats['brand_stats'].get(brand, {})
            brand_win_rate = brand_success.get('wins', 0) / brand_success.get('total', 1) * 100 if brand_success.get('total', 0) > 0 else 50
            
            # Your optimal bid based on your 59.6% sweet spot
            if instant_win > 0:
                your_optimal_bid = instant_win * personal_stats['avg_win_ratio']
            else:
                your_optimal_bid = retail_price * 0.3  # Conservative fallback
            
            # Calculate opportunity score
            opportunity_score = 0
            
            # Higher score for categories/brands you're successful with
            if category_win_rate >= 75:
                opportunity_score += 30
            elif category_win_rate >= 50:
                opportunity_score += 20
            elif category_win_rate >= 25:
                opportunity_score += 10
            
            if brand_win_rate >= 75:
                opportunity_score += 30
            elif brand_win_rate >= 50:
                opportunity_score += 20
            elif brand_win_rate >= 25:
                opportunity_score += 10
            
            # Higher score if current bid is below your optimal bid
            if current_bid < your_optimal_bid:
                bid_gap = your_optimal_bid - current_bid
                opportunity_score += min(40, bid_gap / your_optimal_bid * 100)
            
            # Bonus for high savings potential
            if instant_win > 0:
                potential_savings = (instant_win - your_optimal_bid) / instant_win * 100
                if potential_savings >= 50:
                    opportunity_score += 20
                elif potential_savings >= 30:
                    opportunity_score += 10
            
            return {
                'item': item_dict,
                'your_optimal_bid': your_optimal_bid,
                'category_success_rate': category_win_rate,
                'brand_success_rate': brand_win_rate,
                'opportunity_score': min(100, opportunity_score),
                'current_bid': current_bid,
                'instant_win': instant_win,
                'potential_savings': (instant_win - your_optimal_bid) if instant_win > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Error analyzing item: {e}")
            return None
    
    def extract_brand(self, product_name):
        """Extract brand from product name."""
        brands = ['Apple', 'Sony', 'Samsung', 'Nintendo', 'Microsoft', 'Bose', 'Beats', 
                 'Turtle Beach', 'Logitech', 'Razer', 'SteelSeries', 'HyperX', 'Corsair',
                 'Dell', 'HP', 'Lenovo', 'ASUS', 'MSI', 'Alienware', 'MacBook', 'iPad',
                 'iPhone', 'AirPods', 'PlayStation', 'Xbox', 'Switch']
        
        product_upper = product_name.upper()
        for brand in brands:
            if brand.upper() in product_upper:
                return brand
        return 'Other'
    
    def categorize_item(self, product_name):
        """Categorize item based on product name."""
        product_lower = product_name.lower()
        
        if any(word in product_lower for word in ['headphone', 'headset', 'earphone', 'earbud', 'airpods', 'speaker', 'soundbar', 'audio']):
            return 'Audio'
        elif any(word in product_lower for word in ['iphone', 'phone', 'smartphone', 'mobile']):
            return 'Mobile'
        elif any(word in product_lower for word in ['laptop', 'macbook', 'computer', 'pc', 'desktop']):
            return 'Computing'
        elif any(word in product_lower for word in ['gaming', 'xbox', 'playstation', 'nintendo', 'switch', 'ps5', 'ps4']):
            return 'Gaming'
        elif any(word in product_lower for word in ['tablet', 'ipad']):
            return 'Tablet'
        elif any(word in product_lower for word in ['tv', 'television', 'monitor', 'display']):
            return 'Display'
        else:
            return 'Electronics'
    
    async def monitor_for_opportunities(self):
        """Monitor auctions for personalized opportunities."""
        print("🎯 PERSONAL REAL-TIME AUCTION MONITOR")
        print("=" * 60)
        print(f"👤 Monitoring for: {self.username}")
        print(f"🎲 Using your 75% win rate strategy")
        print(f"💰 Targeting your 57% average savings")
        print("=" * 60)
        
        while True:
            try:
                print(f"\n🔍 Scanning auctions... {datetime.now().strftime('%H:%M:%S')}")
                
                auctions = await self.get_current_auctions()
                if not auctions:
                    print("❌ No auctions found")
                    await asyncio.sleep(30)
                    continue
                
                opportunities = []
                
                for item in auctions:
                    analysis = self.analyze_item_for_you(item)
                    if analysis and analysis['opportunity_score'] >= 60:  # High opportunity threshold
                        opportunities.append(analysis)
                
                # Sort by opportunity score
                opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
                
                if opportunities:
                    print(f"\n🚨 FOUND {len(opportunities)} PERSONALIZED OPPORTUNITIES!")
                    print("=" * 60)
                    
                    for i, opp in enumerate(opportunities[:5], 1):  # Top 5
                        item = opp['item']
                        print(f"\n🎯 OPPORTUNITY #{i} (Score: {opp['opportunity_score']:.0f}/100)")
                        print(f"📦 {item['product_name']}")
                        print(f"🏷️ Brand: {item['brand']} | Category: {item['category']}")
                        print(f"💰 Retail: ${item['retail_price']:,.2f} | Instant Win: ${opp['instant_win']:,.2f}")
                        print(f"📊 Current Bid: ${opp['current_bid']:,.2f}")
                        print(f"🎯 YOUR Optimal Bid: ${opp['your_optimal_bid']:,.2f}")
                        print(f"📈 Your Success Rates: {item['category']} {opp['category_success_rate']:.0f}% | {item['brand']} {opp['brand_success_rate']:.0f}%")
                        print(f"💵 Potential Savings: ${opp['potential_savings']:,.2f}")
                        
                        # Risk assessment
                        if opp['your_optimal_bid'] > opp['current_bid'] * 1.5:
                            risk = "🟢 LOW RISK"
                        elif opp['your_optimal_bid'] > opp['current_bid'] * 1.2:
                            risk = "🟡 MEDIUM RISK"
                        else:
                            risk = "🔴 HIGH RISK"
                        
                        print(f"⚖️ Risk Level: {risk}")
                        print(f"🔗 Lot: {item['lot_id']}")
                        print("-" * 40)
                else:
                    print("✅ No high-opportunity items found matching your profile")
                
                print(f"\n⏰ Next scan in 30 seconds...")
                await asyncio.sleep(30)
                
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error during monitoring: {e}")
                await asyncio.sleep(30)
        
        if self.session:
            await self.session.close()

async def main():
    """Main function to run personal monitoring."""
    monitor = PersonalRealtimeMonitor()
    await monitor.monitor_for_opportunities()

if __name__ == "__main__":
    asyncio.run(main()) 