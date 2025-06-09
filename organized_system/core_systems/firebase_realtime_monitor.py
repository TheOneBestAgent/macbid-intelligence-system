#!/usr/bin/env python3
"""
Firebase Firestore Real-time Auction Monitor
Using exact parameters discovered in macbid_breakdown
"""

import requests
import json
import time
import logging
from datetime import datetime
import urllib.parse
from typing import Dict, List, Optional

class FirebaseRealtimeMonitor:
    def __init__(self):
        # EXACT FIREBASE CONFIG from macbid_breakdown
        self.database = "projects/recommerce-a0291/databases/(default)"
        self.base_url = "https://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
        
        # SESSION DATA from macbid_breakdown
        self.gsessionid = "Ai4lxEZXgb836imXETBIn2QN9qMseZz2wcAvJ3byRJI"
        self.sid = "BajU2WcOCBGD2Ozj9gg-Nw"
        self.ver = "8"
        
        # EXACT HEADERS from macbid_breakdown
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.6",
            "content-type": "application/x-www-form-urlencoded",
            "priority": "u=1, i",
            "sec-ch-ua": '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"macOS"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "cross-site",
            "sec-fetch-storage-access": "none",
            "sec-gpc": "1",
            "referrer": "https://www.mac.bid/",
            "referrerPolicy": "strict-origin-when-cross-origin"
        }
        
        # Tracking state
        self.monitored_lots = set()
        self.target_id_counter = 200  # Start higher to avoid conflicts
        self.rid_counter = 99100  # Start higher than observed
        self.aid_counter = 9000   # Start higher than observed
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🔥 Firebase Firestore Real-time Monitor initialized")
        self.logger.info(f"   Database: {self.database}")
        self.logger.info(f"   Session: {self.gsessionid}")
    
    def _build_listen_url(self, rid: int, aid: int, extra_params: str = "") -> str:
        """Build Firebase Listen channel URL with exact parameters"""
        params = {
            "VER": self.ver,
            "database": self.database,
            "gsessionid": self.gsessionid,
            "SID": self.sid,
            "RID": str(rid),
            "AID": str(aid),
            "zx": f"firebase_{int(time.time() * 1000)}",
            "t": "1"
        }
        
        if extra_params:
            params.update(urllib.parse.parse_qs(extra_params))
        
        url = f"{self.base_url}?" + urllib.parse.urlencode(params, doseq=True)
        return url
    
    def add_lot_target(self, lot_id: str) -> bool:
        """Add a specific auction lot to real-time monitoring"""
        try:
            # Build document path exactly like macbid_breakdown
            document_path = f"projects/recommerce-a0291/databases/(default)/documents/auction-lots/{lot_id}"
            
            # Build request body exactly like macbid_breakdown
            request_data = {
                "database": self.database,
                "addTarget": {
                    "documents": {
                        "documents": [document_path]
                    },
                    "targetId": self.target_id_counter
                }
            }
            
            # URL encode the request data
            body_data = {
                "count": "1",
                "ofs": str(self.rid_counter - 99000),
                "req0___data__": json.dumps(request_data)
            }
            
            url = self._build_listen_url(self.rid_counter, self.aid_counter)
            
            response = requests.post(
                url,
                headers=self.headers,
                data=urllib.parse.urlencode(body_data),
                timeout=10
            )
            
            if response.status_code == 200:
                self.monitored_lots.add(lot_id)
                self.logger.info(f"✅ Added lot {lot_id} to real-time monitoring (Target ID: {self.target_id_counter})")
                
                # Increment counters
                self.target_id_counter += 2
                self.rid_counter += 1
                self.aid_counter += 1
                
                return True
            else:
                self.logger.warning(f"⚠️ Failed to add lot {lot_id}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error adding lot {lot_id}: {e}")
            return False
    
    def remove_lot_target(self, target_id: int) -> bool:
        """Remove a lot from real-time monitoring"""
        try:
            # Build request body for removing target
            request_data = {
                "database": self.database,
                "removeTarget": target_id
            }
            
            body_data = {
                "count": "1",
                "ofs": str(self.rid_counter - 99000),
                "req0___data__": json.dumps(request_data)
            }
            
            url = self._build_listen_url(self.rid_counter, self.aid_counter)
            
            response = requests.post(
                url,
                headers=self.headers,
                data=urllib.parse.urlencode(body_data),
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info(f"✅ Removed target {target_id} from monitoring")
                
                # Increment counters
                self.rid_counter += 1
                self.aid_counter += 1
                
                return True
            else:
                self.logger.warning(f"⚠️ Failed to remove target {target_id}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error removing target {target_id}: {e}")
            return False
    
    def listen_for_updates(self) -> Optional[Dict]:
        """Listen for real-time updates from Firebase"""
        try:
            # Build RPC URL for listening
            params = {
                "gsessionid": self.gsessionid,
                "VER": self.ver,
                "database": self.database,
                "RID": "rpc",
                "SID": self.sid,
                "AID": str(self.aid_counter),
                "CI": "0",
                "TYPE": "xmlhttp",
                "zx": f"listen_{int(time.time() * 1000)}",
                "t": "1"
            }
            
            url = f"{self.base_url}?" + urllib.parse.urlencode(params)
            
            response = requests.get(
                url,
                headers={k: v for k, v in self.headers.items() if k != "content-type"},
                timeout=30  # Longer timeout for listening
            )
            
            if response.status_code == 200:
                # Parse response for real-time updates
                content = response.text
                if content and content.strip():
                    self.logger.info(f"📡 Received real-time update: {len(content)} characters")
                    return {"status": "update", "content": content, "timestamp": datetime.now().isoformat()}
                else:
                    return {"status": "heartbeat", "timestamp": datetime.now().isoformat()}
            else:
                self.logger.warning(f"⚠️ Listen request failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error listening for updates: {e}")
            return None
    
    def monitor_specific_lots(self, lot_ids: List[str], duration_minutes: int = 10):
        """Monitor specific auction lots for real-time updates"""
        self.logger.info(f"🎯 Starting real-time monitoring for {len(lot_ids)} lots")
        
        # Add all lots to monitoring
        added_lots = []
        for lot_id in lot_ids:
            if self.add_lot_target(lot_id):
                added_lots.append(lot_id)
                time.sleep(0.5)  # Small delay between additions
        
        if not added_lots:
            self.logger.error("❌ No lots successfully added to monitoring")
            return
        
        self.logger.info(f"✅ Successfully monitoring {len(added_lots)} lots")
        
        # Listen for updates
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        update_count = 0
        
        while time.time() < end_time:
            update = self.listen_for_updates()
            
            if update:
                update_count += 1
                
                if update["status"] == "update":
                    self.logger.info(f"🔔 Real-time update #{update_count}")
                    self.logger.info(f"   Content preview: {update['content'][:100]}...")
                elif update["status"] == "heartbeat":
                    self.logger.info(f"💓 Heartbeat #{update_count}")
            
            time.sleep(2)  # Check every 2 seconds
        
        self.logger.info(f"🏁 Monitoring complete: {update_count} updates received in {duration_minutes} minutes")
    
    def test_firebase_connection(self):
        """Test Firebase Firestore connection with known lot IDs"""
        self.logger.info("🧪 Testing Firebase Firestore connection...")
        
        # Test with lot IDs found in macbid_breakdown
        test_lots = ["48504-3018N", "48012-2990W"]
        
        for lot_id in test_lots:
            self.logger.info(f"Testing lot {lot_id}...")
            success = self.add_lot_target(lot_id)
            
            if success:
                # Try to listen for immediate updates
                update = self.listen_for_updates()
                if update:
                    self.logger.info(f"✅ Firebase connection working for lot {lot_id}")
                else:
                    self.logger.warning(f"⚠️ No immediate response for lot {lot_id}")
            
            time.sleep(1)
        
        self.logger.info("🎉 Firebase connection test complete!")

if __name__ == "__main__":
    # Test the Firebase real-time monitor
    monitor = FirebaseRealtimeMonitor()
    
    print("🔥 FIREBASE FIRESTORE REAL-TIME MONITOR TEST")
    print("=" * 60)
    
    # Test connection
    monitor.test_firebase_connection()
    
    # Monitor some lots for 2 minutes
    print("\n📡 Starting 2-minute real-time monitoring test...")
    test_lots = ["48504-3018N", "48012-2990W", "35699935"]  # Mix of known IDs
    monitor.monitor_specific_lots(test_lots, duration_minutes=2)
    
    print("\n🎉 FIREBASE REAL-TIME MONITORING READY!") 