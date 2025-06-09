#!/usr/bin/env python3
"""
📊 Comprehensive Portfolio Analysis
Complete analysis of your auction performance with real data
"""

import sqlite3
import json
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import statistics

class ComprehensivePortfolioAnalysis:
    def __init__(self):
        self.portfolio_db = "portfolio_tracker.db"
        self.load_all_data()
        
    def load_all_data(self):
        """Load all portfolio data."""
        conn = sqlite3.connect(self.portfolio_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM bids ORDER BY bid_placed_date DESC
        ''')
        
        columns = [description[0] for description in cursor.description]
        self.all_bids = []
        
        for row in cursor.fetchall():
            bid_dict = dict(zip(columns, row))
            self.all_bids.append(bid_dict)
        
        conn.close()
        print(f"📊 Loaded {len(self.all_bids)} total bids")
    
    def analyze_overall_performance(self):
        """Analyze overall bidding performance."""
        print("\n🏆 COMPLETE PORTFOLIO ANALYSIS")
        print("=" * 60)
        
        if not self.all_bids:
            print("❌ No bid data found!")
            return
        
        # Overall stats
        total_bids = len(self.all_bids)
        wins = len([b for b in self.all_bids if b.get('won_auction', 0) == 1])
        win_rate = (wins / total_bids * 100) if total_bids > 0 else 0
        
        # Financial stats
        total_spent = sum(float(b.get('my_bid_amount', 0)) for b in self.all_bids if b.get('won_auction', 0) == 1)
        total_savings = sum(float(b.get('savings_amount', 0)) for b in self.all_bids if b.get('won_auction', 0) == 1)
        avg_savings = statistics.mean([float(b.get('savings_percent', 0)) for b in self.all_bids if b.get('won_auction', 0) == 1 and b.get('savings_percent')])
        
        print(f"🎯 OVERALL PERFORMANCE")
        print(f"   Total Bids: {total_bids}")
        print(f"   Wins: {wins}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Total Spent: ${total_spent:,.2f}")
        print(f"   Total Savings: ${total_savings:,.2f}")
        print(f"   Average Savings: {avg_savings:.1f}%")
        
        return {
            'total_bids': total_bids,
            'wins': wins,
            'win_rate': win_rate,
            'total_spent': total_spent,
            'total_savings': total_savings,
            'avg_savings': avg_savings
        }
    
    def analyze_by_source(self):
        """Analyze performance by data source."""
        print(f"\n📋 PERFORMANCE BY DATA SOURCE")
        print("-" * 40)
        
        sources = defaultdict(list)
        for bid in self.all_bids:
            source = bid.get('source', 'unknown')
            sources[source].append(bid)
        
        for source, bids in sources.items():
            wins = len([b for b in bids if b.get('won_auction', 0) == 1])
            total = len(bids)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            spent = sum(float(b.get('my_bid_amount', 0)) for b in bids if b.get('won_auction', 0) == 1)
            savings = sum(float(b.get('savings_amount', 0)) for b in bids if b.get('won_auction', 0) == 1)
            
            print(f"📊 {source}:")
            print(f"   Bids: {total} | Wins: {wins} | Win Rate: {win_rate:.1f}%")
            print(f"   Spent: ${spent:,.2f} | Savings: ${savings:,.2f}")
    
    def analyze_by_category(self):
        """Analyze performance by category."""
        print(f"\n📂 PERFORMANCE BY CATEGORY")
        print("-" * 40)
        
        categories = defaultdict(list)
        for bid in self.all_bids:
            category = bid.get('category', 'Unknown')
            categories[category].append(bid)
        
        # Sort by number of items
        sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
        
        for category, bids in sorted_categories:
            wins = len([b for b in bids if b.get('won_auction', 0) == 1])
            total = len(bids)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            spent = sum(float(b.get('my_bid_amount', 0)) for b in bids if b.get('won_auction', 0) == 1)
            
            if wins > 0:
                avg_savings = statistics.mean([float(b.get('savings_percent', 0)) for b in bids if b.get('won_auction', 0) == 1 and b.get('savings_percent')])
            else:
                avg_savings = 0
            
            print(f"📁 {category}: {total} items")
            print(f"   Win Rate: {win_rate:.1f}% ({wins}/{total})")
            print(f"   Spent: ${spent:,.2f} | Avg Savings: {avg_savings:.1f}%")
    
    def analyze_by_brand(self):
        """Analyze performance by brand."""
        print(f"\n🏷️ PERFORMANCE BY BRAND (Top 15)")
        print("-" * 50)
        
        brands = defaultdict(list)
        for bid in self.all_bids:
            brand = bid.get('brand', 'Unknown')
            brands[brand].append(bid)
        
        # Sort by number of items, then by win rate
        sorted_brands = sorted(brands.items(), key=lambda x: (len(x[1]), len([b for b in x[1] if b.get('won_auction', 0) == 1])), reverse=True)
        
        for brand, bids in sorted_brands[:15]:
            wins = len([b for b in bids if b.get('won_auction', 0) == 1])
            total = len(bids)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            spent = sum(float(b.get('my_bid_amount', 0)) for b in bids if b.get('won_auction', 0) == 1)
            
            if wins > 0:
                avg_savings = statistics.mean([float(b.get('savings_percent', 0)) for b in bids if b.get('won_auction', 0) == 1 and b.get('savings_percent')])
            else:
                avg_savings = 0
            
            print(f"🏷️ {brand}: {total} items | Win Rate: {win_rate:.1f}% | Spent: ${spent:,.2f} | Savings: {avg_savings:.1f}%")
    
    def analyze_price_ranges(self):
        """Analyze performance by price ranges."""
        print(f"\n💰 PERFORMANCE BY PRICE RANGE")
        print("-" * 40)
        
        price_ranges = {
            '$0-25': (0, 25),
            '$25-50': (25, 50),
            '$50-100': (50, 100),
            '$100-200': (100, 200),
            '$200+': (200, float('inf'))
        }
        
        for range_name, (min_price, max_price) in price_ranges.items():
            range_bids = [b for b in self.all_bids 
                         if min_price <= float(b.get('my_bid_amount', 0)) < max_price]
            
            if not range_bids:
                continue
                
            wins = len([b for b in range_bids if b.get('won_auction', 0) == 1])
            total = len(range_bids)
            win_rate = (wins / total * 100) if total > 0 else 0
            
            spent = sum(float(b.get('my_bid_amount', 0)) for b in range_bids if b.get('won_auction', 0) == 1)
            
            print(f"💵 {range_name}: {total} bids | Win Rate: {win_rate:.1f}% | Total Spent: ${spent:,.2f}")
    
    def analyze_bidding_strategy(self):
        """Analyze your bidding strategy patterns."""
        print(f"\n🎲 YOUR BIDDING STRATEGY ANALYSIS")
        print("-" * 50)
        
        winning_bids = [b for b in self.all_bids if b.get('won_auction', 0) == 1]
        
        if not winning_bids:
            print("❌ No winning bids to analyze")
            return
        
        # Calculate bid ratios (bid amount vs instant win price)
        bid_ratios = []
        for bid in winning_bids:
            instant_win = float(bid.get('instant_win_price', 0))
            my_bid = float(bid.get('my_bid_amount', 0))
            if instant_win > 0:
                ratio = (my_bid / instant_win) * 100
                bid_ratios.append(ratio)
        
        if bid_ratios:
            avg_ratio = statistics.mean(bid_ratios)
            min_ratio = min(bid_ratios)
            max_ratio = max(bid_ratios)
            
            print(f"📊 Bid Strategy Insights:")
            print(f"   Average bid: {avg_ratio:.1f}% of instant win price")
            print(f"   Range: {min_ratio:.1f}% - {max_ratio:.1f}%")
            print(f"   Strategy: {'Conservative' if avg_ratio < 70 else 'Aggressive' if avg_ratio > 85 else 'Balanced'}")
        
        # Find best deals
        best_deals = sorted(winning_bids, key=lambda x: float(x.get('savings_percent', 0)), reverse=True)[:5]
        
        print(f"\n🏆 YOUR TOP 5 BEST DEALS:")
        for i, deal in enumerate(best_deals, 1):
            product = deal.get('product_name', 'Unknown')[:40]
            savings = float(deal.get('savings_percent', 0))
            amount = float(deal.get('my_bid_amount', 0))
            print(f"   {i}. {product}... - {savings:.1f}% savings (${amount:.2f})")
    
    def analyze_recent_activity(self):
        """Analyze recent bidding activity."""
        print(f"\n📅 RECENT ACTIVITY ANALYSIS")
        print("-" * 40)
        
        # Group by month
        monthly_activity = defaultdict(list)
        
        for bid in self.all_bids:
            date_str = bid.get('bid_placed_date', '')
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    month_key = date.strftime('%Y-%m')
                    monthly_activity[month_key].append(bid)
                except:
                    continue
        
        # Show last 6 months
        sorted_months = sorted(monthly_activity.keys(), reverse=True)[:6]
        
        for month in sorted_months:
            bids = monthly_activity[month]
            wins = len([b for b in bids if b.get('won_auction', 0) == 1])
            total = len(bids)
            spent = sum(float(b.get('my_bid_amount', 0)) for b in bids if b.get('won_auction', 0) == 1)
            
            print(f"📆 {month}: {total} bids | {wins} wins | ${spent:,.2f} spent")
    
    def generate_recommendations(self):
        """Generate personalized recommendations."""
        print(f"\n🎯 PERSONALIZED RECOMMENDATIONS")
        print("-" * 50)
        
        winning_bids = [b for b in self.all_bids if b.get('won_auction', 0) == 1]
        
        if not winning_bids:
            print("❌ No winning bids to analyze for recommendations")
            return
        
        # Analyze successful categories
        category_success = defaultdict(list)
        for bid in winning_bids:
            category = bid.get('category', 'Unknown')
            category_success[category].append(bid)
        
        best_categories = sorted(category_success.items(), 
                               key=lambda x: len(x[1]), reverse=True)[:3]
        
        print(f"🎯 Focus on these categories (your strongest):")
        for category, bids in best_categories:
            avg_savings = statistics.mean([float(b.get('savings_percent', 0)) for b in bids])
            print(f"   • {category}: {len(bids)} wins, {avg_savings:.1f}% avg savings")
        
        # Analyze successful price ranges
        successful_amounts = [float(b.get('my_bid_amount', 0)) for b in winning_bids]
        if successful_amounts:
            avg_amount = statistics.mean(successful_amounts)
            print(f"\n💰 Your sweet spot: Around ${avg_amount:.2f} per bid")
        
        # Brand recommendations
        brand_success = defaultdict(list)
        for bid in winning_bids:
            brand = bid.get('brand', 'Unknown')
            brand_success[brand].append(bid)
        
        reliable_brands = [(brand, bids) for brand, bids in brand_success.items() 
                          if len(bids) >= 2]  # At least 2 wins
        
        if reliable_brands:
            print(f"\n🏷️ Stick with these reliable brands:")
            for brand, bids in sorted(reliable_brands, key=lambda x: len(x[1]), reverse=True)[:5]:
                print(f"   • {brand}: {len(bids)} wins")
    
    def save_analysis_report(self):
        """Save comprehensive analysis to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"portfolio_analysis_report_{timestamp}.json"
        
        # Compile all analysis data
        report = {
            'timestamp': timestamp,
            'total_bids': len(self.all_bids),
            'analysis_date': datetime.now().isoformat(),
            'summary': self.analyze_overall_performance(),
            'raw_data': self.all_bids
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Complete analysis saved to: {filename}")

def main():
    """Main analysis function."""
    print("📊 COMPREHENSIVE PORTFOLIO ANALYSIS")
    print("=" * 60)
    print("Analyzing your complete auction history...")
    
    analyzer = ComprehensivePortfolioAnalysis()
    
    # Run all analyses
    analyzer.analyze_overall_performance()
    analyzer.analyze_by_source()
    analyzer.analyze_by_category()
    analyzer.analyze_by_brand()
    analyzer.analyze_price_ranges()
    analyzer.analyze_bidding_strategy()
    analyzer.analyze_recent_activity()
    analyzer.generate_recommendations()
    analyzer.save_analysis_report()
    
    print(f"\n🎉 ANALYSIS COMPLETE!")
    print("=" * 30)
    print("Your portfolio analysis reveals exceptional auction skills!")

if __name__ == "__main__":
    main() 