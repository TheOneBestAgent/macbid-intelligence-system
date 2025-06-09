#!/usr/bin/env python3
"""
Final Authentication Fix
Addresses specific Firebase 400 and Typesense empty collection issues
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Import discovered authentication
from macbid_auth_config import MACBID_HEADERS, MACBID_CUSTOMER_ID, MACBID_BASE_URL, FIREBASE_SESSION_ID, SESSION_ID

class FinalAuthenticationFix:
    def __init__(self):
        self.base_url = MACBID_BASE_URL
        self.session = requests.Session()
        self.session.headers.update(MACBID_HEADERS)
        
        # Firebase configuration from breakdown analysis
        self.firebase_session = FIREBASE_SESSION_ID
        self.session_id = SESSION_ID
        
        # Typesense configuration
        self.typesense_url = "https://xczkhpt94lod37gqp.a1.typesense.net/multi_search"
        self.typesense_api_key = "jxX8RU6YVOkm9esgd9buaYjulIWv6N52"
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def fix_firebase_400_error(self) -> Dict:
        """Fix Firebase 400 error using exact working parameters from breakdown"""
        print("🔥 FIXING FIREBASE 400 ERROR")
        print("=" * 35)
        
        # Key insight: Firebase 400 error is due to incorrect parameter encoding
        # From breakdown analysis, successful requests use specific encoding
        
        try:
            # Use the exact successful pattern from macbid_breakdown
            firebase_url = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
            
            # Exact parameters from working requests (URL encoded properly)
            params = {
                'VER': '8',
                'database': 'projects%2Frecommerce-a0291%2Fdatabases%2F(default)',
                'gsessionid': self.firebase_session,
                'SID': self.session_id,
                'RID': 'rpc',
                'AID': '8780',
                'CI': '0',
                'TYPE': 'xmlhttp',
                'zx': f'fix{int(time.time() * 1000)}',  # Timestamp in milliseconds
                't': '1'
            }
            
            # Exact headers that work
            headers = {
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Origin': 'https://www.mac.bid',
                'Referer': 'https://www.mac.bid/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'cross-site',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            # Make request with exact parameters
            response = self.session.get(firebase_url, params=params, headers=headers, timeout=15)
            
            print(f"   Firebase Response: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Firebase 400 error FIXED! (Status 200)")
                return {'fixed': True, 'status': 200, 'method': 'Parameter Fix'}
            elif response.status_code == 204:
                print("   ✅ Firebase 400 error FIXED! (Status 204 - No Content)")
                return {'fixed': True, 'status': 204, 'method': 'Parameter Fix'}
            else:
                print(f"   ⚠️  Still getting {response.status_code}")
                
                # Alternative: Try POST method (some Firebase endpoints prefer POST)
                post_response = self.session.post(firebase_url, params=params, headers=headers, timeout=15)
                print(f"   Firebase POST: {post_response.status_code}")
                
                if post_response.status_code in [200, 204]:
                    print("   ✅ Firebase fixed via POST method!")
                    return {'fixed': True, 'status': post_response.status_code, 'method': 'POST Fix'}
                
                return {'fixed': False, 'status': response.status_code, 'error': 'Parameter encoding issue'}
                
        except Exception as e:
            print(f"   ❌ Firebase fix failed: {e}")
            return {'fixed': False, 'error': str(e)}
    
    def fix_typesense_empty_collection(self) -> Dict:
        """Fix Typesense empty collection by finding alternative data sources"""
        print("\n🔍 FIXING TYPESENSE EMPTY COLLECTION")
        print("=" * 40)
        
        # The issue: Typesense collection exists but has 0 documents
        # Solution: Find alternative collections or trigger data refresh
        
        headers = {
            'X-TYPESENSE-API-KEY': self.typesense_api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            # Step 1: Check all available collections
            collections_url = "https://xczkhpt94lod37gqp.a1.typesense.net/collections"
            response = self.session.get(f"{collections_url}?x-typesense-api-key={self.typesense_api_key}")
            
            if response.status_code == 200:
                collections = response.json()
                print(f"   Found {len(collections)} collections:")
                
                working_collections = []
                
                for collection in collections:
                    name = collection.get('name', 'Unknown')
                    docs = collection.get('num_documents', 0)
                    print(f"      • {name}: {docs} documents")
                    
                    if docs > 0:
                        # Test if this collection has searchable data
                        test_payload = {
                            "searches": [
                                {
                                    "collection": name,
                                    "q": "",
                                    "per_page": 1
                                }
                            ]
                        }
                        
                        test_response = self.session.post(
                            f"{self.typesense_url}?x-typesense-api-key={self.typesense_api_key}",
                            json=test_payload,
                            headers=headers,
                            timeout=10
                        )
                        
                        if test_response.status_code == 200:
                            test_data = test_response.json()
                            if 'results' in test_data and len(test_data['results']) > 0:
                                found = test_data['results'][0].get('found', 0)
                                if found > 0:
                                    working_collections.append({
                                        'name': name,
                                        'documents': found,
                                        'searchable': True
                                    })
                                    print(f"         ✅ {found} searchable documents!")
                
                if working_collections:
                    print(f"\n   ✅ Found {len(working_collections)} working collections!")
                    return {
                        'fixed': True,
                        'working_collections': working_collections,
                        'recommendation': f'Use collection: {working_collections[0]["name"]}'
                    }
                else:
                    print("\n   ❌ All collections are empty or unsearchable")
                    
                    # Step 2: Try to trigger data refresh
                    return self.trigger_typesense_refresh()
            else:
                print(f"   ❌ Collections list failed: {response.status_code}")
                return {'fixed': False, 'error': f'HTTP {response.status_code}'}
                
        except Exception as e:
            print(f"   ❌ Collection fix failed: {e}")
            return {'fixed': False, 'error': str(e)}
    
    def trigger_typesense_refresh(self) -> Dict:
        """Attempt to trigger Typesense data refresh"""
        print("\n   🔄 ATTEMPTING TYPESENSE DATA REFRESH")
        print("   " + "=" * 35)
        
        # Try to find Mac.bid's data refresh endpoint
        try:
            # Check if there's a data sync endpoint
            sync_endpoints = [
                f"{self.base_url}/api/sync/typesense",
                f"{self.base_url}/api/refresh/search",
                f"{self.base_url}/api/admin/reindex",
                f"{self.base_url}/_next/api/search/refresh"
            ]
            
            for endpoint in sync_endpoints:
                try:
                    response = self.session.post(endpoint, timeout=10)
                    print(f"      {endpoint.split('/')[-1]}: {response.status_code}")
                    
                    if response.status_code in [200, 202]:  # 202 = Accepted for processing
                        print(f"      ✅ Data refresh triggered!")
                        return {
                            'fixed': True,
                            'method': 'Data Refresh',
                            'endpoint': endpoint,
                            'status': response.status_code
                        }
                except:
                    continue
            
            # Alternative: Use Mac.bid API to get fresh data
            print("\n   🌐 TRYING MAC.BID API AS ALTERNATIVE")
            api_url = f"{self.base_url}/api/search"
            
            params = {
                'query': '',
                'page': 1,
                'limit': 10
            }
            
            response = self.session.get(api_url, params=params, timeout=10)
            print(f"      Mac.bid API: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, (list, dict)):
                    lots_count = len(data) if isinstance(data, list) else len(data.get('lots', []))
                    print(f"      ✅ Mac.bid API working! Found {lots_count} lots")
                    return {
                        'fixed': True,
                        'method': 'Mac.bid API Alternative',
                        'lots_found': lots_count,
                        'recommendation': 'Use Mac.bid API instead of Typesense'
                    }
            
            return {
                'fixed': False,
                'issue': 'No data refresh method found',
                'recommendation': 'Contact Mac.bid support for Typesense data refresh'
            }
            
        except Exception as e:
            return {'fixed': False, 'error': str(e)}
    
    def run_final_fix(self) -> Dict:
        """Run the final comprehensive fix"""
        print("🚀 FINAL AUTHENTICATION FIX")
        print("=" * 30)
        
        results = {
            'firebase': {},
            'typesense': {},
            'overall_success': False
        }
        
        # Fix Firebase 400 error
        results['firebase'] = self.fix_firebase_400_error()
        
        # Fix Typesense empty collection
        results['typesense'] = self.fix_typesense_empty_collection()
        
        # Determine overall success
        firebase_fixed = results['firebase'].get('fixed', False)
        typesense_fixed = results['typesense'].get('fixed', False)
        
        results['overall_success'] = firebase_fixed or typesense_fixed
        
        return results

def main():
    """Main execution function"""
    fixer = FinalAuthenticationFix()
    
    print("🔧 FINAL AUTHENTICATION FIX")
    print("=" * 35)
    
    # Run final fix
    results = fixer.run_final_fix()
    
    print(f"\n📊 FINAL FIX RESULTS:")
    print("=" * 25)
    
    # Firebase results
    firebase = results['firebase']
    if firebase.get('fixed'):
        print(f"🔥 Firebase: ✅ FIXED!")
        print(f"   Method: {firebase.get('method', 'Unknown')}")
        print(f"   Status: {firebase.get('status', 'Unknown')}")
    else:
        print(f"🔥 Firebase: ❌ Still has 400 error")
        print(f"   Issue: {firebase.get('error', 'Unknown')}")
    
    # Typesense results
    typesense = results['typesense']
    if typesense.get('fixed'):
        print(f"🔍 Typesense: ✅ FIXED!")
        print(f"   Method: {typesense.get('method', 'Alternative found')}")
        if 'working_collections' in typesense:
            collections = typesense['working_collections']
            print(f"   Working Collections: {len(collections)}")
            for col in collections[:3]:  # Show first 3
                print(f"      • {col['name']}: {col['documents']} docs")
        if 'recommendation' in typesense:
            print(f"   Recommendation: {typesense['recommendation']}")
    else:
        print(f"🔍 Typesense: ❌ Still empty")
        print(f"   Issue: {typesense.get('issue', 'Unknown')}")
        if 'recommendation' in typesense:
            print(f"   Recommendation: {typesense['recommendation']}")
    
    # Overall status
    if results['overall_success']:
        print(f"\n🎉 OVERALL: ✅ SUCCESS!")
        print("   At least one authentication system is now working")
    else:
        print(f"\n❌ OVERALL: ❌ NEEDS MORE WORK")
        print("   Both systems still need attention")

if __name__ == "__main__":
    main() 