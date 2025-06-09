#!/usr/bin/env python3
"""
🔧 ULTIMATE API FIXER - Mac.bid & Firebase
Combines all authentication methods to fix the remaining two APIs:
- Mac.bid API (needs JWT authentication)
- Firebase API (needs proper session parameters)
"""

import requests
import aiohttp
import asyncio
import json
import time
import urllib.parse
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import existing auth config
import sys
sys.path.append('organized_system/core_systems')
try:
    from macbid_auth_config import MACBID_HEADERS, MACBID_CUSTOMER_ID, MACBID_BASE_URL, FIREBASE_SESSION_ID, SESSION_ID
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

class UltimateAPIFixer:
    def __init__(self):
        self.session = requests.Session()
        
        # Authentication setup
        if AUTH_AVAILABLE:
            self.session.headers.update(MACBID_HEADERS)
            self.customer_id = MACBID_CUSTOMER_ID
            self.firebase_session = FIREBASE_SESSION_ID
            self.session_id = SESSION_ID
        else:
            self.customer_id = "2710619"
            self.firebase_session = "hgpyx2kZyefNRKokgOt42EbyB-KeoJs0X_5OgkavHwc"
            self.session_id = "lmTKFrLnGL0yxLa5jxrfRw"
        
        # Load JWT token for Mac.bid API
        self.jwt_token = self.load_jwt_token()
        
        # API configurations
        self.apis = {
            'macbid': {
                'url': 'https://api.macdiscount.com/auctionsummary',
                'alt_url': f'https://api.macdiscount.com/auctions/customer/{self.customer_id}/active-auctions',
                'status': 'needs_fix'
            },
            'firebase': {
                'url': 'https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel',
                'status': 'needs_fix'
            }
        }
        
        print(f"🔧 ULTIMATE API FIXER INITIALIZED")
        print(f"   Customer ID: {self.customer_id}")
        print(f"   JWT Available: {'✅' if self.jwt_token else '❌'}")
        print(f"   Firebase Session: {self.firebase_session[:20]}...")
        
    def load_jwt_token(self) -> Optional[str]:
        """Load JWT token from stored credentials"""
        try:
            # Try multiple locations
            locations = [
                Path.home() / '.macbid_scraper' / 'api_tokens.json',
                'api_tokens.json',
                'organized_system/personal_systems/api_tokens.json'
            ]
            
            for location in locations:
                if location.exists():
                    with open(location, 'r') as f:
                        data = json.load(f)
                        token = data.get('tokens', {}).get('authorization')
                        if token:
                            print(f"   ✅ JWT token loaded from: {location}")
                            return token
            
            print("   ⚠️ No JWT token found - will attempt without auth")
            return None
            
        except Exception as e:
            print(f"   ❌ Error loading JWT token: {e}")
            return None
    
    def fix_macbid_api(self) -> Dict[str, Any]:
        """Fix Mac.bid API with multiple authentication methods"""
        print("\n🔍 FIXING MAC.BID API")
        print("=" * 30)
        
        results = []
        
        # Method 1: Basic auctionsummary endpoint
        print("   Method 1: Basic auction summary...")
        try:
            response = self.session.get(
                self.apis['macbid']['url'],
                params={'pg': 1, 'ppg': 5},
                timeout=10
            )
            result1 = {
                'method': 'Basic auction summary',
                'status': response.status_code,
                'success': response.status_code == 200,
                'data_size': len(response.text) if response.status_code == 200 else 0
            }
            results.append(result1)
            print(f"      Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"      ✅ Working! Found {len(data.get('data', []))} items")
                return {
                    'fixed': True,
                    'working_method': 'basic_auction_summary',
                    'results': results,
                    'working_url': self.apis['macbid']['url']
                }
        except Exception as e:
            result1 = {'method': 'Basic auction summary', 'error': str(e), 'success': False}
            results.append(result1)
            print(f"      ❌ Error: {e}")
        
        # Method 2: Customer-specific endpoint with JWT
        if self.jwt_token:
            print("   Method 2: Customer-specific with JWT...")
            try:
                auth_headers = self.session.headers.copy()
                auth_headers.update({
                    'authorization': self.jwt_token,
                    'content-type': 'application/json',
                    'origin': 'https://www.mac.bid',
                    'referer': 'https://www.mac.bid/'
                })
                
                response = self.session.get(
                    self.apis['macbid']['alt_url'],
                    headers=auth_headers,
                    timeout=10
                )
                result2 = {
                    'method': 'Customer-specific JWT',
                    'status': response.status_code,
                    'success': response.status_code == 200,
                    'data_size': len(response.text) if response.status_code == 200 else 0
                }
                results.append(result2)
                print(f"      Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"      ✅ Working! Customer-specific data loaded")
                    return {
                        'fixed': True,
                        'working_method': 'customer_jwt',
                        'results': results,
                        'working_url': self.apis['macbid']['alt_url']
                    }
            except Exception as e:
                result2 = {'method': 'Customer-specific JWT', 'error': str(e), 'success': False}
                results.append(result2)
                print(f"      ❌ Error: {e}")
        
        # Method 3: Alternative endpoints
        print("   Method 3: Alternative endpoints...")
        alt_endpoints = [
            'https://api.macdiscount.com/search?q=&limit=10',
            'https://api.macdiscount.com/turbo-clock-auctions',
            f'https://api.macdiscount.com/auction/getAuctionItems?loc=17,18&pg=1&ppg=10'
        ]
        
        for endpoint in alt_endpoints:
            try:
                response = self.session.get(endpoint, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    print(f"      ✅ Alternative endpoint working: {endpoint}")
                    return {
                        'fixed': True,
                        'working_method': 'alternative_endpoint',
                        'results': results,
                        'working_url': endpoint
                    }
                else:
                    print(f"      Status {response.status_code}: {endpoint}")
            except Exception as e:
                print(f"      ❌ {endpoint}: {e}")
        
        return {
            'fixed': False,
            'working_method': None,
            'results': results,
            'message': 'All Mac.bid API methods failed'
        }
    
    def fix_firebase_api(self) -> Dict[str, Any]:
        """Fix Firebase API with exact parameters from working examples"""
        print("\n🔥 FIXING FIREBASE API")
        print("=" * 25)
        
        try:
            # Use exact parameters from working macbid_breakdown examples
            firebase_url = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
            
            # Method 1: GET request with exact parameters
            print("   Method 1: GET request with URL parameters...")
            params = {
                'VER': '8',
                'database': 'projects%2Frecommerce-a0291%2Fdatabases%2F(default)',  # Pre-encoded
                'gsessionid': self.firebase_session,
                'SID': self.session_id,
                'RID': 'rpc',
                'AID': '8780',
                'CI': '0',
                'TYPE': 'xmlhttp',
                'zx': f'fix{int(time.time() * 1000)}',
                't': '1'
            }
            
            firebase_headers = {
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
                headers=firebase_headers,
                timeout=15
            )
            
            print(f"      Status: {response.status_code}")
            print(f"      Response size: {len(response.text)} bytes")
            
            if response.status_code in [200, 204]:
                print(f"      ✅ Firebase GET method working!")
                return {
                    'fixed': True,
                    'method': 'GET_with_params',
                    'status': response.status_code,
                    'response_size': len(response.text),
                    'url': firebase_url
                }
            
            # Method 2: POST request with form data (like working examples)
            print("   Method 2: POST request with form data...")
            
            # Create form data for monitoring a test lot
            test_lot_id = '48360-2549A'  # Known working lot from breakdown
            database_path = f"projects/recommerce-a0291/databases/(default)"
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
            
            post_headers = firebase_headers.copy()
            post_headers['content-type'] = 'application/x-www-form-urlencoded'
            
            response = self.session.post(
                firebase_url,
                params=post_params,
                headers=post_headers,
                data=urllib.parse.urlencode(form_data),
                timeout=15
            )
            
            print(f"      Status: {response.status_code}")
            print(f"      Response size: {len(response.text)} bytes")
            
            if response.status_code in [200, 204]:
                print(f"      ✅ Firebase POST method working!")
                return {
                    'fixed': True,
                    'method': 'POST_with_form_data',
                    'status': response.status_code,
                    'response_size': len(response.text),
                    'lot_id': test_lot_id,
                    'url': firebase_url
                }
            
            # If both methods fail, provide detailed error info
            print(f"      ❌ Both Firebase methods failed")
            return {
                'fixed': False,
                'get_status': params.get('status', 'error'),
                'post_status': response.status_code,
                'error': f"GET and POST both failed. Latest response: {response.text[:200]}..."
            }
            
        except Exception as e:
            print(f"   ❌ Firebase fix error: {e}")
            return {
                'fixed': False,
                'error': str(e)
            }
    
    async def test_both_apis_async(self) -> Dict[str, Any]:
        """Test both APIs with async requests for speed"""
        print("\n⚡ ASYNC API TESTING")
        print("=" * 20)
        
        async def test_macbid_async():
            try:
                headers = {'authorization': self.jwt_token} if self.jwt_token else {}
                async with aiohttp.ClientSession(headers=headers) as session:
                    url = f'https://api.macdiscount.com/auctions/customer/{self.customer_id}/active-auctions'
                    async with session.get(url, timeout=10) as response:
                        return {
                            'macbid_async': {
                                'status': response.status,
                                'success': response.status == 200,
                                'size': len(await response.text()) if response.status == 200 else 0
                            }
                        }
            except Exception as e:
                return {'macbid_async': {'error': str(e), 'success': False}}
        
        async def test_firebase_async():
            try:
                firebase_url = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
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
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(firebase_url, params=params, headers=headers, timeout=10) as response:
                        return {
                            'firebase_async': {
                                'status': response.status,
                                'success': response.status in [200, 204],
                                'size': len(await response.text()) if response.status in [200, 204] else 0
                            }
                        }
            except Exception as e:
                return {'firebase_async': {'error': str(e), 'success': False}}
        
        # Run both tests concurrently
        results = await asyncio.gather(test_macbid_async(), test_firebase_async())
        
        # Combine results
        combined = {}
        for result in results:
            combined.update(result)
        
        return combined
    
    def run_comprehensive_fix(self) -> Dict[str, Any]:
        """Run comprehensive API fix and return results"""
        print("🚀 COMPREHENSIVE API FIX")
        print("=" * 30)
        
        start_time = time.time()
        
        # Fix Mac.bid API
        macbid_result = self.fix_macbid_api()
        
        # Fix Firebase API
        firebase_result = self.fix_firebase_api()
        
        # Test async methods
        async_results = asyncio.run(self.test_both_apis_async())
        
        # Calculate overall success
        macbid_fixed = macbid_result.get('fixed', False)
        firebase_fixed = firebase_result.get('fixed', False)
        
        apis_working = sum([macbid_fixed, firebase_fixed])
        success_rate = (apis_working / 2) * 100
        
        processing_time = time.time() - start_time
        
        # Final results
        results = {
            'timestamp': datetime.now().isoformat(),
            'processing_time': round(processing_time, 2),
            'apis_fixed': apis_working,
            'total_apis': 2,
            'success_rate': success_rate,
            'macbid_api': macbid_result,
            'firebase_api': firebase_result,
            'async_tests': async_results,
            'status': 'FULLY_FIXED' if apis_working == 2 else 'PARTIALLY_FIXED' if apis_working == 1 else 'NEEDS_WORK'
        }
        
        # Print final summary
        print(f"\n📊 FINAL RESULTS")
        print("=" * 20)
        print(f"   APIs Fixed: {apis_working}/2")
        print(f"   Success Rate: {success_rate}%")
        print(f"   Mac.bid API: {'✅ FIXED' if macbid_fixed else '❌ NEEDS WORK'}")
        print(f"   Firebase API: {'✅ FIXED' if firebase_fixed else '❌ NEEDS WORK'}")
        print(f"   Processing Time: {processing_time:.2f} seconds")
        print(f"   Overall Status: {results['status']}")
        
        if success_rate == 100:
            print("\n🎉 ALL APIS WORKING! 100% SUCCESS!")
        elif success_rate >= 50:
            print("\n⚠️  PARTIAL SUCCESS - Some APIs working")
        else:
            print("\n❌ APIs NEED MORE WORK")
        
        return results

def main():
    """Main function to run the ultimate API fixer"""
    fixer = UltimateAPIFixer()
    results = fixer.run_comprehensive_fix()
    
    # Save results
    with open(f"api_fix_results_{int(time.time())}.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    main() 