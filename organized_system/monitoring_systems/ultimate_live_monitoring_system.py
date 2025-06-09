#!/usr/bin/env python3
"""
🎯 Ultimate Live Monitoring System for Mac.bid
Scales up monitoring, provides real-time updates, and sends alerts
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright
import re
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import logging
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('live_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltimateLiveMonitoringSystem:
    def __init__(self):
        self.load_credentials()
        self.setup_session_config()
        self.setup_database()
        self.setup_alert_config()
        
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        self.premium_brands = ['Apple', 'Sony', 'Samsung', 'Nintendo', 'Dyson', 'Bose', 'DeWalt', 'Milwaukee']
        
        # API endpoints
        self.api_base = "https://api.macdiscount.com"
        
        # Working CSS selectors from JS analysis
        self.bid_selectors = [
            ".h1.font-weight-normal.text-accent span",
            "#productInfo > div > div:nth-child(4) > div > div.font-size-sm.text-muted",
            "#productInfo > div > div:nth-child(5) > div > div.font-size-sm.text-muted",
            "span.font-size-lg:has-text('$')",
            ".current-price",
            "span[class*='text-accent']"
        ]
        
        # Monitoring configuration
        self.monitoring_active = False
        self.check_interval = 300  # 5 minutes
        self.max_lots_per_cycle = 50
        self.browser_pool_size = 3
        
    def load_credentials(self):
        """Load user credentials and email settings."""
        config_file = Path.home() / '.macbid_scraper' / 'credentials.json'
        try:
            with open(config_file, 'r') as f:
                creds = json.load(f)
                self.customer_id = creds.get('customer_id', '2710619')
                self.jwt_token = creds.get('jwt_token', '')
                self.username = creds.get('username', 'darvonmedia@gmail.com')
                
                # Email settings for alerts
                self.email_settings = creds.get('email_alerts', {
                    'enabled': True,
                    'smtp_server': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'email': self.username,
                    'password': '',  # App password needed
                    'to_email': self.username
                })
                
                logger.info(f"📧 Using account: {self.username} (ID: {self.customer_id})")
        except FileNotFoundError:
            logger.warning("⚠️ No credentials found, using defaults")
            self.customer_id = '2710619'
            self.jwt_token = ''
            self.username = 'darvonmedia@gmail.com'
            self.email_settings = {'enabled': False}
    
    def setup_session_config(self):
        """Setup HTTP session configuration."""
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Referer': 'https://mac.bid',
            'Origin': 'https://mac.bid'
        }
        
        if self.jwt_token:
            self.headers['Authorization'] = f'Bearer {self.jwt_token}'
    
    def setup_database(self):
        """Setup SQLite database for tracking lots and bid history."""
        self.db_path = 'ultimate_live_monitoring.db'
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Lots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lots (
                    lot_id TEXT PRIMARY KEY,
                    auction_id TEXT,
                    lot_number TEXT,
                    product_name TEXT,
                    retail_price REAL,
                    auction_location TEXT,
                    is_premium_brand BOOLEAN,
                    first_seen TIMESTAMP,
                    last_checked TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    alert_enabled BOOLEAN DEFAULT 1
                )
            ''')
            
            # Bid history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS bid_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lot_id TEXT,
                    current_bid REAL,
                    bid_count INTEGER,
                    timestamp TIMESTAMP,
                    source TEXT,
                    FOREIGN KEY (lot_id) REFERENCES lots (lot_id)
                )
            ''')
            
            # Alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lot_id TEXT,
                    alert_type TEXT,
                    message TEXT,
                    timestamp TIMESTAMP,
                    sent BOOLEAN DEFAULT 0,
                    FOREIGN KEY (lot_id) REFERENCES lots (lot_id)
                )
            ''')
            
            conn.commit()
            logger.info("✅ Database initialized")
    
    def setup_alert_config(self):
        """Setup alert configuration."""
        self.alert_config = {
            'bid_increase_threshold': 10.0,  # Alert if bid increases by $10+
            'new_bid_alert': True,  # Alert on first bid
            'closing_soon_hours': 24,  # Alert if closing within 24 hours
            'high_value_threshold': 500.0,  # Alert for items over $500 retail
            'discount_threshold': 70.0,  # Alert if discount > 70%
        }
    
    async def discover_lots_at_scale(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Discover lots at scale using multiple search terms and categories."""
        logger.info("🔍 Discovering lots at scale...")
        
        all_lots = []
        
        # Comprehensive search terms
        search_terms = [
            # Premium brands
            'apple', 'sony', 'samsung', 'nintendo', 'dyson', 'bose', 'dewalt', 'milwaukee',
            # Categories
            'electronics', 'gaming', 'headphones', 'laptop', 'camera', 'phone', 'tablet',
            'tools', 'vacuum', 'speaker', 'watch', 'tv', 'monitor', 'keyboard', 'mouse',
            # High-value terms
            'macbook', 'iphone', 'ipad', 'playstation', 'xbox', 'airpods', 'beats'
        ]
        
        for term in search_terms:
            try:
                url = f"{self.api_base}/search?q={term}&limit=50"
                async with session.get(url, headers=self.headers, timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        hits = data.get('hits', [])
                        
                        # Filter to SC locations and open auctions
                        sc_lots = []
                        for hit in hits:
                            location = hit.get('auction_location', '')
                            is_open = hit.get('is_open', False)
                            if any(sc_loc in location for sc_loc in self.sc_locations) and is_open:
                                # Add premium brand flag
                                product_name = hit.get('product_name', '').lower()
                                hit['is_premium_brand'] = any(brand.lower() in product_name for brand in self.premium_brands)
                                sc_lots.append(hit)
                        
                        all_lots.extend(sc_lots)
                        logger.info(f"   📍 '{term}': {len(sc_lots)} open SC lots")
                
                await asyncio.sleep(0.1)  # Fast discovery
                
            except Exception as e:
                logger.error(f"   ❌ Search error with {term}: {e}")
        
        # Remove duplicates and prioritize premium brands
        unique_lots = {}
        for lot in all_lots:
            lot_id = lot.get('lot_id')
            if lot_id:
                if lot_id not in unique_lots or lot.get('is_premium_brand', False):
                    unique_lots[lot_id] = lot
        
        # Sort by priority: premium brands first, then by retail price
        sorted_lots = sorted(
            unique_lots.values(),
            key=lambda x: (
                not x.get('is_premium_brand', False),  # Premium brands first
                -float(x.get('retail_price', 0))  # Higher retail price first
            )
        )
        
        logger.info(f"✅ Discovered {len(sorted_lots)} unique lots ({len([l for l in sorted_lots if l.get('is_premium_brand', False)])} premium)")
        return sorted_lots[:self.max_lots_per_cycle]
    
    async def scrape_live_bid_data(self, lot_id: str, page) -> Dict:
        """Scrape live bid data using proven CSS selectors."""
        try:
            url = f"https://mac.bid/lot/{lot_id}"
            
            # Navigate with optimized settings
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            await page.wait_for_timeout(2000)  # Wait for dynamic content
            
            bid_data = {
                'lot_id': lot_id,
                'current_bid': 0.0,
                'bid_count': 0,
                'status': 'Unknown',
                'scraping_success': False,
                'selector_used': None,
                'timestamp': datetime.now().isoformat()
            }
            
            # Try proven CSS selectors
            current_bid = None
            selector_used = None
            
            for selector in self.bid_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    
                    for element in elements:
                        try:
                            text = await element.text_content()
                            if text and text.strip():
                                # Extract numeric value
                                currency_matches = re.findall(r'\$[\d,]+\.?\d*', text)
                                if currency_matches:
                                    bid_text = currency_matches[0].replace('$', '').replace(',', '')
                                    try:
                                        current_bid = float(bid_text)
                                        selector_used = selector
                                        break
                                    except:
                                        continue
                                
                                # Look for just numbers
                                number_matches = re.findall(r'[\d,]+\.?\d*', text.replace(',', ''))
                                if number_matches and len(number_matches[0]) >= 2:
                                    try:
                                        potential_bid = float(number_matches[0])
                                        if 0 < potential_bid < 50000:  # Reasonable range
                                            current_bid = potential_bid
                                            selector_used = selector
                                            break
                                    except:
                                        continue
                        except Exception:
                            continue
                    
                    if current_bid is not None:
                        break
                        
                except Exception:
                    continue
            
            # Try to get bid count from page text
            try:
                page_text = await page.text_content('body')
                bid_count_matches = re.findall(r'(\d+)\s+bid', page_text.lower())
                if bid_count_matches:
                    bid_data['bid_count'] = int(bid_count_matches[0])
            except:
                pass
            
            if current_bid is not None:
                bid_data.update({
                    'current_bid': current_bid,
                    'status': 'Open',
                    'scraping_success': True,
                    'selector_used': selector_used
                })
            
            return bid_data
            
        except Exception as e:
            logger.error(f"Error scraping lot {lot_id}: {e}")
            return {
                'lot_id': lot_id,
                'current_bid': 0.0,
                'status': 'Error',
                'scraping_success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def store_lot_data(self, lot: Dict):
        """Store lot data in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Insert or update lot
            cursor.execute('''
                INSERT OR REPLACE INTO lots 
                (lot_id, auction_id, lot_number, product_name, retail_price, 
                 auction_location, is_premium_brand, first_seen, last_checked, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 
                        COALESCE((SELECT first_seen FROM lots WHERE lot_id = ?), ?),
                        ?, 1)
            ''', (
                lot['lot_id'],
                lot.get('auction_id', ''),
                lot.get('lot_number', ''),
                lot.get('product_name', ''),
                float(lot.get('retail_price', 0)),
                lot.get('auction_location', ''),
                lot.get('is_premium_brand', False),
                lot['lot_id'],  # For COALESCE
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
    
    def store_bid_history(self, lot_id: str, bid_data: Dict):
        """Store bid history in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO bid_history 
                (lot_id, current_bid, bid_count, timestamp, source)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                lot_id,
                bid_data['current_bid'],
                bid_data.get('bid_count', 0),
                bid_data['timestamp'],
                'live_scraping'
            ))
            
            conn.commit()
    
    def check_for_alerts(self, lot_id: str, current_bid: float, lot_data: Dict) -> List[Dict]:
        """Check if any alerts should be triggered."""
        alerts = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get previous bid data
            cursor.execute('''
                SELECT current_bid FROM bid_history 
                WHERE lot_id = ? 
                ORDER BY timestamp DESC 
                LIMIT 2
            ''', (lot_id,))
            
            bid_history = cursor.fetchall()
            
            # New bid alert
            if len(bid_history) == 1 and current_bid > 0:  # First bid
                alerts.append({
                    'type': 'first_bid',
                    'message': f"🎯 FIRST BID: ${current_bid:.2f} on {lot_data.get('product_name', 'Unknown')}"
                })
            
            # Bid increase alert
            elif len(bid_history) >= 2:
                previous_bid = bid_history[1][0]
                increase = current_bid - previous_bid
                
                if increase >= self.alert_config['bid_increase_threshold']:
                    alerts.append({
                        'type': 'bid_increase',
                        'message': f"📈 BID INCREASE: +${increase:.2f} (${previous_bid:.2f} → ${current_bid:.2f}) on {lot_data.get('product_name', 'Unknown')}"
                    })
            
            # High value / discount alerts
            retail_price = float(lot_data.get('retail_price', 0))
            if retail_price > self.alert_config['high_value_threshold'] and current_bid > 0:
                discount = ((retail_price - current_bid) / retail_price) * 100
                
                if discount >= self.alert_config['discount_threshold']:
                    alerts.append({
                        'type': 'high_discount',
                        'message': f"💰 HIGH DISCOUNT: {discount:.1f}% off ${retail_price:.2f} retail (current bid: ${current_bid:.2f}) on {lot_data.get('product_name', 'Unknown')}"
                    })
        
        return alerts
    
    def store_alerts(self, lot_id: str, alerts: List[Dict]):
        """Store alerts in database."""
        if not alerts:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for alert in alerts:
                cursor.execute('''
                    INSERT INTO alerts (lot_id, alert_type, message, timestamp)
                    VALUES (?, ?, ?, ?)
                ''', (
                    lot_id,
                    alert['type'],
                    alert['message'],
                    datetime.now().isoformat()
                ))
            
            conn.commit()
    
    async def send_email_alert(self, alerts: List[Dict]):
        """Send email alerts."""
        if not self.email_settings.get('enabled', False) or not alerts:
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_settings['email']
            msg['To'] = self.email_settings['to_email']
            msg['Subject'] = f"Mac.bid Alert - {len(alerts)} New Notifications"
            
            body = "🎯 Mac.bid Live Monitoring Alerts\n\n"
            for alert in alerts:
                body += f"• {alert['message']}\n"
            
            body += f"\nGenerated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_settings['smtp_server'], self.email_settings['smtp_port'])
            server.starttls()
            server.login(self.email_settings['email'], self.email_settings['password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"📧 Sent email alert with {len(alerts)} notifications")
            
        except Exception as e:
            logger.error(f"❌ Failed to send email alert: {e}")
    
    async def monitoring_cycle(self):
        """Run one complete monitoring cycle."""
        logger.info("🔄 Starting monitoring cycle...")
        
        connector = aiohttp.TCPConnector(ssl=self.ssl_context, limit=20)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        ) as session:
            
            # Discover lots
            lots = await self.discover_lots_at_scale(session)
            
            if not lots:
                logger.warning("❌ No lots discovered")
                return
            
            # Process lots with browser pool
            async with async_playwright() as p:
                browsers = []
                
                # Create browser pool
                for i in range(self.browser_pool_size):
                    browser = await p.chromium.launch(
                        headless=True,
                        args=['--no-sandbox', '--disable-dev-shm-usage']
                    )
                    browsers.append(browser)
                
                try:
                    all_alerts = []
                    processed_count = 0
                    
                    # Process lots in batches
                    batch_size = len(lots) // self.browser_pool_size + 1
                    
                    for i in range(0, len(lots), batch_size):
                        batch = lots[i:i + batch_size]
                        browser_index = i // batch_size
                        
                        if browser_index >= len(browsers):
                            break
                        
                        browser = browsers[browser_index]
                        context = await browser.new_context(
                            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                        )
                        page = await context.new_page()
                        
                        for lot in batch:
                            try:
                                lot_id = lot.get('lot_id')
                                if not lot_id:
                                    continue
                                
                                # Store lot data
                                self.store_lot_data(lot)
                                
                                # Scrape live bid data
                                bid_data = await self.scrape_live_bid_data(lot_id, page)
                                
                                if bid_data['scraping_success']:
                                    # Store bid history
                                    self.store_bid_history(lot_id, bid_data)
                                    
                                    # Check for alerts
                                    alerts = self.check_for_alerts(lot_id, bid_data['current_bid'], lot)
                                    
                                    if alerts:
                                        self.store_alerts(lot_id, alerts)
                                        all_alerts.extend(alerts)
                                        
                                        for alert in alerts:
                                            logger.info(f"🚨 ALERT: {alert['message']}")
                                
                                processed_count += 1
                                
                                if processed_count % 10 == 0:
                                    logger.info(f"📊 Processed {processed_count}/{len(lots)} lots...")
                                
                                await asyncio.sleep(1)  # Rate limiting
                                
                            except Exception as e:
                                logger.error(f"❌ Error processing lot {lot.get('lot_id', 'unknown')}: {e}")
                        
                        await context.close()
                    
                    # Send email alerts if any
                    if all_alerts:
                        await self.send_email_alert(all_alerts)
                    
                    logger.info(f"✅ Monitoring cycle completed: {processed_count} lots processed, {len(all_alerts)} alerts generated")
                    
                finally:
                    # Close all browsers
                    for browser in browsers:
                        await browser.close()
    
    async def start_continuous_monitoring(self):
        """Start continuous monitoring loop."""
        logger.info("🎯 STARTING ULTIMATE LIVE MONITORING SYSTEM")
        logger.info("=" * 60)
        logger.info(f"⏰ Check interval: {self.check_interval} seconds")
        logger.info(f"📊 Max lots per cycle: {self.max_lots_per_cycle}")
        logger.info(f"🌐 Browser pool size: {self.browser_pool_size}")
        
        self.monitoring_active = True
        
        try:
            while self.monitoring_active:
                cycle_start = datetime.now()
                
                try:
                    await self.monitoring_cycle()
                except Exception as e:
                    logger.error(f"❌ Error in monitoring cycle: {e}")
                
                # Calculate sleep time
                cycle_duration = (datetime.now() - cycle_start).total_seconds()
                sleep_time = max(0, self.check_interval - cycle_duration)
                
                if sleep_time > 0:
                    logger.info(f"😴 Sleeping for {sleep_time:.1f} seconds until next cycle...")
                    await asyncio.sleep(sleep_time)
                else:
                    logger.warning(f"⚠️ Cycle took {cycle_duration:.1f}s, longer than {self.check_interval}s interval!")
                
        except KeyboardInterrupt:
            logger.info("🛑 Monitoring stopped by user")
        finally:
            self.monitoring_active = False
    
    def get_monitoring_stats(self) -> Dict:
        """Get monitoring statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total lots
            cursor.execute('SELECT COUNT(*) FROM lots WHERE is_active = 1')
            total_lots = cursor.fetchone()[0]
            
            # Premium lots
            cursor.execute('SELECT COUNT(*) FROM lots WHERE is_active = 1 AND is_premium_brand = 1')
            premium_lots = cursor.fetchone()[0]
            
            # Recent alerts
            cursor.execute('''
                SELECT COUNT(*) FROM alerts 
                WHERE timestamp > datetime('now', '-24 hours')
            ''')
            recent_alerts = cursor.fetchone()[0]
            
            # Bid history count
            cursor.execute('SELECT COUNT(*) FROM bid_history')
            total_bids_tracked = cursor.fetchone()[0]
            
            return {
                'total_lots': total_lots,
                'premium_lots': premium_lots,
                'recent_alerts': recent_alerts,
                'total_bids_tracked': total_bids_tracked
            }
    
    def display_recent_alerts(self, hours: int = 24):
        """Display recent alerts."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT a.alert_type, a.message, a.timestamp, l.product_name, l.lot_id
                FROM alerts a
                JOIN lots l ON a.lot_id = l.lot_id
                WHERE a.timestamp > datetime('now', '-{} hours')
                ORDER BY a.timestamp DESC
                LIMIT 20
            '''.format(hours))
            
            alerts = cursor.fetchall()
            
            if alerts:
                print(f"\n🚨 RECENT ALERTS (Last {hours} hours)")
                print("=" * 60)
                
                for alert_type, message, timestamp, product_name, lot_id in alerts:
                    dt = datetime.fromisoformat(timestamp)
                    print(f"{dt.strftime('%H:%M:%S')} - {message}")
                    print(f"    🔗 https://mac.bid/lot/{lot_id}")
                    print()
            else:
                print(f"📭 No alerts in the last {hours} hours")

async def main():
    """Main function with menu system."""
    system = UltimateLiveMonitoringSystem()
    
    while True:
        print("\n🎯 ULTIMATE LIVE MONITORING SYSTEM")
        print("=" * 50)
        
        stats = system.get_monitoring_stats()
        print(f"📊 Stats: {stats['total_lots']} lots ({stats['premium_lots']} premium)")
        print(f"🚨 Recent alerts: {stats['recent_alerts']} (24h)")
        print(f"📈 Total bids tracked: {stats['total_bids_tracked']}")
        
        print("\nOptions:")
        print("1. Start continuous monitoring")
        print("2. Run single monitoring cycle")
        print("3. View recent alerts")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            await system.start_continuous_monitoring()
        elif choice == '2':
            await system.monitoring_cycle()
        elif choice == '3':
            hours = input("Hours to look back (default 24): ").strip()
            hours = int(hours) if hours.isdigit() else 24
            system.display_recent_alerts(hours)
        elif choice == '4':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    asyncio.run(main()) 