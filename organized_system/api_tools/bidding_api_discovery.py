#!/usr/bin/env python3
"""
Mac.bid Bidding API Discovery
Reverse-engineers the actual bidding endpoints used by Mac.bid's frontend
"""

import requests
import json
import time
from datetime import datetime
import re
import os
from typing import Dict, List, Optional

class BiddingAPIDiscovery:
    def __init__(self):
        self.base_url = "https://www.mac.bid"
        self.api_base = "https://www.mac.bid/api"
        
        # Authentication from our working system
        self.session_headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.6',
            'content-type': 'application/json',
            'origin': 'https://www.mac.bid',
            'referer': 'https://www.mac.bid/',
            'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'x-requested-with': 'XMLHttpRequest'
        }
        
        self.session_cookies = {
            '__stripe_mid': 'b1219cc5-9a1f-4e9b-9b3b-ce16a3d90ba32b7fa4',
            'CookieConsent': 'true',
            'ab.storage.deviceId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3A6557c69b-3239-8d82-7b30-ec5862a4de57%7Ce%3Aundefined%7Cc%3A1747345668914%7Cl%3A1749267987617',
            'ab.storage.userId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3A2710619%7Ce%3Aundefined%7Cc%3A1749188938629%7Cl%3A1749267987617',
            '__stripe_sid': '82edccd6-9b05-4a36-a118-e155bd9212b7ec69fb',
            'mp_78faade7af6b4f2ee5e1af36d8ac6232_mixpanel': '%7B%22distinct_id%22%3A%202710619%2C%22%24device_id%22%3A%20%22196d5eae0323e9-06ed80c653d2808-19525636-13c680-196d5eae0323e9%22%2C%22%24initial_referrer%22%3A%20%22%24direct%22%2C%22%24initial_referring_domain%22%3A%20%22%24direct%22%2C%22__mps%22%3A%20%7B%7D%2C%22__mpso%22%3A%20%7B%7D%2C%22__mpus%22%3A%20%7B%7D%2C%22__mpa%22%3A%20%7B%7D%2C%22__mpu%22%3A%20%7B%7D%2C%22__mpr%22%3A%20%5B%5D%2C%22__mpap%22%3A%20%5B%5D%2C%22platform%22%3A%20%22website%22%2C%22selected_locations%22%3A%20%5B%0A%20%20%20%20%22Rock%20Hill%22%2C%0A%20%20%20%20%22Gastonia%22%0A%5D%2C%22%24user_id%22%3A%202710619%2C%22active_items%22%3A%20%5B%0A%20%20%20%20%7B%22id%22%3A%2046608657%2C%22invoice_id%22%3A%2018714030%2C%22box_size%22%3A%20%22large%22%2C%22warehouse_location%22%3A%20%22ANL-D-BIN-55%22%2C%22removal_container%22%3A%20null%2C%22product_name%22%3A%20%22KOKISO%20metal%20%22%2C%22status%22%3A%20%22PENDING-TRANSFER%22%2C%22boxes%22%3A%201%2C%22note%22%3A%20null%2C%22current_location_id%22%3A%2038%2C%22allow_transfers%22%3A%201%2C%22allow_shipping%22%3A%200%2C%22is_turbo%22%3A%200%2C%22free_transfers%22%3A%200%2C%22auction_number%22%3A%20%22ANL2506-05-A2%22%2C%22auction_abandon_date%22%3A%20%222025-06-10T18%3A00%3A00.000Z%22%2C%22abandon_date%22%3A%20null%2C%22lot_number%22%3A%20%221726Z%22%2C%22lot_id%22%3A%2035490378%2C%22has_buyer_assurance%22%3A%200%2C%22item_price%22%3A%205.67%2C%22cover_image%22%3A%20%22https%3A%2F%2Fm.media-amazon.com%2Fimages%2FI%2F71fm%2BEdRyKL.jpg%22%2C%22grand_total%22%3A%205.67%2C%22date_paid%22%3A%20%222025-06-06T09%3A20%3A50.000Z%22%2C%22transfer_id%22%3A%206229971%2C%22start_location_code%22%3A%20%22ANL%22%2C%22dest_location_code%22%3A%20%22RHA%22%2C%22start_location_id%22%3A%2038%2C%22dest_location_id%22%3A%2028%2C%22grouping_id%22%3A%20%2218714030_200_35872237%22%2C%22auction_lot_deadline%22%3A%20null%7D%0A%5D%2C%22mac_bucks_balance%22%3A%200%2C%22mac_bucks_gift_balance%22%3A%200%2C%22active_membership%22%3A%20%7B%22id%22%3A%20123339%2C%22date_created%22%3A%20%222025-05-29T18%3A11%3A59.000Z%22%2C%22membership_plan%22%3A%20%22STANDARD%22%2C%22customer_id%22%3A%202710619%2C%22bill_period%22%3A%20%22MONTHLY%22%2C%22bill_amount%22%3A%209.99%2C%22date_cancelled%22%3A%20null%2C%22external_id%22%3A%20%22sub_1RUFc8DhtPPAHVyel4iCCWV7%22%2C%22cancel_reason%22%3A%20null%2C%22stripe_customer_id%22%3A%20%22cus_S6Y0gK006usyW7%22%2C%22date_updated%22%3A%20null%7D%2C%22watchlist_count%22%3A%207%2C%22onboarding%22%3A%20true%7D',
            'ab.storage.sessionId.ce8b7722-883a-498b-90ff-0aef9d0f0e62': 'g%3Aa18c4004-ac5d-06ae-84af-39127b94f2a6%7Ce%3A1749269831396%7Cc%3A1749267987616%7Cl%3A1749268031396'
        }
        
        self.discovered_endpoints = []
        
    def discover_bidding_endpoints(self) -> List[Dict]:
        """Discover potential bidding API endpoints"""
        
        print("🔍 DISCOVERING MAC.BID BIDDING API ENDPOINTS")
        print("="*50)
        
        # Common bidding endpoint patterns
        potential_endpoints = [
            "/api/bid",
            "/api/bids",
            "/api/place-bid",
            "/api/place_bid",
            "/api/auction/bid",
            "/api/auctions/bid",
            "/api/lot/bid",
            "/api/lots/bid",
            "/api/v1/bid",
            "/api/v2/bid",
            "/bid",
            "/bids",
            "/place-bid",
            "/auction-bid",
            "/api/bidding/place",
            "/api/bidding/submit",
            "/graphql",  # Many modern sites use GraphQL
        ]
        
        results = []
        
        for endpoint in potential_endpoints:
            result = self.test_endpoint(endpoint)
            if result:
                results.append(result)
                self.discovered_endpoints.append(result)
        
        return results
    
    def test_endpoint(self, endpoint: str) -> Optional[Dict]:
        """Test if an endpoint exists and what methods it accepts"""
        
        full_url = f"{self.base_url}{endpoint}"
        
        try:
            # Test OPTIONS request first (reveals allowed methods)
            options_response = requests.options(
                full_url,
                headers=self.session_headers,
                cookies=self.session_cookies,
                timeout=10
            )
            
            if options_response.status_code in [200, 204]:
                allowed_methods = options_response.headers.get('Allow', '')
                
                print(f"✅ Found endpoint: {endpoint}")
                print(f"   Status: {options_response.status_code}")
                print(f"   Allowed Methods: {allowed_methods}")
                
                # Test POST request (most likely for bidding)
                if 'POST' in allowed_methods:
                    post_result = self.test_post_request(full_url)
                    
                    return {
                        'endpoint': endpoint,
                        'full_url': full_url,
                        'status_code': options_response.status_code,
                        'allowed_methods': allowed_methods,
                        'post_test': post_result,
                        'discovered_at': datetime.now().isoformat()
                    }
            
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: {str(e)}")
            
        return None
    
    def test_post_request(self, url: str) -> Dict:
        """Test POST request to potential bidding endpoint"""
        
        # Test with minimal bid data
        test_bid_data = {
            'lot_id': 35863830,  # Our test lot
            'auction_id': 48796,
            'bid_amount': 1.00,  # Minimal test bid
            'customer_id': 2710619
        }
        
        try:
            response = requests.post(
                url,
                headers=self.session_headers,
                cookies=self.session_cookies,
                json=test_bid_data,
                timeout=10
            )
            
            result = {
                'status_code': response.status_code,
                'response_headers': dict(response.headers),
                'response_text': response.text[:500],  # First 500 chars
                'content_type': response.headers.get('content-type', '')
            }
            
            if response.status_code == 200:
                print(f"   🎯 POST Success: {response.status_code}")
            elif response.status_code in [400, 401, 403]:
                print(f"   ⚠️  POST Auth/Validation: {response.status_code}")
            elif response.status_code == 404:
                print(f"   ❌ POST Not Found: {response.status_code}")
            else:
                print(f"   ❓ POST Unknown: {response.status_code}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            return {
                'error': str(e),
                'status_code': None
            }
    
    def analyze_frontend_javascript(self) -> List[str]:
        """Analyze Mac.bid's frontend JavaScript for bidding endpoints"""
        
        print("\n🔍 ANALYZING FRONTEND JAVASCRIPT")
        print("="*40)
        
        try:
            # Get the main page
            response = requests.get(
                self.base_url,
                headers=self.session_headers,
                cookies=self.session_cookies
            )
            
            if response.status_code == 200:
                html_content = response.text
                
                # Extract JavaScript file URLs
                js_urls = re.findall(r'<script[^>]*src="([^"]*\.js[^"]*)"', html_content)
                
                endpoints_found = []
                
                for js_url in js_urls[:5]:  # Check first 5 JS files
                    if js_url.startswith('/'):
                        js_url = self.base_url + js_url
                    
                    endpoints = self.analyze_js_file(js_url)
                    endpoints_found.extend(endpoints)
                
                return list(set(endpoints_found))  # Remove duplicates
                
        except Exception as e:
            print(f"❌ Error analyzing frontend: {e}")
            
        return []
    
    def analyze_js_file(self, js_url: str) -> List[str]:
        """Analyze a JavaScript file for API endpoints"""
        
        try:
            response = requests.get(js_url, timeout=10)
            
            if response.status_code == 200:
                js_content = response.text
                
                # Look for API endpoint patterns
                patterns = [
                    r'["\'](/api/[^"\']*bid[^"\']*)["\']',
                    r'["\']([^"\']*bid[^"\']*)["\']',
                    r'fetch\(["\']([^"\']*)["\']',
                    r'axios\.post\(["\']([^"\']*)["\']',
                    r'\.post\(["\']([^"\']*)["\']'
                ]
                
                endpoints = []
                for pattern in patterns:
                    matches = re.findall(pattern, js_content, re.IGNORECASE)
                    for match in matches:
                        if 'bid' in match.lower() or 'auction' in match.lower():
                            endpoints.append(match)
                
                if endpoints:
                    print(f"   📄 {js_url}: Found {len(endpoints)} potential endpoints")
                
                return endpoints
                
        except Exception as e:
            print(f"   ❌ Error analyzing {js_url}: {e}")
            
        return []
    
    def test_graphql_endpoint(self) -> Optional[Dict]:
        """Test if Mac.bid uses GraphQL for bidding"""
        
        print("\n🔍 TESTING GRAPHQL ENDPOINT")
        print("="*30)
        
        graphql_url = f"{self.base_url}/graphql"
        
        # Test GraphQL introspection query
        introspection_query = {
            "query": """
            query IntrospectionQuery {
                __schema {
                    mutationType {
                        name
                        fields {
                            name
                            description
                        }
                    }
                }
            }
            """
        }
        
        try:
            response = requests.post(
                graphql_url,
                headers=self.session_headers,
                cookies=self.session_cookies,
                json=introspection_query,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'data' in data and '__schema' in data['data']:
                    mutations = data['data']['__schema']['mutationType']
                    
                    if mutations and 'fields' in mutations:
                        bid_mutations = [
                            field for field in mutations['fields']
                            if 'bid' in field['name'].lower()
                        ]
                        
                        if bid_mutations:
                            print(f"✅ GraphQL bidding mutations found:")
                            for mutation in bid_mutations:
                                print(f"   - {mutation['name']}: {mutation.get('description', 'No description')}")
                            
                            return {
                                'endpoint': '/graphql',
                                'type': 'GraphQL',
                                'bid_mutations': bid_mutations,
                                'discovered_at': datetime.now().isoformat()
                            }
            
            print(f"❌ GraphQL: {response.status_code} - {response.text[:100]}")
            
        except Exception as e:
            print(f"❌ GraphQL error: {e}")
            
        return None
    
    def generate_discovery_report(self) -> Dict:
        """Generate comprehensive discovery report"""
        
        print("\n📊 GENERATING DISCOVERY REPORT")
        print("="*35)
        
        # Run all discovery methods
        rest_endpoints = self.discover_bidding_endpoints()
        js_endpoints = self.analyze_frontend_javascript()
        graphql_result = self.test_graphql_endpoint()
        
        report = {
            'discovery_timestamp': datetime.now().isoformat(),
            'rest_endpoints': rest_endpoints,
            'javascript_endpoints': js_endpoints,
            'graphql_endpoint': graphql_result,
            'summary': {
                'total_endpoints_found': len(rest_endpoints) + len(js_endpoints) + (1 if graphql_result else 0),
                'rest_endpoints_count': len(rest_endpoints),
                'js_endpoints_count': len(js_endpoints),
                'graphql_available': bool(graphql_result)
            }
        }
        
        # Save report
        os.makedirs('data_outputs', exist_ok=True)
        with open('data_outputs/bidding_api_discovery_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 DISCOVERY SUMMARY:")
        print(f"   REST Endpoints: {len(rest_endpoints)}")
        print(f"   JS Endpoints: {len(js_endpoints)}")
        print(f"   GraphQL: {'Yes' if graphql_result else 'No'}")
        print(f"   Total Found: {report['summary']['total_endpoints_found']}")
        
        return report

def main():
    """Main discovery function"""
    
    print("🎯 MAC.BID BIDDING API DISCOVERY")
    print("="*50)
    print("Discovering real bidding endpoints for automated bidding...")
    
    discovery = BiddingAPIDiscovery()
    report = discovery.generate_discovery_report()
    
    print(f"\n✅ Discovery complete! Report saved to: data_outputs/bidding_api_discovery_report.json")
    
    if report['summary']['total_endpoints_found'] > 0:
        print(f"\n🎯 NEXT STEPS:")
        print(f"1. Review discovered endpoints in the report")
        print(f"2. Test the most promising endpoints")
        print(f"3. Implement real bidding functionality")
    else:
        print(f"\n⚠️  No obvious bidding endpoints found.")
        print(f"   May need browser automation or deeper analysis.")

if __name__ == "__main__":
    main() 