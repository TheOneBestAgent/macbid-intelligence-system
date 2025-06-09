#!/usr/bin/env python3
"""
Mac.bid Authentication Discovery System
Extracts proper authentication patterns from network traffic analysis
"""

import json
import re
import os
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse
import requests
from datetime import datetime

class MacBidAuthenticationDiscovery:
    def __init__(self):
        self.base_url = "https://www.mac.bid"
        self.customer_id = "2710619"
        self.auth_patterns = {}
        self.session_data = {}
        self.headers = {}
        self.cookies = {}
        
    def analyze_macbid_breakdown(self) -> Dict:
        """Analyze the macbid_breakdown file for authentication patterns"""
        print("🔍 ANALYZING MAC.BID AUTHENTICATION PATTERNS")
        print("=" * 60)
        
        breakdown_path = "../../macbid_breakdown/macbid_breakdown"
        if not os.path.exists(breakdown_path):
            print("❌ macbid_breakdown file not found")
            return {}
            
        try:
            with open(breakdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract authentication patterns
            auth_data = self._extract_auth_patterns(content)
            
            print("\n📊 AUTHENTICATION ANALYSIS RESULTS:")
            print("-" * 40)
            
            for category, data in auth_data.items():
                print(f"\n{category.upper()}:")
                if isinstance(data, dict):
                    for key, value in data.items():
                        print(f"   ✅ {key}: {value}")
                elif isinstance(data, list):
                    for item in data[:5]:  # Show first 5 items
                        print(f"   ✅ {item}")
                    if len(data) > 5:
                        print(f"   ... and {len(data) - 5} more")
                else:
                    print(f"   ✅ {data}")
                    
            return auth_data
            
        except Exception as e:
            print(f"❌ Error analyzing breakdown: {e}")
            return {}
    
    def _extract_auth_patterns(self, content: str) -> Dict:
        """Extract authentication patterns from content"""
        patterns = {
            'firebase_sessions': [],
            'nextjs_headers': [],
            'api_endpoints': [],
            'session_ids': [],
            'authentication_tokens': [],
            'cookies': [],
            'user_agents': [],
            'referers': []
        }
        
        # Extract Firebase session IDs
        firebase_pattern = r'gsessionid=([A-Za-z0-9_-]+)'
        patterns['firebase_sessions'] = list(set(re.findall(firebase_pattern, content)))
        
        # Extract NextJS data headers
        nextjs_pattern = r'"x-nextjs-data":\s*"([^"]*)"'
        patterns['nextjs_headers'] = list(set(re.findall(nextjs_pattern, content)))
        
        # Extract API endpoints
        api_pattern = r'https://[^"\s]+\.mac\.bid[^"\s]*'
        patterns['api_endpoints'] = list(set(re.findall(api_pattern, content)))
        
        # Extract session IDs (SID parameter)
        sid_pattern = r'SID=([A-Za-z0-9_-]+)'
        patterns['session_ids'] = list(set(re.findall(sid_pattern, content)))
        
        # Extract authentication tokens
        token_pattern = r'"token":\s*"([^"]+)"'
        patterns['authentication_tokens'] = list(set(re.findall(token_pattern, content)))
        
        # Extract User-Agent patterns
        ua_pattern = r'"user-agent":\s*"([^"]+)"'
        patterns['user_agents'] = list(set(re.findall(ua_pattern, content)))
        
        # Extract Referer patterns
        ref_pattern = r'"referer":\s*"([^"]+)"'
        patterns['referers'] = list(set(re.findall(ref_pattern, content)))
        
        return patterns
    
    def build_authenticated_session(self) -> Dict:
        """Build authenticated session configuration"""
        print("\n🔧 BUILDING AUTHENTICATED SESSION")
        print("=" * 40)
        
        # Analyze breakdown for patterns
        auth_data = self.analyze_macbid_breakdown()
        
        if not auth_data:
            print("❌ No authentication data found")
            return {}
        
        # Build session configuration
        session_config = {
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            },
            'cookies': {},
            'firebase_session': None,
            'session_id': None,
            'customer_id': self.customer_id
        }
        
        # Add NextJS data header if found
        if auth_data.get('nextjs_headers'):
            session_config['headers']['x-nextjs-data'] = auth_data['nextjs_headers'][0]
        
        # Add Firebase session if found
        if auth_data.get('firebase_sessions'):
            session_config['firebase_session'] = auth_data['firebase_sessions'][0]
            
        # Add session ID if found
        if auth_data.get('session_ids'):
            session_config['session_id'] = auth_data['session_ids'][0]
        
        print("✅ Session configuration built successfully")
        return session_config
    
    def test_authentication(self, session_config: Dict) -> bool:
        """Test authentication with discovered patterns"""
        print("\n🧪 TESTING AUTHENTICATION")
        print("=" * 30)
        
        try:
            session = requests.Session()
            session.headers.update(session_config['headers'])
            
            # Test basic page access
            response = session.get(f"{self.base_url}/locations/sc")
            print(f"   📄 Page Access: {response.status_code}")
            
            # Test API access with NextJS data
            if 'x-nextjs-data' in session_config['headers']:
                api_response = session.get(
                    f"{self.base_url}/_next/data/build-id/locations/sc.json",
                    headers={'x-nextjs-data': '1'}
                )
                print(f"   🔌 API Access: {api_response.status_code}")
            
            # Test Typesense search
            typesense_url = "https://search.mac.bid/collections/lots/documents/search"
            typesense_params = {
                'q': '*',
                'query_by': 'product_name,description,keywords',
                'filter_by': 'location_id:=sc',
                'per_page': 10,
                'page': 1
            }
            
            typesense_response = session.get(typesense_url, params=typesense_params)
            print(f"   🔍 Typesense Search: {typesense_response.status_code}")
            
            if typesense_response.status_code == 200:
                data = typesense_response.json()
                print(f"   📊 Found {data.get('found', 0)} lots")
                
            return True
            
        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            return False
    
    def generate_auth_config_file(self, session_config: Dict) -> str:
        """Generate authentication configuration file"""
        config_content = f'''# Mac.bid Authentication Configuration
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

MACBID_CUSTOMER_ID = "{self.customer_id}"
MACBID_BASE_URL = "{self.base_url}"

# Headers for authenticated requests
MACBID_HEADERS = {{
'''
        
        if session_config and 'headers' in session_config:
            for key, value in session_config['headers'].items():
                config_content += f'    "{key}": "{value}",\n'
            
        config_content += '}\n\n'
        
        if session_config.get('firebase_session'):
            config_content += f'FIREBASE_SESSION_ID = "{session_config["firebase_session"]}"\n'
            
        if session_config.get('session_id'):
            config_content += f'SESSION_ID = "{session_config["session_id"]}"\n'
            
        config_content += '''
# Usage Example:
# import requests
# session = requests.Session()
# session.headers.update(MACBID_HEADERS)
# response = session.get(f"{MACBID_BASE_URL}/locations/sc")
'''
        
        config_file = "macbid_auth_config.py"
        with open(config_file, 'w') as f:
            f.write(config_content)
            
        print(f"✅ Authentication config saved to: {config_file}")
        return config_file
    
    def run_complete_discovery(self) -> Dict:
        """Run complete authentication discovery process"""
        print("🚀 MAC.BID AUTHENTICATION DISCOVERY")
        print("=" * 50)
        
        # Step 1: Analyze breakdown file
        auth_data = self.analyze_macbid_breakdown()
        
        # Step 2: Build session configuration
        session_config = self.build_authenticated_session()
        
        # Step 3: Test authentication
        auth_working = self.test_authentication(session_config)
        
        # Step 4: Generate config file
        config_file = self.generate_auth_config_file(session_config)
        
        # Summary
        print(f"\n📋 DISCOVERY SUMMARY")
        print("=" * 25)
        print(f"   🔍 Patterns Found: {len(auth_data)} categories")
        print(f"   🔧 Session Built: {'✅' if session_config else '❌'}")
        print(f"   🧪 Auth Working: {'✅' if auth_working else '❌'}")
        print(f"   📄 Config File: {config_file}")
        
        return {
            'auth_data': auth_data,
            'session_config': session_config,
            'auth_working': auth_working,
            'config_file': config_file
        }

def main():
    """Main execution function"""
    discovery = MacBidAuthenticationDiscovery()
    results = discovery.run_complete_discovery()
    
    if results['auth_working']:
        print("\n🎉 SUCCESS: Authentication patterns discovered and working!")
        print("   Use the generated config file in your applications.")
    else:
        print("\n⚠️  WARNING: Authentication patterns found but may need refinement.")
        print("   Check the generated config file and test manually.")

if __name__ == "__main__":
    main()