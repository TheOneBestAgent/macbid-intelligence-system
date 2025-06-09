#!/usr/bin/env python3
"""
Real-time Product Monitor for mac.bid
Uses efficient polling to detect new product additions with minimal delay.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from datetime import datetime
import aiohttp
import hashlib

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from playwright.async_api import async_playwright
from src.scraper.auth_handler import create_auth_credentials


class RealtimeProductMonitor:
    """Monitor for real-time product additions on mac.bid."""
    
    def __init__(self):
        self.known_products = set()
        self.new_products = []
        self.product_changes = []
        self.session_cookies = None
        self.last_check = None
        
    async def get_auth_session(self):
        """Get authenticated session for API access."""
        print("🔐 Getting authenticated session...")
        
        auth_creds = create_auth_credentials(
            username="darvonshops@gmail.com",
            password="^sy3i@NiV14tv7",
            auth_type="form"
        )
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Login to get session
                await page.goto("https://mac.bid", wait_until='domcontentloaded')
                await asyncio.sleep(3)
                
                login_button = await page.query_selector('button:has-text("Log In")')
                if login_button:
                    await login_button.click()
                    await asyncio.sleep(2)
                    
                    email_field = await page.query_selector('input[name="email"], #si-email')
                    password_field = await page.query_selector('input[name="password"], #si-password')
                    
                    if email_field and password_field:
                        await email_field.fill(auth_creds.username)
                        await password_field.fill(auth_creds.password)
                        await password_field.press('Enter')
                        await asyncio.sleep(5)
                        
                        # Extract session cookies
                        cookies = await context.cookies()
                        self.session_cookies = {cookie['name']: cookie['value'] for cookie in cookies}
                        
                        print("✅ Session established!")
                        return True
                        
            except Exception as e:
                print(f"❌ Auth failed: {e}")
                return False
            finally:
                await browser.close()
        
        return False
    
    async def monitor_products_realtime(self):
        """Monitor products with high-frequency polling for near real-time detection."""
        print("🚀 Starting real-time product monitoring...")
        print("   Checking every 5 seconds for new products...")
        
        # Initialize with current products
        await self.initialize_known_products()
        
        check_count = 0
        
        while True:
            try:
                check_count += 1
                current_time = datetime.now()
                
                # Check multiple pages for comprehensive coverage
                new_products_found = []
                
                for page in range(1, 4):  # Check first 3 pages
                    products = await self.fetch_products_page(page)
                    
                    for product in products:
                        product_id = self.get_product_id(product)
                        
                        if product_id and product_id not in self.known_products:
                            new_products_found.append(product)
                            self.known_products.add(product_id)
                
                # Report new products
                if new_products_found:
                    for product in new_products_found:
                        await self.handle_new_product_detected(product, current_time)
                
                # Status update every minute
                if check_count % 12 == 0:  # Every 12 checks (1 minute)
                    print(f"⏰ {current_time.strftime('%H:%M:%S')} - Monitoring... ({len(self.known_products)} products tracked)")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                print(f"⚠️  Monitoring error: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def initialize_known_products(self):
        """Initialize the set of known products."""
        print("📊 Initializing known products...")
        
        for page in range(1, 6):  # Check first 5 pages
            products = await self.fetch_products_page(page)
            
            for product in products:
                product_id = self.get_product_id(product)
                if product_id:
                    self.known_products.add(product_id)
        
        print(f"✅ Initialized with {len(self.known_products)} known products")
    
    async def fetch_products_page(self, page=1):
        """Fetch products from a specific page."""
        url = f"https://api.macdiscount.com/auctionsummary?pg={page}&ppg=20"
        
        headers = {}
        if self.session_cookies:
            cookie_str = "; ".join([f"{k}={v}" for k, v in self.session_cookies.items()])
            headers['Cookie'] = cookie_str
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('items', []) or data.get('auctions', []) or []
                    else:
                        print(f"⚠️  API error {response.status} for page {page}")
                        return []
        except Exception as e:
            print(f"⚠️  Fetch error for page {page}: {e}")
            return []
    
    def get_product_id(self, product):
        """Extract a unique product ID."""
        # Try multiple possible ID fields
        for id_field in ['id', 'auction_id', 'product_id', 'item_id']:
            if id_field in product and product[id_field]:
                return str(product[id_field])
        
        # Fallback: create hash from title + price
        title = product.get('title', '')
        price = product.get('current_price', product.get('price', ''))
        if title:
            return hashlib.md5(f"{title}_{price}".encode()).hexdigest()[:12]
        
        return None
    
    async def handle_new_product_detected(self, product, detection_time):
        """Handle detection of a new product."""
        product_id = self.get_product_id(product)
        
        product_info = {
            'timestamp': detection_time.isoformat(),
            'product_id': product_id,
            'title': product.get('title', 'Unknown'),
            'current_price': product.get('current_price', product.get('price', 0)),
            'auction_end': product.get('auction_end', ''),
            'category': product.get('category', ''),
            'description': product.get('description', '')[:200] if product.get('description') else '',
            'image_url': product.get('image_url', ''),
            'full_data': product
        }
        
        self.new_products.append(product_info)
        
        # Alert
        print(f"\n🆕 NEW PRODUCT DETECTED!")
        print(f"   🆔 ID: {product_id}")
        print(f"   📝 Title: {product_info['title']}")
        print(f"   💰 Price: ${product_info['current_price']}")
        print(f"   ⏰ Detected: {detection_time.strftime('%H:%M:%S')}")
        print(f"   🔗 Category: {product_info['category']}")
        
        # Save to file
        with open('new_products_realtime.json', 'w') as f:
            json.dump(self.new_products, f, indent=2, default=str)
        
        # Also append to a log file
        with open('product_alerts.log', 'a') as f:
            f.write(f"{detection_time.isoformat()} - NEW: {product_info['title']} - ${product_info['current_price']}\n")
    
    async def monitor_turbo_auctions(self):
        """Monitor special turbo auctions separately."""
        print("⚡ Starting turbo auction monitoring...")
        
        known_turbo = set()
        
        while True:
            try:
                url = "https://api.macdiscount.com/turbo-clock-auctions"
                headers = {}
                if self.session_cookies:
                    cookie_str = "; ".join([f"{k}={v}" for k, v in self.session_cookies.items()])
                    headers['Cookie'] = cookie_str
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            turbo_auctions = data if isinstance(data, list) else data.get('items', [])
                            
                            for auction in turbo_auctions:
                                auction_id = self.get_product_id(auction)
                                if auction_id and auction_id not in known_turbo:
                                    known_turbo.add(auction_id)
                                    print(f"⚡ NEW TURBO AUCTION: {auction.get('title', 'Unknown')}")
                
                await asyncio.sleep(10)  # Check turbo auctions every 10 seconds
                
            except Exception as e:
                print(f"⚠️  Turbo monitoring error: {e}")
                await asyncio.sleep(30)


async def main():
    """Main monitoring function."""
    print("🔥 MAC.BID Real-time Product Monitor")
    print("=" * 50)
    print("🎯 This will detect new products within 5-10 seconds of being added!")
    print()
    
    monitor = RealtimeProductMonitor()
    
    # Get authenticated session (optional, works without it too)
    auth_success = await monitor.get_auth_session()
    if not auth_success:
        print("⚠️  Continuing without authentication (some features may be limited)")
    
    print("\n🚀 Starting monitoring tasks...")
    
    # Run both monitoring tasks concurrently
    tasks = [
        monitor.monitor_products_realtime(),
        monitor.monitor_turbo_auctions()
    ]
    
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped by user")
        print("📊 Check 'new_products_realtime.json' and 'product_alerts.log' for results")
    except Exception as e:
        print(f"❌ Error: {e}") 