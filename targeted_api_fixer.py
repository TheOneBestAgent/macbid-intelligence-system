#!/usr/bin/env python3
"""
🎯 TARGETED API FIXER
Specifically fixes the remaining 2 non-working APIs:
- Mac.bid API (for auction details)
- Firebase API (for real-time bidding)
"""

import requests
import json
import time
import urllib.parse
import aiohttp
import asyncio
from datetime import datetime
from pathlib import Path

class TargetedAPIFixer:
    def __init__(self):
        self.session = requests.Session()
        
        # Load existing authentication
        self.load_auth_config()
        
        # API endpoints to fix
        self.target_apis = {
            'macbid_api': {
                'url': 'https://api.macdiscount.com/auctionsummary',
                'customer_url': f'https://api.macdiscount.com/auctions/customer/{self.customer_id}/active-auctions',
                'status': 'not_working',
                'priority': 'HIGH'
            },
            'firebase_api': {
                'url': 'https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel',
                'status': 'not_working', 
                'priority': 'HIGH'
            }
        }
        
        print("🎯 TARGETED API FIXER")
        print("=" * 25)
        print(f"Customer ID: {self.customer_id}")
        print(f"Target APIs: {len(self.target_apis)}")
        
    def load_auth_config(self):
        """Load authentication configuration"""
        try:
            import sys
            sys.path.append('organized_system/core_systems')
            from macbid_auth_config import MACBID_HEADERS, MACBID_CUSTOMER_ID, FIREBASE_SESSION_ID, SESSION_ID
            
            self.session.headers.update(MACBID_HEADERS)
            self.customer_id = MACBID_CUSTOMER_ID
            self.firebase_session = FIREBASE_SESSION_ID
            self.session_id = SESSION_ID
            print("✅ Loaded existing auth config")
            
        except ImportError:
            # Fallback values
            self.customer_id = "2710619"
            self.firebase_session = "hgpyx2kZyefNRKokgOt42EbyB-KeoJs0X_5OgkavHwc"
            self.session_id = "lmTKFrLnGL0yxLa5jxrfRw"
            print("⚠️  Using fallback auth values")
        
        # Try to load JWT token
        self.jwt_token = self.load_jwt_token()
    
    def load_jwt_token(self):
        """Load JWT token for Mac.bid API authentication"""
        try:
            token_file = Path.home() / '.macbid_scraper' / 'api_tokens.json'
            if token_file.exists():
                with open(token_file, 'r') as f:
                    data = json.load(f)
                    token = data.get('tokens', {}).get('authorization')
                    if token:
                        print(f"✅ JWT token loaded: {token[:30]}...")
                        return token
            
            print("⚠️  No JWT token found")
            return None
            
        except Exception as e:
            print(f"❌ Error loading JWT: {e}")
            return None
    
    def fix_macbid_api(self):
        """Fix Mac.bid API with multiple methods"""
        print("\n🔍 FIXING MAC.BID API")
        print("-" * 20)
        
        # Method 1: Basic endpoint without auth
        print("Method 1: Basic auctionsummary...")
        try:
            response = self.session.get(
                self.target_apis['macbid_api']['url'],
                params={'pg': 1, 'ppg': 10},
                timeout=10
            )
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                lot_count = len(data.get('data', []))
                print(f"   ✅ SUCCESS! Found {lot_count} auction lots")
                self.target_apis['macbid_api']['status'] = 'working'
                self.target_apis['macbid_api']['method'] = 'basic_endpoint'
                self.target_apis['macbid_api']['lots_found'] = lot_count
                return True
            else:
                print(f"   Error: {response.text[:100]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Method 2: Customer-specific endpoint with JWT
        if self.jwt_token:
            print("Method 2: Customer endpoint with JWT...")
            try:
                auth_headers = self.session.headers.copy()
                auth_headers.update({
                    'authorization': self.jwt_token,
                    'content-type': 'application/json',
                    'origin': 'https://www.mac.bid',
                    'referer': 'https://www.mac.bid/'
                })
                
                response = self.session.get(
                    self.target_apis['macbid_api']['customer_url'],
                    headers=auth_headers,
                    timeout=10
                )
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ SUCCESS! Customer-specific data loaded")
                    self.target_apis['macbid_api']['status'] = 'working'
                    self.target_apis['macbid_api']['method'] = 'customer_jwt'
                    return True
                else:
                    print(f"   Error: {response.text[:100]}...")
                    
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        # Method 3: Alternative API endpoints
        print("Method 3: Alternative endpoints...")
        alternatives = [
            'https://api.macdiscount.com/search?q=&limit=20',
            'https://api.macdiscount.com/turbo-clock-auctions',
            f'https://api.macdiscount.com/auction/getAuctionItems?loc=17,18&pg=1&ppg=20'
        ]
        
        for alt_url in alternatives:
            try:
                response = self.session.get(alt_url, timeout=10)
                print(f"   {alt_url}: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ Alternative endpoint working!")
                    self.target_apis['macbid_api']['status'] = 'working'
                    self.target_apis['macbid_api']['method'] = 'alternative'
                    self.target_apis['macbid_api']['working_url'] = alt_url
                    return True
                    
            except Exception as e:
                print(f"   ❌ {alt_url}: {e}")
        
        print("   ❌ All Mac.bid API methods failed")
        return False
    
    def fix_firebase_api(self):
        """Fix Firebase API for real-time updates"""
        print("\n🔥 FIXING FIREBASE API")
        print("-" * 20)
        
        firebase_url = self.target_apis['firebase_api']['url']
        
        # Method 1: Standard Firebase connection
        print("Method 1: Standard Firebase GET...")
        try:
            params = {
                'VER': '8',
                'database': 'projects%2Frecommerce-a0291%2Fdatabases%2F(default)',
                'gsessionid': self.firebase_session,
                'SID': self.session_id,
                'RID': 'rpc',
                'AID': '8780',
                'CI': '0',
                'TYPE': 'xmlhttp',
                'zx': f'fix{int(time.time() * 1000)}',
                't': '1'
            }
            
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.6',
                'cache-control': 'no-cache',
                'origin': 'https://www.mac.bid',
                'referer': 'https://www.mac.bid/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'cross-site',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = self.session.get(
                firebase_url,
                params=params,
                headers=headers,
                timeout=15
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Response size: {len(response.text)} bytes")
            
            if response.status_code in [200, 204]:
                print(f"   ✅ SUCCESS! Firebase connected")
                self.target_apis['firebase_api']['status'] = 'working'
                self.target_apis['firebase_api']['method'] = 'standard_get'
                self.target_apis['firebase_api']['response_size'] = len(response.text)
                return True
            else:
                print(f"   Error: {response.text[:150]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Method 2: Firebase POST with document monitoring
        print("Method 2: Firebase POST with lot monitoring...")
        try:
            # Monitor a specific lot
            test_lot_id = '48360-2549A'
            database_path = "projects/recommerce-a0291/databases/(default)"
            document_path = f"{database_path}/documents/auction-lots/{test_lot_id}"
            
            request_data = {
                "database": database_path,
                "addTarget": {
                    "documents": {
                        "documents": [document_path]
                    },
                    "targetId": 36
                }
            }
            
            form_data = {
                'count': '1',
                'ofs': '0',
                'req0___data__': json.dumps(request_data)
            }
            
            post_params = {
                'VER': '8',
                'database': urllib.parse.quote(database_path, safe=''),
                'gsessionid': self.firebase_session,
                'SID': self.session_id,
                'RID': '18109',
                'AID': '8665',
                'zx': f'fix{int(time.time() * 1000)}',
                't': '1'
            }
            
            post_headers = headers.copy()
            post_headers['content-type'] = 'application/x-www-form-urlencoded'
            
            response = self.session.post(
                firebase_url,
                params=post_params,
                headers=post_headers,
                data=urllib.parse.urlencode(form_data),
                timeout=15
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Response size: {len(response.text)} bytes")
            
            if response.status_code in [200, 204]:
                print(f"   ✅ SUCCESS! Firebase POST working")
                self.target_apis['firebase_api']['status'] = 'working'
                self.target_apis['firebase_api']['method'] = 'post_monitoring'
                self.target_apis['firebase_api']['monitored_lot'] = test_lot_id
                return True
            else:
                print(f"   Error: {response.text[:150]}...")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("   ❌ All Firebase methods failed")
        return False
    
    async def test_apis_async(self):
        """Test both APIs concurrently for efficiency"""
        print("\n⚡ ASYNC API TESTING")
        print("-" * 18)
        
        async def test_macbid():
            try:
                headers = {}
                if self.jwt_token:
                    headers['authorization'] = self.jwt_token
                
                async with aiohttp.ClientSession(headers=headers) as session:
                    url = 'https://api.macdiscount.com/auctionsummary?pg=1&ppg=5'
                    async with session.get(url, timeout=10) as response:
                        success = response.status == 200
                        return {
                            'macbid_async': {
                                'status': response.status,
                                'success': success,
                                'size': len(await response.text()) if success else 0
                            }
                        }
            except Exception as e:
                return {'macbid_async': {'error': str(e), 'success': False}}
        
        async def test_firebase():
            try:
                params = {
                    'VER': '8',
                    'database': 'projects%2Frecommerce-a0291%2Fdatabases%2F(default)',
                    'gsessionid': self.firebase_session,
                    'SID': self.session_id,
                    'RID': 'rpc',
                    'AID': '8780',
                    't': '1'
                }
                
                headers = {
                    'accept': '*/*',
                    'origin': 'https://www.mac.bid',
                    'referer': 'https://www.mac.bid/'
                }
                
                firebase_url = 'https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel'
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(firebase_url, params=params, headers=headers, timeout=10) as response:
                        success = response.status in [200, 204]
                        return {
                            'firebase_async': {
                                'status': response.status,
                                'success': success,
                                'size': len(await response.text()) if success else 0
                            }
                        }
            except Exception as e:
                return {'firebase_async': {'error': str(e), 'success': False}}
        
        # Run both tests concurrently
        results = await asyncio.gather(test_macbid(), test_firebase())
        
        # Combine results
        combined = {}
        for result in results:
            combined.update(result)
        
        print(f"Mac.bid async: {combined.get('macbid_async', {}).get('status', 'error')}")
        print(f"Firebase async: {combined.get('firebase_async', {}).get('status', 'error')}")
        
        return combined
    
    def run_comprehensive_fix(self):
        """Run comprehensive fix targeting the two broken APIs"""
        print("🚀 RUNNING TARGETED FIX")
        print("=" * 25)
        
        start_time = time.time()
        
        # Fix both APIs
        macbid_fixed = self.fix_macbid_api()
        firebase_fixed = self.fix_firebase_api()
        
        # Run async tests
        async_results = asyncio.run(self.test_apis_async())
        
        # Calculate success
        apis_fixed = sum([macbid_fixed, firebase_fixed])
        success_rate = (apis_fixed / 2) * 100
        processing_time = time.time() - start_time
        
        # Results summary
        results = {
            'timestamp': datetime.now().isoformat(),
            'processing_time': round(processing_time, 2),
            'apis_targeted': 2,
            'apis_fixed': apis_fixed,
            'success_rate': success_rate,
            'macbid_api': self.target_apis['macbid_api'],
            'firebase_api': self.target_apis['firebase_api'],
            'async_results': async_results
        }
        
        # Print summary
        print(f"\n📊 TARGETED FIX RESULTS")
        print("=" * 30)
        print(f"APIs Fixed: {apis_fixed}/2")
        print(f"Success Rate: {success_rate}%")
        print(f"Mac.bid API: {'✅ FIXED' if macbid_fixed else '❌ STILL BROKEN'}")
        print(f"Firebase API: {'✅ FIXED' if firebase_fixed else '❌ STILL BROKEN'}")
        print(f"Processing Time: {processing_time:.1f}s")
        
        if success_rate == 100:
            print("\n🎉 TARGET ACHIEVED! ALL APIS FIXED!")
        elif success_rate >= 50:
            print("\n⚠️  PARTIAL SUCCESS - Some progress made")
        else:
            print("\n❌ APIS STILL NEED WORK")
        
        # Save results
        with open(f"targeted_fix_results_{int(time.time())}.json", 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: targeted_fix_results_{int(time.time())}.json")
        
        return results

if __name__ == "__main__":
    fixer = TargetedAPIFixer()
    results = fixer.run_comprehensive_fix() 