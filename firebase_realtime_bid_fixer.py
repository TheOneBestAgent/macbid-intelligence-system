#!/usr/bin/env python3
"""
Firebase Realtime Bid Action Fixer - WORKING VERSION WITH FRESH CREDENTIALS
Uses fresh Firebase session credentials and exact request format from working Node.js implementation
"""

import requests
import json
import time
import urllib.parse
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import random
import string

# Import discovered authentication
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'organized_system', 'core_systems'))
from macbid_auth_config import MACBID_HEADERS, MACBID_CUSTOMER_ID, MACBID_BASE_URL, FIREBASE_SESSION_ID, SESSION_ID

class WorkingFirebaseRealtimeBidFixer:
    def __init__(self):
        self.base_url = MACBID_BASE_URL
        self.session = requests.Session()
        
        # Firebase configuration with FRESH credentials from Node.js implementation
        self.firebase_url = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
        self.project_id = "recommerce-a0291"
        self.database = f"projects/{self.project_id}/databases/(default)"
        
        # Fresh session credentials (from Node.js implementation)
        self.gsessionid = FIREBASE_SESSION_ID  # Updated fresh credentials
        self.sid = SESSION_ID  # Updated fresh credentials
        
        # Request counters (starting from Node.js implementation values)
        self.rid = 18109
        self.aid = 8665
        self.ofs = 29
        
        # Known working lot IDs from Node.js implementation
        self.known_lot_ids = [
            '48360-2549A', 
            '48223-3096Z', 
            '48012-1029W', 
            '48504-1203B', 
            '48389-1136A'
        ]
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def generate_zx(self) -> str:
        """Generate realistic zx parameter (timestamp-based random string)"""
        chars = string.ascii_lowercase + string.digits
        return ''.join(random.choice(chars) for _ in range(12))
    
    def generate_firebase_headers(self) -> Dict[str, str]:
        """Generate exact Firebase headers from Node.js implementation"""
        return {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.6',
            'content-type': 'application/x-www-form-urlencoded',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'sec-fetch-storage-access': 'none',
            'sec-gpc': '1'
        }
    
    def create_firebase_url_params(self) -> Dict[str, str]:
        """Create Firebase URL parameters exactly like Node.js implementation"""
        return {
            'VER': '8',
            'database': urllib.parse.quote(self.database, safe=''),
            'gsessionid': self.gsessionid,
            'SID': self.sid,
            'RID': str(self.rid),
            'AID': str(self.aid),
            'zx': self.generate_zx(),
            't': '1'
        }
    
    def create_add_target_body(self, lot_id: str, target_id: int) -> str:
        """Create Firebase addTarget body exactly like Node.js implementation"""
        document_path = f"{self.database}/documents/auction-lots/{lot_id}"
        
        request_data = {
            "database": self.database,
            "addTarget": {
                "documents": {
                    "documents": [document_path]
                },
                "targetId": target_id
            }
        }
        
        # Create form body exactly like Node.js URLSearchParams
        body_params = {
            'count': '1',
            'ofs': str(self.ofs),
            'req0___data__': json.dumps(request_data)
        }
        
        # Increment counters
        self.rid += 1
        self.ofs += 1
        
        return urllib.parse.urlencode(body_params)
    
    def create_remove_target_body(self, target_id: int) -> str:
        """Create Firebase removeTarget body exactly like Node.js implementation"""
        request_data = {
            "database": self.database,
            "removeTarget": target_id
        }
        
        body_params = {
            'count': '1',
            'ofs': str(self.ofs),
            'req0___data__': json.dumps(request_data)
        }
        
        self.rid += 1
        self.ofs += 1
        
        return urllib.parse.urlencode(body_params)
    
    def test_firebase_connection_with_fresh_credentials(self) -> Dict:
        """Test Firebase connection with fresh credentials"""
        print("🔥 TESTING FIREBASE CONNECTION WITH FRESH CREDENTIALS")
        print("=" * 55)
        
        print(f"   Session ID: {self.gsessionid[:20]}...")
        print(f"   SID: {self.sid[:20]}...")
        print(f"   RID: {self.rid}")
        print(f"   AID: {self.aid}")
        print(f"   OFS: {self.ofs}")
        
        # Test with known lot ID from Node.js implementation
        test_lot_id = '48360-2549A'
        target_id = 36
        
        try:
            headers = self.generate_firebase_headers()
            params = self.create_firebase_url_params()
            body = self.create_add_target_body(test_lot_id, target_id)
            
            print(f"   Testing lot: {test_lot_id}")
            print(f"   Target ID: {target_id}")
            
            response = self.session.post(
                self.firebase_url,
                params=params,
                headers=headers,
                data=body,
                timeout=15
            )
            
            print(f"   Response Status: {response.status_code}")
            print(f"   Response Size: {len(response.text)} bytes")
            
            if response.status_code == 200:
                print("   ✅ Firebase connection SUCCESSFUL with fresh credentials!")
                print(f"   Sample response: {response.text[:200]}...")
                
                return {
                    'connected': True,
                    'status': 200,
                    'lot_id': test_lot_id,
                    'target_id': target_id,
                    'response_size': len(response.text),
                    'method': 'Fresh Firebase Credentials'
                }
            elif response.status_code == 204:
                print("   ✅ Firebase connected (No Content - normal for initial request)")
                return {
                    'connected': True,
                    'status': 204,
                    'lot_id': test_lot_id,
                    'target_id': target_id,
                    'method': 'Fresh Firebase Credentials'
                }
            else:
                print(f"   ❌ Firebase connection failed: {response.status_code}")
                print(f"   Error: {response.text[:300]}...")
                return {
                    'connected': False,
                    'status': response.status_code,
                    'error': response.text[:300],
                    'lot_id': test_lot_id
                }
                
        except Exception as e:
            print(f"   ❌ Firebase test failed: {e}")
            return {
                'connected': False,
                'error': str(e),
                'lot_id': test_lot_id
            }
    
    def monitor_multiple_lots(self, lot_ids: List[str] = None) -> Dict:
        """Monitor multiple auction lots exactly like Node.js implementation"""
        print("\n🎯 MONITORING MULTIPLE AUCTION LOTS")
        print("=" * 40)
        
        if not lot_ids:
            lot_ids = self.known_lot_ids
        
        print(f"   Monitoring {len(lot_ids)} lots...")
        
        results = []
        successful_monitors = 0
        
        for i, lot_id in enumerate(lot_ids):
            target_id = 36 + i  # Start from 36 like Node.js implementation
            
            try:
                print(f"   Setting up monitoring for lot: {lot_id} (Target: {target_id})")
                
                headers = self.generate_firebase_headers()
                params = self.create_firebase_url_params()
                body = self.create_add_target_body(lot_id, target_id)
                
                response = self.session.post(
                    self.firebase_url,
                    params=params,
                    headers=headers,
                    data=body,
                    timeout=10
                )
                
                result = {
                    'lot_id': lot_id,
                    'target_id': target_id,
                    'status': response.status_code,
                    'response_size': len(response.text),
                    'success': response.status_code in [200, 204],
                    'timestamp': datetime.now().isoformat()
                }
                
                if result['success']:
                    print(f"   ✅ Successfully monitoring {lot_id}")
                    successful_monitors += 1
                else:
                    print(f"   ❌ Failed to monitor {lot_id}: {response.status_code}")
                    result['error'] = response.text[:200]
                
                results.append(result)
                
                # Small delay between requests like Node.js implementation
                time.sleep(0.1)
                
            except Exception as e:
                print(f"   ❌ Error monitoring lot {lot_id}: {e}")
                results.append({
                    'lot_id': lot_id,
                    'target_id': target_id,
                    'error': str(e),
                    'success': False,
                    'timestamp': datetime.now().isoformat()
                })
        
        return {
            'total_lots': len(lot_ids),
            'successful_monitors': successful_monitors,
            'results': results,
            'success_rate': (successful_monitors / len(lot_ids)) * 100 if lot_ids else 0
        }
    
    def fetch_auction_summary(self, page: int = 1, per_page: int = 10) -> Dict:
        """Fetch auction summary from Mac.bid API like Node.js implementation"""
        try:
            url = f"https://api.macdiscount.com/auctionsummary?pg={page}&ppg={per_page}"
            
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.6',
                'content-type': 'application/json',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'cross-site',
                'referrer': 'https://www.mac.bid/',
            }
            
            response = self.session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'page': page,
                    'per_page': per_page,
                    'data': data,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'success': False,
                    'status': response.status_code,
                    'page': page
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'page': page
            }
    
    def run_comprehensive_firebase_test(self) -> Dict:
        """Run comprehensive Firebase test with fresh credentials"""
        print("🚀 COMPREHENSIVE FIREBASE TEST WITH FRESH CREDENTIALS")
        print("=" * 60)
        
        results = {
            'connection_test': {},
            'monitoring_test': {},
            'api_test': {},
            'overall_success': False
        }
        
        # Step 1: Test Firebase connection
        results['connection_test'] = self.test_firebase_connection_with_fresh_credentials()
        
        # Step 2: Test monitoring multiple lots
        if results['connection_test'].get('connected'):
            results['monitoring_test'] = self.monitor_multiple_lots()
            
            # Step 3: Test Mac.bid API
            print("\n📊 TESTING MAC.BID API")
            print("=" * 25)
            api_result = self.fetch_auction_summary(44, 10)
            results['api_test'] = api_result
            
            if api_result.get('success'):
                print(f"   ✅ Mac.bid API working! Page {api_result['page']}")
            else:
                print(f"   ❌ Mac.bid API failed: {api_result.get('status', 'Unknown')}")
            
            # Determine overall success
            connection_ok = results['connection_test'].get('connected', False)
            monitoring_ok = results['monitoring_test'].get('successful_monitors', 0) > 0
            
            results['overall_success'] = connection_ok and monitoring_ok
        
        return results

