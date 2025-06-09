#!/usr/bin/env python3
"""
🏆 Winning Bid Pattern Analyzer - Find Your Sweet Spot Bidding Strategy
Track winning bid patterns, identify undervalued categories, and find optimal bid amounts
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class WinningBidAnalyzer:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        self.db_file = "bid_analysis.db"
        self.init_database()
        
        # Categories for bid analysis
        self.categories = {
            'Electronics': ['laptop', 'phone', 'tablet', 'tv', 'camera'],
            'Audio': ['headphones', 'speaker', 'soundbar', 'beats', 'bose'],
            'Appliances': ['refrigerator', 'washer', 'dryer', 'microwave'],
            'Tools': ['drill', 'saw', 'dewalt', 'milwaukee'],
            'Gaming': ['xbox', 'playstation', 'nintendo', 'gaming'],
            'Luxury': ['rolex', 'omega', 'diamond', 'gold', 'jewelry']
        }
        
    def init_database(self):
        """Initialize bid analysis database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                product_name TEXT,
                category TEXT,
                auction_location TEXT,
                retail_price REAL,
                instant_win_price REAL,
                current_bid REAL,
                bid_ratio REAL,
                value_score REAL,
                sweet_spot_score REAL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def create_session(self):
        """Create HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=15)
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
                    
                    sc_hits = []
                    for hit in hits:
                        if hit.get('auction_location') in self.sc_locations:
                            sc_hits.append(hit)
                            
                    return sc_hits
                else:
                    return []
        except Exception as e:
            return []
            
    def categorize_item(self, product_name):
        """Categorize item based on product name."""
        if not product_name:
            return "Unknown"
            
        product_lower = product_name.lower()
        
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword.lower() in product_lower:
                    return category
                    
        return "Other"
        
    def calculate_bid_metrics(self, item):
        """Calculate comprehensive bid analysis metrics."""
        retail_price = item.get('retail_price', 0)
        instant_win_price = item.get('instant_win_price', 0)
        current_bid = item.get('current_bid', 0)
        
        metrics = {
            'bid_ratio': 0,
            'value_score': 0,
            'sweet_spot_score': 0,
            'discount_potential': 0,
            'competition_level': 'LOW'
        }
        
        if retail_price > 0:
            # Bid ratio (current bid vs retail price)
            if current_bid > 0:
                metrics['bid_ratio'] = current_bid / retail_price
                
                # Competition level based on bid ratio
                if metrics['bid_ratio'] > 0.7:
                    metrics['competition_level'] = 'HIGH'
                elif metrics['bid_ratio'] > 0.4:
                    metrics['competition_level'] = 'MEDIUM'
                else:
                    metrics['competition_level'] = 'LOW'
                    
            # Value score (potential savings vs retail)
            if instant_win_price > 0:
                discount = (retail_price - instant_win_price) / retail_price
                metrics['value_score'] = min(discount * 100, 100)
                metrics['discount_potential'] = discount * 100
                
            # Sweet spot score (optimal bidding range)
            # Higher score = better opportunity for strategic bidding
            if instant_win_price > 0 and current_bid >= 0:
                # Ideal range: 40-70% of retail price
                if current_bid == 0:
                    # No bids yet - high opportunity
                    metrics['sweet_spot_score'] = 90
                else:
                    bid_percentage = (current_bid / retail_price) * 100
                    if 40 <= bid_percentage <= 70:
                        metrics['sweet_spot_score'] = 80
                    elif bid_percentage < 40:
                        metrics['sweet_spot_score'] = 95  # Great opportunity
                    else:
                        metrics['sweet_spot_score'] = 30  # Too competitive
                        
        return metrics
        
    async def collect_bid_data(self):
        """Collect bid pattern data across categories."""
        print("🏆 WINNING BID PATTERN ANALYZER")
        print("📊 Analyzing bid patterns and sweet spots...")
        print()
        
        all_items = []
        seen_lot_ids = set()
        
        for category, keywords in self.categories.items():
            print(f"🔍 Analyzing {category} bidding patterns...")
            
            category_items = []
            
            for keyword in keywords:
                results = await self.search_for_term(keyword)
                
                for result in results:
                    lot_id = result.get('lot_id')
                    if lot_id and lot_id not in seen_lot_ids:
                        retail_price = result.get('retail_price', 0)
                        
                        if retail_price >= 50:  # Minimum value threshold
                            # Calculate bid metrics
                            bid_metrics = self.calculate_bid_metrics(result)
                            
                            # Enhance result
                            result['category'] = category
                            result['bid_metrics'] = bid_metrics
                            
                            category_items.append(result)
                            seen_lot_ids.add(lot_id)
                            
                await asyncio.sleep(0.15)
                
            all_items.extend(category_items)
            print(f"   Found {len(category_items)} {category} items")
            
        return all_items
        
    def analyze_bid_patterns(self, items):
        """Analyze bid patterns by category."""
        category_analysis = {}
        
        # Group by category
        by_category = defaultdict(list)
        for item in items:
            category = item.get('category', 'Unknown')
            by_category[category].append(item)
            
        # Analyze each category
        for category, category_items in by_category.items():
            if len(category_items) < 3:  # Need minimum sample
                continue
                
            # Extract metrics
            bid_ratios = []
            value_scores = []
            sweet_spot_scores = []
            retail_prices = []
            
            for item in category_items:
                metrics = item.get('bid_metrics', {})
                bid_ratios.append(metrics.get('bid_ratio', 0))
                value_scores.append(metrics.get('value_score', 0))
                sweet_spot_scores.append(metrics.get('sweet_spot_score', 0))
                retail_prices.append(item.get('retail_price', 0))
                
            # Calculate category statistics
            avg_bid_ratio = statistics.mean([r for r in bid_ratios if r > 0]) if any(bid_ratios) else 0
            avg_value_score = statistics.mean(value_scores)
            avg_sweet_spot = statistics.mean(sweet_spot_scores)
            avg_retail_price = statistics.mean(retail_prices)
            
            # Competition analysis
            high_competition = len([r for r in bid_ratios if r > 0.6])
            low_competition = len([r for r in bid_ratios if r < 0.3])
            no_bids = len([r for r in bid_ratios if r == 0])
            
            category_analysis[category] = {
                'total_items': len(category_items),
                'avg_bid_ratio': avg_bid_ratio,
                'avg_value_score': avg_value_score,
                'avg_sweet_spot_score': avg_sweet_spot,
                'avg_retail_price': avg_retail_price,
                'high_competition_items': high_competition,
                'low_competition_items': low_competition,
                'no_bid_items': no_bids,
                'opportunity_rating': self.calculate_opportunity_rating(avg_sweet_spot, no_bids, len(category_items))
            }
            
        return category_analysis
        
    def calculate_opportunity_rating(self, avg_sweet_spot, no_bids, total_items):
        """Calculate opportunity rating for category."""
        # Base score from sweet spot average
        score = avg_sweet_spot
        
        # Bonus for items with no bids
        no_bid_ratio = no_bids / total_items if total_items > 0 else 0
        score += no_bid_ratio * 20
        
        # Rating categories
        if score >= 80:
            return "EXCELLENT"
        elif score >= 65:
            return "GOOD"
        elif score >= 50:
            return "FAIR"
        else:
            return "POOR"
            
    def find_sweet_spot_opportunities(self, items):
        """Find the best sweet spot bidding opportunities."""
        opportunities = []
        
        for item in items:
            metrics = item.get('bid_metrics', {})
            sweet_spot_score = metrics.get('sweet_spot_score', 0)
            
            # High sweet spot opportunities
            if sweet_spot_score >= 80:
                retail_price = item.get('retail_price', 0)
                instant_win_price = item.get('instant_win_price', 0)
                current_bid = item.get('current_bid', 0)
                
                # Calculate suggested bid range
                suggested_min = retail_price * 0.3  # 30% of retail
                suggested_max = retail_price * 0.6  # 60% of retail
                
                opportunities.append({
                    'item': item,
                    'sweet_spot_score': sweet_spot_score,
                    'suggested_bid_min': suggested_min,
                    'suggested_bid_max': suggested_max,
                    'current_bid': current_bid,
                    'competition_level': metrics.get('competition_level', 'UNKNOWN'),
                    'value_score': metrics.get('value_score', 0)
                })
                
        # Sort by sweet spot score
        opportunities.sort(key=lambda x: x['sweet_spot_score'], reverse=True)
        return opportunities
        
    def display_bid_analysis_report(self, items, category_analysis, opportunities):
        """Display comprehensive bid analysis report."""
        print(f"\n🏆 WINNING BID PATTERN ANALYSIS REPORT")
        print("=" * 80)
        
        if not items:
            print("❌ No bid data collected")
            return
            
        print(f"📊 Analyzed {len(items)} items across {len(self.categories)} categories")
        print()
        
        # Overall market analysis
        total_retail_value = sum(item.get('retail_price', 0) for item in items)
        avg_sweet_spot = statistics.mean([item.get('bid_metrics', {}).get('sweet_spot_score', 0) for item in items])
        no_bid_items = len([item for item in items if item.get('current_bid', 0) == 0])
        
        print(f"💰 MARKET OVERVIEW")
        print("-" * 50)
        print(f"📦 Total Items Analyzed: {len(items)}")
        print(f"💵 Total Retail Value: ${total_retail_value:,.2f}")
        print(f"🎯 Average Sweet Spot Score: {avg_sweet_spot:.1f}/100")
        print(f"🆓 Items with No Bids: {no_bid_items} ({no_bid_items/len(items)*100:.1f}%)")
        
        # Category analysis
        print(f"\n📂 CATEGORY BID ANALYSIS")
        print("-" * 80)
        print(f"{'Category':12s} | {'Opportunity':11s} | {'Avg Sweet Spot':13s} | {'No Bids':8s} | {'Items':6s}")
        print("-" * 80)
        
        for category, analysis in sorted(category_analysis.items(), 
                                       key=lambda x: x[1]['avg_sweet_spot_score'], reverse=True):
            opportunity = analysis['opportunity_rating']
            sweet_spot = analysis['avg_sweet_spot_score']
            no_bids = analysis['no_bid_items']
            total = analysis['total_items']
            
            # Color coding
            if opportunity == "EXCELLENT":
                icon = "🟢"
            elif opportunity == "GOOD":
                icon = "🟡"
            else:
                icon = "🔴"
                
            print(f"{icon} {category:10s} | {opportunity:9s} | {sweet_spot:11.1f} | {no_bids:6d} | {total:4d}")
            
        # Sweet spot opportunities
        if opportunities:
            print(f"\n🎯 TOP SWEET SPOT OPPORTUNITIES")
            print("-" * 80)
            
            for i, opp in enumerate(opportunities[:15], 1):
                item = opp['item']
                product_name = item.get('product_name', 'Unknown')[:45]
                retail_price = item.get('retail_price', 0)
                current_bid = opp['current_bid']
                suggested_min = opp['suggested_bid_min']
                suggested_max = opp['suggested_bid_max']
                sweet_spot_score = opp['sweet_spot_score']
                competition = opp['competition_level']
                location = item.get('auction_location', 'Unknown')
                
                comp_icon = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(competition, "❓")
                
                print(f"{i:2d}. 💎 {product_name}...")
                print(f"     💵 Retail: ${retail_price} | Current Bid: ${current_bid}")
                print(f"     🎯 Suggested Bid Range: ${suggested_min:.0f} - ${suggested_max:.0f}")
                print(f"     ⭐ Sweet Spot Score: {sweet_spot_score:.1f} | {comp_icon} Competition: {competition}")
                print(f"     📍 Location: {location}")
                print()
                
        # Bidding strategy recommendations
        print(f"\n💡 BIDDING STRATEGY RECOMMENDATIONS")
        print("-" * 60)
        
        if category_analysis:
            # Best category for bidding
            best_category = max(category_analysis.items(), key=lambda x: x[1]['avg_sweet_spot_score'])
            worst_category = min(category_analysis.items(), key=lambda x: x[1]['avg_sweet_spot_score'])
            
            print(f"✅ FOCUS ON: {best_category[0]}")
            print(f"   • High sweet spot score ({best_category[1]['avg_sweet_spot_score']:.1f})")
            print(f"   • {best_category[1]['no_bid_items']} items with no bids")
            print(f"   • Opportunity rating: {best_category[1]['opportunity_rating']}")
            print()
            print(f"❌ AVOID: {worst_category[0]}")
            print(f"   • Low sweet spot score ({worst_category[1]['avg_sweet_spot_score']:.1f})")
            print(f"   • High competition category")
            print()
            print(f"🎯 GENERAL STRATEGY:")
            print(f"   • Target items with 0 current bids")
            print(f"   • Bid 30-60% of retail price for best value")
            print(f"   • Focus on categories with 'EXCELLENT' or 'GOOD' ratings")
            print(f"   • Avoid items with >70% bid ratio (too competitive)")
            
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"bid_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'summary': {
                    'total_items': len(items),
                    'avg_sweet_spot_score': avg_sweet_spot,
                    'no_bid_items': no_bid_items
                },
                'category_analysis': category_analysis,
                'top_opportunities': opportunities[:20]
            }, f, indent=2)
            
        print(f"\n💾 Bid analysis report saved to: {filename}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Winning Bid Pattern Analyzer')
    parser.add_argument('--category', type=str, help='Analyze specific category only')
    parser.add_argument('--min-value', type=int, default=50, help='Minimum retail value')
    parser.add_argument('--opportunities-only', action='store_true', help='Show only sweet spot opportunities')
    
    args = parser.parse_args()
    
    analyzer = WinningBidAnalyzer()
    await analyzer.create_session()
    
    try:
        items = await analyzer.collect_bid_data()
        
        # Apply filters
        if args.category:
            items = [item for item in items if item.get('category', '').lower() == args.category.lower()]
            
        if args.min_value:
            items = [item for item in items if item.get('retail_price', 0) >= args.min_value]
            
        category_analysis = analyzer.analyze_bid_patterns(items)
        opportunities = analyzer.find_sweet_spot_opportunities(items)
        
        if args.opportunities_only and opportunities:
            print("🎯 SWEET SPOT OPPORTUNITIES")
            for i, opp in enumerate(opportunities[:10], 1):
                item = opp['item']
                print(f"{i}. {item.get('product_name', 'Unknown')[:40]}...")
                print(f"   Suggested bid: ${opp['suggested_bid_min']:.0f}-${opp['suggested_bid_max']:.0f}")
                print(f"   Sweet spot score: {opp['sweet_spot_score']:.1f}")
        else:
            analyzer.display_bid_analysis_report(items, category_analysis, opportunities)
            
    finally:
        await analyzer.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 