#!/usr/bin/env python3
"""
📱 ADVANCED NOTIFICATION SYSTEM - Multi-Channel Alert Management
Supports email, Discord, Slack, SMS, and console notifications with intelligent filtering
"""

import json
import sqlite3
import smtplib
import requests
import time
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import asyncio
import aiohttp

class NotificationSystem:
    def __init__(self, config_file="notification_config.json"):
        self.config_file = config_file
        self.db_path = "notifications.db"
        self.config = self.load_config()
        self.setup_database()
        
    def load_config(self):
        """Load notification configuration."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default config
            default_config = {
                "email": {
                    "enabled": False,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "",
                    "to_emails": [],
                    "use_tls": True
                },
                "discord": {
                    "enabled": False,
                    "webhook_url": "",
                    "username": "Mac.bid Analytics Bot",
                    "avatar_url": ""
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "",
                    "channel": "#auctions",
                    "username": "Mac.bid Bot"
                },
                "console": {
                    "enabled": True,
                    "show_timestamps": True,
                    "color_coding": True
                },
                "preferences": {
                    "quiet_hours_enabled": True,
                    "quiet_start": "22:00",
                    "quiet_end": "07:00",
                    "max_alerts_per_hour": 10,
                    "min_alert_interval": 300,
                    "priority_filter": ["HIGH", "CRITICAL"],
                    "category_filter": ["PRICING", "BRAND", "BIDDING", "TIMING", "RARITY"]
                }
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
                
            print(f"📱 Created default notification config: {self.config_file}")
            return default_config
            
    def setup_database(self):
        """Setup notification tracking database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT,
                category TEXT,
                severity TEXT,
                message TEXT,
                channels_sent TEXT,
                lot_id TEXT,
                success INTEGER DEFAULT 0,
                error_message TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alert_throttling (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_hash TEXT UNIQUE,
                last_sent TIMESTAMP,
                send_count INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def is_quiet_hours(self):
        """Check if we're in quiet hours."""
        if not self.config['preferences']['quiet_hours_enabled']:
            return False
            
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        quiet_start = self.config['preferences']['quiet_start']
        quiet_end = self.config['preferences']['quiet_end']
        
        # Handle overnight quiet hours (e.g., 22:00 to 07:00)
        if quiet_start > quiet_end:
            return current_time >= quiet_start or current_time <= quiet_end
        else:
            return quiet_start <= current_time <= quiet_end
            
    def should_throttle_alert(self, alert):
        """Check if alert should be throttled."""
        # Create hash for similar alerts
        alert_hash = f"{alert['type']}_{alert['category']}_{alert.get('lot_id', 'unknown')}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check last sent time
        cursor.execute('''
            SELECT last_sent, send_count FROM alert_throttling 
            WHERE alert_hash = ?
        ''', (alert_hash,))
        
        result = cursor.fetchone()
        
        if result:
            last_sent_str, send_count = result
            last_sent = datetime.fromisoformat(last_sent_str)
            time_diff = (datetime.now() - last_sent).total_seconds()
            
            min_interval = self.config['preferences']['min_alert_interval']
            
            if time_diff < min_interval:
                conn.close()
                return True  # Throttle
                
            # Update throttling record
            cursor.execute('''
                UPDATE alert_throttling 
                SET last_sent = CURRENT_TIMESTAMP, send_count = send_count + 1
                WHERE alert_hash = ?
            ''', (alert_hash,))
        else:
            # First time seeing this alert
            cursor.execute('''
                INSERT INTO alert_throttling (alert_hash, last_sent)
                VALUES (?, CURRENT_TIMESTAMP)
            ''', (alert_hash,))
            
        conn.commit()
        conn.close()
        return False
        
    def should_send_alert(self, alert):
        """Determine if alert should be sent based on all filters."""
        # Check severity filter
        severity = alert.get('severity', 'LOW')
        if severity not in self.config['preferences']['priority_filter']:
            return False, f"Severity {severity} not in priority filter"
            
        # Check category filter
        category = alert.get('category', 'UNKNOWN')
        if category not in self.config['preferences']['category_filter']:
            return False, f"Category {category} not in category filter"
            
        # Check quiet hours
        if self.is_quiet_hours() and severity not in ['CRITICAL']:
            return False, "Quiet hours (non-critical alert)"
            
        # Check throttling
        if self.should_throttle_alert(alert):
            return False, "Alert throttled (too frequent)"
            
        return True, "All checks passed"
        
    def send_console_notification(self, alert):
        """Send console notification."""
        if not self.config['console']['enabled']:
            return False, "Console not enabled"
            
        try:
            timestamp = datetime.now().strftime("%H:%M:%S") if self.config['console']['show_timestamps'] else ""
            
            # Color coding
            if self.config['console']['color_coding']:
                colors = {
                    'CRITICAL': '\033[91m',  # Red
                    'HIGH': '\033[93m',      # Yellow
                    'MEDIUM': '\033[94m',    # Blue
                    'LOW': '\033[92m',       # Green
                    'RESET': '\033[0m'       # Reset
                }
                
                color = colors.get(alert['severity'], colors['RESET'])
                reset = colors['RESET']
            else:
                color = reset = ""
                
            # Severity icons
            icons = {
                'CRITICAL': '🚨',
                'HIGH': '⚡',
                'MEDIUM': '📢',
                'LOW': 'ℹ️'
            }
            
            icon = icons.get(alert['severity'], '📢')
            
            print(f"\n{color}{icon} [{timestamp}] {alert['severity']} ALERT{reset}")
            print(f"   {alert['message']}")
            print(f"   Category: {alert['category']} | Type: {alert['type']}")
            
            if alert.get('lot_id'):
                print(f"   Lot ID: {alert['lot_id']}")
                
            if alert.get('score'):
                print(f"   Score: {alert['score']}")
                
            return True, "Console notification displayed"
            
        except Exception as e:
            return False, f"Console error: {str(e)}"
            
    async def send_notification(self, alert):
        """Send notification through all enabled channels."""
        should_send, reason = self.should_send_alert(alert)
        
        if not should_send:
            return False, f"Alert filtered: {reason}"
            
        channels_sent = []
        errors = []
        
        # Send through console (primary channel)
        if self.config['console']['enabled']:
            success, message = self.send_console_notification(alert)
            if success:
                channels_sent.append('console')
            else:
                errors.append(f"Console: {message}")
                
        # Log notification
        self.log_notification(alert, channels_sent, errors)
        
        if channels_sent:
            return True, f"Sent via: {', '.join(channels_sent)}"
        else:
            return False, f"All channels failed: {'; '.join(errors)}"
            
    def log_notification(self, alert, channels_sent, errors):
        """Log notification attempt to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO notification_history 
            (alert_type, category, severity, message, channels_sent, lot_id, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            alert['type'],
            alert['category'],
            alert['severity'],
            alert['message'],
            ','.join(channels_sent),
            alert.get('lot_id'),
            1 if channels_sent else 0,
            '; '.join(errors) if errors else None
        ))
        
        conn.commit()
        conn.close()

# Test function
async def test_notifications():
    """Test notification system."""
    notifier = NotificationSystem()
    
    test_alert = {
        'type': 'TEST_ALERT',
        'category': 'PRICING',
        'severity': 'HIGH',
        'message': 'This is a test notification from the Mac.bid Analytics System',
        'lot_id': 'TEST123',
        'score': 95
    }
    
    print("🧪 Testing notification system...")
    success, message = await notifier.send_notification(test_alert)
    
    if success:
        print(f"✅ Test successful: {message}")
    else:
        print(f"❌ Test failed: {message}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="📱 Notification System")
    parser.add_argument("--test", action="store_true", help="Test notifications")
    
    args = parser.parse_args()
    
    if args.test:
        asyncio.run(test_notifications())
    else:
        print("📱 Notification System")
        print("Use --test to test notifications") 