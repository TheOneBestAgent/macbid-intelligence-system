#!/usr/bin/env python3
"""
🎯 Ultimate Authenticated Monitoring System for Mac.bid
Scales up monitoring, real-time tracking, alerts, and integration
"""

import asyncio
import json
import sqlite3
import smtplib
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import async_playwright
import re
import email.mime.text
import email.mime.multipart
import aiohttp
import ssl
from typing import List, Dict, Optional

class UltimateMonitoringSystem:
    def __init__(self):
        self.load_credentials()
        self.setup_database()
        self.setup_email()
        self.browser_pool = []
        self.monitoring_active = False
        
        # South Carolina warehouse locations from memory bank
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        
        # Premium brands from memory bank
        self.premium_brands = ['Apple', 'Sony', 'Samsung', 'Nintendo', 'Dyson', 'Bose', 'DeWalt', 'Milwaukee']
        
        # Search terms for lot discovery
        self.search_terms = [
            'Apple MacBook', 'Apple iPhone', 'Apple iPad', 'Apple Watch',
            'Sony Camera', 'Sony PlayStation', 'Sony Headphones',
            'Samsung Galaxy', 'Samsung TV', 'Nintendo Switch',
            'Dyson Vacuum', 'Bose Speakers', 'DeWalt Tools', 'Milwaukee Tools'
        ]
    
    def load_credentials(self):
        """Load user credentials and settings."""
        config_file = Path.home() / '.macbid_scraper' / 'credentials.json'
        try:
            with open(config_file, 'r') as f:
                creds = json.load(f)
                self.customer_id = creds.get('customer_id', '2710619')
                self.username = creds.get('username', 'darvonmedia@gmail.com')
                self.password = creds.get('password', '')
                print(f"📧 Using account: {self.username} (ID: {self.customer_id})")
        except FileNotFoundError:
            print("⚠️ No credentials found")
            self.customer_id = '2710619'
            self.username = 'darvonmedia@gmail.com'
            self.password = 'TaO55i1M6upWFw'  # From memory bank
    
    def setup_database(self):
        """Setup SQLite database for monitoring data."""
        self.db_path = 'ultimate_monitoring.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Lots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lots (
                lot_id TEXT PRIMARY KEY,
                title TEXT,
                retail_price REAL,
                location TEXT,
                auction_id TEXT,
                lot_number TEXT,
                condition_name TEXT,
                description TEXT,
                image_url TEXT,
                expected_close_date TEXT,
                is_active INTEGER DEFAULT 1,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bid history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bid_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                current_bid REAL,
                total_bids INTEGER,
                unique_bidders INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lot_id) REFERENCES lots (lot_id)
            )
        ''')
        
        # Opportunities table (integration with existing system)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opportunities (
                lot_id TEXT PRIMARY KEY,
                opportunity_score REAL,
                price_factor REAL,
                timing_factor REAL,
                bid_pattern_factor REAL,
                rarity_factor REAL,
                last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lot_id) REFERENCES lots (lot_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("📊 Database initialized")
    
    def setup_email(self):
        """Setup email configuration for alerts."""
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email': self.username,  # Using same email as login
            'password': self.password,  # You might want a separate app password
            'to_email': self.username
        }
    
    async def login_to_macbid(self, page):
        """Login to Mac.bid with robust error handling."""
        try:
            print("🔐 Logging in to Mac.bid...")
            
            await page.goto('https://mac.bid', wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)
            
            # Click login button
            login_selectors = ['button:has-text("Log In")', 'a[href*="login"]']
            for selector in login_selectors:
                try:
                    await page.click(selector)
                    break
                except:
                    continue
            
            await page.wait_for_timeout(2000)
            
            # Fill credentials
            await page.fill('input[type="email"]', self.username)
            await page.fill('input[type="password"]', self.password)
            
            # Submit
            submit_selectors = ['button:has-text("Sign In")', 'button[type="submit"]']
            for selector in submit_selectors:
                try:
                    await page.click(selector)
                    break
                except:
                    continue
            
            await page.wait_for_timeout(3000)
            
            # Verify login
            page_content = await page.text_content('body')
            if 'logout' in page_content.lower() or 'sign out' in page_content.lower():
                print("   ✅ Login successful")
                return True
            else:
                print("   ❌ Login failed")
                return False
                
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False
    
    async def discover_lots_via_api(self) -> List[Dict]:
        """Discover lots using the public API endpoints."""
        lots = []
        unique_lots = {}  # Track unique lots by ID
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        
        try:
            async with aiohttp.ClientSession(
                connector=aiohttp.TCPConnector(ssl=ssl_context),
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                
                # Search for premium items using public API
                for term in self.search_terms:
                    try:
                        # Use public search API
                        url = f"https://api.macdiscount.com/search?q={term}&limit=50"
                        print(f"   🔍 Searching for: {term}")
                        
                        async with session.get(url) as response:
                            if response.status == 200:
                                data = await response.json()
                                # Handle 'hits' response format from public API
                                lot_data = data.get('hits', [])
                                
                                for lot in lot_data:
                                    # Filter for SC locations - use correct field name
                                    location = lot.get('auction_location', '')
                                    if any(sc_loc in location for sc_loc in self.sc_locations):
                                        lot_id = lot.get('id', lot.get('mac_lot_id', ''))
                                        if lot_id and lot_id not in unique_lots:
                                            unique_lots[lot_id] = lot
                                            lots.append(lot)
                                            
                                print(f"      Found {len(lot_data)} items, {len([l for l in lot_data if any(sc in l.get('auction_location', '') for sc in self.sc_locations)])} in SC")
                                            
                        await asyncio.sleep(0.3)  # Rate limiting for public API
                        
                    except Exception as e:
                        print(f"   ❌ Search error for {term}: {e}")
                        continue
                
                print(f"   📦 Discovered {len(lots)} unique lots via public API")
                return lots
                
        except Exception as e:
            print(f"❌ API discovery error: {e}")
            return []
    
    async def extract_current_bid(self, page, lot_id: str) -> Dict:
        """Extract current bid from authenticated page."""
        try:
            url = f"https://mac.bid/lot/{lot_id}"
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            await page.wait_for_timeout(5000)  # Wait for real-time updates
            
            # Extract all dollar amounts
            all_text = await page.text_content('body')
            dollar_matches = re.findall(r'\$[\d,]+\.?\d*', all_text)
            
            amounts = []
            for match in dollar_matches:
                try:
                    amount = float(match.replace('$', '').replace(',', ''))
                    amounts.append(amount)
                except:
                    continue
            
            unique_amounts = sorted(list(set(amounts)))
            
            # Determine current bid (exclude retail price and $1 starting bid)
            current_bid = 0.0
            for amount in unique_amounts:
                if amount > 1 and amount < 5000:  # Reasonable bid range
                    # Skip if it's likely the retail price
                    if not any(abs(amount - retail) < 1 for retail in unique_amounts if retail > 1000):
                        current_bid = max(current_bid, amount)
            
            # Extract additional info
            total_bids = 0
            unique_bidders = 0
            
            # Look for bid count in text
            bid_count_match = re.search(r'(\d+)\s*bid', all_text, re.IGNORECASE)
            if bid_count_match:
                total_bids = int(bid_count_match.group(1))
            
            # Look for bidder count
            bidder_count_match = re.search(r'(\d+)\s*bidder', all_text, re.IGNORECASE)
            if bidder_count_match:
                unique_bidders = int(bidder_count_match.group(1))
            
            return {
                'lot_id': lot_id,
                'current_bid': current_bid,
                'total_bids': total_bids,
                'unique_bidders': unique_bidders,
                'all_amounts': unique_amounts,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"   ❌ Error extracting bid for {lot_id}: {e}")
            return {
                'lot_id': lot_id,
                'current_bid': 0.0,
                'total_bids': 0,
                'unique_bidders': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def store_lot_data(self, lot_data: Dict):
        """Store lot data in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO lots 
                (lot_id, title, retail_price, location, auction_id, lot_number, 
                 condition_name, description, image_url, expected_close_date, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (
                lot_data.get('id', lot_data.get('mac_lot_id', '')),
                lot_data.get('auction_title', lot_data.get('title', '')),
                lot_data.get('retail_price', lot_data.get('discount', 0)),
                lot_data.get('auction_location', lot_data.get('location_name', '')),
                lot_data.get('auction_id', ''),
                lot_data.get('auction_number', lot_data.get('lot_number', '')),
                lot_data.get('condition', lot_data.get('condition_name', '')),
                lot_data.get('description', ''),
                lot_data.get('image_url', ''),
                lot_data.get('expected_close_date', '')
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Error storing lot data: {e}")
        finally:
            conn.close()
    
    def store_bid_data(self, bid_data: Dict):
        """Store bid data in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO bid_history 
                (lot_id, current_bid, total_bids, unique_bidders)
                VALUES (?, ?, ?, ?)
            ''', (
                bid_data['lot_id'],
                bid_data['current_bid'],
                bid_data['total_bids'],
                bid_data['unique_bidders']
            ))
            
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Error storing bid data: {e}")
        finally:
            conn.close()
    
    def calculate_opportunity_score(self, lot_id: str) -> float:
        """Calculate opportunity score using memory bank analytics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get lot and latest bid data
            cursor.execute('''
                SELECT l.retail_price, l.title, l.expected_close_date,
                       bh.current_bid, bh.total_bids, bh.unique_bidders
                FROM lots l
                LEFT JOIN bid_history bh ON l.lot_id = bh.lot_id
                WHERE l.lot_id = ?
                ORDER BY bh.timestamp DESC
                LIMIT 1
            ''', (lot_id,))
            
            result = cursor.fetchone()
            if not result:
                return 0.0
            
            retail_price, title, close_date, current_bid, total_bids, unique_bidders = result
            
            # Price factor (lower current bid vs retail = higher score)
            price_factor = 0.0
            if retail_price and retail_price > 0:
                if current_bid is None or current_bid == 0:
                    price_factor = 1.0  # No bids yet
                else:
                    price_factor = max(0, 1 - (current_bid / retail_price))
            else:
                price_factor = 0.5  # Default if no retail price
            
            # Timing factor (closer to end = higher urgency)
            timing_factor = 0.5  # Default
            if close_date:
                try:
                    close_dt = datetime.fromisoformat(close_date.replace('Z', '+00:00'))
                    now = datetime.now()
                    time_left = (close_dt - now).total_seconds()
                    if time_left > 0:
                        # Higher score for items ending soon (within 24 hours)
                        if time_left < 86400:  # 24 hours
                            timing_factor = 0.9
                        elif time_left < 172800:  # 48 hours
                            timing_factor = 0.7
                        else:
                            timing_factor = 0.5
                except:
                    pass
            
            # Bid pattern factor (low competition = higher score)
            bid_pattern_factor = 0.5
            if total_bids is not None and unique_bidders is not None:
                if total_bids == 0:
                    bid_pattern_factor = 1.0  # No competition
                elif unique_bidders < 5:
                    bid_pattern_factor = 0.8  # Low competition
                elif unique_bidders < 10:
                    bid_pattern_factor = 0.6  # Medium competition
                else:
                    bid_pattern_factor = 0.3  # High competition
            
            # Rarity factor (premium brands = higher score)
            rarity_factor = 0.5
            if title:
                title_lower = title.lower()
                for brand in self.premium_brands:
                    if brand.lower() in title_lower:
                        rarity_factor = 0.9
                        break
            
            # Calculate weighted score (from memory bank formula)
            opportunity_score = (
                price_factor * 0.4 +
                timing_factor * 0.2 +
                bid_pattern_factor * 0.3 +
                rarity_factor * 0.1
            )
            
            # Store the score
            cursor.execute('''
                INSERT OR REPLACE INTO opportunities 
                (lot_id, opportunity_score, price_factor, timing_factor, 
                 bid_pattern_factor, rarity_factor, last_calculated)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (lot_id, opportunity_score, price_factor, timing_factor, 
                  bid_pattern_factor, rarity_factor))
            
            conn.commit()
            return opportunity_score
            
        except Exception as e:
            print(f"   ❌ Error calculating opportunity score: {e}")
            return 0.0
        finally:
            conn.close()
    
    def send_alert(self, lot_id: str, alert_type: str, message: str):
        """Send email alert for important events."""
        try:
            msg = email.mime.multipart.MIMEMultipart()
            msg['From'] = self.email_config['email']
            msg['To'] = self.email_config['to_email']
            msg['Subject'] = f"Mac.bid Alert: {alert_type}"
            
            body = f"""
