#!/usr/bin/env python3
"""
🚀 REAL-TIME ENHANCED MONITOR - Ultra-Fast Market Intelligence
5-second polling with ML predictions, smart alerts, and comprehensive analytics
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
import time
from datetime import datetime, timedelta
from collections import defaultdict

# Import our enhanced modules
try:
    from bid_predictor import BidPredictor
    from notification_system import NotificationSystem
    ML_AVAILABLE = True
    NOTIFICATIONS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Some modules not available: {e}")
    BidPredictor = None
    NotificationSystem = None
    ML_AVAILABLE = False
    NOTIFICATIONS_AVAILABLE = False

class RealtimeEnhancedMonitor:
    def __init__(self, poll_interval=5):
        self.poll_interval = poll_interval
        self.db_path = "realtime_monitor.db"
        self.session = None
        self.ssl_context = self.create_ssl_context()
        
        # Initialize enhanced components
        self.ml_predictor = BidPredictor() if ML_AVAILABLE else None
        self.notifier = NotificationSystem() if NOTIFICATIONS_AVAILABLE else None
        
        # Tracking sets
        self.known_lots = set()
        self.scan_count = 0
        self.total_items_found = 0
        self.total_alerts_sent = 0
        self.start_time = None
        
        self.setup_database()
        
        # South Carolina locations
        self.sc_locations = [
            "Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"
        ]
        
        # Premium brands for priority monitoring
        self.premium_brands = {
            'apple': {'priority': 'CRITICAL', 'min_value': 200},
            'sony': {'priority': 'HIGH', 'min_value': 150},
            'samsung': {'priority': 'HIGH', 'min_value': 150},
            'nintendo': {'priority': 'HIGH', 'min_value': 100},
            'dyson': {'priority': 'MEDIUM', 'min_value': 200},
            'bose': {'priority': 'MEDIUM', 'min_value': 100}
        }

    def create_ssl_context(self):
        """Create SSL context for API requests."""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context

    def setup_database(self):
        """Setup real-time monitoring database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS realtime_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                lot_id TEXT,
                product_name TEXT,
                brand TEXT,
                category TEXT,
                auction_location TEXT,
                retail_price REAL,
                instant_win_price REAL,
                current_bid REAL,
                discount_percent REAL,
                opportunity_score REAL,
                urgency_score REAL,
                value_score REAL,
                alert_sent INTEGER DEFAULT 0,
                alert_type TEXT,
                alert_priority TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    async def create_session(self):
        """Create HTTP session for API requests."""
        connector = aiohttp.TCPConnector(
            ssl=self.ssl_context,
            limit=15,
            limit_per_host=10
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )

    async def close_session(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()

    async def rapid_scan_new_arrivals(self):
        """Rapid scan for new arrivals across multiple pages."""
        new_detections = []
        scan_start = time.time()
        
        try:
            # Scan first 3 pages for maximum coverage
            tasks = []
            for page in range(1, 4):
                task = self.scan_page_for_arrivals(page)
                tasks.append(task)
                
            # Execute scans concurrently
            page_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for page_num, result in enumerate(page_results, 1):
                if isinstance(result, Exception):
                    continue
                    
                for item in result:
                    lot_id = item.get('lot_id')
                    if lot_id and lot_id not in self.known_lots:
                        self.known_lots.add(lot_id)
                        
                        # Enhanced processing
                        enhanced_item = await self.process_new_detection(item)
                        if enhanced_item:
                            new_detections.append(enhanced_item)
                            
        except Exception as e:
            print(f"⚠️ Rapid scan error: {e}")
            
        scan_time = time.time() - scan_start
        self.scan_count += 1
        
        return new_detections, scan_time

    async def scan_page_for_arrivals(self, page):
        """Scan a specific page for new arrivals."""
        url = "https://api.macdiscount.com/search"
        params = {
            'q': '',
            'limit': 100,
            'page': page
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    items = data.get('items', []) if isinstance(data, dict) else data
                    
                    # Filter for SC locations
                    sc_items = []
                    for item in items:
                        location = item.get('auction_location', '')
                        if any(sc_loc in location for sc_loc in self.sc_locations):
                            sc_items.append(item)
                            
                    return sc_items
                else:
                    return []
                    
        except Exception as e:
            return []

    async def process_new_detection(self, item):
        """Process newly detected item with full analytics."""
        try:
            # Extract basic info
            lot_id = item.get('lot_id')
            product_name = item.get('product_name', 'Unknown Product')
            retail_price = item.get('retail_price', 0)
            instant_win_price = item.get('instant_win_price', 0)
            current_bid = item.get('current_bid', 0)
            
            # Calculate discount
            discount_percent = 0
            if retail_price > 0 and instant_win_price > 0:
                discount_percent = ((retail_price - instant_win_price) / retail_price) * 100
                
            # Detect brand and category
            brand, category = self.detect_brand_category(product_name)
            
            # Calculate analytics scores
            opportunity_score = self.calculate_opportunity_score(item, brand, discount_percent)
            urgency_score = self.calculate_urgency_score(item, discount_percent)
            value_score = min(discount_percent, 100)
            
            # Enhanced item data
            enhanced_item = {
                'lot_id': lot_id,
                'product_name': product_name,
                'brand': brand,
                'category': category,
                'auction_location': item.get('auction_location'),
                'retail_price': retail_price,
                'instant_win_price': instant_win_price,
                'current_bid': current_bid,
                'discount_percent': discount_percent,
                'opportunity_score': opportunity_score,
                'urgency_score': urgency_score,
                'value_score': value_score,
                'detection_time': datetime.now().isoformat()
            }
            
            # Save to database
            self.save_detection(enhanced_item)
            
            # Generate alerts if warranted
            await self.check_and_send_alerts(enhanced_item)
            
            return enhanced_item
            
        except Exception as e:
            return None

    def detect_brand_category(self, product_name):
        """Detect brand and category from product name."""
        if not product_name:
            return 'Unknown', 'Unknown'
            
        product_lower = product_name.lower()
        
        # Brand detection
        detected_brand = 'Unknown'
        for brand in self.premium_brands:
            if brand in product_lower:
                detected_brand = brand
                break
                
        # Category detection
        category_keywords = {
            'Electronics': ['laptop', 'computer', 'tablet', 'phone', 'iphone', 'ipad', 'macbook'],
            'Audio': ['headphones', 'speaker', 'audio', 'sound', 'airpods', 'beats'],
            'Gaming': ['gaming', 'game', 'console', 'controller', 'xbox', 'playstation', 'nintendo'],
            'Appliances': ['vacuum', 'dyson', 'kitchen', 'appliance'],
            'Tools': ['drill', 'saw', 'tool', 'dewalt', 'milwaukee'],
            'Luxury': ['luxury', 'premium', 'designer', 'high-end']
        }
        
        detected_category = 'Other'
        for category, keywords in category_keywords.items():
            if any(keyword in product_lower for keyword in keywords):
                detected_category = category
                break
                
        return detected_brand, detected_category

    def calculate_opportunity_score(self, item, brand, discount_percent):
        """Calculate overall opportunity score (0-100)."""
        score = 0
        
        # Base score from discount
        score += min(discount_percent, 50)
        
        # Brand premium
        if brand in self.premium_brands:
            brand_info = self.premium_brands[brand]
            if brand_info['priority'] == 'CRITICAL':
                score += 30
            elif brand_info['priority'] == 'HIGH':
                score += 20
            elif brand_info['priority'] == 'MEDIUM':
                score += 10
                
        # High value bonus
        retail_price = item.get('retail_price', 0)
        if retail_price > 1000:
            score += 15
        elif retail_price > 500:
            score += 10
        elif retail_price > 200:
            score += 5
            
        # No bid bonus
        if item.get('current_bid', 0) == 0:
            score += 10
            
        return min(score, 100)

    def calculate_urgency_score(self, item, discount_percent):
        """Calculate urgency score based on how quickly action is needed."""
        score = 0
        
        # Extreme discounts are urgent
        if discount_percent > 80:
            score += 50
        elif discount_percent > 60:
            score += 30
        elif discount_percent > 40:
            score += 20
            
        # Zero price items are extremely urgent
        if item.get('instant_win_price', 0) == 0:
            score += 50
            
        # High-value items with no bids are urgent
        if (item.get('retail_price', 0) > 500 and 
            item.get('current_bid', 0) == 0):
            score += 20
            
        return min(score, 100)

    def save_detection(self, enhanced_item):
        """Save detection to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO realtime_detections (
                lot_id, product_name, brand, category, auction_location,
                retail_price, instant_win_price, current_bid, discount_percent,
                opportunity_score, urgency_score, value_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            enhanced_item['lot_id'],
            enhanced_item['product_name'],
            enhanced_item['brand'],
            enhanced_item['category'],
            enhanced_item['auction_location'],
            enhanced_item['retail_price'],
            enhanced_item['instant_win_price'],
            enhanced_item['current_bid'],
            enhanced_item['discount_percent'],
            enhanced_item['opportunity_score'],
            enhanced_item['urgency_score'],
            enhanced_item['value_score']
        ))
        
        conn.commit()
        conn.close()

    async def check_and_send_alerts(self, enhanced_item):
        """Check if item warrants alerts and send them."""
        # Determine alert level
        if enhanced_item['urgency_score'] >= 70:
            alert_type = "CRITICAL_OPPORTUNITY"
            severity = "CRITICAL"
        elif enhanced_item['opportunity_score'] >= 80:
            alert_type = "HIGH_OPPORTUNITY"
            severity = "HIGH"
        elif enhanced_item['opportunity_score'] >= 60:
            alert_type = "MEDIUM_OPPORTUNITY"
            severity = "MEDIUM"
        else:
            return  # No alert needed
            
        # Create alert
        alert = {
            'type': alert_type,
            'category': 'REALTIME_DETECTION',
            'severity': severity,
            'message': self.create_alert_message(enhanced_item),
            'lot_id': enhanced_item['lot_id'],
            'score': enhanced_item['opportunity_score']
        }
        
        # Send notification
        if self.notifier:
            try:
                success, message = await self.notifier.send_notification(alert)
                if success:
                    self.total_alerts_sent += 1
            except Exception as e:
                print(f"⚠️ Notification error: {e}")
        else:
            # Fallback console alert
            self.send_console_alert(alert)

    def create_alert_message(self, item):
        """Create formatted alert message."""
        brand_text = f"{item['brand'].title()} " if item['brand'] != 'Unknown' else ""
        
        message = f"🚨 {brand_text}{item['product_name'][:40]}"
        
        if item['retail_price'] > 0:
            message += f" | ${item['retail_price']:,.0f}"
            
        if item['discount_percent'] > 0:
            message += f" | {item['discount_percent']:.0f}% OFF"
            
        if item['current_bid'] == 0:
            message += " | NO BIDS YET"
            
        message += f" | {item['auction_location']}"
        
        return message

    def send_console_alert(self, alert):
        """Send console alert as fallback."""
        icons = {'CRITICAL': '🚨', 'HIGH': '⚡', 'MEDIUM': '📢', 'LOW': 'ℹ️'}
        icon = icons.get(alert['severity'], '📢')
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n{icon} [{timestamp}] {alert['severity']} REALTIME ALERT")
        print(f"   {alert['message']}")
        print(f"   Score: {alert['score']}")

    def show_session_stats(self):
        """Show current session statistics."""
        if self.start_time:
            runtime = time.time() - self.start_time
            runtime_minutes = runtime / 60
            
            print(f"\n📊 REALTIME MONITORING STATS")
            print("="*50)
            print(f"⏱️  Runtime: {runtime_minutes:.1f} minutes")
            print(f"🔍 Total Scans: {self.scan_count}")
            print(f"🆕 Items Found: {self.total_items_found}")
            print(f"🚨 Alerts Sent: {self.total_alerts_sent}")
            if runtime_minutes > 0:
                print(f"📈 Scan Rate: {self.scan_count / runtime_minutes:.1f} scans/min")
            if self.scan_count > 0:
                print(f"🎯 Detection Rate: {self.total_items_found / self.scan_count:.1f} items/scan")

    async def run_realtime_monitoring(self):
        """Run continuous real-time monitoring."""
        print("🚀 REALTIME ENHANCED MONITOR STARTED")
        print(f"⚡ Polling every {self.poll_interval} seconds")
        print(f"🤖 ML Predictions: {'Enabled' if self.ml_predictor else 'Disabled'}")
        print(f"📱 Notifications: {'Enabled' if self.notifier else 'Console Only'}")
        print(f"📍 Monitoring: {', '.join(self.sc_locations)}")
        print("🔄 Press Ctrl+C to stop\n")
        
        await self.create_session()
        self.start_time = time.time()
        
        try:
            while True:
                cycle_start = time.time()
                
                # Rapid scan for new arrivals
                new_detections, scan_time = await self.rapid_scan_new_arrivals()
                
                if new_detections:
                    self.total_items_found += len(new_detections)
                    print(f"🆕 [{datetime.now().strftime('%H:%M:%S')}] Found {len(new_detections)} new items in {scan_time:.1f}s")
                    
                    # Show top opportunities
                    top_opportunities = sorted(new_detections, 
                                             key=lambda x: x['opportunity_score'], 
                                             reverse=True)[:3]
                    
                    for item in top_opportunities:
                        print(f"   🎯 {item['product_name'][:30]} | Score: {item['opportunity_score']:.0f} | {item['discount_percent']:.0f}% off")
                else:
                    # Status update every 12 scans (1 minute at 5-second intervals)
                    if self.scan_count % 12 == 0:
                        print(f"⏰ [{datetime.now().strftime('%H:%M:%S')}] Monitoring... ({len(self.known_lots)} lots tracked)")
                
                # Show stats every 5 minutes
                if self.scan_count % 60 == 0:
                    self.show_session_stats()
                
                # Wait for next scan
                cycle_time = time.time() - cycle_start
                sleep_time = max(0, self.poll_interval - cycle_time)
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Realtime monitoring stopped")
            self.show_session_stats()
            
        finally:
            await self.close_session()

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="🚀 Realtime Enhanced Monitor")
    parser.add_argument("--interval", type=int, default=5, 
                       help="Polling interval in seconds (default: 5)")
    parser.add_argument("--test", action="store_true", 
                       help="Run one test scan")
    
    args = parser.parse_args()
    
    monitor = RealtimeEnhancedMonitor(poll_interval=args.interval)
    
    if args.test:
        print("🧪 Running test scan...")
        await monitor.create_session()
        
        try:
            detections, scan_time = await monitor.rapid_scan_new_arrivals()
            print(f"✅ Test complete: {len(detections)} items found in {scan_time:.1f}s")
            
            if detections:
                top_item = max(detections, key=lambda x: x['opportunity_score'])
                print(f"🏆 Top opportunity: {top_item['product_name']} (Score: {top_item['opportunity_score']:.0f})")
                
        finally:
            await monitor.close_session()
    else:
        await monitor.run_realtime_monitoring()

if __name__ == "__main__":
    asyncio.run(main()) 