#!/usr/bin/env python3
"""
🔥 FIREBASE API FINAL FIX
Specialized fix for Firebase real-time API 400 errors
"""

import requests
import json
import time
import urllib.parse
from datetime import datetime

class FirebaseFinalFix:
    def __init__(self):
        self.session = requests.Session()
        
        # Load auth
        try:
            import sys
            sys.path.append('organized_system/core_systems')
            from macbid_auth_config import FIREBASE_SESSION_ID, SESSION_ID
            
            self.firebase_session = FIREBASE_SESSION_ID
            self.session_id = SESSION_ID
            print("✅ Loaded Firebase credentials")
        except ImportError:
            self.firebase_session = "hgpyx2kZyefNRKokgOt42EbyB-KeoJs0X_5OgkavHwc"
            self.session_id = "lmTKFrLnGL0yxLa5jxrfRw"
            print("⚠️  Using fallback Firebase credentials")
        
        print(f"🔥 FIREBASE FINAL FIX")
        print(f"   Session: {self.firebase_session[:20]}...")
        print(f"   SID: {self.session_id[:20]}...")
    
    def try_fresh_credentials(self):
        """Try to extract fresh Firebase credentials from macbid_breakdown"""
        print("\n🔍 EXTRACTING FRESH FIREBASE CREDENTIALS")
        print("-" * 40)
        
        try:
            breakdown_file = "macbid_breakdown/macbid_breakdown"
            with open(breakdown_file, 'r') as f:
                content = f.read()
            
            # Find Firebase requests
            firebase_lines = [line for line in content.split('\n') 
                            if 'firestore.googleapis.com' in line and 'gsessionid=' in line]
            
            if firebase_lines:
                latest_line = firebase_lines[-1]
                
                # Extract credentials
                import re
                gsessionid_match = re.search(r'gsessionid=([^&\s]+)', latest_line)
                sid_match = re.search(r'SID=([^&\s]+)', latest_line)
                
                if gsessionid_match and sid_match:
                    fresh_gsessionid = gsessionid_match.group(1)
                    fresh_sid = sid_match.group(1)
                    
                    print(f"   ✅ Found fresh credentials:")
                    print(f"      gsessionid: {fresh_gsessionid[:20]}...")
                    print(f"      SID: {fresh_sid[:20]}...")
                    
                    return fresh_gsessionid, fresh_sid
            
            print("   ⚠️ No fresh credentials found in breakdown")
            return None, None
            
        except Exception as e:
            print(f"   ❌ Error extracting fresh credentials: {e}")
            return None, None
    
    def try_websocket_approach(self):
        """Try WebSocket approach for Firebase real-time"""
        print("\n🌐 WEBSOCKET APPROACH")
        print("-" * 20)
        
        try:
            import websocket
            print("   ✅ WebSocket library available")
            
            # Firebase WebSocket URL
            ws_url = f"wss://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
            
            # This would require a full WebSocket implementation
            print("   ℹ️  WebSocket approach would require full implementation")
            print("   ℹ️  Recommended for future development")
            return False
            
        except ImportError:
            print("   ⚠️ WebSocket library not available")
            return False
    
    def try_alternative_firebase_endpoints(self):
        """Try alternative Firebase endpoints"""
        print("\n🔄 ALTERNATIVE FIREBASE ENDPOINTS")
        print("-" * 35)
        
        # Alternative Firebase endpoints
        alternatives = [
            {
                'name': 'REST API',
                'url': 'https://firestore.googleapis.com/v1/projects/recommerce-a0291/databases/(default)/documents/auction-lots',
                'method': 'GET'
            },
            {
                'name': 'Firebase Database',
                'url': 'https://recommerce-a0291-default-rtdb.firebaseio.com/auction-lots.json',
                'method': 'GET'
            },
            {
                'name': 'Firebase Functions',
                'url': 'https://us-central1-recommerce-a0291.cloudfunctions.net/api/auction-lots',
                'method': 'GET'
            }
        ]
        
        for alt in alternatives:
            try:
                print(f"   Testing {alt['name']}: {alt['url']}")
                
                headers = {
                    'accept': 'application/json',
                    'origin': 'https://www.mac.bid',
                    'referer': 'https://www.mac.bid/'
                }
                
                if alt['method'] == 'GET':
                    response = self.session.get(alt['url'], headers=headers, timeout=10)
                else:
                    response = self.session.post(alt['url'], headers=headers, timeout=10)
                
                print(f"      Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"      ✅ {alt['name']} working!")
                    return True, alt
                elif response.status_code == 401:
                    print(f"      🔐 {alt['name']} needs authentication")
                else:
                    print(f"      ❌ {alt['name']}: {response.status_code}")
                    
            except Exception as e:
                print(f"      ❌ {alt['name']}: {e}")
        
        return False, None
    
    def try_simplified_firebase(self):
        """Try simplified Firebase connection"""
        print("\n🎯 SIMPLIFIED FIREBASE")
        print("-" * 22)
        
        firebase_url = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
        
        # Minimal parameters
        minimal_params = {
            'VER': '8',
            'database': 'projects/recommerce-a0291/databases/(default)',  # Not URL encoded
            'gsessionid': self.firebase_session,
            'SID': self.session_id
        }
        
        minimal_headers = {
            'accept': '*/*',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        try:
            print("   Testing minimal Firebase connection...")
            response = self.session.get(
                firebase_url,
                params=minimal_params,
                headers=minimal_headers,
                timeout=10
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Response size: {len(response.text)} bytes")
            
            if response.status_code in [200, 204]:
                print("   ✅ Simplified Firebase working!")
                return True
            else:
                print(f"   Response preview: {response.text[:200]}...")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def run_comprehensive_firebase_fix(self):
        """Run all Firebase fix attempts"""
        print("🚀 COMPREHENSIVE FIREBASE FIX")
        print("=" * 35)
        
        start_time = time.time()
        results = []
        
        # Method 1: Fresh credentials
        fresh_gsessionid, fresh_sid = self.try_fresh_credentials()
        if fresh_gsessionid and fresh_sid:
            self.firebase_session = fresh_gsessionid
            self.session_id = fresh_sid
            results.append("fresh_credentials_extracted")
        
        # Method 2: Simplified approach
        simplified_success = self.try_simplified_firebase()
        if simplified_success:
            results.append("simplified_firebase_success")
        
        # Method 3: Alternative endpoints
        alt_success, alt_endpoint = self.try_alternative_firebase_endpoints()
        if alt_success:
            results.append(f"alternative_success_{alt_endpoint['name']}")
        
        # Method 4: WebSocket approach (assessment)
        websocket_available = self.try_websocket_approach()
        if websocket_available:
            results.append("websocket_available")
        
        # Final assessment
        firebase_fixed = len([r for r in results if 'success' in r]) > 0
        processing_time = time.time() - start_time
        
        # Results
        final_results = {
            'timestamp': datetime.now().isoformat(),
            'processing_time': round(processing_time, 2),
            'firebase_fixed': firebase_fixed,
            'successful_methods': [r for r in results if 'success' in r],
            'all_attempts': results,
            'recommendations': []
        }
        
        print(f"\n📊 FIREBASE FIX RESULTS")
        print("=" * 25)
        print(f"Firebase Fixed: {'✅ YES' if firebase_fixed else '❌ NO'}")
        print(f"Successful Methods: {len([r for r in results if 'success' in r])}")
        print(f"Processing Time: {processing_time:.1f}s")
        
        if firebase_fixed:
            print("\n🎉 FIREBASE API FIXED!")
            final_results['recommendations'].append("Firebase real-time connection established")
        else:
            print("\n💡 FIREBASE RECOMMENDATIONS:")
            print("   1. 🌐 Implement WebSocket connection for real-time updates")
            print("   2. 🔄 Use polling with working Mac.bid API as alternative")
            print("   3. 🔐 Verify Firebase authentication tokens are current")
            
            final_results['recommendations'].extend([
                "Implement WebSocket connection for real-time updates",
                "Use polling with working Mac.bid API as alternative",
                "Verify Firebase authentication tokens are current"
            ])
        
        # Save results
        with open(f"firebase_fix_results_{int(time.time())}.json", 'w') as f:
            json.dump(final_results, f, indent=2)
        
        print(f"\n💾 Firebase results saved")
        
        return final_results

if __name__ == "__main__":
    fixer = FirebaseFinalFix()
    results = fixer.run_comprehensive_firebase_fix() 