Mac.bid Monitoring Alert

Alert Type: {alert_type}
Lot ID: {lot_id}
Message: {message}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

View Lot: https://mac.bid/lot/{lot_id}

---
Ultimate Monitoring System
            """
            
            msg.attach(email.mime.text.MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            text = msg.as_string()
            server.sendmail(self.email_config['email'], self.email_config['to_email'], text)
            server.quit()
            
            # Log alert
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO alerts (lot_id, alert_type, message)
                VALUES (?, ?, ?)
            ''', (lot_id, alert_type, message))
            conn.commit()
            conn.close()
            
            print(f"   📧 Alert sent: {alert_type} for lot {lot_id}")
            
        except Exception as e:
            print(f"   ❌ Error sending alert: {e}")
    
    def check_for_alerts(self, lot_id: str, current_bid_data: Dict, previous_bid_data: Dict = None):
        """Check if any alerts should be triggered."""
        try:
            current_bid = current_bid_data.get('current_bid', 0)
            
            # New bid alert
            if previous_bid_data:
                previous_bid = previous_bid_data.get('current_bid', 0)
                if current_bid > previous_bid:
                    self.send_alert(
                        lot_id, 
                        "New Bid", 
                        f"Bid increased from ${previous_bid:.2f} to ${current_bid:.2f}"
                    )
            
            # High opportunity alert
            opportunity_score = self.calculate_opportunity_score(lot_id)
            if opportunity_score > 0.8:
                self.send_alert(
                    lot_id,
                    "High Opportunity",
                    f"Opportunity score: {opportunity_score:.2f} - Current bid: ${current_bid:.2f}"
                )
            
            # No bid opportunity alert
            if current_bid == 0:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT retail_price FROM lots WHERE lot_id = ?', (lot_id,))
                result = cursor.fetchone()
                if result and result[0] > 100:  # Only for items over $100 retail
                    self.send_alert(
                        lot_id,
                        "No Bid Opportunity",
                        f"No bids yet on ${result[0]:.2f} retail item"
                    )
                conn.close()
                
        except Exception as e:
            print(f"   ❌ Error checking alerts: {e}")
    
    async def monitor_lots_continuously(self):
        """Main monitoring loop."""
        print("🚀 Starting continuous monitoring...")
        self.monitoring_active = True
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Login once
            login_success = await self.login_to_macbid(page)
            if not login_success:
                print("❌ Failed to login - stopping monitoring")
                return
            
            cycle_count = 0
            
            while self.monitoring_active:
                try:
                    cycle_count += 1
                    print(f"\n🔄 Monitoring Cycle #{cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                    
                    # Discover new lots every 10 cycles
                    if cycle_count % 10 == 1:
                        print("🔍 Discovering new lots...")
                        discovered_lots = await self.discover_lots_via_api()
                        for lot in discovered_lots:
                            self.store_lot_data(lot)
                    
                    # Get active lots from database
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('SELECT lot_id FROM lots WHERE is_active = 1 LIMIT 20')
                    active_lots = [row[0] for row in cursor.fetchall()]
                    conn.close()
                    
                    print(f"   📊 Monitoring {len(active_lots)} active lots")
                    
                    # Monitor each lot
                    for lot_id in active_lots:
                        try:
                            # Get previous bid data
                            conn = sqlite3.connect(self.db_path)
                            cursor = conn.cursor()
                            cursor.execute('''
                                SELECT current_bid, total_bids, unique_bidders 
                                FROM bid_history 
                                WHERE lot_id = ? 
                                ORDER BY timestamp DESC 
                                LIMIT 1
                            ''', (lot_id,))
                            previous_result = cursor.fetchone()
                            previous_bid_data = None
                            if previous_result:
                                previous_bid_data = {
                                    'current_bid': previous_result[0],
                                    'total_bids': previous_result[1],
                                    'unique_bidders': previous_result[2]
                                }
                            conn.close()
                            
                            # Extract current bid data
                            current_bid_data = await self.extract_current_bid(page, lot_id)
                            
                            # Store bid data
                            self.store_bid_data(current_bid_data)
                            
                            # Check for alerts
                            self.check_for_alerts(lot_id, current_bid_data, previous_bid_data)
                            
                            # Brief pause between lots
                            await asyncio.sleep(2)
                            
                        except Exception as e:
                            print(f"   ❌ Error monitoring lot {lot_id}: {e}")
                            continue
                    
                    # Wait before next cycle (5 minutes)
                    print(f"   ⏳ Waiting 5 minutes before next cycle...")
                    await asyncio.sleep(300)
                    
                except Exception as e:
                    print(f"❌ Error in monitoring cycle: {e}")
                    await asyncio.sleep(60)  # Wait 1 minute on error
            
            await browser.close()
    
    def generate_report(self) -> str:
        """Generate monitoring report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get summary stats
        cursor.execute('SELECT COUNT(*) FROM lots WHERE is_active = 1')
        active_lots = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM bid_history WHERE timestamp > datetime("now", "-24 hours")')
        recent_updates = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM alerts WHERE sent_at > datetime("now", "-24 hours")')
        recent_alerts = cursor.fetchone()[0]
        
        # Get top opportunities
        cursor.execute('''
            SELECT l.lot_id, l.title, l.retail_price, o.opportunity_score,
                   bh.current_bid, bh.unique_bidders
            FROM lots l
            JOIN opportunities o ON l.lot_id = o.lot_id
            LEFT JOIN bid_history bh ON l.lot_id = bh.lot_id
            WHERE l.is_active = 1
            ORDER BY o.opportunity_score DESC
            LIMIT 10
        ''')
        top_opportunities = cursor.fetchall()
        
        conn.close()
        
        report = f"""
🎯 ULTIMATE MONITORING SYSTEM REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 SUMMARY STATISTICS
Active Lots: {active_lots}
Updates (24h): {recent_updates}
Alerts (24h): {recent_alerts}

🏆 TOP OPPORTUNITIES
"""
        
        for i, (lot_id, title, retail_price, score, current_bid, bidders) in enumerate(top_opportunities, 1):
            report += f"""
{i:2d}. {title[:50]}{'...' if len(title) > 50 else ''}
    Lot ID: {lot_id}
    Opportunity Score: {score:.3f}
    Retail: ${retail_price:.2f} | Current Bid: ${current_bid or 0:.2f}
    Bidders: {bidders or 0}
    Link: https://mac.bid/lot/{lot_id}
"""
        
        return report
    
    async def start_monitoring(self):
        """Start the monitoring system."""
        print("🎯 ULTIMATE AUTHENTICATED MONITORING SYSTEM")
        print("=" * 50)
        print("Features:")
        print("✅ 1. Scaled monitoring for multiple lots")
        print("✅ 2. Real-time bid tracking")
        print("✅ 3. Email alerts for bid changes")
        print("✅ 4. Integration with existing analytics")
        print()
        
        try:
            await self.monitor_lots_continuously()
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
            self.monitoring_active = False
        except Exception as e:
            print(f"❌ Monitoring error: {e}")

async def main():
    """Main function."""
    system = UltimateMonitoringSystem()
    await system.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main()) 