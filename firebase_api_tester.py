#!/usr/bin/env python3
"""
Firebase API Tester
===================
Test Firebase API using the exact format from successful captured requests
"""

import json
import time
import random
import string
import aiohttp
import asyncio
from pathlib import Path
from datetime import datetime

class FirebaseAPITester:
    def __init__(self):
        self.session_file = "firebase_playwright_session_1749444354.json"
        self.session_data = self._load_session_data()
        
    def _load_session_data(self):
        """Load session data from captured file"""
        if Path(self.session_file).exists():
            with open(self.session_file, 'r') as f:
                data = json.load(f)
                return data.get('session_data', {})
        return {}
    
    def _generate_zx(self):
        """Generate zx parameter like in successful requests"""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    
    def _generate_aid(self):
        """Generate AID parameter"""
        return str(random.randint(8590, 8650))
    
    def _generate_rid(self):
        """Generate RID parameter"""
        return str(random.randint(87000, 91000))
    
    async def test_firebase_post_request(self):
        """Test Firebase POST request using captured format"""
        print("🔥 Testing Firebase POST request...")
        
        # Use session data from captured requests
        gsessionid = self.session_data.get('gsessionid', '')
        database = self.session_data.get('database', 'projects%2Frecommerce-a0291%2Fdatabases%2F(default)')
        ver = self.session_data.get('ver', '8')
        
        if not gsessionid:
            print("❌ No gsessionid found in session data")
            return False
        
        # Build URL like successful requests
        url = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
        
        params = {
            'VER': ver,
            'database': database,
            'RID': self._generate_rid(),
            'CVER': '22',
            'X-HTTP-Session-Id': 'gsessionid',
            'zx': self._generate_zx(),
            't': '1'
        }
        
        headers = {
            'sec-ch-ua-platform': '"macOS"',
            'referer': 'https://www.mac.bid/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="136", "HeadlessChrome";v="136", "Not.A/Brand";v="99"',
            'content-type': 'application/x-www-form-urlencoded',
            'sec-ch-ua-mobile': '?0'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params, headers=headers, timeout=10) as response:
                    status = response.status
                    text = await response.text()
                    
                    print(f"📊 POST Request Status: {status}")
                    if status == 200:
                        print("✅ Firebase POST request successful!")
                        print(f"📄 Response: {text[:200]}...")
                        return True
                    else:
                        print(f"❌ Firebase POST failed: {text[:200]}...")
                        return False
                        
        except Exception as e:
            print(f"❌ Firebase POST error: {e}")
            return False
    
    async def test_firebase_get_request(self):
        """Test Firebase GET request using captured format"""
        print("🔥 Testing Firebase GET request...")
        
        # Use session data
        gsessionid = self.session_data.get('gsessionid', '')
        database = self.session_data.get('database', 'projects%2Frecommerce-a0291%2Fdatabases%2F(default)')
        ver = self.session_data.get('ver', '8')
        sid = self.session_data.get('sid', '')
        
        if not gsessionid or not sid:
            print("❌ Missing required session parameters")
            return False
        
        # Build URL like successful GET requests
        url = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
        
        params = {
            'gsessionid': gsessionid,
            'VER': ver,
            'database': database,
            'RID': 'rpc',
            'SID': sid,
            'AID': self._generate_aid(),
            'CI': '0',
            'TYPE': 'xmlhttp',
            'zx': self._generate_zx(),
            't': '1'
        }
        
        headers = {
            'sec-ch-ua-platform': '"macOS"',
            'referer': 'https://www.mac.bid/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="136", "HeadlessChrome";v="136", "Not.A/Brand";v="99"',
            'sec-ch-ua-mobile': '?0'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers, timeout=10) as response:
                    status = response.status
                    text = await response.text()
                    
                    print(f"📊 GET Request Status: {status}")
                    if status == 200:
                        print("✅ Firebase GET request successful!")
                        print(f"📄 Response: {text[:200]}...")
                        return True
                    else:
                        print(f"❌ Firebase GET failed: {text[:200]}...")
                        return False
                        
        except Exception as e:
            print(f"❌ Firebase GET error: {e}")
            return False
    
    async def test_with_different_sessions(self):
        """Test with different session IDs from captured data"""
        print("🔥 Testing with multiple session IDs from captured data...")
        
        # Load captured requests to get different session IDs
        if not Path(self.session_file).exists():
            print("❌ No session file found")
            return False
        
        with open(self.session_file, 'r') as f:
            data = json.load(f)
        
        captured_requests = data.get('captured_requests', [])
        successful_gsessions = []
        
        # Extract all successful gsessionid values
        for req in captured_requests:
            if req.get('response_status') == 200:
                params = req.get('query_params', {})
                gsessionid = params.get('gsessionid')
                if gsessionid and gsessionid not in successful_gsessions:
                    successful_gsessions.append(gsessionid)
        
        print(f"📊 Found {len(successful_gsessions)} successful session IDs")
        
        for i, gsessionid in enumerate(successful_gsessions[:3]):  # Test first 3
            print(f"\n🧪 Testing session {i+1}/{len(successful_gsessions)}: {gsessionid[:20]}...")
            
            # Test with this specific gsessionid
            url = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
            
            params = {
                'gsessionid': gsessionid,
                'VER': '8',
                'database': 'projects%2Frecommerce-a0291%2Fdatabases%2F(default)',
                'RID': 'rpc',
                'SID': self.session_data.get('sid', ''),
                'AID': '0',
                'CI': '0',
                'TYPE': 'xmlhttp',
                'zx': self._generate_zx(),
                't': '1'
            }
            
            headers = {
                'referer': 'https://www.mac.bid/',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, params=params, headers=headers, timeout=10) as response:
                        status = response.status
                        print(f"   📊 Status: {status}")
                        
                        if status == 200:
                            print(f"   ✅ SUCCESS with session {i+1}!")
                            text = await response.text()
                            print(f"   📄 Response: {text[:100]}...")
                            return True
                        else:
                            text = await response.text()
                            print(f"   ❌ Failed: {text[:100]}...")
                            
            except Exception as e:
                print(f"   ❌ Error: {e}")
        
        return False
    
    async def test_exact_replay(self):
        """Test by replaying exact successful requests"""
        print("🔥 Testing exact replay of successful requests...")
        
        if not Path(self.session_file).exists():
            print("❌ No session file found")
            return False
        
        with open(self.session_file, 'r') as f:
            data = json.load(f)
        
        captured_requests = data.get('captured_requests', [])
        
        # Find first successful request
        for i, req in enumerate(captured_requests):
            if req.get('response_status') == 200 and req.get('method') == 'GET':
                print(f"🎯 Replaying request #{i+1}: {req['method']} {req['url'][:80]}...")
                
                url = req['url']
                headers = {
                    'referer': req['headers'].get('referer', 'https://www.mac.bid/'),
                    'user-agent': req['headers'].get('user-agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
                }
                
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=headers, timeout=10) as response:
                            status = response.status
                            text = await response.text()
                            
                            print(f"📊 Exact Replay Status: {status}")
                            if status == 200:
                                print("✅ Exact replay successful!")
                                print(f"📄 Response: {text[:200]}...")
                                return True
                            else:
                                print(f"❌ Exact replay failed: {text[:200]}...")
                                
                except Exception as e:
                    print(f"❌ Exact replay error: {e}")
                
                # Try only first successful request
                break
        
        return False

