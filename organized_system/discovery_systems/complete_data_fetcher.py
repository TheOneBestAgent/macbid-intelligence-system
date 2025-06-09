#!/usr/bin/env python3
"""
🎯 Complete Data Fetcher
Fetch ALL your auction data from the newly unlocked endpoints
"""

import json
import os
import asyncio
import aiohttp
from datetime import datetime

class CompleteDataFetcher:
    def __init__(self):
        self.tokens_file = os.path.expanduser("~/.macbid_scraper/api_tokens.json")
        self.load_tokens()
        
    def load_tokens(self):
        """Load JWT tokens."""
        try:
            with open(self.tokens_file, 'r') as f:
                token_data = json.load(f)
                self.jwt_token = token_data.get('tokens', {}).get('authorization')
                self.customer_id = token_data.get('customer_id')
                self.username = token_data.get('username')
                self.working_endpoints = token_data.get('working_endpoints', [])
        except:
            self.jwt_token = None
            self.customer_id = None
            self.username = None
            self.working_endpoints = []
    
    def get_headers(self):
        """Get authenticated headers."""
        return {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.6',
            'authorization': self.jwt_token,
            'content-type': 'application/json',
            'origin': 'https://www.mac.bid',
            'referer': 'https://www.mac.bid/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    async def fetch_complete_bid_history(self, max_pages=10):
        """Fetch complete bid history."""
        print("📋 FETCHING COMPLETE BID HISTORY")
        print("=" * 50)
        
        if 'Bid History' not in self.working_endpoints:
            print("❌ Bid History endpoint not available")
            return None
        
        all_bids = []
        connector = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(connector=connector)
        
        try:
            for page in range(1, max_pages + 1):
                url = f"https://api.macdiscount.com/user/{self.customer_id}/bid-history?pg={page}"
                print(f"📄 Fetching page {page}...")
                
                async with session.get(url, headers=self.get_headers(), timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and 'data' in data:
                            page_bids = data['data']
                            if page_bids:
                                all_bids.extend(page_bids)
                                print(f"   ✅ Got {len(page_bids)} bids")
                                
                                # Check pagination
                                pagination = data.get('pagination', {})
                                current_page = pagination.get('current_page', page)
                                total_pages = pagination.get('total_pages', 1)
                                
                                print(f"   📊 Page {current_page}/{total_pages}")
                                
                                if current_page >= total_pages:
                                    print("   🏁 Reached last page")
                                    break
                            else:
                                print("   📭 No more bids")
                                break
                        else:
                            print("   ❌ Invalid response format")
                            break
                    else:
                        print(f"   ❌ Error: Status {response.status}")
                        break
        
        finally:
            await session.close()
        
        print(f"\n📊 TOTAL BID HISTORY: {len(all_bids)} bids")
        return all_bids
    
    async def fetch_watchlist_data(self, max_pages=5):
        """Fetch complete watchlist data."""
        print("\n👁️ FETCHING WATCHLIST DATA")
        print("=" * 50)
        
        watchlist_data = {}
        modes = ['lost', 'won']
        
        connector = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(connector=connector)
        
        try:
            for mode in modes:
                print(f"\n🔍 Fetching watchlist {mode} items...")
                mode_items = []
                
                for page in range(1, max_pages + 1):
                    url = f"https://api.macdiscount.com/user/{self.customer_id}/watchlist-closed-items?mode={mode}&pg={page}&ppg=30"
                    
                    async with session.get(url, headers=self.get_headers(), timeout=15) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data:
                                mode_items.extend(data)
                                print(f"   📄 Page {page}: {len(data)} items")
                                if len(data) < 30:  # Last page
                                    break
                            else:
                                break
                        else:
                            print(f"   ❌ Error: Status {response.status}")
                            break
                
                watchlist_data[mode] = mode_items
                print(f"   📊 Total {mode}: {len(mode_items)} items")
        
        finally:
            await session.close()
        
        return watchlist_data
    
    def analyze_complete_bidding_performance(self, bid_history, watchlist_data):
        """Analyze complete bidding performance."""
        print(f"\n📊 COMPLETE BIDDING ANALYSIS")
        print("=" * 60)
        
        if not bid_history:
            print("❌ No bid history to analyze")
            return
        
        # Basic stats
        total_bids = len(bid_history)
        won_bids = len([b for b in bid_history if b.get('winning_customer_id') == self.customer_id])
        win_rate = (won_bids / total_bids * 100) if total_bids > 0 else 0
        
        print(f"🎯 COMPLETE BIDDING PERFORMANCE:")
        print(f"   Total Bids Placed: {total_bids}")
        print(f"   Bids Won: {won_bids}")
        print(f"   Actual Win Rate: {win_rate:.1f}%")
        
        # Bid amounts analysis
        bid_amounts = [float(b.get('max_bid', 0)) for b in bid_history]
        if bid_amounts:
            avg_bid = sum(bid_amounts) / len(bid_amounts)
            max_bid = max(bid_amounts)
            min_bid = min(bid_amounts)
            
            print(f"\n💰 BIDDING PATTERNS:")
            print(f"   Average Bid: ${avg_bid:.2f}")
            print(f"   Highest Bid: ${max_bid:.2f}")
            print(f"   Lowest Bid: ${min_bid:.2f}")
        
        # Recent activity
        recent_bids = sorted(bid_history, key=lambda x: x.get('date_created', ''), reverse=True)[:10]
        print(f"\n📅 RECENT BIDDING ACTIVITY:")
        for i, bid in enumerate(recent_bids, 1):
            product = bid.get('product_name', 'Unknown')[:30]
            amount = bid.get('max_bid', 0)
            won = "✅ WON" if bid.get('winning_customer_id') == self.customer_id else "❌ LOST"
            date = bid.get('date_created', '')[:10]
            print(f"   {i}. {date}: ${amount} - {product}... {won}")
        
        # Watchlist analysis
        if watchlist_data:
            lost_items = len(watchlist_data.get('lost', []))
            won_items = len(watchlist_data.get('won', []))
            
            print(f"\n👁️ WATCHLIST ANALYSIS:")
            print(f"   Items Watched & Lost: {lost_items}")
            print(f"   Items Watched & Won: {won_items}")
            if lost_items + won_items > 0:
                watchlist_win_rate = (won_items / (lost_items + won_items)) * 100
                print(f"   Watchlist Win Rate: {watchlist_win_rate:.1f}%")
    
    def save_complete_data(self, bid_history, watchlist_data):
        """Save all fetched data."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save bid history
        if bid_history:
            filename = f"complete_bid_history_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(bid_history, f, indent=2)
            print(f"\n💾 Bid history saved to: {filename}")
        
        # Save watchlist data
        if watchlist_data:
            filename = f"complete_watchlist_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(watchlist_data, f, indent=2)
            print(f"💾 Watchlist data saved to: {filename}")
        
        # Save summary
        summary = {
            'timestamp': timestamp,
            'customer_id': self.customer_id,
            'username': self.username,
            'total_bids': len(bid_history) if bid_history else 0,
            'watchlist_lost': len(watchlist_data.get('lost', [])) if watchlist_data else 0,
            'watchlist_won': len(watchlist_data.get('won', [])) if watchlist_data else 0,
            'working_endpoints': self.working_endpoints
        }
        
        filename = f"complete_summary_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"💾 Summary saved to: {filename}")

async def main():
    """Main function to fetch complete data."""
    fetcher = CompleteDataFetcher()
    
    print("🎯 COMPLETE DATA FETCHER")
    print("=" * 60)
    print("Fetching ALL your auction data from unlocked endpoints...")
    print(f"👤 Customer ID: {fetcher.customer_id}")
    print(f"📧 Username: {fetcher.username}")
    print(f"🔑 Working Endpoints: {len(fetcher.working_endpoints)}")
    print()
    
    if not fetcher.jwt_token:
        print("❌ No JWT token found!")
        return
    
    # Fetch all data
    bid_history = await fetcher.fetch_complete_bid_history(max_pages=20)
    watchlist_data = await fetcher.fetch_watchlist_data(max_pages=10)
    
    # Analyze the data
    fetcher.analyze_complete_bidding_performance(bid_history, watchlist_data)
    
    # Save everything
    fetcher.save_complete_data(bid_history, watchlist_data)
    
    print(f"\n🎉 COMPLETE DATA FETCH SUCCESSFUL!")
    print("=" * 50)
    print("You now have access to your COMPLETE auction history!")
    print("This includes every bid you've ever placed, not just wins!")
    
    if bid_history:
        total_bids = len(bid_history)
        won_bids = len([b for b in bid_history if b.get('winning_customer_id') == fetcher.customer_id])
        print(f"\n🏆 REALITY CHECK:")
        print(f"   You've placed {total_bids} total bids")
        print(f"   You've won {won_bids} auctions")
        print(f"   Your REAL win rate: {(won_bids/total_bids*100):.1f}%")
        print(f"   This is much more realistic than the 98% from purchase data only!")

if __name__ == "__main__":
    asyncio.run(main()) 