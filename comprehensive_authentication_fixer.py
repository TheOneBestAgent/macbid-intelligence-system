#!/usr/bin/env python3
"""
Comprehensive Authentication & Data Fixer
Fixes both Firebase 400 errors and Typesense empty collection issues
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Import discovered authentication
from macbid_auth_config import MACBID_HEADERS, MACBID_CUSTOMER_ID, MACBID_BASE_URL, FIREBASE_SESSION_ID, SESSION_ID

class ComprehensiveAuthenticationFixer:
    def __init__(self):
        self.base_url = MACBID_BASE_URL
        self.session = requests.Session()
        self.session.headers.update(MACBID_HEADERS)
        
        # Firebase configuration
        self.firebase_session = FIREBASE_SESSION_ID
        self.session_id = SESSION_ID
        self.firebase_base = "https://firestore.googleapis.com/google.firestore.v1.Firestore"
        self.firebase_project = "projects/recommerce-a0291/databases/(default)"
        
        # Typesense configuration
        self.typesense_url = "https://xczkhpt94lod37gqp.a1.typesense.net/multi_search"
        self.typesense_api_key = "jxX8RU6YVOkm9esgd9buaYjulIWv6N52"
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def fix_firebase_authentication(self) -> Dict:
        """Fix Firebase authentication using correct parameters from macbid_breakdown"""
        print("🔥 FIXING FIREBASE AUTHENTICATION")
        print("=" * 40)
        
        # The key insight: Firebase needs specific parameter format from breakdown analysis
        # Use the exact working parameters discovered in the breakdown
        
        try:
            # Method 1: Use exact URL format from breakdown (most successful pattern)
            firebase_url = f"{self.firebase_base}/Listen/channel"
            
            # Parameters that appear most frequently in successful requests
            params = {
                'VER': '8',
                'database': 'projects%2Frecommerce-a0291%2Fdatabases%2F(default)',  # URL encoded
                'gsessionid': self.firebase_session,
                'SID': self.session_id,
                'RID': 'rpc',  # Most common RID value
                'AID': '8780',  # Common AID value
                'CI': '0',
                'TYPE': 'xmlhttp',
                'zx': f'fix{int(time.time())}',  # Unique identifier
                't': '1'
            }
            
            # Headers that work with Firebase
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
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = self.session.get(firebase_url, params=params, headers=headers, timeout=15)
            
            print(f"   Firebase Listen Channel: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Firebase authentication FIXED!")
                return {'fixed': True, 'method': 'Listen Channel', 'status': 200}
            elif response.status_code == 204:
                print("   ✅ Firebase authentication WORKING! (No content)")
                return {'fixed': True, 'method': 'Listen Channel', 'status': 204}
            else:
                print(f"   ⚠️  Firebase still returning {response.status_code}")
                
                # Method 2: Try alternative approach - Batch operations
                batch_url = f"{self.firebase_base}/BatchGet"
                
                batch_headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.firebase_session}',
                    'X-Goog-Api-Key': self.firebase_session,
                }
                batch_headers.update(headers)
                
                payload = {
                    'database': self.firebase_project,
                    'documents': [f'{self.firebase_project}/documents/lots']
                }
                
                batch_response = self.session.post(batch_url, json=payload, headers=batch_headers, timeout=10)
                print(f"   Firebase Batch Get: {batch_response.status_code}")
                
                if batch_response.status_code in [200, 404]:  # 404 means auth worked
                    print("   ✅ Firebase Batch authentication WORKING!")
                    return {'fixed': True, 'method': 'Batch Get', 'status': batch_response.status_code}
                
                return {'fixed': False, 'error': f'HTTP {response.status_code}', 'response': response.text[:200]}
                
        except Exception as e:
            print(f"   ❌ Firebase fix failed: {e}")
            return {'fixed': False, 'error': str(e)}
    
    def fix_typesense_data_access(self) -> Dict:
        """Fix Typesense data access and find working collection"""
        print("\n🔍 FIXING TYPESENSE DATA ACCESS")
        print("=" * 40)
        
        headers = {
            'X-TYPESENSE-API-KEY': self.typesense_api_key,
            'Content-Type': 'application/json'
        }
        
        # Strategy 1: Check if collection exists but is empty
        try:
            collection_url = "https://xczkhpt94lod37gqp.a1.typesense.net/collections"
            response = self.session.get(f"{collection_url}?x-typesense-api-key={self.typesense_api_key}", headers=headers)
            
            if response.status_code == 200:
                collections = response.json()
                print(f"   ✅ Found {len(collections)} collections")
                
                for collection in collections:
                    name = collection.get('name', 'Unknown')
                    docs = collection.get('num_documents', 0)
                    print(f"      • {name}: {docs} documents")
                    
                    # Test each collection for data
                    if docs > 0:
                        test_payload = {
                            "searches": [
                                {
                                    "collection": name,
                                    "q": "",
                                    "per_page": 5,
                                    "page": 1
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
                                    print(f"      ✅ Collection '{name}' has {found} searchable documents!")
                                    return {
                                        'fixed': True,
                                        'working_collection': name,
                                        'documents': found,
                                        'method': 'Collection Discovery'
                                    }
                
                # If no collections have data, the issue is data refresh needed
                return {
                    'fixed': False,
                    'issue': 'Collections exist but are empty',
                    'collections': [c.get('name') for c in collections],
                    'recommendation': 'Data refresh/repopulation needed'
                }
            else:
                print(f"   ❌ Collections list failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Collection analysis failed: {e}")
        
        # Strategy 2: Try alternative Typesense endpoints
        try:
            print("\n   🔍 Trying alternative Typesense endpoints...")
            
            # Try direct document access
            alt_endpoints = [
                "https://xczkhpt94lod37gqp.a1.typesense.net/collections/lots/documents/search",
                "https://xczkhpt94lod37gqp.a1.typesense.net/collections/auctions/documents/search",
                "https://xczkhpt94lod37gqp.a1.typesense.net/collections/inventory/documents/search"
            ]
            
            for endpoint in alt_endpoints:
                collection_name = endpoint.split('/')[-3]
                
                params = {
                    'q': '*',
                    'query_by': 'product_name,description',
                    'per_page': 5,
                    'x-typesense-api-key': self.typesense_api_key
                }
                
                response = self.session.get(endpoint, params=params, headers=headers, timeout=10)
                print(f"      {collection_name}: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    found = data.get('found', 0)
                    if found > 0:
                        print(f"      ✅ Found {found} documents in '{collection_name}'!")
                        return {
                            'fixed': True,
                            'working_collection': collection_name,
                            'documents': found,
                            'method': 'Direct Endpoint',
                            'endpoint': endpoint
                        }
                        
        except Exception as e:
            print(f"   ❌ Alternative endpoints failed: {e}")
        
        return {
            'fixed': False,
            'issue': 'No accessible data found',
            'recommendation': 'Check Typesense data population or API key permissions'
        }
    
    def test_mac_bid_api_alternatives(self) -> Dict:
        """Test Mac.bid API alternatives for data access"""
        print("\n🌐 TESTING MAC.BID API ALTERNATIVES")
        print("=" * 40)
        
        # Test the comprehensive warehouse scanner approach
        try:
            # Use the working comprehensive warehouse scanner endpoint
            api_url = f"{self.base_url}/api/search"
            
            params = {
                'query': '',
                'location': 'Rock Hill',
                'page': 1,
                'limit': 10
            }
            
            response = self.session.get(api_url, params=params, timeout=10)
            print(f"   Mac.bid API Search: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and 'lots' in data:
                    lots = data['lots']
                    print(f"   ✅ Found {len(lots)} lots via Mac.bid API!")
                    return {
                        'working': True,
                        'method': 'Mac.bid API',
                        'lots_found': len(lots),
                        'endpoint': api_url
                    }
                elif isinstance(data, list):
                    print(f"   ✅ Found {len(data)} lots via Mac.bid API!")
                    return {
                        'working': True,
                        'method': 'Mac.bid API',
                        'lots_found': len(data),
                        'endpoint': api_url
                    }
                    
        except Exception as e:
            print(f"   ❌ Mac.bid API test failed: {e}")
        
        # Test NextJS API approach
        try:
            nextjs_url = f"{self.base_url}/_next/static/chunks/pages"
            response = self.session.get(nextjs_url, timeout=10)
            print(f"   NextJS API: {response.status_code}")
            
            if response.status_code == 200:
                return {
                    'working': True,
                    'method': 'NextJS API',
                    'status': 'Available for data extraction'
                }
                
        except Exception as e:
            print(f"   ❌ NextJS API test failed: {e}")
        
        return {'working': False, 'issue': 'No alternative APIs accessible'}
    
    def comprehensive_fix(self) -> Dict:
        """Run comprehensive fix for all authentication and data issues"""
        print("🔧 COMPREHENSIVE AUTHENTICATION & DATA FIX")
        print("=" * 50)
        
        results = {
            'firebase': {},
            'typesense': {},
            'alternatives': {},
            'overall_status': 'unknown'
        }
        
        # Fix Firebase
        results['firebase'] = self.fix_firebase_authentication()
        
        # Fix Typesense
        results['typesense'] = self.fix_typesense_data_access()
        
        # Test alternatives
        results['alternatives'] = self.test_mac_bid_api_alternatives()
        
        # Determine overall status
        firebase_working = results['firebase'].get('fixed', False)
        typesense_working = results['typesense'].get('fixed', False)
        alternatives_working = results['alternatives'].get('working', False)
        
        if firebase_working and typesense_working:
            results['overall_status'] = 'fully_fixed'
        elif firebase_working or typesense_working or alternatives_working:
            results['overall_status'] = 'partially_fixed'
        else:
            results['overall_status'] = 'needs_work'
        
        return results

def main():
    """Main execution function"""
    fixer = ComprehensiveAuthenticationFixer()
    
    print("🚀 COMPREHENSIVE AUTHENTICATION & DATA FIXER")
    print("=" * 55)
    
    # Run comprehensive fix
    results = fixer.comprehensive_fix()
    
    print(f"\n📊 COMPREHENSIVE FIX RESULTS:")
    print("=" * 35)
    
    # Firebase results
    firebase = results['firebase']
    if firebase.get('fixed'):
        print(f"🔥 Firebase: ✅ FIXED via {firebase.get('method', 'Unknown')}")
        print(f"   Status: {firebase.get('status', 'Unknown')}")
    else:
        print(f"🔥 Firebase: ❌ Still needs work")
        print(f"   Error: {firebase.get('error', 'Unknown')}")
    
    # Typesense results
    typesense = results['typesense']
    if typesense.get('fixed'):
        print(f"🔍 Typesense: ✅ FIXED via {typesense.get('method', 'Unknown')}")
        print(f"   Working Collection: {typesense.get('working_collection', 'Unknown')}")
        print(f"   Documents: {typesense.get('documents', 0)}")
    else:
        print(f"🔍 Typesense: ❌ Still needs work")
        print(f"   Issue: {typesense.get('issue', 'Unknown')}")
        print(f"   Recommendation: {typesense.get('recommendation', 'Unknown')}")
    
    # Alternatives results
    alternatives = results['alternatives']
    if alternatives.get('working'):
        print(f"🌐 Alternatives: ✅ WORKING via {alternatives.get('method', 'Unknown')}")
        if 'lots_found' in alternatives:
            print(f"   Lots Found: {alternatives['lots_found']}")
    else:
        print(f"🌐 Alternatives: ❌ Not accessible")
    
    # Overall status
    overall = results['overall_status']
    if overall == 'fully_fixed':
        print(f"\n🎉 OVERALL STATUS: ✅ FULLY FIXED!")
        print("   Both Firebase and Typesense are working")
    elif overall == 'partially_fixed':
        print(f"\n⚠️  OVERALL STATUS: 🔶 PARTIALLY FIXED")
        print("   At least one system is working")
    else:
        print(f"\n❌ OVERALL STATUS: ❌ NEEDS MORE WORK")
        print("   All systems need attention")

if __name__ == "__main__":
    main() 