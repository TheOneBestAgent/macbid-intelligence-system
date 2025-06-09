#!/usr/bin/env python3
"""
🔐 Test New Captured Endpoints
Test the bid history and watchlist endpoints just captured
"""

import json
import os
import asyncio
import aiohttp
from datetime import datetime

class NewEndpointTester:
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
        except:
            self.jwt_token = None
            self.customer_id = None
            self.username = None
    
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
    
    async def test_bid_history(self):
        """Test the bid history endpoint."""
        print("📋 TESTING BID HISTORY ENDPOINT")
        print("=" * 50)
        
        connector = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(connector=connector)
        
        try:
            url = f"https://api.macdiscount.com/user/{self.customer_id}/bid-history?pg=1"
            print(f"🔍 Testing: {url}")
            
            async with session.get(url, headers=self.get_headers(), timeout=15) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ SUCCESS! Bid History Accessible!")
                    
                    if isinstance(data, list):
                        print(f"📊 Found {len(data)} bid history items")
                        if len(data) > 0:
                            sample = data[0]
                            print(f"📋 Sample keys: {list(sample.keys())}")
                            print(f"📄 Sample bid: {json.dumps(sample, indent=2)[:300]}...")
                    elif isinstance(data, dict):
                        print(f"📋 Response keys: {list(data.keys())}")
                        print(f"📄 Response: {json.dumps(data, indent=2)[:300]}...")
                    
                    return data
                else:
                    text = await response.text()
                    print(f"❌ Failed: {text[:200]}...")
                    return None
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
        
        finally:
            await session.close()
    
    async def test_watchlist_endpoints(self):
        """Test the watchlist endpoints."""
        print("\n👁️ TESTING WATCHLIST ENDPOINTS")
        print("=" * 50)
        
        endpoints = {
            'Watchlist Lost': f"https://api.macdiscount.com/user/{self.customer_id}/watchlist-closed-items?mode=lost&pg=1&ppg=30",
            'Watchlist Won': f"https://api.macdiscount.com/user/{self.customer_id}/watchlist-closed-items?mode=won&pg=1&ppg=30"
        }
        
        results = {}
        connector = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(connector=connector)
        
        try:
            for endpoint_name, url in endpoints.items():
                print(f"\n🔍 Testing {endpoint_name}...")
                print(f"   URL: {url}")
                
                try:
                    async with session.get(url, headers=self.get_headers(), timeout=15) as response:
                        print(f"   Status: {response.status}")
                        
                        if response.status == 200:
                            data = await response.json()
                            print(f"   ✅ SUCCESS!")
                            
                            if isinstance(data, list):
                                print(f"   📊 Items: {len(data)}")
                                if len(data) > 0:
                                    sample = data[0]
                                    print(f"   📋 Sample keys: {list(sample.keys())[:5]}")
                            elif isinstance(data, dict):
                                print(f"   📋 Response keys: {list(data.keys())[:5]}")
                            
                            results[endpoint_name] = data
                        else:
                            text = await response.text()
                            print(f"   ❌ Failed: {text[:100]}...")
                            results[endpoint_name] = None
                
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    results[endpoint_name] = None
        
        finally:
            await session.close()
        
        return results
    
    async def update_token_file(self, bid_history_data, watchlist_data):
        """Update the token file with new working endpoints."""
        try:
            with open(self.tokens_file, 'r') as f:
                token_data = json.load(f)
            
            # Add new working endpoints
            working_endpoints = token_data.get('working_endpoints', [])
            
            if bid_history_data is not None:
                if 'Bid History' not in working_endpoints:
                    working_endpoints.append('Bid History')
            
            if watchlist_data.get('Watchlist Lost') is not None:
                if 'Watchlist Lost' not in working_endpoints:
                    working_endpoints.append('Watchlist Lost')
            
            if watchlist_data.get('Watchlist Won') is not None:
                if 'Watchlist Won' not in working_endpoints:
                    working_endpoints.append('Watchlist Won')
            
            token_data['working_endpoints'] = working_endpoints
            token_data['last_updated'] = datetime.now().isoformat()
            
            # Add sample data
            if bid_history_data:
                token_data['sample_data']['Bid History'] = {
                    'count': len(bid_history_data) if isinstance(bid_history_data, list) else 1,
                    'sample': bid_history_data[0] if isinstance(bid_history_data, list) and len(bid_history_data) > 0 else bid_history_data
                }
            
            for endpoint_name, data in watchlist_data.items():
                if data:
                    token_data['sample_data'][endpoint_name] = {
                        'count': len(data) if isinstance(data, list) else 1,
                        'sample': data[0] if isinstance(data, list) and len(data) > 0 else data
                    }
            
            with open(self.tokens_file, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            print(f"\n✅ Updated token file with new endpoints!")
            print(f"🔑 Total working endpoints: {len(working_endpoints)}")
            
        except Exception as e:
            print(f"❌ Error updating token file: {e}")

async def main():
    """Main function to test new endpoints."""
    tester = NewEndpointTester()
    
    print("🎉 TESTING NEW CAPTURED ENDPOINTS")
    print("=" * 60)
    print("Testing bid history and watchlist endpoints...")
    print(f"👤 Customer ID: {tester.customer_id}")
    print(f"📧 Username: {tester.username}")
    print()
    
    if not tester.jwt_token:
        print("❌ No JWT token found!")
        return
    
    # Test bid history
    bid_history_data = await tester.test_bid_history()
    
    # Test watchlist endpoints
    watchlist_data = await tester.test_watchlist_endpoints()
    
    # Update token file
    await tester.update_token_file(bid_history_data, watchlist_data)
    
    # Summary
    print(f"\n🎉 ENDPOINT TESTING COMPLETE!")
    print("=" * 40)
    
    working_count = 0
    if bid_history_data is not None:
        working_count += 1
        print("✅ Bid History: WORKING")
    else:
        print("❌ Bid History: FAILED")
    
    for endpoint_name, data in watchlist_data.items():
        if data is not None:
            working_count += 1
            print(f"✅ {endpoint_name}: WORKING")
        else:
            print(f"❌ {endpoint_name}: FAILED")
    
    print(f"\n🏆 TOTAL NEW ENDPOINTS UNLOCKED: {working_count}")
    
    if working_count > 0:
        print(f"\n🚀 NEXT STEPS:")
        print("1. Your JWT token now works for even more endpoints!")
        print("2. You can access your complete bid history")
        print("3. You can see your watchlist wins and losses")
        print("4. Run enhanced_personal_monitor.py for better matching")

if __name__ == "__main__":
    asyncio.run(main()) 