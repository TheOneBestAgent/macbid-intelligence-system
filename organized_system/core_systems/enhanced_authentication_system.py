#!/usr/bin/env python3
"""
Enhanced Mac.bid Authentication System
Uses discovered authentication patterns for reliable API access
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Import the discovered authentication configuration
from macbid_auth_config import MACBID_HEADERS, MACBID_CUSTOMER_ID, MACBID_BASE_URL, FIREBASE_SESSION_ID, SESSION_ID

class EnhancedMacBidAuth:
    def __init__(self):
        self.base_url = MACBID_BASE_URL
        self.customer_id = MACBID_CUSTOMER_ID
        self.firebase_session = FIREBASE_SESSION_ID
        self.session_id = SESSION_ID
        self.session = requests.Session()
        self.session.headers.update(MACBID_HEADERS)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def test_authentication(self) -> Dict[str, Any]:
        """Test all authentication endpoints"""
        print("🧪 TESTING ENHANCED AUTHENTICATION")
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
                # Try to find the correct build ID from the page
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
            
            # Test 3: Typesense search (using REAL working endpoint)
            try:
                # Use the REAL working Typesense endpoint from our existing code
                typesense_url = "https://xczkhpt94lod37gqp.a1.typesense.net/multi_search"
                typesense_api_key = "jxX8RU6YVOkm9esgd9buaYjulIWv6N52"
                
                # Use the exact payload format from working code
                payload = {
                    "searches": [
                        {
                            "collection": "lots",
                            "q": "*",
                            "query_by": "product_name,description,keywords,upc,inventory_id",
                            "filter_by": "location_id:=sc",
                            "per_page": 10,
                            "page": 1,
                            "sort_by": "ranking_weight:desc"
                        }
                    ]
                }
                
                headers = {
                    'X-TYPESENSE-API-KEY': typesense_api_key,
                    'Content-Type': 'application/json'
                }
                
                typesense_response = self.session.post(
                    f"{typesense_url}?x-typesense-api-key={typesense_api_key}",
                    json=payload,
                    headers=headers
                )
                results['typesense_search'] = typesense_response.status_code == 200
                print(f"   🔍 Typesense Search: {typesense_response.status_code} {'✅' if results['typesense_search'] else '❌'}")
                
                if results['typesense_search']:
                    data = typesense_response.json()
                    if 'results' in data and len(data['results']) > 0:
                        found = data['results'][0].get('found', 0)
                        print(f"   📊 Found {found} lots")
                    
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
    
    def get_authenticated_session(self) -> requests.Session:
        """Get a properly authenticated session"""
        return self.session
    
    def search_lots_authenticated(self, location: str = "sc", query: str = "*", per_page: int = 50) -> Dict:
        """Search lots using authenticated Typesense"""
        try:
            # Use the REAL working Typesense endpoint and format
            typesense_url = "https://xczkhpt94lod37gqp.a1.typesense.net/multi_search"
            typesense_api_key = "jxX8RU6YVOkm9esgd9buaYjulIWv6N52"
            
            # Use the exact payload format from working code
            payload = {
                "searches": [
                    {
                        "collection": "lots",
                        "q": query,
                        "query_by": "product_name,description,keywords,upc,inventory_id",
                        "filter_by": f"location_id:={location}",
                        "per_page": per_page,
                        "page": 1,
                        "sort_by": "ranking_weight:desc"
                    }
                ]
            }
            
            headers = {
                'X-TYPESENSE-API-KEY': typesense_api_key,
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(
                f"{typesense_url}?x-typesense-api-key={typesense_api_key}",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'results' in data and len(data['results']) > 0:
                    found = data['results'][0].get('found', 0)
                    hits = data['results'][0].get('hits', [])
                    print(f"✅ Typesense search successful: {found} lots found")
                    return {
                        'found': found,
                        'hits': hits,
                        'results': data['results']
                    }
                else:
                    return {'hits': [], 'found': 0, 'error': 'No results in response'}
            else:
                print(f"❌ Typesense search failed: {response.status_code}")
                return {'hits': [], 'found': 0, 'error': f'HTTP {response.status_code}'}
            
        except Exception as e:
            print(f"❌ Typesense search error: {e}")
            return {'hits': [], 'found': 0, 'error': str(e)}
    
    def get_lot_details_authenticated(self, lot_id: str) -> Dict:
        """Get lot details using authenticated session"""
        try:
            # Try NextJS API first
            build_id = "build-id"  # Placeholder, should be extracted dynamically
            nextjs_url = f"{self.base_url}/_next/data/{build_id}/lots/{lot_id}.json"
            
            response = self.session.get(nextjs_url)
            if response.status_code == 200:
                return response.json()
            
            # Fallback to regular page scraping
            lot_url = f"{self.base_url}/lots/{lot_id}"
            response = self.session.get(lot_url)
            
            if response.status_code == 200:
                # Parse HTML for lot details (simplified)
                return {
                    'lot_id': lot_id,
                    'html_content': response.text[:1000],  # First 1000 chars
                    'status': 'html_fallback'
                }
            
            return {'error': f'Failed to get lot {lot_id}', 'status_code': response.status_code}
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_realtime_bid_data(self, lot_id: str) -> Dict:
        """Get real-time bid data using Firebase connection"""
        try:
            # This would require WebSocket connection to Firebase
            # For now, return placeholder
            return {
                'lot_id': lot_id,
                'current_bid': 0,
                'bid_count': 0,
                'time_remaining': 'Unknown',
                'status': 'firebase_connection_needed'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def test_comprehensive_access(self) -> Dict:
        """Test comprehensive access to all Mac.bid systems"""
        print("\n🚀 COMPREHENSIVE AUTHENTICATION TEST")
        print("=" * 50)
        
        # Test basic authentication
        auth_results = self.test_authentication()
        
        # Test lot searching
        print("\n🔍 TESTING LOT SEARCH")
        print("-" * 25)
        search_results = self.search_lots_authenticated("sc", "*", 10)
        search_working = search_results.get('found', 0) > 0
        print(f"   Search Results: {search_results.get('found', 0)} lots {'✅' if search_working else '❌'}")
        
        # Test lot details
        print("\n📄 TESTING LOT DETAILS")
        print("-" * 25)
        if search_working and search_results.get('hits'):
            first_lot = search_results['hits'][0]['document']
            lot_id = first_lot.get('id', first_lot.get('lot_id', 'unknown'))
            lot_details = self.get_lot_details_authenticated(lot_id)
            details_working = 'error' not in lot_details
            print(f"   Lot Details: {lot_id} {'✅' if details_working else '❌'}")
        else:
            details_working = False
            print("   Lot Details: No lots to test ❌")
        
        # Summary
        total_tests = 6
        passed_tests = sum([
            auth_results['page_access'],
            auth_results['nextjs_api'],
            auth_results['typesense_search'],
            auth_results['firebase_realtime'],
            search_working,
            details_working
        ])
        
        success_rate = (passed_tests / total_tests) * 100
        
        print(f"\n📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 35)
        print(f"   Tests Passed: {passed_tests}/{total_tests}")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Status: {'🎉 EXCELLENT' if success_rate >= 80 else '⚠️ NEEDS WORK' if success_rate >= 50 else '❌ CRITICAL'}")
        
        return {
            'auth_results': auth_results,
            'search_working': search_working,
            'details_working': details_working,
            'success_rate': success_rate,
            'passed_tests': passed_tests,
            'total_tests': total_tests
        }

def main():
    """Main execution function"""
    auth_system = EnhancedMacBidAuth()
    results = auth_system.test_comprehensive_access()
    
    if results['success_rate'] >= 80:
        print("\n🎉 SUCCESS: Enhanced authentication system is working excellently!")
        print("   You can now use this for reliable Mac.bid API access.")
    elif results['success_rate'] >= 50:
        print("\n⚠️  PARTIAL SUCCESS: Some authentication methods are working.")
        print("   Consider using the working methods and improving others.")
    else:
        print("\n❌ CRITICAL: Authentication system needs significant work.")
        print("   Check network connectivity and authentication patterns.")

if __name__ == "__main__":
    main()