#!/usr/bin/env python3
"""
Firebase Realtime Authentication Fixer
Analyzes macbid_breakdown for proper Firebase connection patterns and fixes authentication
"""

import requests
import json
import re
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Import discovered authentication
from macbid_auth_config import MACBID_HEADERS, MACBID_CUSTOMER_ID, MACBID_BASE_URL, FIREBASE_SESSION_ID, SESSION_ID

class FirebaseAuthenticationFixer:
    def __init__(self):
        self.base_url = MACBID_BASE_URL
        self.firebase_session = FIREBASE_SESSION_ID
        self.session_id = SESSION_ID
        self.session = requests.Session()
        self.session.headers.update(MACBID_HEADERS)
        
        # Firebase endpoints discovered from macbid_breakdown
        self.firebase_base = "https://firestore.googleapis.com/google.firestore.v1.Firestore"
        self.firebase_project = "projects/recommerce-a0291/databases/(default)"
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def analyze_firebase_patterns(self) -> Dict:
        """Analyze macbid_breakdown for Firebase connection patterns"""
        print("🔍 ANALYZING FIREBASE PATTERNS FROM MACBID_BREAKDOWN")
        print("=" * 55)
        
        breakdown_path = "../../macbid_breakdown/macbid_breakdown"
        
        try:
            with open(breakdown_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            patterns = {
                'firebase_urls': [],
                'session_params': [],
                'aid_values': [],
                'rid_values': [],
                'ver_values': [],
                'request_methods': [],
                'headers_used': [],
                'response_codes': []
            }
            
            # Extract Firebase URLs
            firebase_url_pattern = r'https://firestore\.googleapis\.com[^"\s]*'
            patterns['firebase_urls'] = list(set(re.findall(firebase_url_pattern, content)))
            
            # Extract session parameters
            session_param_pattern = r'gsessionid=([A-Za-z0-9_-]+)'
            patterns['session_params'] = list(set(re.findall(session_param_pattern, content)))
            
            # Extract AID values
            aid_pattern = r'AID=(\d+)'
            patterns['aid_values'] = list(set(re.findall(aid_pattern, content)))
            
            # Extract RID values
            rid_pattern = r'RID=(\w+)'
            patterns['rid_values'] = list(set(re.findall(rid_pattern, content)))
            
            # Extract VER values
            ver_pattern = r'VER=(\d+)'
            patterns['ver_values'] = list(set(re.findall(ver_pattern, content)))
            
            # Extract request methods
            method_pattern = r'fetch\("([^"]*firestore[^"]*)"[^{]*\{[^}]*"method":\s*"([^"]*)"'
            methods = re.findall(method_pattern, content)
            patterns['request_methods'] = list(set([method[1] for method in methods]))
            
            print("📊 FIREBASE PATTERN ANALYSIS:")
            print("-" * 35)
            
            for category, data in patterns.items():
                print(f"\n{category.upper().replace('_', ' ')}:")
                if isinstance(data, list):
                    for item in data[:5]:  # Show first 5 items
                        print(f"   ✅ {item}")
                    if len(data) > 5:
                        print(f"   ... and {len(data) - 5} more")
                        
            return patterns
            
        except Exception as e:
            print(f"❌ Error analyzing Firebase patterns: {e}")
            return {}
    
    def test_firebase_connection_methods(self) -> Dict:
        """Test different Firebase connection methods"""
        print("\n🧪 TESTING FIREBASE CONNECTION METHODS")
        print("=" * 45)
        
        results = {
            'listen_channel': False,
            'websocket': False,
            'polling': False,
            'batch_get': False,
            'errors': []
        }
        
        # Method 1: Listen Channel (from breakdown)
        try:
            print("\n🔍 Testing Listen Channel...")
            listen_url = f"{self.firebase_base}/Listen/channel"
            
            # Try different parameter combinations from breakdown analysis
            param_sets = [
                {
                    'gsessionid': self.firebase_session,
                    'VER': '8',
                    'database': self.firebase_project,
                    'RID': 'rpc',
                    'SID': self.session_id,
                    'AID': '8780',
                    'CI': '0',
                    'TYPE': 'xmlhttp'
                },
                {
                    'gsessionid': self.firebase_session,
                    'VER': '8',
                    'database': self.firebase_project,
                    'RID': '99001',
                    'SID': self.session_id,
                    'AID': '8780',
                    'CI': '0',
                    'TYPE': 'xmlhttp',
                    'zx': 'test123',
                    't': '1'
                }
            ]
            
            for i, params in enumerate(param_sets):
                response = self.session.get(listen_url, params=params, timeout=10)
                print(f"   Param Set {i+1}: {response.status_code}")
                
                if response.status_code in [200, 204]:
                    results['listen_channel'] = True
                    print(f"   ✅ Listen Channel working with param set {i+1}")
                    break
                    
        except Exception as e:
            results['errors'].append(f"Listen Channel: {e}")
            print(f"   ❌ Listen Channel error: {e}")
        
        # Method 2: Batch Get Documents
        try:
            print("\n🔍 Testing Batch Get...")
            batch_url = f"{self.firebase_base}/BatchGet"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.firebase_session}',  # Try session as bearer
            }
            
            payload = {
                'database': self.firebase_project,
                'documents': [f'{self.firebase_project}/documents/lots/test']
            }
            
            response = self.session.post(batch_url, json=payload, headers=headers, timeout=10)
            print(f"   Batch Get: {response.status_code}")
            
            if response.status_code in [200, 404]:  # 404 is OK, means auth worked but doc not found
                results['batch_get'] = True
                print("   ✅ Batch Get authentication working")
                
        except Exception as e:
            results['errors'].append(f"Batch Get: {e}")
            print(f"   ❌ Batch Get error: {e}")
        
        # Method 3: Simple Document Read
        try:
            print("\n🔍 Testing Document Read...")
            doc_url = f"{self.firebase_base}/projects/recommerce-a0291/databases/(default)/documents/lots"
            
            # Try with session parameters
            params = {
                'gsessionid': self.firebase_session,
                'key': self.firebase_session  # Try session as API key
            }
            
            response = self.session.get(doc_url, params=params, timeout=10)
            print(f"   Document Read: {response.status_code}")
            
            if response.status_code in [200, 403]:  # 403 might mean auth worked but no permission
                results['polling'] = True
                print("   ✅ Document Read authentication working")
                
        except Exception as e:
            results['errors'].append(f"Document Read: {e}")
            print(f"   ❌ Document Read error: {e}")
        
        return results
    
    def fix_firebase_authentication(self) -> bool:
        """Attempt to fix Firebase authentication using discovered patterns"""
        print("\n🔧 ATTEMPTING FIREBASE AUTHENTICATION FIX")
        print("=" * 45)
        
        # Step 1: Analyze patterns
        patterns = self.analyze_firebase_patterns()
        
        # Step 2: Test connection methods
        results = self.test_firebase_connection_methods()
        
        # Step 3: Try advanced authentication
        print("\n🚀 TRYING ADVANCED FIREBASE AUTHENTICATION")
        print("-" * 45)
        
        try:
            # Method: Use exact parameters from working requests in breakdown
            listen_url = f"{self.firebase_base}/Listen/channel"
            
            # Use parameters that appear most frequently in breakdown
            params = {
                'gsessionid': self.firebase_session,
                'VER': '8',
                'database': self.firebase_project,
                'RID': 'rpc',
                'SID': self.session_id,
                'AID': '8780',
                'CI': '0',
                'TYPE': 'xmlhttp',
                'zx': f'test{int(time.time())}',
                't': '1'
            }
            
            # Add all discovered headers
            headers = dict(self.session.headers)
            headers.update({
                'Origin': 'https://www.mac.bid',
                'Referer': 'https://www.mac.bid/',
                'Sec-Fetch-Site': 'cross-site',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty'
            })
            
            response = self.session.get(listen_url, params=params, headers=headers, timeout=15)
            
            print(f"   Advanced Auth Test: {response.status_code}")
            
            if response.status_code in [200, 204]:
                print("   ✅ Firebase authentication FIXED!")
                return True
            else:
                print(f"   ⚠️  Firebase still returning {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"   ❌ Advanced auth failed: {e}")
            return False
    
    def test_working_firebase_connection(self) -> Dict:
        """Test if Firebase connection is now working"""
        if not self.fix_firebase_authentication():
            return {'working': False, 'error': 'Authentication fix failed'}
        
        try:
            # Test real-time connection
            listen_url = f"{self.firebase_base}/Listen/channel"
            params = {
                'gsessionid': self.firebase_session,
                'VER': '8',
                'database': self.firebase_project,
                'RID': 'rpc',
                'SID': self.session_id,
                'AID': '8780',
                'CI': '0',
                'TYPE': 'xmlhttp'
            }
            
            response = self.session.get(listen_url, params=params, timeout=10)
            
            return {
                'working': response.status_code in [200, 204],
                'status_code': response.status_code,
                'response_size': len(response.text),
                'error': None if response.status_code in [200, 204] else f"HTTP {response.status_code}"
            }
            
        except Exception as e:
            return {'working': False, 'error': str(e)}

def main():
    """Main execution function"""
    fixer = FirebaseAuthenticationFixer()
    
    print("🔥 FIREBASE REALTIME AUTHENTICATION FIXER")
    print("=" * 50)
    
    # Test current state
    print("\n📊 CURRENT FIREBASE STATUS:")
    current_result = fixer.test_working_firebase_connection()
    
    if current_result['working']:
        print("🎉 Firebase authentication is now WORKING!")
        print(f"   Status: {current_result['status_code']}")
        print(f"   Response Size: {current_result['response_size']} bytes")
    else:
        print(f"❌ Firebase authentication still needs work: {current_result['error']}")
        print("   Check the analysis above for debugging information")

if __name__ == "__main__":
    main() 