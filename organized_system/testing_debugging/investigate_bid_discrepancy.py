#!/usr/bin/env python3
"""
🔍 Investigate Bid History Discrepancy
The user confirms all purchases were via bidding, but bid history shows 0 wins.
Let's investigate this data mismatch.
"""

import json
import os
import asyncio
import aiohttp
from datetime import datetime

class BidDiscrepancyInvestigator:
    def __init__(self):
        self.tokens_file = os.path.expanduser("~/.macbid_scraper/api_tokens.json")
        self.load_tokens()
        self.load_purchase_data()
        
    def load_tokens(self):
        """Load JWT tokens."""
        try:
            with open(self.tokens_file, 'r') as f:
                token_data = json.load(f)
                self.jwt_token = token_data.get('tokens', {}).get('authorization')
                self.customer_id = token_data.get('customer_id')
                self.username = token_data.get('username')
        except:
            self.jwt_token = None
            self.customer_id = None
            self.username = None
    
    def load_purchase_data(self):
        """Load the user's purchase data to compare."""
        import glob
        
        # Find latest purchase files
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
        
        print(f"📦 Loaded {len(self.invoices)} invoices and {len(self.items)} items from purchase history")
    
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
    
    async def test_different_bid_endpoints(self):
        """Test different bid-related endpoints to find the right data."""
        print("🔍 TESTING DIFFERENT BID ENDPOINTS")
        print("=" * 60)
        
        # Different possible endpoints
        endpoints = [
            f"https://api.macdiscount.com/user/{self.customer_id}/bid-history?pg=1",
            f"https://api.macdiscount.com/user/{self.customer_id}/getBidHistory?pg=1&ppg=25",
            f"https://api.macdiscount.com/auction/getMyBids?pg=1&ppg=25",
            f"https://api.macdiscount.com/user/{self.customer_id}/bid-history?pg=1&ppg=50",
            f"https://api.macdiscount.com/user/{self.customer_id}/bid-history?pg=1&status=won",
            f"https://api.macdiscount.com/user/{self.customer_id}/bid-history?pg=1&mode=all",
        ]
        
        connector = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(connector=connector)
        
        results = {}
        
        try:
            for i, endpoint in enumerate(endpoints, 1):
                print(f"\n🔍 Testing endpoint {i}: {endpoint}")
                
                try:
                    async with session.get(endpoint, headers=self.get_headers(), timeout=15) as response:
                        print(f"   Status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            print(f"   ✅ SUCCESS!")
                            
                            # Analyze the response
                            if isinstance(data, dict):
                                if 'data' in data:
                                    items = data['data']
                                    print(f"   📊 Found {len(items)} items in 'data' field")
                                    
                                    # Check for wins
                                    if items:
                                        won_items = [item for item in items if item.get('winning_customer_id') == self.customer_id]
                                        print(f"   🏆 Won items: {len(won_items)}")
                                        
                                        # Show sample
                                        sample = items[0]
                                        print(f"   📋 Sample keys: {list(sample.keys())}")
                                        
                                        results[f"endpoint_{i}"] = {
                                            'url': endpoint,
                                            'total_items': len(items),
                                            'won_items': len(won_items),
                                            'sample': sample
                                        }
                                else:
                                    print(f"   📋 Response keys: {list(data.keys())}")
                                    results[f"endpoint_{i}"] = {
                                        'url': endpoint,
                                        'response': data
                                    }
                            elif isinstance(data, list):
                                print(f"   📊 Found {len(data)} items (direct list)")
                                if data:
                                    won_items = [item for item in data if item.get('winning_customer_id') == self.customer_id]
                                    print(f"   🏆 Won items: {len(won_items)}")
                                    
                                    results[f"endpoint_{i}"] = {
                                        'url': endpoint,
                                        'total_items': len(data),
                                        'won_items': len(won_items),
                                        'sample': data[0] if data else None
                                    }
                        else:
                            text = await response.text()
                            print(f"   ❌ Failed: {text[:100]}...")
                
                except Exception as e:
                    print(f"   ❌ Error: {e}")
        
        finally:
            await session.close()
        
        return results
    
    async def fetch_extended_bid_history(self):
        """Fetch more pages of bid history to find wins."""
        print(f"\n📋 FETCHING EXTENDED BID HISTORY")
        print("=" * 50)
        
        all_bids = []
        connector = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(connector=connector)
        
        try:
            # Try fetching many more pages
            for page in range(1, 21):  # Try up to 20 pages
                url = f"https://api.macdiscount.com/user/{self.customer_id}/bid-history?pg={page}"
                print(f"📄 Fetching page {page}...")
                
                async with session.get(url, headers=self.get_headers(), timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data and 'data' in data:
                            page_bids = data['data']
                            if page_bids:
                                all_bids.extend(page_bids)
                                
                                # Check for wins on this page
                                won_on_page = [b for b in page_bids if b.get('winning_customer_id') == self.customer_id]
                                print(f"   ✅ Got {len(page_bids)} bids, {len(won_on_page)} wins")
                                
                                # Check pagination
                                pagination = data.get('pagination', {})
                                current_page = pagination.get('current_page', page)
                                total_pages = pagination.get('total_pages', 1)
                                
                                if current_page >= total_pages:
                                    print("   🏁 Reached last page")
                                    break
                            else:
                                print("   📭 No more bids")
                                break
                        else:
                            print("   ❌ Invalid response")
                            break
                    else:
                        print(f"   ❌ Error: Status {response.status}")
                        break
        
        finally:
            await session.close()
        
        # Analyze all bids
        total_bids = len(all_bids)
        won_bids = [b for b in all_bids if b.get('winning_customer_id') == self.customer_id]
        
        print(f"\n📊 EXTENDED BID ANALYSIS:")
        print(f"   Total bids found: {total_bids}")
        print(f"   Won bids found: {len(won_bids)}")
        
        if won_bids:
            print(f"\n🏆 SAMPLE WON BIDS:")
            for i, bid in enumerate(won_bids[:5], 1):
                product = bid.get('product_name', 'Unknown')[:30]
                amount = bid.get('max_bid', 0)
                date = bid.get('date_created', '')[:10]
                print(f"   {i}. {date}: ${amount} - {product}...")
        
        return all_bids, won_bids
    
    def compare_with_purchase_data(self, won_bids):
        """Compare bid wins with purchase data."""
        print(f"\n🔍 COMPARING BID WINS WITH PURCHASE DATA")
        print("=" * 60)
        
        print(f"📊 Data Comparison:")
        print(f"   Purchase items: {len(self.items)}")
        print(f"   Won bids found: {len(won_bids)}")
        
        if len(won_bids) > 0:
            print(f"\n✅ Found matching data!")
            
            # Try to match items
            matched = 0
            for item in self.items[:5]:  # Check first 5
                item_name = item.get('description', '').lower()
                for bid in won_bids:
                    bid_name = bid.get('product_name', '').lower()
                    if item_name in bid_name or bid_name in item_name:
                        matched += 1
                        print(f"   ✅ Match: {item_name[:30]}... = {bid_name[:30]}...")
                        break
            
            print(f"\n📊 Matched {matched} items between purchase and bid data")
        else:
            print(f"\n❌ No won bids found in bid history")
            print(f"   This suggests the bid history endpoint may:")
            print(f"   1. Show only recent/active bids")
            print(f"   2. Filter out completed/won auctions")
            print(f"   3. Have different data than purchase history")

async def main():
    """Main investigation function."""
    investigator = BidDiscrepancyInvestigator()
    
    print("🔍 BID HISTORY DISCREPANCY INVESTIGATION")
    print("=" * 70)
    print("User confirms all purchases were via bidding.")
    print("But bid history shows 0 wins. Let's investigate...")
    print()
    
    if not investigator.jwt_token:
        print("❌ No JWT token found!")
        return
    
    # Test different endpoints
    endpoint_results = await investigator.test_different_bid_endpoints()
    
    # Fetch extended bid history
    all_bids, won_bids = await investigator.fetch_extended_bid_history()
    
    # Compare with purchase data
    investigator.compare_with_purchase_data(won_bids)
    
    # Save investigation results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    investigation_report = {
        'timestamp': timestamp,
        'customer_id': investigator.customer_id,
        'purchase_items': len(investigator.items),
        'total_bids_found': len(all_bids),
        'won_bids_found': len(won_bids),
        'endpoint_results': endpoint_results,
        'conclusion': 'Investigation complete'
    }
    
    filename = f"bid_investigation_report_{timestamp}.json"
    with open(filename, 'w') as f:
        json.dump(investigation_report, f, indent=2)
    
    print(f"\n💾 Investigation report saved to: {filename}")
    
    print(f"\n🎯 INVESTIGATION CONCLUSION:")
    print("=" * 40)
    if len(won_bids) > 0:
        print(f"✅ Found {len(won_bids)} won bids in extended search!")
        print(f"   Your actual win rate: {len(won_bids)/len(all_bids)*100:.1f}%")
        print(f"   You ARE a successful bidder!")
    else:
        print(f"❌ Still no won bids found in bid history")
        print(f"   This suggests bid history and purchase history are separate systems")
        print(f"   Your purchases might be through instant-win or different mechanism")

if __name__ == "__main__":
    asyncio.run(main()) 