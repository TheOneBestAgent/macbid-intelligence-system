#!/usr/bin/env python3
"""
🎯 Authenticated Live Page Bid Scraper for Mac.bid
Uses authentication and robust scraping with provided CSS selectors
"""

import asyncio
import aiohttp
import ssl
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

class AuthenticatedLiveScraper:
    def __init__(self):
        self.load_credentials()
        self.setup_session_config()
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        
        # CSS selectors from user for accurate bid data
        self.bid_selectors = [
            "#general > div.row.mb-4 > div.col-lg-5.pt-2.pt-lg-0.px-lg-4 > div > div.d-flex.flex-column.flex-sm-row.flex-lg-column.flex-xl-row.justify-content-start.align-items-center.mb-3 > div.h1.font-weight-normal.text-accent.mb-0 > div > span:nth-child(2)",
            "#productInfo > div > div:nth-child(4) > div > div.font-size-sm.text-muted",
            "#productInfo > div > div:nth-child(5) > div > div.font-size-sm.text-muted",
            ".h1.font-weight-normal.text-accent span",
            ".current-bid",
            ".bid-amount",
            "span[class*='text-accent']",
            "div[class*='text-accent']"
        ]
        
    def load_credentials(self):
        """Load user credentials."""
        config_file = Path.home() / '.macbid_scraper' / 'credentials.json'
        try:
            with open(config_file, 'r') as f:
                creds = json.load(f)
                self.customer_id = creds.get('customer_id', '2710619')
                self.jwt_token = creds.get('jwt_token', '')
                self.username = creds.get('username', 'darvonmedia@gmail.com')
                self.password = creds.get('password', '')
                print(f"📧 Using account: {self.username} (ID: {self.customer_id})")
        except FileNotFoundError:
            print("⚠️ No credentials found, using defaults")
            self.customer_id = '2710619'
            self.jwt_token = ''
            self.username = 'darvonmedia@gmail.com'
            self.password = ''
    
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
    
    async def get_sample_lots(self, session: aiohttp.ClientSession) -> list:
        """Get a few sample lots for testing."""
        print("🔍 Getting sample lots for testing...")
        
        # Use known working lot IDs or search for a few
        try:
            url = "https://api.macdiscount.com/search?q=apple&limit=10"
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
                            sc_lots.append(hit)
                    
                    print(f"✅ Found {len(sc_lots)} open SC lots")
                    return sc_lots[:3]  # Just test 3 lots
                    
        except Exception as e:
            print(f"❌ Error getting lots: {e}")
        
        return []
    
    async def authenticate_browser(self, page):
        """Authenticate the browser session."""
        try:
            print("🔐 Authenticating browser session...")
            
            # Go to login page
            await page.goto('https://mac.bid/login', timeout=30000)
            await page.wait_for_timeout(2000)
            
            # Check if already logged in
            if 'dashboard' in page.url or 'account' in page.url:
                print("✅ Already authenticated")
                return True
            
            # Try to fill login form if credentials available
            if self.username and self.password:
                try:
                    # Look for email/username field
                    email_selectors = [
                        'input[type="email"]',
                        'input[name="email"]',
                        'input[name="username"]',
                        '#email',
                        '#username'
                    ]
                    
                    for selector in email_selectors:
                        try:
                            await page.fill(selector, self.username, timeout=5000)
                            print(f"✅ Filled email with selector: {selector}")
                            break
                        except:
                            continue
                    
                    # Look for password field
                    password_selectors = [
                        'input[type="password"]',
                        'input[name="password"]',
                        '#password'
                    ]
                    
                    for selector in password_selectors:
                        try:
                            await page.fill(selector, self.password, timeout=5000)
                            print(f"✅ Filled password with selector: {selector}")
                            break
                        except:
                            continue
                    
                    # Submit form
                    submit_selectors = [
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("Login")',
                        'button:has-text("Sign In")'
                    ]
                    
                    for selector in submit_selectors:
                        try:
                            await page.click(selector, timeout=5000)
                            print(f"✅ Clicked submit with selector: {selector}")
                            break
                        except:
                            continue
                    
                    # Wait for navigation
                    await page.wait_for_timeout(3000)
                    
                    if 'login' not in page.url:
                        print("✅ Login successful")
                        return True
                    
                except Exception as e:
                    print(f"⚠️ Auto-login failed: {e}")
            
            print("⚠️ Manual authentication may be required")
            return True  # Continue anyway
            
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    async def scrape_live_bid_data(self, lot_id: str, page) -> dict:
        """Scrape live bid data from auction page using provided CSS selectors."""
        try:
            url = f"https://mac.bid/lot/{lot_id}"
            
            print(f"      🌐 Loading: {url}")
            
            # Navigate to lot page with longer timeout
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            await page.wait_for_timeout(5000)  # Wait for dynamic content
            
            bid_data = {
                'lot_id': lot_id,
                'url': url,
                'live_current_bid': 0.0,
                'live_status': 'Unknown',
                'scraping_success': False,
                'selector_used': None,
                'page_title': '',
                'found_elements': []
            }
            
            # Get page title for debugging
            try:
                title = await page.title()
                bid_data['page_title'] = title
                print(f"         📄 Page title: {title}")
            except:
                pass
            
            # Try to find current bid using provided selectors
            current_bid = None
            selector_used = None
            found_elements = []
            
            for selector in self.bid_selectors:
                try:
                    print(f"         🔍 Trying selector: {selector[:50]}...")
                    elements = await page.query_selector_all(selector)
                    
                    for element in elements:
                        try:
                            text = await element.text_content()
                            if text and text.strip():
                                found_elements.append({
                                    'selector': selector,
                                    'text': text.strip()
                                })
                                print(f"         📄 Found text: '{text.strip()}'")
                                
                                # Extract numeric value from text like "$123.45" or "123.45"
                                import re
                                # Look for currency patterns
                                currency_matches = re.findall(r'\$[\d,]+\.?\d*', text)
                                if currency_matches:
                                    # Remove $ and commas, convert to float
                                    bid_text = currency_matches[0].replace('$', '').replace(',', '')
                                    try:
                                        current_bid = float(bid_text)
                                        selector_used = selector
                                        print(f"         ✅ Found bid: ${current_bid:.2f}")
                                        break
                                    except:
                                        continue
                                
                                # Look for just numbers
                                number_matches = re.findall(r'[\d,]+\.?\d*', text.replace(',', ''))
                                if number_matches and len(number_matches[0]) >= 2:  # At least 2 digits
                                    try:
                                        potential_bid = float(number_matches[0])
                                        if potential_bid > 0 and potential_bid < 10000:  # Reasonable bid range
                                            current_bid = potential_bid
                                            selector_used = selector
                                            print(f"         ✅ Found bid: ${current_bid:.2f}")
                                            break
                                    except:
                                        continue
                        except Exception as e:
                            print(f"         ❌ Element error: {e}")
                            continue
                    
                    if current_bid is not None:
                        break
                        
                except Exception as e:
                    print(f"         ❌ Selector error: {e}")
                    continue
            
            # Store found elements for debugging
            bid_data['found_elements'] = found_elements
            
            # Check if page loaded properly
            page_content = await page.content()
            if 'mac.bid' in page_content and len(page_content) > 1000:
                bid_data['page_loaded'] = True
            else:
                bid_data['page_loaded'] = False
                print(f"         ⚠️ Page may not have loaded properly")
            
            # Update bid data
            if current_bid is not None:
                bid_data.update({
                    'live_current_bid': current_bid,
                    'live_status': 'Open',
                    'scraping_success': True,
                    'selector_used': selector_used
                })
                print(f"      ✅ Successfully scraped: ${current_bid:.2f}")
            else:
                print(f"      ❌ Could not find bid data")
                # Try to get any text from the page for debugging
                try:
                    body_text = await page.query_selector('body')
                    if body_text:
                        text_content = await body_text.text_content()
                        if text_content and len(text_content) > 100:
                            bid_data['page_sample'] = text_content[:500]
                except:
                    pass
            
            return bid_data
            
        except Exception as e:
            print(f"      ❌ Error scraping lot {lot_id}: {e}")
            return {
                'lot_id': lot_id,
                'live_current_bid': 0.0,
                'live_status': 'Error',
                'scraping_success': False,
                'error': str(e)
            }
    
    async def run_authenticated_scraping(self):
        """Run authenticated scraping test."""
        print("🎯 AUTHENTICATED LIVE PAGE BID SCRAPER")
        print("=" * 60)
        print("✅ Using provided CSS selectors with authentication")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        connector = aiohttp.TCPConnector(ssl=self.ssl_context, limit=15)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        ) as session:
            
            # Get sample lots
            lots = await self.get_sample_lots(session)
            
            if not lots:
                print("❌ No lots found for testing")
                return
            
            print(f"\n🎯 Testing live scraping on {len(lots)} lots...")
            
            async with async_playwright() as p:
                # Launch browser with more options
                browser = await p.chromium.launch(
                    headless=False,  # Show browser for debugging
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security'
                    ]
                )
                
                try:
                    # Create context with user agent
                    context = await browser.new_context(
                        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                        viewport={'width': 1280, 'height': 720}
                    )
                    
                    page = await context.new_page()
                    
                    # Authenticate
                    auth_success = await self.authenticate_browser(page)
                    if not auth_success:
                        print("❌ Authentication failed")
                        return
                    
                    enhanced_lots = []
                    
                    for i, lot in enumerate(lots, 1):
                        lot_id = lot.get('lot_id')
                        if not lot_id:
                            continue
                        
                        print(f"   🔍 {i}/{len(lots)}: Scraping lot {lot_id}")
                        
                        # Scrape live bid data
                        live_data = await self.scrape_live_bid_data(lot_id, page)
                        
                        # Merge API data with live scraped data
                        enhanced_lot = lot.copy()
                        enhanced_lot.update(live_data)
                        enhanced_lot['api_current_bid'] = float(lot.get('current_bid', 0))
                        
                        enhanced_lots.append(enhanced_lot)
                        
                        # Rate limiting
                        await asyncio.sleep(3)
                    
                    # Display results
                    self.display_results(enhanced_lots)
                    
                    # Save results
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    filename = f"authenticated_live_scraping_{timestamp}.json"
                    
                    with open(filename, 'w') as f:
                        json.dump({
                            'timestamp': timestamp,
                            'customer_id': self.customer_id,
                            'total_lots': len(enhanced_lots),
                            'successful_scrapes': len([l for l in enhanced_lots if l.get('scraping_success', False)]),
                            'css_selectors_used': self.bid_selectors,
                            'lots': enhanced_lots
                        }, f, indent=2)
                    
                    print(f"\n💾 Results saved: {filename}")
                    
                finally:
                    await browser.close()
        
        print(f"✅ Authenticated scraping completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def display_results(self, lots: list):
        """Display scraping results."""
        if not lots:
            print("❌ No lots processed")
            return
        
        print(f"\n🎯 AUTHENTICATED LIVE SCRAPING RESULTS")
        print("=" * 80)
        
        for i, lot in enumerate(lots, 1):
            live_bid = lot.get('live_current_bid', 0)
            live_status = lot.get('live_status', 'Unknown')
            api_bid = lot.get('api_current_bid', 0)
            retail_price = float(lot.get('retail_price', 0))
            scraping_success = lot.get('scraping_success', False)
            selector_used = lot.get('selector_used', 'None')
            page_title = lot.get('page_title', '')
            found_elements = lot.get('found_elements', [])
            
            print(f"\n{i:2d}. {lot.get('product_name', 'Unknown Product')}")
            print(f"    📄 Page: {page_title}")
            print(f"    Status: {live_status}")
            
            if scraping_success:
                print(f"    ✅ LIVE SCRAPED: ${live_bid:.2f}")
                print(f"    🔍 Selector used: {selector_used[:50] if selector_used else 'None'}...")
                if api_bid != live_bid:
                    print(f"    ⚠️ API showed: ${api_bid:.2f} (DIFFERENT)")
            else:
                print(f"    ❌ Scraping failed, API: ${api_bid:.2f}")
                if found_elements:
                    print(f"    📄 Found {len(found_elements)} elements:")
                    for elem in found_elements[:3]:  # Show first 3
                        print(f"         '{elem['text'][:50]}...'")
            
            print(f"    💰 Retail: ${retail_price:.2f}")
            print(f"    📍 {lot.get('auction_location', 'Unknown')} | Lot #{lot.get('lot_number', 'N/A')}")
            print(f"    🔗 https://mac.bid/lot/{lot.get('lot_id')}")
        
        # Summary
        total_lots = len(lots)
        successful_scrapes = len([l for l in lots if l.get('scraping_success', False)])
        
        print(f"\n📊 SUMMARY")
        print("=" * 30)
        print(f"📈 Total lots: {total_lots}")
        print(f"✅ Successful scrapes: {successful_scrapes}")
        print(f"📊 Success rate: {(successful_scrapes/total_lots)*100:.1f}%")

async def main():
    """Main function."""
    scraper = AuthenticatedLiveScraper()
    await scraper.run_authenticated_scraping()

if __name__ == "__main__":
    asyncio.run(main()) 