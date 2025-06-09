#!/usr/bin/env python3
"""
🎯 Authenticated Bid Scraper for Mac.bid
Logs in first, then extracts the current bid from authenticated pages
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import re

class AuthenticatedBidScraper:
    def __init__(self):
        self.load_credentials()
    
    def load_credentials(self):
        """Load user credentials."""
        config_file = Path.home() / '.macbid_scraper' / 'credentials.json'
        try:
            with open(config_file, 'r') as f:
                creds = json.load(f)
                self.customer_id = creds.get('customer_id', '2710619')
                self.username = creds.get('username', 'darvonmedia@gmail.com')
                self.password = creds.get('password', '')
                print(f"📧 Using account: {self.username} (ID: {self.customer_id})")
        except FileNotFoundError:
            print("⚠️ No credentials found, using defaults")
            self.customer_id = '2710619'
            self.username = 'darvonmedia@gmail.com'
            self.password = ''
    
    async def login(self, page):
        """Log into Mac.bid."""
        try:
            print("🔐 Attempting to log in...")
            
            # Go to login page
            await page.goto('https://mac.bid/login', wait_until='domcontentloaded')
            await page.wait_for_timeout(2000)
            
            # Fill in login form
            email_selector = 'input[type="email"], input[name="email"], #email'
            password_selector = 'input[type="password"], input[name="password"], #password'
            
            # Try to find email field
            try:
                await page.wait_for_selector(email_selector, timeout=5000)
                await page.fill(email_selector, self.username)
                print(f"   ✅ Filled email: {self.username}")
            except:
                print("   ❌ Could not find email field")
                return False
            
            # Try to find password field
            try:
                await page.wait_for_selector(password_selector, timeout=5000)
                await page.fill(password_selector, self.password)
                print("   ✅ Filled password")
            except:
                print("   ❌ Could not find password field")
                return False
            
            # Submit form
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Log In")',
                'button:has-text("Sign In")',
                '.btn-primary'
            ]
            
            for selector in submit_selectors:
                try:
                    await page.click(selector)
                    print(f"   ✅ Clicked submit button: {selector}")
                    break
                except:
                    continue
            else:
                print("   ❌ Could not find submit button")
                return False
            
            # Wait for login to complete
            await page.wait_for_timeout(3000)
            
            # Check if login was successful
            current_url = page.url
            if 'login' not in current_url.lower():
                print("   ✅ Login successful!")
                return True
            else:
                print("   ❌ Login failed - still on login page")
                return False
                
        except Exception as e:
            print(f"   ❌ Login error: {e}")
            return False
    
    async def extract_authenticated_bid_data(self, page):
        """Extract bid data from authenticated page."""
        try:
            print("   🔍 Extracting bid data from authenticated page...")
            
            # Wait for page to fully load
            await page.wait_for_load_state('networkidle')
            await page.wait_for_timeout(5000)
            
            # Get all dollar amounts for comparison
            all_text = await page.text_content('body')
            all_dollar_matches = re.findall(r'\$[\d,]+\.?\d*', all_text)
            all_amounts = []
            for match in all_dollar_matches:
                try:
                    amount = float(match.replace('$', '').replace(',', ''))
                    all_amounts.append(amount)
                except:
                    continue
            
            unique_amounts = sorted(list(set(all_amounts)))
            
            return {
                'success': True,
                'all_dollar_amounts': unique_amounts
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def scrape_authenticated_bid(self, lot_id: str) -> dict:
        """Scrape bid data after authentication."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                # Step 1: Login
                login_success = await self.login(page)
                if not login_success:
                    await browser.close()
                    return {
                        'lot_id': lot_id,
                        'error': 'Login failed',
                        'timestamp': datetime.now().isoformat()
                    }
                
                # Step 2: Navigate to lot page
                url = f"https://mac.bid/lot/{lot_id}"
                print(f"🌐 Loading lot page: {url}")
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                # Step 3: Wait for dynamic content
                print("   ⏳ Waiting for dynamic content to load...")
                await page.wait_for_timeout(10000)  # Wait 10 seconds for real-time updates
                
                # Step 4: Extract bid data
                bid_data = await self.extract_authenticated_bid_data(page)
                
                await browser.close()
                
                return {
                    'lot_id': lot_id,
                    'url': url,
                    'login_success': login_success,
                    'bid_data': bid_data,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Error scraping lot {lot_id}: {e}")
            return {
                'lot_id': lot_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def test_authenticated_scraping(self, lot_id: str, expected_bid: float):
        """Test authenticated scraping on a specific lot."""
        print(f"🎯 TESTING AUTHENTICATED BID SCRAPER")
        print("=" * 50)
        print(f"Lot ID: {lot_id}")
        print(f"Expected Bid: ${expected_bid:.2f}")
        print()
        
        if not self.password:
            print("❌ No password found in credentials. Please add password to ~/.macbid_scraper/credentials.json")
            return
        
        result = await self.scrape_authenticated_bid(lot_id)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"🎯 RESULTS")
        print("=" * 30)
        print(f"Login Success: {'✅' if result['login_success'] else '❌'}")
        
        bid_data = result['bid_data']
        
        if not bid_data['success']:
            print("❌ Failed to extract bid data")
            if 'error' in bid_data:
                print(f"Error: {bid_data['error']}")
            return
        
        # Show all dollar amounts found
        print(f"💰 ALL DOLLAR AMOUNTS FOUND:")
        amounts = bid_data['all_dollar_amounts']
        for amount in amounts:
            difference = abs(amount - expected_bid)
            marker = "🎯" if difference < 1.0 else "  "
            print(f"{marker} ${amount:.2f}")
        
        # Check if expected bid is present
        if expected_bid in amounts or any(abs(a - expected_bid) < 1.0 for a in amounts):
            print(f"✅ Expected bid ${expected_bid:.2f} found in authenticated page!")
        else:
            print(f"❌ Expected bid ${expected_bid:.2f} still NOT found")
        
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"authenticated_bid_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Detailed results saved: {filename}")

async def main():
    """Test the authenticated bid scraper on the known MacBook Pro lot."""
    scraper = AuthenticatedBidScraper()
    
    # Test on the MacBook Pro lot we know has $560 bid
    await scraper.test_authenticated_scraping(
        lot_id="35383973",
        expected_bid=560.0
    )

if __name__ == "__main__":
    asyncio.run(main()) 