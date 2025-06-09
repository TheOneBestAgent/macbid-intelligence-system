#!/usr/bin/env python3
"""
Mac.bid Network Traffic Analyzer
Captures and analyzes actual network requests made by Mac.bid's frontend
"""

import requests
import json
import time
from datetime import datetime
import re
import os
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs

class NetworkTrafficAnalyzer:
    def __init__(self):
        self.base_url = "https://www.mac.bid"
        
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
        
        self.captured_requests = []
        
    def analyze_auction_page_requests(self, lot_id: int = 35863830) -> List[Dict]:
        """Analyze network requests made when loading an auction page"""
        
        print(f"🔍 ANALYZING AUCTION PAGE REQUESTS")
        print(f"   Lot ID: {lot_id}")
        print("="*50)
        
        # Load the auction page and capture requests
        auction_url = f"{self.base_url}/lot/{lot_id}"
        
        try:
            response = requests.get(
                auction_url,
                headers=self.session_headers,
                cookies=self.session_cookies,
                timeout=15
            )
            
            if response.status_code == 200:
                print(f"✅ Auction page loaded successfully")
                
                # Extract API calls from the page
                api_calls = self.extract_api_calls_from_html(response.text)
                
                # Test discovered API endpoints
                tested_endpoints = []
                for api_call in api_calls:
                    result = self.test_api_endpoint(api_call)
                    if result:
                        tested_endpoints.append(result)
                
                return tested_endpoints
                
        except Exception as e:
            print(f"❌ Error loading auction page: {e}")
            
        return []
    
    def extract_api_calls_from_html(self, html_content: str) -> List[str]:
        """Extract API endpoint patterns from HTML content"""
        
        print("🔍 Extracting API calls from HTML...")
        
        # Look for Next.js API patterns
        patterns = [
            r'/_next/static/chunks/pages/[^"\']*\.js',
            r'/api/[^"\']*',
            r'fetch\(["\']([^"\']*)["\']',
            r'axios\.[a-z]+\(["\']([^"\']*)["\']',
            r'"url":\s*["\']([^"\']*)["\']',
            r'"endpoint":\s*["\']([^"\']*)["\']',
            r'buildId["\']:\s*["\']([^"\']*)["\']'
        ]
        
        api_calls = []
        
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            api_calls.extend(matches)
        
        # Filter for relevant endpoints
        relevant_calls = []
        for call in api_calls:
            if any(keyword in call.lower() for keyword in ['bid', 'auction', 'lot', 'api']):
                relevant_calls.append(call)
        
        print(f"   Found {len(relevant_calls)} relevant API calls")
        return list(set(relevant_calls))  # Remove duplicates
    
    def test_api_endpoint(self, endpoint: str) -> Optional[Dict]:
        """Test an API endpoint with various HTTP methods"""
        
        if not endpoint.startswith('http'):
            if endpoint.startswith('/'):
                full_url = self.base_url + endpoint
            else:
                full_url = f"{self.base_url}/{endpoint}"
        else:
            full_url = endpoint
        
        print(f"🧪 Testing: {endpoint}")
        
        methods_to_test = ['GET', 'POST', 'PUT', 'PATCH']
        results = {}
        
        for method in methods_to_test:
            try:
                if method == 'GET':
                    response = requests.get(
                        full_url,
                        headers=self.session_headers,
                        cookies=self.session_cookies,
                        timeout=10
                    )
                elif method == 'POST':
                    # Test with potential bid data
                    test_data = {
                        'lot_id': 35863830,
                        'bid_amount': 1.00,
                        'customer_id': 2710619
                    }
                    response = requests.post(
                        full_url,
                        headers=self.session_headers,
                        cookies=self.session_cookies,
                        json=test_data,
                        timeout=10
                    )
                elif method == 'PUT':
                    response = requests.put(
                        full_url,
                        headers=self.session_headers,
                        cookies=self.session_cookies,
                        json={'test': True},
                        timeout=10
                    )
                elif method == 'PATCH':
                    response = requests.patch(
                        full_url,
                        headers=self.session_headers,
                        cookies=self.session_cookies,
                        json={'test': True},
                        timeout=10
                    )
                
                results[method] = {
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'content_type': response.headers.get('content-type', ''),
                    'response_size': len(response.content),
                    'response_preview': response.text[:200] if response.text else ''
                }
                
                if response.status_code in [200, 201, 202]:
                    print(f"   ✅ {method}: {response.status_code}")
                elif response.status_code in [400, 401, 403, 422]:
                    print(f"   ⚠️  {method}: {response.status_code} (Auth/Validation)")
                elif response.status_code == 404:
                    print(f"   ❌ {method}: 404")
                else:
                    print(f"   ❓ {method}: {response.status_code}")
                
            except Exception as e:
                results[method] = {'error': str(e)}
                print(f"   ❌ {method}: {str(e)}")
        
        return {
            'endpoint': endpoint,
            'full_url': full_url,
            'methods_tested': results,
            'tested_at': datetime.now().isoformat()
        }
    
    def discover_nextjs_api_routes(self) -> List[Dict]:
        """Discover Next.js API routes by analyzing the build manifest"""
        
        print("\n🔍 DISCOVERING NEXT.JS API ROUTES")
        print("="*40)
        
        # Try to get Next.js build manifest
        manifest_urls = [
            "/_next/static/chunks/pages/_app.js",
            "/_next/static/chunks/webpack.js",
            "/_next/static/chunks/main.js",
            "/_next/static/chunks/framework.js"
        ]
        
        discovered_routes = []
        
        for manifest_url in manifest_urls:
            try:
                response = requests.get(
                    self.base_url + manifest_url,
                    headers=self.session_headers,
                    cookies=self.session_cookies,
                    timeout=10
                )
                
                if response.status_code == 200:
                    print(f"✅ Loaded: {manifest_url}")
                    
                    # Extract API routes from JavaScript
                    routes = self.extract_routes_from_js(response.text)
                    discovered_routes.extend(routes)
                    
            except Exception as e:
                print(f"❌ Error loading {manifest_url}: {e}")
        
        return list(set(discovered_routes))  # Remove duplicates
    
    def extract_routes_from_js(self, js_content: str) -> List[str]:
        """Extract API routes from JavaScript content"""
        
        # Look for API route patterns in Next.js
        patterns = [
            r'["\']\/api\/[^"\']*["\']',
            r'router\.push\(["\']([^"\']*)["\']',
            r'fetch\(["\']([^"\']*)["\']',
            r'["\']([^"\']*\/api\/[^"\']*)["\']'
        ]
        
        routes = []
        for pattern in patterns:
            matches = re.findall(pattern, js_content)
            for match in matches:
                if '/api/' in match and ('bid' in match.lower() or 'auction' in match.lower() or 'lot' in match.lower()):
                    routes.append(match.strip('"\''))
        
        return routes
    
    def test_common_bidding_patterns(self) -> List[Dict]:
        """Test common bidding API patterns used by auction sites"""
        
        print("\n🎯 TESTING COMMON BIDDING PATTERNS")
        print("="*40)
        
        # Common patterns used by auction sites
        bidding_patterns = [
            # REST API patterns
            "/api/auctions/{auction_id}/bids",
            "/api/lots/{lot_id}/bids",
            "/api/bids",
            "/api/bid/place",
            "/api/bidding/submit",
            
            # Next.js API routes
            "/api/bid",
            "/api/place-bid",
            "/api/auction/bid",
            "/api/lot/bid",
            
            # GraphQL
            "/graphql",
            "/api/graphql",
            
            # WebSocket endpoints (for real-time bidding)
            "/socket.io/",
            "/ws/bidding",
            "/api/ws/auction"
        ]
        
        results = []
        
        for pattern in bidding_patterns:
            # Replace placeholders with actual values
            test_url = pattern.replace('{auction_id}', '48796').replace('{lot_id}', '35863830')
            
            result = self.test_api_endpoint(test_url)
            if result:
                results.append(result)
        
        return results
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive network analysis report"""
        
        print("\n📊 GENERATING COMPREHENSIVE REPORT")
        print("="*45)
        
        # Run all analysis methods
        auction_requests = self.analyze_auction_page_requests()
        nextjs_routes = self.discover_nextjs_api_routes()
        bidding_patterns = self.test_common_bidding_patterns()
        
        report = {
            'analysis_timestamp': datetime.now().isoformat(),
            'auction_page_requests': auction_requests,
            'nextjs_api_routes': nextjs_routes,
            'bidding_pattern_tests': bidding_patterns,
            'summary': {
                'auction_requests_found': len(auction_requests),
                'nextjs_routes_found': len(nextjs_routes),
                'bidding_patterns_tested': len(bidding_patterns),
                'total_endpoints_analyzed': len(auction_requests) + len(nextjs_routes) + len(bidding_patterns)
            },
            'recommendations': self.generate_recommendations(auction_requests, nextjs_routes, bidding_patterns)
        }
        
        # Save report
        os.makedirs('data_outputs', exist_ok=True)
        with open('data_outputs/network_traffic_analysis.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 ANALYSIS SUMMARY:")
        print(f"   Auction Requests: {len(auction_requests)}")
        print(f"   Next.js Routes: {len(nextjs_routes)}")
        print(f"   Bidding Patterns: {len(bidding_patterns)}")
        print(f"   Total Analyzed: {report['summary']['total_endpoints_analyzed']}")
        
        return report
    
    def generate_recommendations(self, auction_requests: List, nextjs_routes: List, bidding_patterns: List) -> List[str]:
        """Generate recommendations based on analysis results"""
        
        recommendations = []
        
        # Analyze successful endpoints
        successful_endpoints = []
        
        for request_group in [auction_requests, bidding_patterns]:
            for request in request_group:
                if 'methods_tested' in request:
                    for method, result in request['methods_tested'].items():
                        if isinstance(result, dict) and result.get('status_code') in [200, 201, 202]:
                            successful_endpoints.append({
                                'endpoint': request['endpoint'],
                                'method': method,
                                'status': result['status_code']
                            })
        
        if successful_endpoints:
            recommendations.append(f"Found {len(successful_endpoints)} potentially working endpoints")
            recommendations.append("Priority endpoints for bidding implementation:")
            for endpoint in successful_endpoints[:3]:  # Top 3
                recommendations.append(f"  - {endpoint['method']} {endpoint['endpoint']} (Status: {endpoint['status']})")
        else:
            recommendations.append("No obvious REST API endpoints found")
            recommendations.append("Consider browser automation approach (Selenium/Playwright)")
            recommendations.append("May need to reverse-engineer WebSocket connections")
        
        if nextjs_routes:
            recommendations.append(f"Found {len(nextjs_routes)} Next.js routes to investigate")
        
        return recommendations

def main():
    """Main analysis function"""
    
    print("🎯 MAC.BID NETWORK TRAFFIC ANALYSIS")
    print("="*50)
    print("Analyzing Mac.bid's network traffic patterns for bidding...")
    
    analyzer = NetworkTrafficAnalyzer()
    report = analyzer.generate_comprehensive_report()
    
    print(f"\n✅ Analysis complete! Report saved to: data_outputs/network_traffic_analysis.json")
    
    if report['recommendations']:
        print(f"\n🎯 RECOMMENDATIONS:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"{i}. {rec}")

if __name__ == "__main__":
    main() 