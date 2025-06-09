#!/usr/bin/env python3
"""
Working Mac.bid Authentication System
Uses the REAL working Typesense endpoint and authentication patterns
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Import the discovered authentication configuration
from macbid_auth_config import MACBID_HEADERS, MACBID_CUSTOMER_ID, MACBID_BASE_URL, FIREBASE_SESSION_ID, SESSION_ID

class WorkingMacBidAuth:
    def __init__(self):
        self.base_url = MACBID_BASE_URL
        self.customer_id = MACBID_CUSTOMER_ID
        self.firebase_session = FIREBASE_SESSION_ID
        self.session_id = SESSION_ID
        self.session = requests.Session()
        self.session.headers.update(MACBID_HEADERS)
        
        # REAL working Typesense configuration from existing code
        self.typesense_url = "https://xczkhpt94lod37gqp.a1.typesense.net/multi_search"
        self.typesense_api_key = "jxX8RU6YVOkm9esgd9buaYjulIWv6N52"
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def test_authentication(self) -> Dict[str, Any]:
        """Test all authentication endpoints with REAL working configurations"""
        print("🧪 TESTING WORKING AUTHENTICATION")
        print("=" * 40)
        
        results = {
            'page_access': False,
            'nextjs_api': False,
            'typesense_search': False,
            'firebase_realtime': False,
            'errors': []
        }
        
        try:
            # Test 1: Basic page access
            response = self.session.get(f"{self.base_url}/locations/sc")
            results['page_access'] = response.status_code == 200
            print(f"   📄 Page Access: {response.status_code} {'✅' if results['page_access'] else '❌'}")
            
            # Test 2: NextJS API access
            try:
                build_id = self._extract_build_id(response.text)
                if build_id:
                    nextjs_url = f"{self.base_url}/_next/data/{build_id}/locations/sc.json"
                    nextjs_response = self.session.get(nextjs_url)
                    results['nextjs_api'] = nextjs_response.status_code == 200
                    print(f"   🔌 NextJS API: {nextjs_response.status_code} {'✅' if results['nextjs_api'] else '❌'}")
                    
                    if results['nextjs_api']:
                        data = nextjs_response.json()
                        print(f"   📊 NextJS Data: {len(str(data))} bytes")
                else:
                    print("   🔌 NextJS API: Build ID not found ❌")
            except Exception as e:
                results['errors'].append(f"NextJS API: {e}")
                print(f"   🔌 NextJS API: Error ❌")
            
            # Test 3: REAL Typesense search (using working endpoint and format)
            try:
                payload = {
                    "searches": [
                        {
                            "collection": "lots",
                            "q": "*",
                            "query_by": "product_name,description,keywords,upc,inventory_id",
                                                         "filter_by": "auction_location:=[`Rock Hill`] && is_open:=[1]",
                            "per_page": 10,
                            "page": 1,
                            "sort_by": "ranking_weight:desc"
                        }
                    ]
                }
                
                headers = {
                    'X-TYPESENSE-API-KEY': self.typesense_api_key,
                    'Content-Type': 'application/json'
                }
                
                typesense_response = self.session.post(
                    f"{self.typesense_url}?x-typesense-api-key={self.typesense_api_key}",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                results['typesense_search'] = typesense_response.status_code == 200
                print(f"   🔍 Typesense Search: {typesense_response.status_code} {'✅' if results['typesense_search'] else '❌'}")
                
                if results['typesense_search']:
                    data = typesense_response.json()
                    if 'results' in data and len(data['results']) > 0:
                        found = data['results'][0].get('found', 0)
                        print(f"   📊 Found {found} lots in SC")
                    
            except Exception as e:
                results['errors'].append(f"Typesense: {e}")
                print(f"   🔍 Typesense Search: Error ❌")
            
            # Test 4: Firebase Realtime Database
            try:
                firebase_url = f"https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
                firebase_params = {
                    'gsessionid': self.firebase_session,
                    'VER': '8',
                    'database': 'projects/recommerce-a0291/databases/(default)',
                    'RID': 'rpc',
                    'SID': self.session_id,
                    'AID': '8780',
                    'CI': '0',
                    'TYPE': 'xmlhttp'
                }
                
                firebase_response = self.session.get(firebase_url, params=firebase_params, timeout=5)
                results['firebase_realtime'] = firebase_response.status_code in [200, 204]
                print(f"   🔥 Firebase Realtime: {firebase_response.status_code} {'✅' if results['firebase_realtime'] else '❌'}")
                
            except Exception as e:
                results['errors'].append(f"Firebase: {e}")
                print(f"   🔥 Firebase Realtime: Error ❌")
            
        except Exception as e:
            results['errors'].append(f"General: {e}")
            print(f"   ❌ General error: {e}")
        
        return results
    
    def _extract_build_id(self, html_content: str) -> Optional[str]:
        """Extract NextJS build ID from HTML content"""
        import re
        
        # Look for build ID in script tags
        build_id_pattern = r'"buildId":"([^"]+)"'
        match = re.search(build_id_pattern, html_content)
        if match:
            return match.group(1)
        
        # Alternative pattern
        build_id_pattern2 = r'/_next/data/([^/]+)/'
        match2 = re.search(build_id_pattern2, html_content)
        if match2:
            return match2.group(1)
            
        return None
    
    def search_lots_working(self, location: str = "sc", query: str = "*", per_page: int = 50) -> Dict:
        """Search lots using REAL working Typesense configuration"""
        try:
            print(f"🔍 Searching {location} for '{query}' (max {per_page} results)...")
            
            # Use the exact payload format from working code
            payload = {
                "searches": [
                    {
                        "collection": "lots",
                        "q": query,
                        "query_by": "product_name,description,keywords,upc,inventory_id",
                                                 "filter_by": f"auction_location:=[`{location.title()}`] && is_open:=[1]",
                        "per_page": per_page,
                        "page": 1,
                        "sort_by": "ranking_weight:desc"
                    }
                ]
            }
            
            headers = {
                'X-TYPESENSE-API-KEY': self.typesense_api_key,
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(
                f"{self.typesense_url}?x-typesense-api-key={self.typesense_api_key}",
                json=payload,
                headers=headers,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and len(data['results']) > 0:
                    found = data['results'][0].get('found', 0)
                    hits = data['results'][0].get('hits', [])
                    print(f"✅ Search successful: {found} lots found")
                    
                    # Show sample results
                    if hits:
                        print(f"   📋 Sample results:")
                        for i, hit in enumerate(hits[:3]):
                            doc = hit.get('document', {})
                            name = doc.get('product_name', 'Unknown')[:50]
                            price = doc.get('retail_price', 0)
                            bid = doc.get('current_bid', 0)
                            print(f"      {i+1}. {name}... (${price} retail, ${bid} bid)")
                    
                    return {
                        'found': found,
                        'hits': hits,
                        'results': data['results'],
                        'status': 'success'
                    }
                else:
                    return {'hits': [], 'found': 0, 'error': 'No results in response', 'status': 'empty'}
            else:
                print(f"❌ Search failed: HTTP {response.status_code}")
                return {'hits': [], 'found': 0, 'error': f'HTTP {response.status_code}', 'status': 'failed'}
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return {'hits': [], 'found': 0, 'error': str(e), 'status': 'error'}
    
    def get_lot_details_working(self, lot_id: str) -> Dict:
        """Get lot details using working authentication"""
        try:
            print(f"📄 Getting details for lot {lot_id}...")
            
            # Try NextJS API first
            response = self.session.get(f"{self.base_url}/locations/sc")
            build_id = self._extract_build_id(response.text)
            
            if build_id:
                nextjs_url = f"{self.base_url}/_next/data/{build_id}/lots/{lot_id}.json"
                response = self.session.get(nextjs_url)
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ NextJS lot details retrieved")
                    return {
                        'lot_id': lot_id,
                        'data': data,
                        'source': 'nextjs_api',
                        'status': 'success'
                    }
            
            # Fallback to regular page scraping
            lot_url = f"{self.base_url}/lots/{lot_id}"
            response = self.session.get(lot_url)
            
            if response.status_code == 200:
                print(f"✅ HTML lot page retrieved")
                return {
                    'lot_id': lot_id,
                    'html_content': response.text[:2000],  # First 2000 chars
                    'source': 'html_page',
                    'status': 'success'
                }
            
            return {
                'lot_id': lot_id,
                'error': f'Failed to get lot {lot_id}',
                'status_code': response.status_code,
                'status': 'failed'
            }
            
        except Exception as e:
            return {
                'lot_id': lot_id,
                'error': str(e),
                'status': 'error'
            }
    
    def test_comprehensive_working_access(self) -> Dict:
        """Test comprehensive access using REAL working configurations"""
        print("\n🚀 COMPREHENSIVE WORKING AUTHENTICATION TEST")
        print("=" * 55)
        
        # Test basic authentication
        auth_results = self.test_authentication()
        
        # Test lot searching with REAL working Typesense
        print("\n🔍 TESTING WORKING LOT SEARCH")
        print("-" * 30)
        search_results = self.search_lots_working("Rock Hill", "*", 10)
        search_working = search_results.get('found', 0) > 0
        print(f"   Search Status: {'✅ WORKING' if search_working else '❌ FAILED'}")
        
        # Test lot details
        print("\n📄 TESTING LOT DETAILS")
        print("-" * 25)
        if search_working and search_results.get('hits'):
            first_lot = search_results['hits'][0]['document']
            lot_id = first_lot.get('id', first_lot.get('lot_id', 'unknown'))
            lot_details = self.get_lot_details_working(lot_id)
            details_working = lot_details.get('status') == 'success'
            print(f"   Lot Details: {lot_id} {'✅' if details_working else '❌'}")
        else:
            details_working = False
            print("   Lot Details: No lots to test ❌")
        
        # Test multiple locations
        print("\n🏢 TESTING MULTIPLE LOCATIONS")
        print("-" * 30)
        locations = ['Rock Hill', 'Anderson', 'Greenville', 'Gastonia', 'Spartanburg']
        location_results = {}
        
        for location in locations:
            try:
                result = self.search_lots_working(location, "*", 5)
                found = result.get('found', 0)
                location_results[location] = found
                print(f"   {location.upper()}: {found} lots {'✅' if found > 0 else '❌'}")
            except Exception as e:
                location_results[location] = 0
                print(f"   {location.upper()}: Error ❌")
        
        # Summary
        total_tests = 4 + len(locations)  # auth tests + location tests
        passed_tests = sum([
            auth_results['page_access'],
            auth_results['nextjs_api'],
            auth_results['typesense_search'],
            search_working,
        ]) + sum(1 for count in location_results.values() if count > 0)
        
        success_rate = (passed_tests / total_tests) * 100
        total_lots_found = sum(location_results.values())
        
        print(f"\n📊 COMPREHENSIVE WORKING TEST RESULTS")
        print("=" * 40)
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Lots Found: {total_lots_found:,}")
        print(f"   Status: {'🎉 EXCELLENT' if success_rate >= 80 else '⚠️ NEEDS WORK' if success_rate >= 50 else '❌ CRITICAL'}")
        
        return {
            'auth_results': auth_results,
            'search_working': search_working,
            'details_working': details_working,
            'location_results': location_results,
            'success_rate': success_rate,
            'passed_tests': passed_tests,
            'total_tests': total_tests,
            'total_lots_found': total_lots_found
        }

def main():
    """Main execution function"""
    auth_system = WorkingMacBidAuth()
    results = auth_system.test_comprehensive_working_access()
    
    if results['success_rate'] >= 80:
        print("\n🎉 SUCCESS: Working authentication system is EXCELLENT!")
        print("   All major Mac.bid APIs are accessible and working.")
        print(f"   Found {results['total_lots_found']:,} lots across all locations.")
    elif results['success_rate'] >= 50:
        print("\n⚠️  PARTIAL SUCCESS: Some authentication methods are working.")
        print("   Consider using the working methods for your applications.")
    else:
        print("\n❌ CRITICAL: Authentication system needs significant work.")
        print("   Check network connectivity and authentication patterns.")

if __name__ == "__main__":
    main()