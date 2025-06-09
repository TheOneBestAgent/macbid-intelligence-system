#!/usr/bin/env python3
"""
🚀 ENHANCED CONTINUOUS MONITOR - Complete Intelligence System
Real-time monitoring with ML predictions, multi-channel notifications, and advanced analytics
"""

import asyncio
import json
import sqlite3
import time
import subprocess
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# Import our custom modules
try:
    from bid_predictor import BidPredictor
    from notification_system import NotificationSystem
except ImportError:
    print("⚠️ Some modules not available - running in basic mode")
    BidPredictor = None
    NotificationSystem = None

class EnhancedContinuousMonitor:
    def __init__(self, interval_minutes=5):
        self.interval = interval_minutes * 60
        self.db_path = "enhanced_monitor.db"
        self.setup_database()
        
        # Initialize ML predictor if available
        self.predictor = BidPredictor() if BidPredictor else None
        
        # Initialize notification system if available
        self.notifier = NotificationSystem() if NotificationSystem else None
        
        # Analytics modules to run
        self.analytics_modules = [
            {
                "name": "Enhanced New Arrivals",
                "script": "enhanced_new_arrivals.py",
                "args": ["--alerts-only"],
                "priority": "HIGH"
            },
            {
                "name": "Deal Hunter",
                "script": "deal_hunter.py", 
                "args": ["--mode", "steals"],
                "priority": "HIGH"
            },
            {
                "name": "No-Bid Tracker",
                "script": "no_bid_tracker.py",
                "args": ["--min-value", "500"],
                "priority": "MEDIUM"
            },
            {
                "name": "Price Analytics",
                "script": "price_analytics_tracker.py",
                "args": ["--alerts-only"],
                "priority": "MEDIUM"
            },
            {
                "name": "Advanced Product Search",
                "script": "advanced_product_search.py",
                "args": ["--brand", "apple"],
                "priority": "HIGH"
            }
        ]
        
    def setup_database(self):
        """Setup enhanced monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_end TIMESTAMP,
                total_cycles INTEGER DEFAULT 0,
                total_alerts INTEGER DEFAULT 0,
                total_predictions INTEGER DEFAULT 0,
                total_notifications INTEGER DEFAULT 0,
                avg_cycle_duration REAL DEFAULT 0,
                success_rate REAL DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cycle_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                cycle_number INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                module_name TEXT,
                execution_time REAL,
                items_found INTEGER,
                alerts_generated INTEGER,
                predictions_made INTEGER,
                notifications_sent INTEGER,
                status TEXT,
                FOREIGN KEY (session_id) REFERENCES monitoring_sessions (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opportunity_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                lot_id TEXT,
                product_name TEXT,
                alert_type TEXT,
                priority TEXT,
                retail_price REAL,
                instant_win_price REAL,
                discount_percent REAL,
                predicted_winning_bid REAL,
                confidence_score REAL,
                suggested_bid_min REAL,
                suggested_bid_max REAL,
                location TEXT,
                source_module TEXT,
                notification_sent INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def start_monitoring_session(self):
        """Start a new monitoring session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO monitoring_sessions (session_start)
            VALUES (CURRENT_TIMESTAMP)
        ''')
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return session_id
        
    def end_monitoring_session(self, session_id, stats):
        """End monitoring session with statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE monitoring_sessions 
            SET session_end = CURRENT_TIMESTAMP,
                total_cycles = ?,
                total_alerts = ?,
                total_predictions = ?,
                total_notifications = ?,
                avg_cycle_duration = ?,
                success_rate = ?
            WHERE id = ?
        ''', (
            stats['total_cycles'],
            stats['total_alerts'],
            stats['total_predictions'],
            stats['total_notifications'],
            stats['avg_cycle_duration'],
            stats['success_rate'],
            session_id
        ))
        
        conn.commit()
        conn.close()
        
    def run_analytics_module(self, module):
        """Run a single analytics module"""
        try:
            start_time = time.time()
            cmd = [sys.executable, module['script']] + module['args']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            duration = time.time() - start_time
            
            if result.returncode == 0:
                # Parse output for opportunities
                opportunities = self.parse_module_output(result.stdout, module['name'])
                
                return {
                    "success": True,
                    "duration": duration,
                    "output": result.stdout,
                    "opportunities": opportunities,
                    "items_found": len(opportunities),
                    "alerts_generated": len([o for o in opportunities if o.get('is_alert', False)])
                }
            else:
                return {
                    "success": False,
                    "duration": duration,
                    "error": result.stderr,
                    "opportunities": [],
                    "items_found": 0,
                    "alerts_generated": 0
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "duration": 120,
                "error": "Timeout",
                "opportunities": [],
                "items_found": 0,
                "alerts_generated": 0
            }
        except Exception as e:
            return {
                "success": False,
                "duration": 0,
                "error": str(e),
                "opportunities": [],
                "items_found": 0,
                "alerts_generated": 0
            }
            
    def parse_module_output(self, output, module_name):
        """Parse module output to extract opportunities"""
        opportunities = []
        lines = output.split('\n')
        
        current_item = {}
        
        for line in lines:
            line = line.strip()
            
            # Look for key patterns
            if "Found" in line and "items" in line:
                # Extract item count
                continue
                
            # Look for specific opportunity indicators
            if any(indicator in line for indicator in ["→ $0", "Save", "NO BIDS", "ALERT"]):
                # This looks like an opportunity
                opportunity = {
                    "source_module": module_name,
                    "raw_line": line,
                    "is_alert": any(alert_word in line for alert_word in ["ALERT", "CRITICAL", "HIGH"]),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Try to extract basic info
                if "→" in line:
                    parts = line.split("→")
                    if len(parts) >= 2:
                        opportunity["product_info"] = parts[0].strip()
                        opportunity["price_info"] = parts[1].strip()
                        
                # Extract savings if present
                if "Save" in line:
                    import re
                    savings_match = re.search(r'Save \$?([\d,]+\.?\d*)', line)
                    if savings_match:
                        opportunity["savings"] = float(savings_match.group(1).replace(',', ''))
                        
                opportunities.append(opportunity)
                
        return opportunities
        
    def process_opportunities_with_ml(self, opportunities):
        """Process opportunities with ML predictions"""
        if not self.predictor:
            return opportunities
            
        enhanced_opportunities = []
        
        for opp in opportunities:
            try:
                # Create item data for prediction
                item_data = self.extract_item_data_from_opportunity(opp)
                
                if item_data:
                    # Get ML prediction
                    prediction = self.predictor.predict_item(item_data)
                    
                    # Enhance opportunity with prediction
                    opp['ml_prediction'] = prediction
                    opp['predicted_winning_bid'] = prediction['predicted_winning_bid']
                    opp['confidence_score'] = prediction['confidence_score']
                    opp['suggested_bid_min'] = prediction['suggested_bid_min']
                    opp['suggested_bid_max'] = prediction['suggested_bid_max']
                    
                enhanced_opportunities.append(opp)
                
            except Exception as e:
                print(f"Error processing opportunity with ML: {e}")
                enhanced_opportunities.append(opp)
                
        return enhanced_opportunities
        
    def extract_item_data_from_opportunity(self, opportunity):
        """Extract item data from opportunity for ML prediction"""
        # This is a simplified extraction - in practice, you'd parse more carefully
        try:
            item_data = {
                "lot_id": "UNKNOWN",
                "product_name": opportunity.get("product_info", "Unknown Product"),
                "category": "Electronics",  # Default
                "location": "Rock Hill",    # Default
                "retail_price": 1000,       # Default
                "instant_win_price": 500,   # Default
                "discount_percent": 50      # Default
            }
            
            # Try to extract better data from raw_line
            raw_line = opportunity.get("raw_line", "")
            
            # Extract prices if present
            import re
            price_matches = re.findall(r'\$?([\d,]+\.?\d*)', raw_line)
            if len(price_matches) >= 2:
                item_data["retail_price"] = float(price_matches[0].replace(',', ''))
                item_data["instant_win_price"] = float(price_matches[1].replace(',', ''))
                
            # Calculate discount
            if item_data["retail_price"] > 0:
                discount = ((item_data["retail_price"] - item_data["instant_win_price"]) / item_data["retail_price"]) * 100
                item_data["discount_percent"] = discount
                
            return item_data
            
        except Exception as e:
            print(f"Error extracting item data: {e}")
            return None
            
    def send_enhanced_notifications(self, opportunities):
        """Send notifications for high-priority opportunities"""
        if not self.notifier:
            return 0
            
        notifications_sent = 0
        
        for opp in opportunities:
            try:
                # Determine if this opportunity warrants a notification
                if self.should_notify(opp):
                    alert_data = self.create_alert_from_opportunity(opp)
                    
                    if self.notifier.send_notification(alert_data):
                        notifications_sent += 1
                        
                        # Log to database
                        self.log_opportunity_alert(opp, alert_data)
                        
            except Exception as e:
                print(f"Error sending notification: {e}")
                
        return notifications_sent
        
    def should_notify(self, opportunity):
        """Determine if opportunity should trigger notification"""
        # High priority alerts
        if opportunity.get("is_alert", False):
            return True
            
        # High savings
        if opportunity.get("savings", 0) > 1000:
            return True
            
        # High confidence ML predictions
        if opportunity.get("confidence_score", 0) > 0.8:
            return True
            
        # Pricing errors (very high discounts)
        raw_line = opportunity.get("raw_line", "")
        if "→ $0" in raw_line:
            return True
            
        return False
        
    def create_alert_from_opportunity(self, opportunity):
        """Create alert data from opportunity"""
        raw_line = opportunity.get("raw_line", "")
        
        # Determine priority
        if "→ $0" in raw_line or "CRITICAL" in raw_line:
            priority = "CRITICAL"
        elif opportunity.get("savings", 0) > 1000 or "HIGH" in raw_line:
            priority = "HIGH"
        else:
            priority = "MEDIUM"
            
        # Extract basic info
        product_name = opportunity.get("product_info", "Unknown Product")
        if not product_name or product_name == "Unknown Product":
            # Try to extract from raw line
            if "Apple" in raw_line:
                product_name = "Apple Product"
            elif "Sony" in raw_line:
                product_name = "Sony Product"
            else:
                product_name = "Auction Item"
                
        alert_data = {
            "type": opportunity.get("source_module", "UNKNOWN"),
            "priority": priority,
            "product_name": product_name,
            "retail_price": 1000,  # Default
            "instant_win_price": 500,  # Default
            "discount_percent": 50,  # Default
            "location": "Rock Hill",  # Default
            "lot_id": "UNKNOWN",
            "savings_amount": opportunity.get("savings", 500)
        }
        
        # Use ML prediction data if available
        if "ml_prediction" in opportunity:
            pred = opportunity["ml_prediction"]
            alert_data.update({
                "predicted_winning_bid": pred["predicted_winning_bid"],
                "confidence_score": pred["confidence_score"],
                "suggested_bid_min": pred["suggested_bid_min"],
                "suggested_bid_max": pred["suggested_bid_max"]
            })
            
        return alert_data
        
    def log_opportunity_alert(self, opportunity, alert_data):
        """Log opportunity alert to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO opportunity_alerts 
                (lot_id, product_name, alert_type, priority, retail_price,
                 instant_win_price, discount_percent, predicted_winning_bid,
                 confidence_score, suggested_bid_min, suggested_bid_max,
                 location, source_module, notification_sent)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_data.get("lot_id", "UNKNOWN"),
                alert_data.get("product_name", "Unknown"),
                alert_data.get("type", "UNKNOWN"),
                alert_data.get("priority", "MEDIUM"),
                alert_data.get("retail_price", 0),
                alert_data.get("instant_win_price", 0),
                alert_data.get("discount_percent", 0),
                alert_data.get("predicted_winning_bid", 0),
                alert_data.get("confidence_score", 0),
                alert_data.get("suggested_bid_min", 0),
                alert_data.get("suggested_bid_max", 0),
                alert_data.get("location", "Unknown"),
                opportunity.get("source_module", "Unknown"),
                1
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error logging opportunity alert: {e}")
        finally:
            conn.close()
            
    def run_monitoring_cycle(self, session_id, cycle_number):
        """Run one complete enhanced monitoring cycle"""
        print(f"\n🚀 [{datetime.now().strftime('%H:%M:%S')}] Enhanced Monitoring Cycle #{cycle_number}")
        print("="*80)
        
        cycle_start = time.time()
        total_opportunities = []
        total_alerts = 0
        total_predictions = 0
        total_notifications = 0
        
        # Run each analytics module
        for module in self.analytics_modules:
            print(f"   🔍 Running {module['name']}...")
            
            result = self.run_analytics_module(module)
            
            if result['success']:
                opportunities = result['opportunities']
                
                # Process with ML if available
                if self.predictor and opportunities:
                    print(f"   🤖 Processing {len(opportunities)} opportunities with ML...")
                    opportunities = self.process_opportunities_with_ml(opportunities)
                    total_predictions += len(opportunities)
                
                total_opportunities.extend(opportunities)
                total_alerts += result['alerts_generated']
                
                print(f"   ✅ {module['name']}: {result['items_found']} items, {result['alerts_generated']} alerts, {result['duration']:.1f}s")
                
                # Log cycle result
                self.log_cycle_result(session_id, cycle_number, module['name'], result, len(opportunities))
                
            else:
                print(f"   ❌ {module['name']}: Failed - {result['error']}")
                self.log_cycle_result(session_id, cycle_number, module['name'], result, 0)
                
        # Send notifications for high-priority opportunities
        if total_opportunities:
            print(f"   📱 Processing {len(total_opportunities)} opportunities for notifications...")
            total_notifications = self.send_enhanced_notifications(total_opportunities)
            
        cycle_duration = time.time() - cycle_start
        
        print(f"\n🚀 Cycle #{cycle_number} Complete:")
        print(f"   📊 {len(total_opportunities)} opportunities found")
        print(f"   🚨 {total_alerts} alerts generated")
        print(f"   🤖 {total_predictions} ML predictions made")
        print(f"   📱 {total_notifications} notifications sent")
        print(f"   ⏱️  {cycle_duration:.1f}s total duration")
        
        return {
            "opportunities": len(total_opportunities),
            "alerts": total_alerts,
            "predictions": total_predictions,
            "notifications": total_notifications,
            "duration": cycle_duration
        }
        
    def log_cycle_result(self, session_id, cycle_number, module_name, result, opportunities):
        """Log individual cycle result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO cycle_results 
                (session_id, cycle_number, module_name, execution_time,
                 items_found, alerts_generated, predictions_made,
                 notifications_sent, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                cycle_number,
                module_name,
                result['duration'],
                result['items_found'],
                result['alerts_generated'],
                opportunities,  # predictions made for this module
                0,  # notifications sent per module (calculated separately)
                "SUCCESS" if result['success'] else "FAILED"
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error logging cycle result: {e}")
        finally:
            conn.close()
            
    def run_continuous_enhanced_monitoring(self):
        """Run continuous enhanced monitoring"""
        print("🚀 ENHANCED CONTINUOUS MONITOR STARTED")
        print(f"⏱️  Monitoring interval: {self.interval//60} minutes")
        print(f"🤖 ML Predictions: {'Enabled' if self.predictor else 'Disabled'}")
        print(f"📱 Notifications: {'Enabled' if self.notifier else 'Disabled'}")
        print(f"📊 Database: {self.db_path}")
        print("🔄 Press Ctrl+C to stop\n")
        
        session_id = self.start_monitoring_session()
        cycle_count = 0
        session_stats = {
            'total_cycles': 0,
            'total_alerts': 0,
            'total_predictions': 0,
            'total_notifications': 0,
            'total_duration': 0,
            'success_rate': 0
        }
        
        try:
            while True:
                cycle_count += 1
                
                # Run monitoring cycle
                cycle_results = self.run_monitoring_cycle(session_id, cycle_count)
                
                # Update session stats
                session_stats['total_cycles'] = cycle_count
                session_stats['total_alerts'] += cycle_results['alerts']
                session_stats['total_predictions'] += cycle_results['predictions']
                session_stats['total_notifications'] += cycle_results['notifications']
                session_stats['total_duration'] += cycle_results['duration']
                session_stats['avg_cycle_duration'] = session_stats['total_duration'] / cycle_count
                session_stats['success_rate'] = 100.0  # Simplified
                
                # Show session stats every 5 cycles
                if cycle_count % 5 == 0:
                    print(f"\n📊 SESSION STATS (After {cycle_count} cycles):")
                    print(f"   Total Alerts: {session_stats['total_alerts']}")
                    print(f"   Total Predictions: {session_stats['total_predictions']}")
                    print(f"   Total Notifications: {session_stats['total_notifications']}")
                    print(f"   Avg Cycle Duration: {session_stats['avg_cycle_duration']:.1f}s")
                
                # Wait for next cycle
                print(f"\n⏳ Waiting {self.interval//60} minutes until next scan...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Enhanced monitoring stopped after {cycle_count} cycles")
            
            # End session
            self.end_monitoring_session(session_id, session_stats)
            
            # Final stats
            print(f"\n📊 FINAL SESSION STATS:")
            print(f"   Total Cycles: {session_stats['total_cycles']}")
            print(f"   Total Alerts: {session_stats['total_alerts']}")
            print(f"   Total Predictions: {session_stats['total_predictions']}")
            print(f"   Total Notifications: {session_stats['total_notifications']}")
            print(f"   Average Cycle Duration: {session_stats['avg_cycle_duration']:.1f}s")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="🚀 Enhanced Continuous Monitor")
    parser.add_argument("--interval", type=int, default=5, 
                       help="Monitoring interval in minutes (default: 5)")
    parser.add_argument("--test", action="store_true", 
                       help="Run one test cycle")
    
    args = parser.parse_args()
    
    monitor = EnhancedContinuousMonitor(interval_minutes=args.interval)
    
    if args.test:
        print("🧪 Running enhanced test cycle...")
        session_id = monitor.start_monitoring_session()
        results = monitor.run_monitoring_cycle(session_id, 1)
        monitor.end_monitoring_session(session_id, {
            'total_cycles': 1,
            'total_alerts': results['alerts'],
            'total_predictions': results['predictions'],
            'total_notifications': results['notifications'],
            'avg_cycle_duration': results['duration'],
            'success_rate': 100.0
        })
        print(f"✅ Enhanced test complete!")
        
    else:
        monitor.run_continuous_enhanced_monitoring()

if __name__ == "__main__":
    main() 