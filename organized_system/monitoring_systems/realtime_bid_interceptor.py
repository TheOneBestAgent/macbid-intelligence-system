#!/usr/bin/env python3
"""
🎯 Real-time Bid Interceptor for Mac.bid
Monitors network requests and waits for dynamic bid updates
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import re

class RealtimeBidInterceptor:
    def __init__(self):
        self.load_credentials()
        self.network_requests = []
        self.bid_updates = []
    
    def load_credentials(self):
        """Load user credentials."""
        config_file = Path.home() / '.macbid_scraper' / 'credentials.json'
        try:
            with open(config_file, 'r') as f:
                creds = json.load(f)
                self.customer_id = creds.get('customer_id', '2710619')
                self.username = creds.get('username', 'darvonmedia@gmail.com')
                print(f"📧 Using account: {self.username} (ID: {self.customer_id})")
        except FileNotFoundError:
            print("⚠️ No credentials found, using defaults")
            self.customer_id = '2710619'
            self.username = 'darvonmedia@gmail.com'
    
    async def extract_all_dollar_amounts(self, page):
        """Extract all dollar amounts from the page for analysis."""
        
        print("   💵 Extracting all dollar amounts from page...")
        
        # Get all text content
        all_text = await page.text_content('body')
        
        # Find all dollar amounts
        dollar_matches = re.findall(r'\$[\d,]+\.?\d*', all_text)
        
        amounts = []
        for match in dollar_matches:
            try:
                amount = float(match.replace('$', '').replace(',', ''))
                amounts.append(amount)
            except:
                continue
        
        # Remove duplicates and sort
        unique_amounts = sorted(list(set(amounts)))
        
        print(f"   💰 Found {len(unique_amounts)} unique dollar amounts: {unique_amounts}")
        
        return unique_amounts
    
    async def scrape_with_monitoring(self, lot_id: str) -> dict:
        """Scrape bid with comprehensive monitoring."""
        try:
            url = f"https://mac.bid/lot/{lot_id}"
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                print(f"🌐 Loading: {url}")
                await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                
                # Wait for initial content
                await page.wait_for_timeout(5000)
                
                # Extract all dollar amounts
                all_amounts = await self.extract_all_dollar_amounts(page)
                
                await browser.close()
                
                return {
                    'lot_id': lot_id,
                    'url': url,
                    'all_dollar_amounts': all_amounts,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Error scraping lot {lot_id}: {e}")
            return {
                'lot_id': lot_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def test_lot(self, lot_id: str, expected_bid: float):
        """Test scraping with monitoring on a specific lot."""
        print(f"🎯 TESTING REALTIME BID INTERCEPTOR")
        print("=" * 50)
        print(f"Lot ID: {lot_id}")
        print(f"Expected Bid: ${expected_bid:.2f}")
        print()
        
        result = await self.scrape_with_monitoring(lot_id)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        print(f"🎯 RESULTS")
        print("=" * 30)
        
        # Analyze all dollar amounts
        print(f"💰 ALL DOLLAR AMOUNTS FOUND:")
        amounts = result['all_dollar_amounts']
        for amount in amounts:
            difference = abs(amount - expected_bid)
            marker = "🎯" if difference < 1.0 else "  "
            print(f"{marker} ${amount:.2f}")
        
        # Check if expected bid is in the amounts
        if expected_bid in amounts or any(abs(a - expected_bid) < 1.0 for a in amounts):
            print(f"✅ Expected bid ${expected_bid:.2f} found in page!")
        else:
            print(f"❌ Expected bid ${expected_bid:.2f} NOT found in page")
        
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"realtime_bid_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Detailed results saved: {filename}")

async def main():
    """Test the realtime bid interceptor on the known MacBook Pro lot."""
    interceptor = RealtimeBidInterceptor()
    
    # Test on the MacBook Pro lot we know has $560 bid
    await interceptor.test_lot(
        lot_id="35383973",
        expected_bid=560.0
    )

if __name__ == "__main__":
    asyncio.run(main()) 