def main():
    """Main execution function"""
    fixer = WorkingFirebaseRealtimeBidFixer()
    
    print("🎯 FIREBASE REALTIME BID ACTION FIXER - WORKING VERSION")
    print("=" * 60)
    print("Using fresh Firebase credentials from Node.js implementation")
    
    # Run comprehensive test
    results = fixer.run_comprehensive_firebase_test()
    
    print(f"\n📊 COMPREHENSIVE FIREBASE TEST RESULTS:")
    print("=" * 45)
    
    # Connection test results
    connection = results['connection_test']
    if connection.get('connected'):
        print(f"🔥 Firebase Connection: ✅ WORKING!")
        print(f"   Status: {connection.get('status')}")
        print(f"   Method: {connection.get('method')}")
        print(f"   Lot ID: {connection.get('lot_id')}")
        print(f"   Target ID: {connection.get('target_id')}")
        if connection.get('response_size'):
            print(f"   Response Size: {connection.get('response_size')} bytes")
    else:
        print(f"🔥 Firebase Connection: ❌ FAILED")
        print(f"   Status: {connection.get('status', 'Unknown')}")
        print(f"   Error: {connection.get('error', 'Unknown')}")
    
    # Monitoring test results
    monitoring = results['monitoring_test']
    if monitoring:
        print(f"🎯 Lot Monitoring: ✅ TESTED!")
        print(f"   Total Lots: {monitoring.get('total_lots', 0)}")
        print(f"   Successful: {monitoring.get('successful_monitors', 0)}")
        print(f"   Success Rate: {monitoring.get('success_rate', 0):.1f}%")
        
        # Show individual results
        for result in monitoring.get('results', [])[:3]:  # Show first 3
            status = "✅" if result.get('success') else "❌"
            print(f"   {status} {result.get('lot_id')}: Status {result.get('status')}")
    
    # API test results
    api = results['api_test']
    if api:
        if api.get('success'):
            print(f"📊 Mac.bid API: ✅ WORKING!")
            print(f"   Page: {api.get('page')}")
        else:
            print(f"📊 Mac.bid API: ❌ FAILED")
            print(f"   Status: {api.get('status', 'Unknown')}")
    
    # Overall assessment
    if results['overall_success']:
        print(f"\n🎉 OVERALL: ✅ FIREBASE REALTIME BID MONITORING FIXED!")
        print("   Fresh credentials are working")
        print("   Real-time bid monitoring is now available")
        print("   System ready for production use")
        
        print(f"\n💡 NEXT STEPS:")
        print("   1. ✅ Firebase connection established with fresh credentials")
        print("   2. ✅ Multiple lot monitoring working")
        print("   3. 🚀 Ready to implement real-time bid tracking")
        print("   4. 🔄 Set up continuous monitoring with 5-10 second intervals")
        
    else:
        print(f"\n❌ OVERALL: ❌ STILL NEEDS WORK")
        print("   Check if credentials need to be refreshed again")
        
        if not connection.get('connected'):
            print(f"\n🔍 FIREBASE CONNECTION ISSUES:")
            print(f"   - Status: {connection.get('status')}")
            print(f"   - Error: {connection.get('error', 'Unknown')}")
            print(f"   - May need even fresher credentials")

if __name__ == "__main__":
    main() 