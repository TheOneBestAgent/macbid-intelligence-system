#!/usr/bin/env python3
"""
Real-Time Auction Monitor for Mac.bid
Monitors active auctions and tracks bidding activity in real-time
"""

import asyncio
import aiohttp
import sqlite3
import json
import time
from datetime import datetime, timedelta
import threading
import queue
import os
from typing import Dict, List, Optional
import logging

class RealTimeAuctionMonitor:
    def __init__(self):
        self.db_path = "databases/realtime_auction_monitor.db"
        self.setup_database()
        self.setup_logging()
        
        # Configuration
        self.monitor_interval = 30  # seconds between checks
        self.max_concurrent_requests = 10
        self.active_lots = {}  # lot_id -> lot_data
        self.bid_alerts_queue = queue.Queue()
        self.price_alerts_queue = queue.Queue()
        
        # Next.js API configuration
        self.nextjs_build_id = "AslxUFb4wF5GgYRFXlpoC"
        self.base_url = "https://www.mac.bid/_next/data"
        
        # Authentication setup
        self.session_headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.6',
            'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
            'x-nextjs-data': '1'
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
        
        # Monitoring state
        self.is_monitoring = False
        self.monitor_thread = None
        
    def setup_database(self):
        """Setup database for real-time monitoring"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Real-time lot tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS realtime_lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER,
                auction_id INTEGER,
                lot_number TEXT,
                product_name TEXT,
                current_bid REAL,
                instant_win_price REAL,
                retail_price REAL,
                unique_bidders INTEGER,
                total_bids INTEGER,
                expected_close_date TEXT,
                is_open INTEGER,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(lot_id, auction_id)
            )
        ''')
        
        # Bid history tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER,
                auction_id INTEGER,
                bid_amount REAL,
                bidder_count INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Price alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER,
                auction_id INTEGER,
                alert_type TEXT,
                threshold_price REAL,
                current_price REAL,
                message TEXT,
                is_active INTEGER DEFAULT 1,
                created_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                triggered_date DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_logging(self):
        """Setup logging for monitoring activities"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data_outputs/realtime_monitor.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    async def fetch_lot_data(self, session: aiohttp.ClientSession, auction_id: int, lot_id: str) -> Optional[Dict]:
        """Fetch real-time lot data from Next.js API"""
        url = f"{self.base_url}/{self.nextjs_build_id}/index.json"
        params = {'aid': auction_id, 'lid': lot_id}
        
        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('pageProps', {}).get('activeLot')
                else:
                    self.logger.warning(f"Failed to fetch lot {lot_id}: HTTP {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Error fetching lot {lot_id}: {e}")
            return None
    
    def detect_bid_changes(self, lot_id: int, old_data: Dict, new_data: Dict) -> List[Dict]:
        """Detect changes in bidding activity"""
        changes = []
        
        # Check for new bids
        old_bids = old_data.get('total_bids', 0)
        new_bids = new_data.get('total_bids', 0)
        
        if new_bids > old_bids:
            changes.append({
                'type': 'NEW_BID',
                'lot_id': lot_id,
                'old_bids': old_bids,
                'new_bids': new_bids,
                'current_amount': new_data.get('winning_bid_amount', 0)
            })
        
        # Check for new bidders
        old_bidders = old_data.get('unique_bidders', 0)
        new_bidders = new_data.get('unique_bidders', 0)
        
        if new_bidders > old_bidders:
            changes.append({
                'type': 'NEW_BIDDER',
                'lot_id': lot_id,
                'old_bidders': old_bidders,
                'new_bidders': new_bidders
            })
        
        return changes
    
    def check_price_alerts(self, lot_data: Dict) -> List[Dict]:
        """Check if any price alerts should be triggered"""
        alerts = []
        lot_id = lot_data.get('id')
        current_price = lot_data.get('winning_bid_amount', 0)
        instant_win = lot_data.get('instant_win_price', 0)
        retail_price = lot_data.get('retail_price', 0)
        
        # Check for approaching instant win price
        if instant_win > 0 and current_price > 0:
            percentage_to_instant_win = (current_price / instant_win) * 100
            if percentage_to_instant_win >= 80:
                alerts.append({
                    'type': 'APPROACHING_INSTANT_WIN',
                    'lot_id': lot_id,
                    'current_price': current_price,
                    'instant_win_price': instant_win,
                    'percentage': percentage_to_instant_win
                })
        
        # Check for good deal thresholds
        if retail_price > 0 and current_price > 0:
            discount_percentage = ((retail_price - current_price) / retail_price) * 100
            if discount_percentage >= 70:
                alerts.append({
                    'type': 'EXCELLENT_DEAL',
                    'lot_id': lot_id,
                    'current_price': current_price,
                    'retail_price': retail_price,
                    'discount_percentage': discount_percentage
                })
        
        return alerts
    
    def save_lot_update(self, lot_data: Dict):
        """Save lot update to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO realtime_lots 
            (lot_id, auction_id, lot_number, product_name, current_bid, 
             instant_win_price, retail_price, unique_bidders, total_bids, 
             expected_close_date, is_open, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            lot_data.get('id'),
            lot_data.get('auction_id'),
            lot_data.get('lot_number'),
            lot_data.get('product_name'),
            lot_data.get('winning_bid_amount', 0),
            lot_data.get('instant_win_price', 0),
            lot_data.get('retail_price', 0),
            lot_data.get('unique_bidders', 0),
            lot_data.get('total_bids', 0),
            lot_data.get('expected_close_date'),
            lot_data.get('is_open', 0)
        ))
        
        # Save bid history
        cursor.execute('''
            INSERT INTO bid_history 
            (lot_id, auction_id, bid_amount, bidder_count)
            VALUES (?, ?, ?, ?)
        ''', (
            lot_data.get('id'),
            lot_data.get('auction_id'),
            lot_data.get('winning_bid_amount', 0),
            lot_data.get('unique_bidders', 0)
        ))
        
        conn.commit()
        conn.close()
    
    def save_alert(self, alert: Dict):
        """Save alert to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO price_alerts 
            (lot_id, auction_id, alert_type, current_price, message, triggered_date)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (
            alert.get('lot_id'),
            alert.get('auction_id', 0),
            alert.get('type'),
            alert.get('current_price', 0),
            json.dumps(alert)
        ))
        
        conn.commit()
        conn.close()
    
    async def monitor_lots_batch(self, lots_to_monitor: List[Dict]):
        """Monitor a batch of lots concurrently"""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(
            headers=self.session_headers,
            cookies=self.session_cookies,
            connector=connector,
            timeout=timeout
        ) as session:
            
            tasks = []
            for lot in lots_to_monitor:
                task = self.fetch_lot_data(session, lot['auction_id'], lot['lot_id'])
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error monitoring lot {lots_to_monitor[i]['lot_id']}: {result}")
                    continue
                
                if result:
                    lot_info = lots_to_monitor[i]
                    lot_id = result.get('id')
                    
                    # Check for changes
                    if lot_id in self.active_lots:
                        changes = self.detect_bid_changes(lot_id, self.active_lots[lot_id], result)
                        for change in changes:
                            self.logger.info(f"Bid change detected: {change}")
                            self.bid_alerts_queue.put(change)
                    
                    # Check for price alerts
                    alerts = self.check_price_alerts(result)
                    for alert in alerts:
                        self.logger.info(f"Price alert triggered: {alert}")
                        self.price_alerts_queue.put(alert)
                        self.save_alert(alert)
                    
                    # Update stored data
                    self.active_lots[lot_id] = result
                    self.save_lot_update(result)
    
    def add_lot_to_monitor(self, auction_id: int, lot_id: str, priority: int = 1):
        """Add a lot to the monitoring list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO realtime_lots 
            (lot_id, auction_id, last_updated)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (lot_id, auction_id))
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"Added lot {lot_id} from auction {auction_id} to monitoring")
    
    def get_lots_to_monitor(self) -> List[Dict]:
        """Get list of lots currently being monitored"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT lot_id, auction_id, lot_number, product_name
            FROM realtime_lots 
            WHERE is_open = 1 OR is_open IS NULL
            ORDER BY last_updated DESC
        ''')
        
        lots = []
        for row in cursor.fetchall():
            lots.append({
                'lot_id': row[0],
                'auction_id': row[1],
                'lot_number': row[2],
                'product_name': row[3]
            })
        
        conn.close()
        return lots
    
    async def monitoring_loop(self):
        """Main monitoring loop"""
        session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.logger.info(f"Starting monitoring session: {session_id}")
        
        while self.is_monitoring:
            try:
                lots_to_monitor = self.get_lots_to_monitor()
                
                if lots_to_monitor:
                    self.logger.info(f"Monitoring {len(lots_to_monitor)} lots...")
                    await self.monitor_lots_batch(lots_to_monitor)
                else:
                    self.logger.info("No lots to monitor")
                
                # Wait before next check
                await asyncio.sleep(self.monitor_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)  # Short delay before retry
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        if self.is_monitoring:
            self.logger.warning("Monitoring is already active")
            return
        
        self.is_monitoring = True
        self.logger.info("Starting real-time auction monitoring...")
        
        # Run monitoring loop in separate thread
        def run_monitoring():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.monitoring_loop())
        
        self.monitor_thread = threading.Thread(target=run_monitoring, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        if not self.is_monitoring:
            self.logger.warning("Monitoring is not active")
            return
        
        self.is_monitoring = False
        self.logger.info("Stopping real-time auction monitoring...")
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
    
    def get_monitoring_status(self) -> Dict:
        """Get current monitoring status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get active lots count
        cursor.execute("SELECT COUNT(*) FROM realtime_lots WHERE is_open = 1")
        active_lots_count = cursor.fetchone()[0]
        
        # Get recent alerts count
        cursor.execute('''
            SELECT COUNT(*) FROM price_alerts 
            WHERE triggered_date >= datetime('now', '-1 hour')
        ''')
        recent_alerts = cursor.fetchone()[0]
        
        # Get bid activity in last hour
        cursor.execute('''
            SELECT COUNT(*) FROM bid_history 
            WHERE timestamp >= datetime('now', '-1 hour')
        ''')
        recent_bid_activity = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'is_monitoring': self.is_monitoring,
            'active_lots_count': active_lots_count,
            'recent_alerts': recent_alerts,
            'recent_bid_activity': recent_bid_activity,
            'monitor_interval': self.monitor_interval,
            'queue_sizes': {
                'bid_alerts': self.bid_alerts_queue.qsize(),
                'price_alerts': self.price_alerts_queue.qsize()
            }
        }
    
    def generate_monitoring_report(self) -> Dict:
        """Generate comprehensive monitoring report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get most active lots
        cursor.execute('''
            SELECT lot_id, auction_id, product_name, 
                   COUNT(*) as bid_count,
                   MAX(bid_amount) as highest_bid,
                   MIN(bid_amount) as lowest_bid
            FROM bid_history 
            WHERE timestamp >= datetime('now', '-24 hours')
            GROUP BY lot_id, auction_id
            ORDER BY bid_count DESC
            LIMIT 10
        ''')
        
        most_active_lots = []
        for row in cursor.fetchall():
            most_active_lots.append({
                'lot_id': row[0],
                'auction_id': row[1],
                'product_name': row[2],
                'bid_count': row[3],
                'highest_bid': row[4],
                'lowest_bid': row[5]
            })
        
        # Get recent alerts
        cursor.execute('''
            SELECT alert_type, COUNT(*) as count
            FROM price_alerts 
            WHERE triggered_date >= datetime('now', '-24 hours')
            GROUP BY alert_type
        ''')
        
        alert_summary = dict(cursor.fetchall())
        
        # Get current lot status
        cursor.execute('''
            SELECT 
                COUNT(*) as total_lots,
                SUM(CASE WHEN is_open = 1 THEN 1 ELSE 0 END) as open_lots,
                AVG(current_bid) as avg_current_bid,
                AVG(retail_price) as avg_retail_price
            FROM realtime_lots
        ''')
        
        lot_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'monitoring_status': self.get_monitoring_status(),
            'most_active_lots': most_active_lots,
            'alert_summary': alert_summary,
            'lot_statistics': {
                'total_lots': lot_stats[0],
                'open_lots': lot_stats[1],
                'avg_current_bid': lot_stats[2] or 0,
                'avg_retail_price': lot_stats[3] or 0
            }
        }

def main():
    """Main function for testing"""
    monitor = RealTimeAuctionMonitor()
    
    # Add test lot for monitoring
    monitor.add_lot_to_monitor(48796, "3912D")
    
    print("🔴 REAL-TIME AUCTION MONITOR")
    print("="*50)
    
    try:
        # Start monitoring
        monitor.start_monitoring()
        
        print("✅ Monitoring started. Press Ctrl+C to stop...")
        
        # Monitor for alerts
        while True:
            time.sleep(5)
            
            # Check for bid alerts
            while not monitor.bid_alerts_queue.empty():
                alert = monitor.bid_alerts_queue.get()
                print(f"🔔 BID ALERT: {alert}")
            
            # Check for price alerts
            while not monitor.price_alerts_queue.empty():
                alert = monitor.price_alerts_queue.get()
                print(f"💰 PRICE ALERT: {alert}")
            
            # Show status every minute
            status = monitor.get_monitoring_status()
            print(f"📊 Status: {status['active_lots_count']} lots, "
                  f"{status['recent_alerts']} alerts, "
                  f"{status['recent_bid_activity']} bid activity")
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping monitor...")
        monitor.stop_monitoring()
        
        # Generate final report
        report = monitor.generate_monitoring_report()
        print(f"\n📊 FINAL REPORT:")
        print(f"Total Lots Monitored: {report['lot_statistics']['total_lots']}")
        print(f"Active Lots: {report['lot_statistics']['open_lots']}")
        print(f"Alert Summary: {report['alert_summary']}")

if __name__ == "__main__":
    main() 