#!/usr/bin/env python3
"""
🔄 CONTINUOUS MONITOR - Real-time Auction Intelligence
Runs all analytics continuously and sends alerts for high-priority opportunities
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from collections import defaultdict
import subprocess
import sys

class ContinuousMonitor:
    def __init__(self, interval_minutes=5):
        self.interval = interval_minutes * 60  # Convert to seconds
        self.db_path = "continuous_monitor.db"
        self.last_alerts = {}
        self.setup_database()
        
    def setup_database(self):
        """Setup database for tracking alerts and monitoring history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                scan_type TEXT,
                items_found INTEGER,
                alerts_sent INTEGER,
                scan_duration REAL,
                status TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                lot_id TEXT,
                alert_type TEXT,
                priority TEXT,
                product_name TEXT,
                retail_price REAL,
                instant_win_price REAL,
                discount_percent REAL,
                location TEXT,
                message TEXT,
                sent_successfully INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def log_scan(self, scan_type, items_found, alerts_sent, duration, status="SUCCESS"):
        """Log monitoring scan results"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO monitoring_history 
            (scan_type, items_found, alerts_sent, scan_duration, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (scan_type, items_found, alerts_sent, duration, status))
        
        conn.commit()
        conn.close()
        
    def log_alert(self, lot_id, alert_type, priority, product_name, retail_price, 
                  instant_win_price, discount_percent, location, message):
        """Log alert details"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO alert_history 
            (lot_id, alert_type, priority, product_name, retail_price, 
             instant_win_price, discount_percent, location, message, sent_successfully)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (lot_id, alert_type, priority, product_name, retail_price,
              instant_win_price, discount_percent, location, message, 1))
        
        conn.commit()
        conn.close()
        
    def run_scraper(self, script_name, args=[]):
        """Run a scraper and capture output"""
        try:
            start_time = time.time()
            cmd = [sys.executable, script_name] + args
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return {"success": True, "output": result.stdout, "duration": duration}
            else:
                return {"success": False, "error": result.stderr, "duration": duration}
                
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timeout", "duration": 120}
        except Exception as e:
            return {"success": False, "error": str(e), "duration": 0}
            
    def analyze_results(self, output, scraper_type):
        """Analyze scraper output for high-priority alerts"""
        alerts = []
        
        try:
            # Look for key indicators in output
            lines = output.split('\n')
            
            for line in lines:
                # Check for $0 items (pricing errors)
                if "→ $0" in line and "Save" not in line:
                    alerts.append({
                        "type": "PRICING_ERROR",
                        "priority": "CRITICAL",
                        "message": f"🚨 PRICING ERROR: {line.strip()}",
                        "scraper": scraper_type
                    })
                
                # Check for 80%+ discounts
                elif "80%" in line and "Save" in line:
                    alerts.append({
                        "type": "MEGA_DISCOUNT",
                        "priority": "HIGH",
                        "message": f"💎 MEGA DISCOUNT: {line.strip()}",
                        "scraper": scraper_type
                    })
                
                # Check for no-bid high-value items
                elif "NO BIDS" in line and "$" in line:
                    alerts.append({
                        "type": "NO_BID_OPPORTUNITY",
                        "priority": "HIGH",
                        "message": f"🎯 NO BID OPPORTUNITY: {line.strip()}",
                        "scraper": scraper_type
                    })
                
                # Check for Apple products
                elif any(brand in line.lower() for brand in ["apple", "macbook", "iphone", "ipad"]):
                    if "Save" in line or "→" in line:
                        alerts.append({
                            "type": "PREMIUM_BRAND",
                            "priority": "MEDIUM",
                            "message": f"🍎 APPLE DEAL: {line.strip()}",
                            "scraper": scraper_type
                        })
                        
        except Exception as e:
            print(f"Error analyzing results: {e}")
            
        return alerts
        
    def send_alert(self, alert):
        """Send alert (console for now, can be extended to email/SMS)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        priority_icon = {"CRITICAL": "🚨", "HIGH": "⚡", "MEDIUM": "📢", "LOW": "ℹ️"}
        
        print(f"\n{priority_icon.get(alert['priority'], '📢')} [{timestamp}] {alert['priority']} ALERT")
        print(f"   {alert['message']}")
        print(f"   Source: {alert['scraper']}")
        
        # Log to database
        try:
            # Extract basic info for logging (simplified)
            self.log_alert(
                lot_id="unknown",
                alert_type=alert['type'],
                priority=alert['priority'],
                product_name="extracted_from_message",
                retail_price=0,
                instant_win_price=0,
                discount_percent=0,
                location="unknown",
                message=alert['message']
            )
        except Exception as e:
            print(f"Error logging alert: {e}")
            
    def run_monitoring_cycle(self):
        """Run one complete monitoring cycle"""
        print(f"\n🔄 [{datetime.now().strftime('%H:%M:%S')}] Starting monitoring cycle...")
        
        # Define scrapers to run with their priorities
        scrapers = [
            {"script": "enhanced_new_arrivals.py", "args": ["--alerts-only"], "name": "Enhanced Monitor"},
            {"script": "deal_hunter.py", "args": ["--mode", "steals"], "name": "Deal Hunter"},
            {"script": "no_bid_tracker.py", "args": ["--min-value", "500"], "name": "No-Bid Tracker"},
            {"script": "price_analytics_tracker.py", "args": ["--alerts-only"], "name": "Price Analytics"},
        ]
        
        total_alerts = 0
        
        for scraper in scrapers:
            print(f"   🔍 Running {scraper['name']}...")
            
            result = self.run_scraper(scraper['script'], scraper['args'])
            
            if result['success']:
                # Analyze output for alerts
                alerts = self.analyze_results(result['output'], scraper['name'])
                
                # Send alerts
                for alert in alerts:
                    self.send_alert(alert)
                    total_alerts += 1
                
                # Log successful scan
                items_found = result['output'].count('Found') if 'Found' in result['output'] else 0
                self.log_scan(scraper['name'], items_found, len(alerts), result['duration'])
                
                print(f"   ✅ {scraper['name']}: {len(alerts)} alerts, {result['duration']:.1f}s")
                
            else:
                print(f"   ❌ {scraper['name']}: Failed - {result['error']}")
                self.log_scan(scraper['name'], 0, 0, result['duration'], "FAILED")
                
        print(f"🔄 Monitoring cycle complete: {total_alerts} total alerts")
        return total_alerts
        
    def get_monitoring_stats(self):
        """Get monitoring statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get recent stats
        cursor.execute('''
            SELECT 
                COUNT(*) as total_scans,
                SUM(items_found) as total_items,
                SUM(alerts_sent) as total_alerts,
                AVG(scan_duration) as avg_duration,
                SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) as successful_scans
            FROM monitoring_history 
            WHERE timestamp > datetime('now', '-24 hours')
        ''')
        
        stats = cursor.fetchone()
        conn.close()
        
        if stats and stats[0] > 0:
            return {
                "total_scans": stats[0],
                "total_items": stats[1] or 0,
                "total_alerts": stats[2] or 0,
                "avg_duration": stats[3] or 0,
                "success_rate": (stats[4] / stats[0]) * 100 if stats[0] > 0 else 0
            }
        else:
            return {"total_scans": 0, "total_items": 0, "total_alerts": 0, 
                   "avg_duration": 0, "success_rate": 0}
                   
    def run_continuous(self):
        """Run continuous monitoring"""
        print("🚀 CONTINUOUS MONITOR STARTED")
        print(f"⏱️  Monitoring interval: {self.interval//60} minutes")
        print(f"📊 Database: {self.db_path}")
        print("🔄 Press Ctrl+C to stop\n")
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                print(f"\n{'='*60}")
                print(f"🔄 MONITORING CYCLE #{cycle_count}")
                print(f"{'='*60}")
                
                # Run monitoring cycle
                alerts_sent = self.run_monitoring_cycle()
                
                # Show stats every 10 cycles
                if cycle_count % 10 == 0:
                    stats = self.get_monitoring_stats()
                    print(f"\n📊 24-Hour Stats:")
                    print(f"   Total Scans: {stats['total_scans']}")
                    print(f"   Total Alerts: {stats['total_alerts']}")
                    print(f"   Success Rate: {stats['success_rate']:.1f}%")
                    print(f"   Avg Duration: {stats['avg_duration']:.1f}s")
                
                # Wait for next cycle
                print(f"\n⏳ Waiting {self.interval//60} minutes until next scan...")
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            print(f"\n\n🛑 Continuous monitoring stopped after {cycle_count} cycles")
            
            # Final stats
            stats = self.get_monitoring_stats()
            print(f"\n📊 Final 24-Hour Stats:")
            print(f"   Total Scans: {stats['total_scans']}")
            print(f"   Total Alerts: {stats['total_alerts']}")
            print(f"   Success Rate: {stats['success_rate']:.1f}%")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="🔄 Continuous Auction Monitor")
    parser.add_argument("--interval", type=int, default=5, 
                       help="Monitoring interval in minutes (default: 5)")
    parser.add_argument("--stats", action="store_true", 
                       help="Show monitoring statistics")
    parser.add_argument("--test", action="store_true", 
                       help="Run one test cycle")
    
    args = parser.parse_args()
    
    monitor = ContinuousMonitor(interval_minutes=args.interval)
    
    if args.stats:
        stats = monitor.get_monitoring_stats()
        print("📊 MONITORING STATISTICS (Last 24 Hours)")
        print("="*50)
        print(f"Total Scans: {stats['total_scans']}")
        print(f"Total Items Found: {stats['total_items']}")
        print(f"Total Alerts Sent: {stats['total_alerts']}")
        print(f"Average Scan Duration: {stats['avg_duration']:.1f}s")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        
    elif args.test:
        print("🧪 Running test monitoring cycle...")
        alerts = monitor.run_monitoring_cycle()
        print(f"✅ Test complete: {alerts} alerts generated")
        
    else:
        monitor.run_continuous()

if __name__ == "__main__":
    main() 