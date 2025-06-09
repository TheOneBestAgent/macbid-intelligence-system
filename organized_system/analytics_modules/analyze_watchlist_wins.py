#!/usr/bin/env python3
"""
🔍 Analyze Watchlist Wins
Check if the 50 watchlist won items are actually your winning bids
"""

import json
import os
import glob
from datetime import datetime

class WatchlistWinAnalyzer:
    def __init__(self):
        self.load_all_data()
        
    def load_all_data(self):
        """Load all available data files."""
        # Load purchase data
        invoice_files = glob.glob("personal_invoices_*.json")
        item_files = glob.glob("personal_items_*.json")
        
        self.invoices = []
        self.items = []
        
        if invoice_files:
            latest_invoices = max(invoice_files)
            with open(latest_invoices, 'r') as f:
                self.invoices = json.load(f)
        
        if item_files:
            latest_items = max(item_files)
            with open(latest_items, 'r') as f:
                self.items = json.load(f)
        
        # Load watchlist data
        watchlist_files = glob.glob("complete_watchlist_*.json")
        self.watchlist_data = {}
        
        if watchlist_files:
            latest_watchlist = max(watchlist_files)
            with open(latest_watchlist, 'r') as f:
                self.watchlist_data = json.load(f)
        
        # Load bid history
        bid_files = glob.glob("complete_bid_history_*.json")
        self.bid_history = []
        
        if bid_files:
            latest_bids = max(bid_files)
            with open(latest_bids, 'r') as f:
                self.bid_history = json.load(f)
        
        print(f"📦 Loaded data:")
        print(f"   Invoices: {len(self.invoices)}")
        print(f"   Items: {len(self.items)}")
        print(f"   Watchlist Won: {len(self.watchlist_data.get('won', []))}")
        print(f"   Watchlist Lost: {len(self.watchlist_data.get('lost', []))}")
        print(f"   Bid History: {len(self.bid_history)}")
    
    def analyze_watchlist_won_items(self):
        """Analyze the watchlist won items in detail."""
        print(f"\n🏆 ANALYZING WATCHLIST WON ITEMS")
        print("=" * 60)
        
        won_items = self.watchlist_data.get('won', [])
        
        if not won_items:
            print("❌ No watchlist won items found")
            return
        
        print(f"📊 Found {len(won_items)} watchlist won items")
        
        # Show sample items
        print(f"\n📋 SAMPLE WATCHLIST WON ITEMS:")
        for i, item in enumerate(won_items[:5], 1):
            print(f"\n{i}. Watchlist Item:")
            for key, value in item.items():
                if key in ['id', 'customer_id', 'closed_date', 'winning_bid', 'product_name', 'description']:
                    print(f"   {key}: {value}")
        
        # Check if these match your purchase items
        print(f"\n🔍 MATCHING WITH PURCHASE ITEMS:")
        matches = 0
        
        for purchase_item in self.items[:10]:  # Check first 10
            purchase_desc = purchase_item.get('description', '').lower()
            purchase_total = float(purchase_item.get('total', 0))
            
            for watchlist_item in won_items:
                # Try different fields for product name
                watchlist_desc = ''
                if 'product_name' in watchlist_item:
                    watchlist_desc = str(watchlist_item['product_name']).lower()
                elif 'description' in watchlist_item:
                    watchlist_desc = str(watchlist_item['description']).lower()
                
                # Try to match by name similarity
                if purchase_desc and watchlist_desc:
                    # Simple matching - check if significant words overlap
                    purchase_words = set(purchase_desc.split())
                    watchlist_words = set(watchlist_desc.split())
                    
                    common_words = purchase_words.intersection(watchlist_words)
                    if len(common_words) >= 2:  # At least 2 words in common
                        matches += 1
                        print(f"   ✅ MATCH: {purchase_desc[:40]}... = {watchlist_desc[:40]}...")
                        print(f"      Purchase: ${purchase_total} | Watchlist: ${watchlist_item.get('winning_bid', 'N/A')}")
                        break
        
        print(f"\n📊 Found {matches} potential matches between purchase and watchlist data")
        
        return won_items
    
    def compare_all_data_sources(self):
        """Compare all data sources to understand the relationships."""
        print(f"\n🔍 COMPREHENSIVE DATA COMPARISON")
        print("=" * 60)
        
        print(f"📊 Data Source Summary:")
        print(f"   Purchase Items (Invoice Items): {len(self.items)}")
        print(f"   Purchase Invoices: {len(self.invoices)}")
        print(f"   Watchlist Won: {len(self.watchlist_data.get('won', []))}")
        print(f"   Watchlist Lost: {len(self.watchlist_data.get('lost', []))}")
        print(f"   Bid History (Losing Bids): {len(self.bid_history)}")
        
        # Analyze dates
        print(f"\n📅 DATE ANALYSIS:")
        
        # Purchase dates
        if self.items:
            purchase_dates = [item.get('date_created', '')[:10] for item in self.items if item.get('date_created')]
            if purchase_dates:
                print(f"   Purchase date range: {min(purchase_dates)} to {max(purchase_dates)}")
        
        # Watchlist won dates
        won_items = self.watchlist_data.get('won', [])
        if won_items:
            won_dates = [item.get('closed_date', '')[:10] for item in won_items if item.get('closed_date')]
            if won_dates:
                print(f"   Watchlist won date range: {min(won_dates)} to {max(won_dates)}")
        
        # Bid history dates
        if self.bid_history:
            bid_dates = [bid.get('date_created', '')[:10] for bid in self.bid_history if bid.get('date_created')]
            if bid_dates:
                print(f"   Bid history date range: {min(bid_dates)} to {max(bid_dates)}")
    
    def generate_theory(self):
        """Generate a theory about how the data relates."""
        print(f"\n🧠 DATA RELATIONSHIP THEORY")
        print("=" * 50)
        
        purchase_count = len(self.items)
        watchlist_won_count = len(self.watchlist_data.get('won', []))
        bid_history_count = len(self.bid_history)
        
        print(f"🎯 THEORY: Based on the data patterns...")
        print()
        
        if purchase_count == watchlist_won_count:
            print(f"✅ LIKELY MATCH: Purchase Items ({purchase_count}) = Watchlist Won ({watchlist_won_count})")
            print(f"   Theory: Your 'watchlist won' items ARE your successful bids!")
            print(f"   You add items to watchlist, then bid and win them.")
            print()
            print(f"📋 This means:")
            print(f"   • Bid History = Your losing bids ({bid_history_count} items)")
            print(f"   • Watchlist Won = Your winning bids ({watchlist_won_count} items)")
            print(f"   • Purchase Items = Invoice records of your wins ({purchase_count} items)")
            print()
            print(f"🏆 YOUR ACTUAL PERFORMANCE:")
            total_bids = bid_history_count + watchlist_won_count
            win_rate = (watchlist_won_count / total_bids * 100) if total_bids > 0 else 0
            print(f"   Total Bids: {total_bids} ({bid_history_count} lost + {watchlist_won_count} won)")
            print(f"   Win Rate: {win_rate:.1f}%")
            print(f"   You ARE a successful bidder!")
        else:
            print(f"❓ UNCLEAR: Purchase Items ({purchase_count}) ≠ Watchlist Won ({watchlist_won_count})")
            print(f"   Need more investigation to understand the relationship.")

def main():
    """Main analysis function."""
    analyzer = WatchlistWinAnalyzer()
    
    print("🔍 WATCHLIST WIN ANALYSIS")
    print("=" * 60)
    print("Investigating if watchlist won items are your actual winning bids...")
    print()
    
    # Analyze watchlist won items
    won_items = analyzer.analyze_watchlist_won_items()
    
    # Compare all data sources
    analyzer.compare_all_data_sources()
    
    # Generate theory
    analyzer.generate_theory()
    
    # Save analysis
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    analysis_report = {
        'timestamp': timestamp,
        'purchase_items': len(analyzer.items),
        'watchlist_won': len(analyzer.watchlist_data.get('won', [])),
        'watchlist_lost': len(analyzer.watchlist_data.get('lost', [])),
        'bid_history': len(analyzer.bid_history),
        'theory': 'Watchlist won items likely represent winning bids'
    }
    
    filename = f"watchlist_analysis_report_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(analysis_report, f, indent=2)
    
    print(f"\n💾 Analysis report saved to: {filename}")

if __name__ == "__main__":
    main() 