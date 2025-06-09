#!/usr/bin/env python3
"""
🎯 Live Page Bid Scraper for Mac.bid
Direct web scraping using provided CSS selectors for ACCURATE real-time bids
"""

import asyncio
import aiohttp
import ssl
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

class LivePageBidScraper:
    def __init__(self):
        self.load_credentials()
        self.setup_session_config()
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        self.premium_brands = ['Apple', 'Sony', 'Samsung', 'Nintendo', 'Dyson', 'Bose', 'DeWalt', 'Milwaukee']
        
        # CSS selectors from user for accurate bid data
        self.bid_selectors = [
            "#general > div.row.mb-4 > div.col-lg-5.pt-2.pt-lg-0.px-lg-4 > div > div.d-flex.flex-column.flex-sm-row.flex-lg-column.flex-xl-row.justify-content-start.align-items-center.mb-3 > div.h1.font-weight-normal.text-accent.mb-0 > div > span:nth-child(2)",
            "#productInfo > div > div:nth-child(4) > div > div.font-size-sm.text-muted",
            "#productInfo > div > div:nth-child(5) > div > div.font-size-sm.text-muted",
            ".h1.font-weight-normal.text-accent span",
            ".current-bid",
            ".bid-amount"
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
                print(f"📧 Using account: {self.username} (ID: {self.customer_id})")
        except FileNotFoundError:
            print("⚠️ No credentials found, using defaults")
            self.customer_id = '2710619'
            self.jwt_token = ''
            self.username = 'darvonmedia@gmail.com'
    
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
    
    async def get_lots_from_search_api(self, session: aiohttp.ClientSession) -> list:
        """Get lots from search API for discovery."""
        print("🔍 Getting lots from search API for discovery...")
        
        search_terms = ['electronics', 'gaming', 'headphones', 'laptop', 'apple', 'sony']
        all_lots = []
        
        for term in search_terms:
            try:
                url = f"https://api.macdiscount.com/search?q={term}&limit=50"
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
                        
                        all_lots.extend(sc_lots)
                        print(f"   📍 {term}: {len(sc_lots)} open SC lots")
                
                await asyncio.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                print(f"   ❌ Error with {term}: {e}")
        
        # Remove duplicates
        unique_lots = {}
        for lot in all_lots:
            lot_id = lot.get('lot_id')
            if lot_id and lot_id not in unique_lots:
                unique_lots[lot_id] = lot
        
        print(f"✅ Found {len(unique_lots)} unique open SC lots from search API")
        return list(unique_lots.values())
    
    async def scrape_live_bid_data(self, lot_id: str, browser) -> dict:
        """Scrape live bid data from auction page using provided CSS selectors."""
        try:
            url = f"https://mac.bid/lot/{lot_id}"
            page = await browser.new_page()
            
            print(f"      🌐 Loading: {url}")
            
            # Navigate to lot page
            await page.goto(url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(3000)  # Wait for dynamic content
            
            bid_data = {
                'lot_id': lot_id,
                'url': url,
                'live_current_bid': 0.0,
                'live_bid_count': 0,
                'live_status': 'Unknown',
                'scraping_success': False,
                'selector_used': None
            }
            
            # Try to find current bid using provided selectors
            current_bid = None
            selector_used = None
            
            for selector in self.bid_selectors:
                try:
                    print(f"         🔍 Trying selector: {selector[:50]}...")
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        if text:
                            print(f"         📄 Found text: '{text}'")
                            # Extract numeric value from text like "$123.45" or "123.45"
                            import re
                            # Look for currency patterns
                            currency_matches = re.findall(r'\$[\d,]+\.?\d*', text)
                            if currency_matches:
                                # Remove $ and commas, convert to float
                                bid_text = currency_matches[0].replace('$', '').replace(',', '')
                                current_bid = float(bid_text)
                                selector_used = selector
                                print(f"         ✅ Found bid: ${current_bid:.2f}")
                                break
                            
                            # Look for just numbers
                            number_matches = re.findall(r'[\d,]+\.?\d*', text.replace(',', ''))
                            if number_matches:
                                try:
                                    current_bid = float(number_matches[0])
                                    selector_used = selector
                                    print(f"         ✅ Found bid: ${current_bid:.2f}")
                                    break
                                except:
                                    continue
                except Exception as e:
                    print(f"         ❌ Selector error: {e}")
                    continue
            
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
            
            await page.close()
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
    
    async def enhance_lots_with_live_data(self, lots: list) -> list:
        """Enhance lots with live scraped bid data."""
        print(f"\n🎯 Scraping live bid data for {len(lots)} lots...")
        
        enhanced_lots = []
        
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            
            try:
                for i, lot in enumerate(lots[:5], 1):  # Limit to first 5 for testing
                    lot_id = lot.get('lot_id')
                    if not lot_id:
                        continue
                    
                    print(f"   🔍 {i}/{min(len(lots), 5)}: Scraping lot {lot_id}")
                    
                    # Scrape live bid data
                    live_data = await self.scrape_live_bid_data(lot_id, browser)
                    
                    # Merge API data with live scraped data
                    enhanced_lot = lot.copy()
                    enhanced_lot.update({
                        # Live scraped data (ACCURATE)
                        'live_current_bid': live_data['live_current_bid'],
                        'live_status': live_data['live_status'],
                        'scraping_success': live_data['scraping_success'],
                        'selector_used': live_data.get('selector_used'),
                        
                        # Original API data for comparison
                        'api_current_bid': float(lot.get('current_bid', 0)),
                        'api_total_bids': lot.get('total_bids', 0),
                        
                        # Data source tracking
                        'data_source': 'live_page_scraping',
                        'scrape_url': live_data.get('url', ''),
                    })
                    
                    # Calculate discrepancy
                    api_bid = enhanced_lot['api_current_bid']
                    live_bid = enhanced_lot['live_current_bid']
                    enhanced_lot['bid_discrepancy'] = abs(api_bid - live_bid) > 0.01
                    
                    enhanced_lots.append(enhanced_lot)
                    
                    # Rate limiting
                    await asyncio.sleep(2)
                
            finally:
                await browser.close()
        
        print(f"✅ Enhanced {len(enhanced_lots)} lots with live scraped bid data")
        return enhanced_lots
    
    def display_live_results(self, lots: list):
        """Display results with live vs API bid comparison."""
        if not lots:
            print("❌ No lots found")
            return
        
        print(f"\n🎯 LIVE PAGE SCRAPING RESULTS: TRULY ACCURATE BIDS")
        print("=" * 80)
        
        for i, lot in enumerate(lots, 1):
            # Live scraped data
            live_bid = lot.get('live_current_bid', 0)
            live_status = lot.get('live_status', 'Unknown')
            
            # API data for comparison
            api_bid = lot.get('api_current_bid', 0)
            api_count = lot.get('api_total_bids', 0)
            
            retail_price = float(lot.get('retail_price', 0))
            scraping_success = lot.get('scraping_success', False)
            selector_used = lot.get('selector_used', 'None')
            
            print(f"\n{i:2d}. {lot.get('product_name', 'Unknown Product')}")
            print(f"    Status: {live_status}")
            
            if scraping_success:
                print(f"    ✅ LIVE SCRAPED: ${live_bid:.2f}")
                print(f"    🔍 Selector used: {selector_used[:50] if selector_used else 'None'}...")
                if api_bid != live_bid:
                    print(f"    ⚠️ API showed: ${api_bid:.2f} (WRONG)")
            else:
                print(f"    ❌ Scraping failed, API: ${api_bid:.2f}")
            
            print(f"    💰 Retail: ${retail_price:.2f}")
            print(f"    📍 {lot.get('auction_location', 'Unknown')} | Lot #{lot.get('lot_number', 'N/A')}")
            print(f"    🔗 https://mac.bid/lot/{lot.get('lot_id')}")
        
        # Summary statistics
        print(f"\n📊 LIVE SCRAPING SUMMARY")
        print("=" * 50)
        
        total_lots = len(lots)
        successful_scrapes = len([l for l in lots if l.get('scraping_success', False)])
        discrepancies = len([l for l in lots if l.get('bid_discrepancy', False)])
        
        print(f"📈 Total lots analyzed: {total_lots}")
        print(f"✅ Successful live scrapes: {successful_scrapes}")
        print(f"⚠️ API vs Live discrepancies: {discrepancies}")
        print(f"📊 Live scraping success rate: {(successful_scrapes/total_lots)*100:.1f}%")
    
    async def run_live_scraping_scan(self):
        """Run scan with live page scraping for accurate bid data."""
        print("🎯 LIVE PAGE BID SCRAPER")
        print("=" * 60)
        print("✅ Using provided CSS selectors for ACCURATE live bid data")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        connector = aiohttp.TCPConnector(ssl=self.ssl_context, limit=15)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        ) as session:
            
            # Step 1: Get lots from search API
            lots = await self.get_lots_from_search_api(session)
            
            if not lots:
                print("❌ No lots found from search API")
                return
            
            # Step 2: Enhance with live scraped bid data
            enhanced_lots = await self.enhance_lots_with_live_data(lots)
            
            # Step 3: Display results
            self.display_live_results(enhanced_lots)
            
            # Step 4: Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"live_scraped_bids_{timestamp}.json"
            
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
            print(f"✅ Live scraping completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main function."""
    scraper = LivePageBidScraper()
    await scraper.run_live_scraping_scan()

if __name__ == "__main__":
    asyncio.run(main()) 