async def main():
    """Run Firebase API tests"""
    print("🚀 FIREBASE API TESTER")
    print("=" * 60)
    
    tester = FirebaseAPITester()
    
    if not tester.session_data:
        print("❌ No session data loaded")
        return
    
    print(f"📊 Session Data Loaded:")
    print(f"   gsessionid: {tester.session_data.get('gsessionid', 'None')[:30]}...")
    print(f"   sid: {tester.session_data.get('sid', 'None')}")
    print(f"   database: {tester.session_data.get('database', 'None')}")
    
    tests = [
        ("Exact Replay", tester.test_exact_replay),
        ("Multiple Sessions", tester.test_with_different_sessions),
        ("POST Request", tester.test_firebase_post_request),
        ("GET Request", tester.test_firebase_get_request)
    ]
    
    success_count = 0
    for name, test_func in tests:
        print(f"\n🧪 {name} Test")
        print("-" * 40)
        
        try:
            success = await test_func()
            if success:
                success_count += 1
                print(f"✅ {name} test PASSED")
            else:
                print(f"❌ {name} test FAILED")
        except Exception as e:
            print(f"❌ {name} test ERROR: {e}")
        
        await asyncio.sleep(1)  # Brief pause between tests
    
    print(f"\n📊 FINAL RESULTS")
    print("=" * 40)
    print(f"✅ Successful tests: {success_count}/{len(tests)}")
    print(f"📈 Success rate: {success_count/len(tests)*100:.1f}%")
    
    if success_count > 0:
        print("🎉 Firebase API is working! Ready for integration.")
    else:
        print("❌ Firebase API needs further investigation.")

if __name__ == "__main__":
    asyncio.run(main()) 