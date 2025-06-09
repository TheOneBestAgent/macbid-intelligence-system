#!/usr/bin/env python3
"""
Personal Enhanced Unified Mac.bid System
Customized for your actual mac.bid account
"""

import asyncio
import aiohttp
import ssl
import json
import argparse
import getpass
import os
from datetime import datetime
from pathlib import Path


class PersonalUnifiedSystem:
    def __init__(self, username=None, password=None, customer_id=None):
        self.authenticated = False
        self.session_cookies = {}
        
        # API endpoints from both systems
        self.api_endpoints = {
            'public_search': 'https://api.macdiscount.com/search',
            'auction_summary': 'https://api.macdiscount.com/auctionsummary',
            'customer_auctions': 'https://api.macdiscount.com/auctions/customer/{customer_id}/active-auctions',
            'auction_alerts': 'https://api.macdiscount.com/auctions/customer/{customer_id}/auction-alerts',
            'turbo_auctions': 'https://api.macdiscount.com/turbo-clock-auctions',
        }
        
        # Load credentials from secure storage or use provided ones
        stored_creds = self.load_stored_credentials()
        
        # Your personal credentials (prioritize provided, then stored, then prompt)
        self.user_credentials = {
            'username': username or (stored_creds.get('username') if stored_creds else None),
            'password': password or (stored_creds.get('password') if stored_creds else None),
            'customer_id': customer_id or (stored_creds.get('customer_id') if stored_creds else None)
        }
    
    def load_stored_credentials(self):
        """Load credentials from secure storage."""
        try:
            config_file = Path.home() / '.macbid_scraper' / 'credentials.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    creds = json.load(f)
                    if creds.get('configured'):
                        return creds
            return None
        except Exception as e:
            print(f"⚠️ Could not load stored credentials: {e}")
            return None
        
    def setup_credentials(self):
        """Securely set up your mac.bid credentials."""
        print("🔐 Setting up your mac.bid account credentials")
        print("=" * 50)
        
        # Check if we have stored credentials first
        if self.user_credentials['username'] and self.user_credentials['password']:
            print(f"✅ Using stored credentials for: {self.user_credentials['username']}")
            return
        
        # Get username
        if not self.user_credentials['username']:
            self.user_credentials['username'] = input("Enter your mac.bid email: ").strip()
        
        # Get password securely
        if not self.user_credentials['password']:
            self.user_credentials['password'] = getpass.getpass("Enter your mac.bid password: ")
        
        # Customer ID will be discovered during authentication
        print("✅ Credentials set up securely")
        print("💡 Tip: Run 'python setup_personal_credentials.py' to store credentials permanently")
        print()
        
    async def discover_customer_id(self, page):
        """Discover your customer ID from the authenticated session."""
        try:
            # Look for customer ID in page content or network requests
            # This will be populated after successful login
            
            # Method 1: Check for customer ID in page content
            content = await page.content()
            
            # Method 2: Check for customer ID in local storage or cookies
            customer_id = await page.evaluate("""
                () => {
                    // Try to find customer ID in various places
                    const userId = localStorage.getItem('userId') || 
                                  localStorage.getItem('customerId') ||
                                  localStorage.getItem('user_id');
                    return userId;
                }
            """)
            
            if customer_id:
                self.user_credentials['customer_id'] = customer_id
                print(f"   ✅ Discovered customer ID: {customer_id}")
                return customer_id
            else:
                print("   ⚠️ Customer ID not found automatically")
                return None
                
        except Exception as e:
            print(f"   ⚠️ Could not discover customer ID: {e}")
            return None
        
    async def initialize_system(self, authenticate=False):
        print("🚀 Personal Enhanced Unified Mac.bid System")
        print("=" * 60)
        
        if authenticate:
            # Set up credentials if not provided
            if not self.user_credentials['username'] or not self.user_credentials['password']:
                self.setup_credentials()
            
            print("🔐 Attempting authentication with your account...")
            auth_success = await self.attempt_authentication()
            if auth_success:
                print("✅ Authentication successful with your account!")
                self.authenticated = True
            else:
                print("⚠️ Authentication failed, continuing with public access")
        
        print("🔍 Testing API endpoints...")
        await self.test_all_endpoints()
        
        print("✅ Personal unified system ready!")
        return True
        
    async def attempt_authentication(self):
        try:
            from playwright.async_api import async_playwright
            
            print("   🌐 Starting browser automation...")
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                try:
                    await page.goto("https://mac.bid", wait_until='domcontentloaded', timeout=30000)
                    await asyncio.sleep(3)
                    
                    login_button = await page.query_selector('button:has-text("Log In")')
                    if login_button:
                        await login_button.click()
                        await asyncio.sleep(2)
                        
                        email_field = await page.query_selector('input[name="email"], #si-email')
                        password_field = await page.query_selector('input[name="password"], #si-password')
                        
                        if email_field and password_field:
                            print(f"   📧 Logging in as: {self.user_credentials['username']}")
                            await email_field.fill(self.user_credentials['username'])
                            await password_field.fill(self.user_credentials['password'])
                            await password_field.press('Enter')
                            await asyncio.sleep(5)
                            
                            # Check if login was successful
                            current_url = page.url
                            if 'login' not in current_url.lower():
                                # Extract session cookies
                                cookies = await context.cookies()
                                self.session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
                                
                                # Try to discover customer ID
                                await self.discover_customer_id(page)
                                
                                print("   ✅ Session cookies extracted")
                                return True
                            else:
                                print("   ❌ Login failed - check your credentials")
                                return False
                            
                except Exception as e:
                    print(f"   ❌ Browser automation failed: {e}")
                    return False
                finally:
                    await browser.close()
                    
        except ImportError:
            print("   ⚠️ Playwright not available, skipping authentication")
            print("   💡 Install with: pip install playwright && playwright install")
            return False
        except Exception as e:
            print(f"   ❌ Authentication error: {e}")
            return False
            
    async def test_all_endpoints(self):
        print("🔍 Testing API endpoints...")
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        cookies = self.session_cookies if self.authenticated else {}
        
        async with aiohttp.ClientSession(
            connector=connector, 
            timeout=timeout,
            headers=headers,
            cookies=cookies
        ) as session:
            
            print("   📡 Testing public endpoints...")
            public_tests = [
                ('Public Search', f"{self.api_endpoints['public_search']}?q=iPhone&limit=5"),
                ('Auction Summary', f"{self.api_endpoints['auction_summary']}?pg=1&ppg=5")
            ]
            
            for name, url in public_tests:
                try:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            count = len(data.get('hits', data.get('data', [])))
                            print(f"      ✅ {name}: {count} items")
                        else:
                            print(f"      ⚠️ {name}: HTTP {response.status}")
                except Exception as e:
                    print(f"      ❌ {name}: {str(e)[:50]}...")
                    
            if self.authenticated:
                print("   🔐 Testing authenticated endpoints...")
                
                # Test turbo auctions (doesn't require customer ID)
                try:
                    async with session.get(self.api_endpoints['turbo_auctions']) as response:
                        if response.status == 200:
                            data = await response.json()
                            count = len(data) if isinstance(data, list) else len(data.get('data', []))
                            print(f"      ✅ Turbo Auctions: {count} items")
                        else:
                            print(f"      ⚠️ Turbo Auctions: HTTP {response.status}")
                except Exception as e:
                    print(f"      ❌ Turbo Auctions: {str(e)[:50]}...")
                
                # Test customer-specific endpoints if we have customer ID
                if self.user_credentials['customer_id']:
                    customer_tests = [
                        ('Customer Auctions', self.api_endpoints['customer_auctions'].format(
                            customer_id=self.user_credentials['customer_id'])),
                        ('Auction Alerts', self.api_endpoints['auction_alerts'].format(
                            customer_id=self.user_credentials['customer_id']))
                    ]
                    
                    for name, url in customer_tests:
                        try:
                            async with session.get(url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    count = len(data) if isinstance(data, list) else len(data.get('data', []))
                                    print(f"      ✅ {name}: {count} items")
                                elif response.status == 401:
                                    print(f"      🔒 {name}: Authentication required")
                                else:
                                    print(f"      ⚠️ {name}: HTTP {response.status}")
                        except Exception as e:
                            print(f"      ❌ {name}: {str(e)[:50]}...")
                else:
                    print("      ⚠️ Customer-specific endpoints skipped (customer ID not found)")
                    
    async def run_with_your_analytics(self):
        """Run the system with your existing analytics modules."""
        print("🔗 Integrating with your existing analytics...")
        
        try:
            # Import your existing analytics modules
            from enhanced_new_arrivals import EnhancedNewArrivals
            from realtime_enhanced_monitor import RealtimeEnhancedMonitor
            from notification_system import NotificationSystem
            
            # Create instances
            enhanced_arrivals = EnhancedNewArrivals()
            realtime_monitor = RealtimeEnhancedMonitor()
            notifications = NotificationSystem()
            
            print("   ✅ Analytics modules loaded")
            
            # If authenticated, enhance them with your session
            if self.authenticated and self.session_cookies:
                print("   🔐 Applying authentication to analytics modules...")
                
                # Apply session cookies to modules that support it
                for module in [enhanced_arrivals, realtime_monitor]:
                    if hasattr(module, 'session') and hasattr(module.session, 'cookie_jar'):
                        try:
                            for cookie_name, cookie_value in self.session_cookies.items():
                                module.session.cookie_jar.update_cookies({cookie_name: cookie_value})
                            print(f"      ✅ Enhanced {module.__class__.__name__} with authentication")
                        except Exception as e:
                            print(f"      ⚠️ Could not enhance {module.__class__.__name__}: {e}")
                            
            print("   🚀 Ready to run enhanced analytics with your account!")
            return True
            
        except ImportError as e:
            print(f"   ⚠️ Could not import analytics modules: {e}")
            print("   💡 Make sure you're in the directory with your analytics files")
            return False


async def main():
    parser = argparse.ArgumentParser(description='Personal Enhanced Unified Mac.bid System')
    parser.add_argument('--authenticate', action='store_true', 
                       help='Authenticate with your mac.bid account')
    parser.add_argument('--username', type=str, 
                       help='Your mac.bid email (optional, will prompt if not provided)')
    parser.add_argument('--customer-id', type=str,
                       help='Your customer ID (optional, will try to discover)')
    parser.add_argument('--run-analytics', action='store_true',
                       help='Run with your existing analytics modules')
    
    args = parser.parse_args()
    
    # Create system with optional pre-filled credentials
    system = PersonalUnifiedSystem(
        username=args.username,
        customer_id=args.customer_id
    )
    
    try:
        # Initialize system
        await system.initialize_system(authenticate=args.authenticate)
        
        # Run with analytics if requested
        if args.run_analytics:
            await system.run_with_your_analytics()
        
        print("\n" + "=" * 60)
        print("📊 PERSONAL UNIFIED SYSTEM READY")
        print("=" * 60)
        print(f"Account: {system.user_credentials['username'] or 'Not set'}")
        print(f"Authentication: {'✅ Authenticated' if system.authenticated else '❌ Public Only'}")
        print(f"Customer ID: {system.user_credentials['customer_id'] or 'Not discovered'}")
        print(f"Available Endpoints: {len(system.api_endpoints)}")
        print(f"Session Cookies: {len(system.session_cookies)} items")
            
    except Exception as e:
        print(f"❌ System error: {e}")


if __name__ == "__main__":
    asyncio.run(main()) 