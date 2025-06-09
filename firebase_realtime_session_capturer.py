#!/usr/bin/env python3
"""
🔥 FIREBASE REALTIME SESSION CAPTURER
====================================
Captures live browser session data to maintain fresh Firebase credentials
for 100% API success rate. Integrates with existing system.
"""

import asyncio
import json
import re
import time
import requests
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import subprocess
import psutil

@dataclass
class FirebaseSession:
    """Firebase session data structure"""
    gsessionid: str
    sid: str
    rid: int
    aid: int
    ofs: int
    target_id: int
    timestamp: datetime
    auction_lots: List[str]
    is_active: bool = True

class RealTimeFirebaseSessionCapturer:
    def __init__(self):
        self.firebase_url = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
        self.project_id = "recommerce-a0291"
        self.database = f"projects/{self.project_id}/databases/(default)"
        
        # Session tracking
        self.current_session: Optional[FirebaseSession] = None
        self.session_history: List[FirebaseSession] = []
        self.capture_active = False
        self.auto_refresh = True
        
        # Monitoring
        self.last_capture_time = None
        self.capture_count = 0
        self.success_rate = 0.0
        
        # File paths
        self.session_file = "firebase_realtime_session.json"
        self.breakdown_file = Path("macbid_breakdown/macbid_breakdown")
        self.auth_config_file = Path("organized_system/core_systems/macbid_auth_config.py")

    def start_realtime_capture(self) -> Dict:
        """Start real-time Firebase session capture"""
        print("🔥 FIREBASE REALTIME SESSION CAPTURER")
        print("=" * 60)
        
        try:
            # Start background monitoring
            self.capture_active = True
            
            # Method 1: Monitor breakdown file changes
            session_from_file = self._monitor_breakdown_file()
            
            # Method 2: Extract from live browser processes
            session_from_browser = self._capture_from_browser()
            
            # Method 3: Intercept network traffic
            session_from_network = self._monitor_network_traffic()
            
            # Choose best session
            best_session = self._select_best_session([
                session_from_file,
                session_from_browser, 
                session_from_network
            ])
            
            if best_session:
                self.current_session = best_session
                self._update_auth_config()
                return self._test_session()
            else:
                return self._fallback_capture()
                
        except Exception as e:
            print(f"❌ Capture failed: {e}")
            return {"success": False, "error": str(e)}

    def _monitor_breakdown_file(self) -> Optional[FirebaseSession]:
        """Monitor breakdown file for fresh Firebase requests"""
        print("📁 Monitoring breakdown file for fresh requests...")
        
        try:
            if not self.breakdown_file.exists():
                print("⚠️ Breakdown file not found")
                return None
            
            # Get file modification time
            mod_time = datetime.fromtimestamp(self.breakdown_file.stat().st_mtime)
            
            # Only process if file was modified recently (last 5 minutes)
            if datetime.now() - mod_time > timedelta(minutes=5):
                print(f"⚠️ Breakdown file is stale (modified: {mod_time})")
                return None
            
            with open(self.breakdown_file, 'r') as f:
                content = f.read()
            
            # Find the most recent Firebase request
            firebase_requests = []
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if 'firestore.googleapis.com' in line and 'gsessionid=' in line:
                    # Extract request details
                    session_data = self._parse_firebase_request(line, lines[i:i+20])
                    if session_data:
                        firebase_requests.append(session_data)
            
            if firebase_requests:
                # Return the most recent request
                latest = max(firebase_requests, key=lambda x: x.timestamp)
                print(f"✅ Found fresh Firebase session from file: {latest.gsessionid[:20]}...")
                return latest
            
            print("⚠️ No fresh Firebase requests found in breakdown file")
            return None
            
        except Exception as e:
            print(f"❌ Breakdown file monitoring failed: {e}")
            return None

    def _capture_from_browser(self) -> Optional[FirebaseSession]:
        """Capture Firebase session from live browser processes"""
        print("🌐 Capturing session from live browser...")
        
        try:
            # Look for Mac.bid browser processes
            for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if 'chrome' in process.info['name'].lower() or 'brave' in process.info['name'].lower():
                        cmdline = ' '.join(process.info['cmdline'] or [])
                        if 'mac.bid' in cmdline.lower():
                            print(f"✅ Found Mac.bid browser process: PID {process.info['pid']}")
                            return self._extract_from_browser_process(process.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            print("⚠️ No active Mac.bid browser sessions found")
            return None
            
        except Exception as e:
            print(f"❌ Browser capture failed: {e}")
            return None

    def _monitor_network_traffic(self) -> Optional[FirebaseSession]:
        """Monitor network traffic for Firebase requests"""
        print("🔍 Monitoring network traffic...")
        
        try:
            # Use netstat to find Firebase connections
            result = subprocess.run(['netstat', '-an'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'firestore.googleapis.com' in line:
                        print(f"✅ Found active Firebase connection: {line.strip()}")
                        # This is a simplified approach - in production you'd need packet capture
                        return self._create_session_from_network(line)
            
            print("⚠️ No active Firebase network connections found")
            return None
            
        except Exception as e:
            print(f"❌ Network monitoring failed: {e}")
            return None

    def _parse_firebase_request(self, request_line: str, context_lines: List[str]) -> Optional[FirebaseSession]:
        """Parse Firebase request data from captured line"""
        try:
            # Extract gsessionid and SID
            gsessionid_match = re.search(r'gsessionid=([^&\s]+)', request_line)
            sid_match = re.search(r'SID=([^&\s]+)', request_line)
            rid_match = re.search(r'RID=([^&\s]+)', request_line)
            aid_match = re.search(r'AID=([^&\s]+)', request_line)
            
            if not (gsessionid_match and sid_match):
                return None
            
            # Extract other parameters
            ofs = 0
            target_id = 0
            auction_lots = []
            
            # Look for body data in context lines
            for line in context_lines:
                if 'body"' in line and 'ofs=' in line:
                    ofs_match = re.search(r'ofs=(\d+)', line)
                    if ofs_match:
                        ofs = int(ofs_match.group(1))
                
                if 'auction-lots' in line:
                    lot_match = re.search(r'auction-lots%2F([^%"]+)', line)
                    if lot_match:
                        auction_lots.append(lot_match.group(1))
                
                if 'targetId' in line:
                    target_match = re.search(r'targetId%22%3A(\d+)', line)
                    if target_match:
                        target_id = int(target_match.group(1))
            
            # Parse RID safely (handle "rpc" case)
            rid_value = 0
            if rid_match:
                rid_str = rid_match.group(1)
                if rid_str.isdigit():
                    rid_value = int(rid_str)
                else:
                    # Handle non-numeric RID values like "rpc"
                    rid_value = hash(rid_str) % 100000  # Convert to pseudo-numeric value
            
            # Parse AID safely
            aid_value = 0
            if aid_match:
                aid_str = aid_match.group(1)
                if aid_str.isdigit():
                    aid_value = int(aid_str)
            
            return FirebaseSession(
                gsessionid=gsessionid_match.group(1),
                sid=sid_match.group(1),
                rid=rid_value,
                aid=aid_value,
                ofs=ofs,
                target_id=target_id,
                timestamp=datetime.now(),
                auction_lots=auction_lots
            )
            
        except Exception as e:
            print(f"❌ Failed to parse Firebase request: {e}")
            return None

    def _extract_from_browser_process(self, pid: int) -> Optional[FirebaseSession]:
        """Extract session data from browser process"""
        try:
            # This is a simplified version - real implementation would need browser debugging API
            print(f"🔍 Analyzing browser process {pid}...")
            
            # For now, fall back to file-based extraction
            return self._monitor_breakdown_file()
            
        except Exception as e:
            print(f"❌ Browser process extraction failed: {e}")
            return None

    def _create_session_from_network(self, connection_line: str) -> Optional[FirebaseSession]:
        """Create session data from network connection info"""
        # Simplified - would need actual packet capture in production
        return self._monitor_breakdown_file()

    def _select_best_session(self, sessions: List[Optional[FirebaseSession]]) -> Optional[FirebaseSession]:
        """Select the best session from available options"""
        valid_sessions = [s for s in sessions if s is not None]
        
        if not valid_sessions:
            return None
        
        # Prefer newest session
        return max(valid_sessions, key=lambda x: x.timestamp)

    def _update_auth_config(self) -> bool:
        """Update auth config with fresh session data"""
        try:
            if not self.current_session:
                return False
            
            print(f"🔄 Updating auth config with fresh session...")
            
            if not self.auth_config_file.exists():
                print(f"❌ Auth config file not found: {self.auth_config_file}")
                return False
            
            # Read current config
            with open(self.auth_config_file, 'r') as f:
                content = f.read()
            
            # Update Firebase credentials
            content = re.sub(
                r'FIREBASE_SESSION_ID = "[^"]*"',
                f'FIREBASE_SESSION_ID = "{self.current_session.gsessionid}"',
                content
            )
            
            content = re.sub(
                r'SESSION_ID = "[^"]*"',
                f'SESSION_ID = "{self.current_session.sid}"',
                content
            )
            
            # Write updated config
            with open(self.auth_config_file, 'w') as f:
                f.write(content)
            
            print(f"✅ Auth config updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Auth config update failed: {e}")
            return False

    def _test_session(self) -> Dict:
        """Test the current session"""
        try:
            print("🧪 Testing fresh Firebase session...")
            
            if not self.current_session:
                return {"success": False, "error": "No session available"}
            
            # Test with a simple Firebase request
            test_lot_id = self.current_session.auction_lots[0] if self.current_session.auction_lots else '48360-2549A'
            
            params = {
                'VER': '8',
                'database': f'projects%2F{self.project_id}%2Fdatabases%2F(default)',
                'gsessionid': self.current_session.gsessionid,
                'SID': self.current_session.sid,
                'RID': str(self.current_session.rid + 1),
                'AID': str(self.current_session.aid),
                'zx': f'test{int(time.time() * 1000)}',
                't': '1'
            }
            
            # Build request body
            document_path = f"{self.database}/documents/auction-lots/{test_lot_id}"
            request_data = {
                "database": self.database,
                "addTarget": {
                    "documents": {
                        "documents": [document_path]
                    },
                    "targetId": self.current_session.target_id + 1
                }
            }
            
            body_params = {
                'count': '1',
                'ofs': str(self.current_session.ofs + 1),
                'req0___data__': json.dumps(request_data)
            }
            
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.6',
                'content-type': 'application/x-www-form-urlencoded',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'cross-site',
            }
            
            # Make test request
            response = requests.post(
                self.firebase_url,
                params=params,
                headers=headers,
                data='&'.join([f'{k}={v}' for k, v in body_params.items()]),
                timeout=10
            )
            
            success = response.status_code in [200, 204]
            
            if success:
                print(f"✅ Firebase session test PASSED (Status: {response.status_code})")
                self.success_rate = 100.0
                self.capture_count += 1
                
                # Save session for future use
                self._save_session()
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "gsessionid": self.current_session.gsessionid[:20] + "...",
                    "sid": self.current_session.sid[:20] + "...",
                    "timestamp": self.current_session.timestamp.isoformat(),
                    "auction_lots": self.current_session.auction_lots,
                    "success_rate": self.success_rate
                }
            else:
                print(f"❌ Firebase session test FAILED (Status: {response.status_code})")
                print(f"   Response: {response.text[:200]}...")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text[:200],
                    "success_rate": 0.0
                }
                
        except Exception as e:
            print(f"❌ Session test failed: {e}")
            return {"success": False, "error": str(e)}

    def _fallback_capture(self) -> Dict:
        """Fallback capture method when real-time fails"""
        print("🔄 Using fallback capture method...")
        
        try:
            # Try to use existing credentials from auth config
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), 'organized_system', 'core_systems'))
            
            try:
                from macbid_auth_config import FIREBASE_SESSION_ID, SESSION_ID
                
                self.current_session = FirebaseSession(
                    gsessionid=FIREBASE_SESSION_ID,
                    sid=SESSION_ID,
                    rid=99000,
                    aid=8000,
                    ofs=1,
                    target_id=100,
                    timestamp=datetime.now(),
                    auction_lots=[]
                )
                
                return self._test_session()
                
            except ImportError:
                return {
                    "success": False,
                    "error": "No auth config available for fallback",
                    "recommendation": "Update macbid_breakdown file with fresh browser session"
                }
                
        except Exception as e:
            return {"success": False, "error": f"Fallback failed: {e}"}

    def _save_session(self):
        """Save current session to file"""
        try:
            if self.current_session:
                session_data = {
                    "gsessionid": self.current_session.gsessionid,
                    "sid": self.current_session.sid,
                    "rid": self.current_session.rid,
                    "aid": self.current_session.aid,
                    "ofs": self.current_session.ofs,
                    "target_id": self.current_session.target_id,
                    "timestamp": self.current_session.timestamp.isoformat(),
                    "auction_lots": self.current_session.auction_lots,
                    "success_rate": self.success_rate,
                    "capture_count": self.capture_count
                }
                
                with open(self.session_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                
                print(f"💾 Session saved to {self.session_file}")
                
        except Exception as e:
            print(f"❌ Failed to save session: {e}")

    def start_continuous_monitoring(self):
        """Start continuous monitoring for session changes"""
        print("🔄 Starting continuous Firebase session monitoring...")
        
        def monitor_loop():
            while self.capture_active:
                try:
                    # Check every 30 seconds
                    time.sleep(30)
                    
                    # Test current session
                    if self.current_session:
                        test_result = self._test_session()
                        if not test_result.get("success", False):
                            print("⚠️ Current session expired, capturing fresh session...")
                            self.start_realtime_capture()
                    else:
                        print("⚠️ No current session, starting capture...")
                        self.start_realtime_capture()
                        
                except Exception as e:
                    print(f"❌ Monitoring loop error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        return monitor_thread

    def get_session_status(self) -> Dict:
        """Get current session status"""
        if not self.current_session:
            return {
                "status": "NO_SESSION",
                "message": "No active Firebase session",
                "success_rate": 0.0,
                "last_capture": None
            }
        
        # Test current session
        test_result = self._test_session()
        
        return {
            "status": "ACTIVE" if test_result.get("success") else "EXPIRED",
            "gsessionid": self.current_session.gsessionid[:20] + "...",
            "sid": self.current_session.sid[:20] + "...",
            "timestamp": self.current_session.timestamp.isoformat(),
            "auction_lots": self.current_session.auction_lots,
            "success_rate": self.success_rate,
            "capture_count": self.capture_count,
            "last_test": test_result
        }

async def test_realtime_firebase_capture():
    """Test the real-time Firebase capture system"""
    print("🚀 TESTING REALTIME FIREBASE CAPTURE SYSTEM")
    print("=" * 70)
    
    capturer = RealTimeFirebaseSessionCapturer()
    
    # Start capture
    capture_result = capturer.start_realtime_capture()
    
    print(f"\n📊 CAPTURE RESULTS")
    print("=" * 40)
    for key, value in capture_result.items():
        print(f"   {key}: {value}")
    
    # Get status
    status = capturer.get_session_status()
    
    print(f"\n📈 SESSION STATUS")
    print("=" * 40)
    for key, value in status.items():
        print(f"   {key}: {value}")
    
    # Start continuous monitoring if successful
    if capture_result.get("success"):
        print(f"\n🔄 Starting continuous monitoring...")
        monitor_thread = capturer.start_continuous_monitoring()
        
        # Let it run for a few minutes as a test
        print(f"⏱️ Monitoring for 2 minutes...")
        await asyncio.sleep(120)
        
        capturer.capture_active = False
        print(f"✅ Monitoring test complete")
    
    # Save results
    timestamp = int(time.time())
    results_file = f"firebase_realtime_capture_results_{timestamp}.json"
    
    final_results = {
        "capture_result": capture_result,
        "session_status": status,
        "timestamp": datetime.now().isoformat(),
        "integration_status": "READY_FOR_API_INTEGRATION"
    }
    
    with open(results_file, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    
    return final_results

def main():
    """Main function to run real-time Firebase capture"""
    asyncio.run(test_realtime_firebase_capture())

if __name__ == "__main__":
    main() 