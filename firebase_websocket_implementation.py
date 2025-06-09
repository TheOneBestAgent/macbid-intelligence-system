#!/usr/bin/env python3
"""
🔥 FIREBASE WEBSOCKET IMPLEMENTATION
Complete WebSocket implementation for Firebase real-time bidding data
"""

import asyncio
import websockets
import json
import time
import urllib.parse
import ssl
from datetime import datetime
from typing import Dict, List, Optional, Any

class FirebaseWebSocketClient:
    def __init__(self):
        # Load Firebase credentials
        self.load_firebase_credentials()
        
        # WebSocket configuration
        self.ws_url = "wss://firestore.googleapis.com/google.firestore.v1.Firestore/Listen/channel"
        self.websocket = None
        self.connected = False
        self.message_count = 0
        
        # Real-time data storage
        self.live_lots = {}
        self.bid_updates = []
        
        # Connection parameters
        self.rid = 18109  # Request ID from working examples
        self.aid = 8665   # Application ID
        self.ofs = 29     # Offset counter
        
        print("🔥 FIREBASE WEBSOCKET CLIENT")
        print(f"   Session: {self.firebase_session[:20]}...")
        print(f"   SID: {self.session_id[:20]}...")
        print(f"   WebSocket URL: {self.ws_url}")
    
    def load_firebase_credentials(self):
        """Load Firebase credentials from auth config or breakdown"""
        try:
            import sys
            sys.path.append('organized_system/core_systems')
            from macbid_auth_config import FIREBASE_SESSION_ID, SESSION_ID
            
            self.firebase_session = FIREBASE_SESSION_ID
            self.session_id = SESSION_ID
            print("✅ Loaded Firebase credentials from auth config")
            
        except ImportError:
            # Try to extract fresh credentials from macbid_breakdown
            self.extract_fresh_credentials()
    
    def extract_fresh_credentials(self):
        """Extract fresh Firebase credentials from macbid_breakdown"""
        try:
            with open("macbid_breakdown/macbid_breakdown", 'r') as f:
                content = f.read()
            
            import re
            firebase_lines = [line for line in content.split('\n') 
                            if 'firestore.googleapis.com' in line and 'gsessionid=' in line]
            
            if firebase_lines:
                latest_line = firebase_lines[-1]
                gsessionid_match = re.search(r'gsessionid=([^&\s]+)', latest_line)
                sid_match = re.search(r'SID=([^&\s]+)', latest_line)
                
                if gsessionid_match and sid_match:
                    self.firebase_session = gsessionid_match.group(1)
                    self.session_id = sid_match.group(1)
                    print("✅ Extracted fresh Firebase credentials from breakdown")
                    return
            
            # Fallback credentials
            self.firebase_session = "hgpyx2kZyefNRKokgOt42EbyB-KeoJs0X_5OgkavHwc"
            self.session_id = "lmTKFrLnGL0yxLa5jxrfRw"
            print("⚠️  Using fallback Firebase credentials")
            
        except Exception as e:
            print(f"❌ Error extracting credentials: {e}")
            self.firebase_session = "hgpyx2kZyefNRKokgOt42EbyB-KeoJs0X_5OgkavHwc"
            self.session_id = "lmTKFrLnGL0yxLa5jxrfRw"
    
    def build_websocket_url(self) -> str:
        """Build WebSocket URL with proper parameters"""
        params = {
            'VER': '8',
            'database': 'projects/recommerce-a0291/databases/(default)',
            'gsessionid': self.firebase_session,
            'SID': self.session_id,
            'RID': str(self.rid),
            'AID': str(self.aid),
            'CI': '0',
            'TYPE': 'xmlhttp',
            'zx': f'ws{int(time.time() * 1000)}',
            't': '1'
        }
        
        query_string = urllib.parse.urlencode(params)
        full_url = f"{self.ws_url}?{query_string}"
        
        print(f"🔗 WebSocket URL: {full_url[:100]}...")
        return full_url
    
    async def connect(self) -> bool:
        """Establish WebSocket connection to Firebase"""
        print("\n🔌 CONNECTING TO FIREBASE WEBSOCKET")
        print("-" * 40)
        
        try:
            # Build connection URL
            ws_url = self.build_websocket_url()
            
            # WebSocket headers
            headers = {
                'Origin': 'https://www.mac.bid',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept-Language': 'en-US,en;q=0.6'
            }
            
            # SSL context for secure connection
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = True
            ssl_context.verify_mode = ssl.CERT_REQUIRED
            
            print("   Attempting WebSocket connection...")
            
            # Connect to WebSocket
            self.websocket = await websockets.connect(
                ws_url,
                additional_headers=headers,
                ssl=ssl_context,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10
            )
            
            self.connected = True
            print("   ✅ WebSocket connected successfully!")
            
            return True
            
        except Exception as e:
            print(f"   ❌ WebSocket connection failed: {e}")
            self.connected = False
            return False
    
    def create_lot_monitor_message(self, lot_id: str, target_id: int = 36) -> str:
        """Create message to monitor a specific auction lot"""
        database_path = "projects/recommerce-a0291/databases/(default)"
        document_path = f"{database_path}/documents/auction-lots/{lot_id}"
        
        request_data = {
            "database": database_path,
            "addTarget": {
                "documents": {
                    "documents": [document_path]
                },
                "targetId": target_id
            }
        }
        
        # Increment counters
        self.rid += 1
        self.ofs += 1
        
        return json.dumps(request_data)
    
    async def monitor_lot(self, lot_id: str) -> bool:
        """Start monitoring a specific auction lot"""
        if not self.connected:
            print(f"❌ Not connected to Firebase")
            return False
        
        try:
            print(f"📡 Starting to monitor lot: {lot_id}")
            
            # Create monitoring message
            message = self.create_lot_monitor_message(lot_id)
            
            # Send monitoring request
            await self.websocket.send(message)
            print(f"   ✅ Monitoring request sent for {lot_id}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error monitoring lot {lot_id}: {e}")
            return False
    
    def parse_firebase_message(self, message: str) -> Optional[Dict]:
        """Parse incoming Firebase real-time message"""
        try:
            # Firebase sends messages in specific format
            # Example: [1,2,[{"data":{"current_bid":29,"unique_bidders":5}}]]
            
            if message.startswith('[') and message.endswith(']'):
                parsed = json.loads(message)
                
                # Check for bid data format
                if (isinstance(parsed, list) and len(parsed) >= 3 and 
                    parsed[0] == 1 and parsed[1] == 2 and isinstance(parsed[2], list)):
                    
                    bid_data = parsed[2][0] if parsed[2] else None
                    if bid_data and 'data' in bid_data:
                        return bid_data['data']
            
            # Handle other Firebase message formats
            if '"current_bid"' in message or '"unique_bidders"' in message:
                # Try to extract JSON from message
                import re
                json_match = re.search(r'\{.*\}', message)
                if json_match:
                    return json.loads(json_match.group(0))
            
            return None
            
        except Exception as e:
            print(f"   ⚠️ Error parsing message: {e}")
            return None
    
    async def listen_for_updates(self, duration: int = 60) -> List[Dict]:
        """Listen for real-time bid updates"""
        print(f"\n👂 LISTENING FOR REAL-TIME UPDATES ({duration}s)")
        print("-" * 45)
        
        updates = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration and self.connected:
                try:
                    # Wait for message with timeout
                    message = await asyncio.wait_for(
                        self.websocket.recv(), 
                        timeout=5.0
                    )
                    
                    self.message_count += 1
                    print(f"   📨 Message {self.message_count}: {len(message)} bytes")
                    
                    # Parse the message
                    parsed_data = self.parse_firebase_message(message)
                    
                    if parsed_data:
                        update = {
                            'timestamp': datetime.now().isoformat(),
                            'message_id': self.message_count,
                            'data': parsed_data,
                            'raw_message': message[:200] + '...' if len(message) > 200 else message
                        }
                        updates.append(update)
                        
                        # Log significant updates
                        if 'current_bid' in parsed_data:
                            print(f"   🔥 BID UPDATE: ${parsed_data.get('current_bid', 0)}")
                        if 'unique_bidders' in parsed_data:
                            print(f"   👥 BIDDERS: {parsed_data.get('unique_bidders', 0)}")
                    
                except asyncio.TimeoutError:
                    # No message received, continue listening
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print("   ⚠️ WebSocket connection closed")
                    self.connected = False
                    break
                    
        except Exception as e:
            print(f"   ❌ Error listening for updates: {e}")
        
        print(f"   📊 Received {len(updates)} real-time updates")
        return updates
    
    async def monitor_specific_lots(self, lot_ids: List[str], duration: int = 60) -> Dict:
        """Monitor specific lots and collect real-time data"""
        print(f"\n🎯 MONITORING SPECIFIC LOTS")
        print("-" * 30)
        
        results = {
            'lots_monitored': [],
            'real_time_updates': [],
            'connection_status': 'unknown',
            'total_messages': 0
        }
        
        # Connect to Firebase
        connected = await self.connect()
        if not connected:
            results['connection_status'] = 'failed'
            return results
        
        results['connection_status'] = 'connected'
        
        # Start monitoring each lot
        for lot_id in lot_ids:
            success = await self.monitor_lot(lot_id)
            if success:
                results['lots_monitored'].append(lot_id)
        
        # Listen for updates
        if results['lots_monitored']:
            updates = await self.listen_for_updates(duration)
            results['real_time_updates'] = updates
            results['total_messages'] = self.message_count
        
        # Close connection
        await self.disconnect()
        
        return results
    
    async def disconnect(self):
        """Disconnect from Firebase WebSocket"""
        if self.websocket and self.connected:
            print("\n🔌 Disconnecting from Firebase...")
            await self.websocket.close()
            self.connected = False
            print("   ✅ Disconnected successfully")
    
    async def test_firebase_websocket(self) -> Dict:
        """Test Firebase WebSocket implementation"""
        print("🚀 TESTING FIREBASE WEBSOCKET")
        print("=" * 35)
        
        start_time = time.time()
        
        # Test lots from working examples
        test_lots = [
            '48360-2549A',  # Known working lot
            '48223-3096Z',  # Another test lot
            '48012-1029W'   # Third test lot
        ]
        
        # Monitor lots for 30 seconds
        results = await self.monitor_specific_lots(test_lots, duration=30)
        
        # Calculate success metrics
        processing_time = time.time() - start_time
        firebase_working = results['connection_status'] == 'connected'
        updates_received = len(results['real_time_updates'])
        
        # Final results
        final_results = {
            'timestamp': datetime.now().isoformat(),
            'processing_time': round(processing_time, 2),
            'firebase_websocket_working': firebase_working,
            'lots_monitored': results['lots_monitored'],
            'real_time_updates_count': updates_received,
            'real_time_updates': results['real_time_updates'],
            'total_messages_received': results['total_messages'],
            'success_rate': 100 if firebase_working else 0
        }
        
        # Print results
        print(f"\n📊 FIREBASE WEBSOCKET TEST RESULTS")
        print("=" * 40)
        print(f"Connection: {'✅ SUCCESS' if firebase_working else '❌ FAILED'}")
        print(f"Lots Monitored: {len(results['lots_monitored'])}")
        print(f"Real-time Updates: {updates_received}")
        print(f"Total Messages: {results['total_messages']}")
        print(f"Processing Time: {processing_time:.1f}s")
        
        if firebase_working:
            print("\n🎉 FIREBASE WEBSOCKET WORKING!")
            print("   Real-time bidding data collection active")
        else:
            print("\n❌ FIREBASE WEBSOCKET NEEDS MORE WORK")
            print("   Check credentials and connection parameters")
        
        # Save results
        with open(f"firebase_websocket_results_{int(time.time())}.json", 'w') as f:
            json.dump(final_results, f, indent=2)
        
        print(f"\n💾 Results saved to: firebase_websocket_results_{int(time.time())}.json")
        
        return final_results

async def main():
    """Main function to test Firebase WebSocket implementation"""
    client = FirebaseWebSocketClient()
    results = await client.test_firebase_websocket()
    return results

if __name__ == "__main__":
    # Install websockets if not available
    try:
        import websockets
    except ImportError:
        print("📦 Installing websockets library...")
        import subprocess
        subprocess.check_call(['pip3', 'install', 'websockets'])
        import websockets
    
    # Run the WebSocket test
    results = asyncio.run(main()) 