#!/usr/bin/env python3
"""
🚨 SMART ALERTS - Intelligent Notification System
Send alerts via multiple channels for high-priority auction opportunities
"""

import json
import sqlite3
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse

class SmartAlerts:
    def __init__(self):
        self.db_path = "smart_alerts.db"
        self.config_path = "alert_config.json"
        self.setup_database()
        self.load_config()
        
    def setup_database(self):
        """Setup database for alert tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT UNIQUE,
                rule_type TEXT,
                conditions TEXT,
                priority TEXT,
                channels TEXT,
                enabled INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sent_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                rule_name TEXT,
                alert_type TEXT,
                priority TEXT,
                message TEXT,
                channels_sent TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 1
            )
        ''')
        
        # Insert default alert rules
        default_rules = [
            ("pricing_error", "PRICING", '{"discount": 100, "min_value": 100}', "CRITICAL", "console,webhook", 1),
            ("mega_discount", "DISCOUNT", '{"discount": 80, "min_value": 200}', "HIGH", "console,email", 1),
            ("apple_deals", "BRAND", '{"brands": ["apple", "macbook", "iphone"], "discount": 30}', "MEDIUM", "console", 1),
            ("no_bid_high_value", "NO_BID", '{"min_value": 1000}', "HIGH", "console,webhook", 1),
            ("ending_soon", "TIMING", '{"hours": 2, "min_value": 500}', "MEDIUM", "console", 1)
        ]
        
        for rule in default_rules:
            cursor.execute('''
                INSERT OR IGNORE INTO alert_rules 
                (rule_name, rule_type, conditions, priority, channels, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', rule)
        
        conn.commit()
        conn.close()
        
    def load_config(self):
        """Load alert configuration"""
        try:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            # Create default config
            self.config = {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "",
                    "to_emails": []
                },
                "webhook": {
                    "enabled": False,
                    "url": "",
                    "headers": {"Content-Type": "application/json"}
                },
                "console": {
                    "enabled": True,
                    "show_icons": True,
                    "show_timestamp": True
                }
            }
            self.save_config()
            
    def save_config(self):
        """Save alert configuration"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
            
    def check_alert_rules(self, item_data):
        """Check if item matches any alert rules"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM alert_rules WHERE enabled = 1')
        rules = cursor.fetchall()
        conn.close()
        
        triggered_alerts = []
        
        for rule in rules:
            rule_id, rule_name, rule_type, conditions_str, priority, channels, enabled, created_at = rule
            
            try:
                conditions = json.loads(conditions_str)
                
                if self.evaluate_rule(item_data, rule_type, conditions):
                    triggered_alerts.append({
                        "rule_name": rule_name,
                        "rule_type": rule_type,
                        "priority": priority,
                        "channels": channels.split(','),
                        "conditions": conditions,
                        "item": item_data
                    })
                    
            except Exception as e:
                print(f"Error evaluating rule {rule_name}: {e}")
                
        return triggered_alerts
        
    def evaluate_rule(self, item, rule_type, conditions):
        """Evaluate if item matches rule conditions"""
        try:
            if rule_type == "PRICING":
                # Check for pricing errors (100% discount)
                discount = conditions.get("discount", 100)
                min_value = conditions.get("min_value", 0)
                
                item_discount = item.get("discount_percent", 0)
                item_value = item.get("retail_price", 0)
                
                return item_discount >= discount and item_value >= min_value
                
            elif rule_type == "DISCOUNT":
                # Check for high discounts
                discount = conditions.get("discount", 50)
                min_value = conditions.get("min_value", 100)
                
                item_discount = item.get("discount_percent", 0)
                item_value = item.get("retail_price", 0)
                
                return item_discount >= discount and item_value >= min_value
                
            elif rule_type == "BRAND":
                # Check for specific brands
                brands = conditions.get("brands", [])
                min_discount = conditions.get("discount", 0)
                
                product_name = item.get("product_name", "").lower()
                item_discount = item.get("discount_percent", 0)
                
                brand_match = any(brand.lower() in product_name for brand in brands)
                return brand_match and item_discount >= min_discount
                
            elif rule_type == "NO_BID":
                # Check for no-bid high-value items
                min_value = conditions.get("min_value", 500)
                
                has_bids = item.get("current_bid", 0) > 0
                item_value = item.get("retail_price", 0)
                
                return not has_bids and item_value >= min_value
                
            elif rule_type == "TIMING":
                # Check for items ending soon
                hours = conditions.get("hours", 24)
                min_value = conditions.get("min_value", 100)
                
                # This would need closing time parsing
                # For now, return False
                return False
                
        except Exception as e:
            print(f"Error in rule evaluation: {e}")
            
        return False
        
    def send_console_alert(self, alert):
        """Send console alert"""
        if not self.config["console"]["enabled"]:
            return False
            
        priority_icons = {
            "CRITICAL": "🚨",
            "HIGH": "⚡",
            "MEDIUM": "📢",
            "LOW": "ℹ️"
        }
        
        icon = priority_icons.get(alert["priority"], "📢")
        timestamp = datetime.now().strftime("%H:%M:%S") if self.config["console"]["show_timestamp"] else ""
        
        print(f"\n{icon} [{timestamp}] {alert['priority']} ALERT - {alert['rule_name'].upper()}")
        print(f"   📦 {alert['item']['product_name']}")
        print(f"   💰 ${alert['item']['retail_price']:,.0f} → ${alert['item']['instant_win_price']:,.0f}")
        print(f"   📍 {alert['item']['location']}")
        print(f"   💸 {alert['item']['discount_percent']:.1f}% discount")
        print(f"   🔗 Lot: {alert['item']['lot_id']}")
        
        return True
        
    def send_email_alert(self, alert):
        """Send email alert"""
        if not self.config["email"]["enabled"]:
            return False
            
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config["email"]["from_email"]
            msg['To'] = ", ".join(self.config["email"]["to_emails"])
            msg['Subject'] = f"🚨 {alert['priority']} Auction Alert - {alert['rule_name']}"
            
            body = f"""
            New auction opportunity detected!
            
            Product: {alert['item']['product_name']}
            Retail Price: ${alert['item']['retail_price']:,.2f}
            Instant Win: ${alert['item']['instant_win_price']:,.2f}
            Discount: {alert['item']['discount_percent']:.1f}%
            Location: {alert['item']['location']}
            Lot ID: {alert['item']['lot_id']}
            
            Alert Rule: {alert['rule_name']} ({alert['priority']} priority)
            
            Act fast - this opportunity won't last long!
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config["email"]["smtp_server"], self.config["email"]["smtp_port"])
            server.starttls()
            server.login(self.config["email"]["username"], self.config["email"]["password"])
            
            text = msg.as_string()
            server.sendmail(self.config["email"]["from_email"], self.config["email"]["to_emails"], text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
            
    def send_webhook_alert(self, alert):
        """Send webhook alert"""
        if not self.config["webhook"]["enabled"]:
            return False
            
        try:
            payload = {
                "alert_type": alert["rule_name"],
                "priority": alert["priority"],
                "timestamp": datetime.now().isoformat(),
                "item": alert["item"],
                "message": f"🚨 {alert['priority']} Alert: {alert['item']['product_name']} - {alert['item']['discount_percent']:.1f}% off"
            }
            
            response = requests.post(
                self.config["webhook"]["url"],
                json=payload,
                headers=self.config["webhook"]["headers"],
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Error sending webhook: {e}")
            return False
            
    def send_alert(self, alert):
        """Send alert via configured channels"""
        channels_sent = []
        
        for channel in alert["channels"]:
            channel = channel.strip()
            success = False
            
            if channel == "console":
                success = self.send_console_alert(alert)
            elif channel == "email":
                success = self.send_email_alert(alert)
            elif channel == "webhook":
                success = self.send_webhook_alert(alert)
                
            if success:
                channels_sent.append(channel)
                
        # Log alert
        self.log_alert(alert, channels_sent)
        
        return len(channels_sent) > 0
        
    def log_alert(self, alert, channels_sent):
        """Log sent alert to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO sent_alerts 
                (lot_id, rule_name, alert_type, priority, message, channels_sent, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert["item"]["lot_id"],
                alert["rule_name"],
                alert["rule_type"],
                alert["priority"],
                f"{alert['item']['product_name']} - {alert['item']['discount_percent']:.1f}% off",
                ",".join(channels_sent),
                1 if channels_sent else 0
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"Error logging alert: {e}")
        finally:
            conn.close()
            
    def process_items(self, items):
        """Process list of items and send alerts"""
        total_alerts = 0
        
        for item in items:
            alerts = self.check_alert_rules(item)
            
            for alert in alerts:
                if self.send_alert(alert):
                    total_alerts += 1
                    
        return total_alerts
        
    def get_alert_stats(self, days=7):
        """Get alert statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_alerts,
                SUM(success) as successful_alerts,
                COUNT(DISTINCT rule_name) as unique_rules,
                COUNT(DISTINCT lot_id) as unique_items
            FROM sent_alerts 
            WHERE sent_at > datetime('now', '-{} days')
        '''.format(days))
        
        stats = cursor.fetchone()
        conn.close()
        
        if stats and stats[0] > 0:
            return {
                "total_alerts": stats[0],
                "successful_alerts": stats[1],
                "success_rate": (stats[1] / stats[0] * 100) if stats[0] > 0 else 0,
                "unique_rules": stats[2],
                "unique_items": stats[3]
            }
        else:
            return {"total_alerts": 0, "successful_alerts": 0, "success_rate": 0,
                   "unique_rules": 0, "unique_items": 0}
                   
    def test_alerts(self):
        """Test alert system with sample data"""
        test_items = [
            {
                "lot_id": "TEST001",
                "product_name": "Apple MacBook Pro 16-inch",
                "retail_price": 2499.99,
                "instant_win_price": 0,
                "discount_percent": 100,
                "location": "Rock Hill",
                "current_bid": 0
            },
            {
                "lot_id": "TEST002", 
                "product_name": "Sony WH-1000XM5 Headphones",
                "retail_price": 399.99,
                "instant_win_price": 80,
                "discount_percent": 80,
                "location": "Greenville",
                "current_bid": 0
            }
        ]
        
        print("🧪 Testing alert system...")
        alerts_sent = self.process_items(test_items)
        print(f"✅ Test complete: {alerts_sent} alerts sent")

def main():
    parser = argparse.ArgumentParser(description="🚨 Smart Alerts System")
    parser.add_argument("--test", action="store_true", help="Test alert system")
    parser.add_argument("--stats", action="store_true", help="Show alert statistics")
    parser.add_argument("--config", action="store_true", help="Show configuration")
    
    args = parser.parse_args()
    
    alerts = SmartAlerts()
    
    if args.test:
        alerts.test_alerts()
    elif args.stats:
        stats = alerts.get_alert_stats()
        print("📊 ALERT STATISTICS (Last 7 Days)")
        print("="*40)
        print(f"Total Alerts: {stats['total_alerts']}")
        print(f"Successful: {stats['successful_alerts']}")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        print(f"Unique Rules: {stats['unique_rules']}")
        print(f"Unique Items: {stats['unique_items']}")
    elif args.config:
        print("⚙️ ALERT CONFIGURATION")
        print("="*40)
        print(json.dumps(alerts.config, indent=2))
    else:
        print("🚨 Smart Alerts System")
        print("Use --test to test alerts, --stats for statistics, --config for configuration")

if __name__ == "__main__":
    main() 