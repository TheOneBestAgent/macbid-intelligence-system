#!/usr/bin/env python3
"""
Direct Lot Checker
Attempts to access specific lot pages directly to get real current bid information
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime
from typing import List, Dict, Any

class DirectLotChecker:
    def __init__(self):
        self.load_credentials()
        
        # Headers for API requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def load_credentials(self):
        """Load JWT token and customer ID."""
        self.jwt_token = None
        self.customer_id = None
        
        try:
            tokens_file = os.path.expanduser("~/.macbid_scraper/api_tokens.json")
            with open(tokens_file, 'r') as f:
                token_data = json.load(f)
                self.jwt_token = token_data.get('tokens', {}).get('authorization')
                self.customer_id = token_data.get('customer_id')
                
            if self.jwt_token:
                print(f"✅ Using JWT token: {self.jwt_token[:50]}...")
            if self.customer_id:
                print(f"✅ Customer ID: {self.customer_id}")
        except Exception as e:
            print(f"⚠️ Could not load credentials: {e}")
    
    async def check_specific_lots_directly(self):
        """Check specific lots directly using browser automation."""
        print("🎯 Checking Specific Lots Directly")
        print("=" * 50)
        
        # Sample lot IDs from our previous scans
        sample_lots = [
            {'lot_id': '35652282', 'product_name': 'LG Electronics HU715QW Ultra Short Throw 4K Projector', 'location': 'Rock Hill'},
            {'lot_id': '35538508', 'product_name': 'ASUS ROG Strix G16 (2024) Gaming Laptop', 'location': 'Rock Hill'},
            {'lot_id': '35567189', 'product_name': 'KoolMore Refrigerated Snack and Drink Vending Machine', 'location': 'Rock Hill'},
        ]
        
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("❌ Playwright not available. Install with: pip install playwright")
            return
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Use headless=False to see what's happening
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                for i, lot in enumerate(sample_lots, 1):
                    print(f"\n{i}. 🔍 Checking Lot {lot['lot_id']}: {lot['product_name'][:50]}...")
                    
                    # Try different URL patterns to access the lot
                    lot_urls = [
                        f"https://mac.bid/lot/{lot['lot_id']}",
                        f"https://www.mac.bid/lot/{lot['lot_id']}",
                        f"https://mac.bid/auction/lot/{lot['lot_id']}",
                        f"https://www.mac.bid/auction/lot/{lot['lot_id']}",
                    ]
                    
                    lot_found = False
                    for url in lot_urls:
                        try:
                            print(f"   Trying: {url}")
                            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                            await asyncio.sleep(2)
                            
                            # Check if we got a valid lot page
                            page_title = await page.title()
                            page_url = page.url
                            
                            print(f"   Page Title: {page_title}")
                            print(f"   Final URL: {page_url}")
                            
                            # Look for bid information on the page
                            current_bid_selectors = [
                                '.current-bid',
                                '.bid-amount',
                                '.current-price',
                                '[data-testid="current-bid"]',
                                '.price',
                                '.bid-price'
                            ]
                            
                            current_bid = None
                            for selector in current_bid_selectors:
                                try:
                                    bid_elem = await page.query_selector(selector)
                                    if bid_elem:
                                        bid_text = await bid_elem.inner_text()
                                        print(f"   Found bid element ({selector}): {bid_text}")
                                        
                                        import re
                                        bid_match = re.search(r'\$?([\d,]+\.?\d*)', bid_text)
                                        if bid_match:
                                            current_bid = float(bid_match.group(1).replace(',', ''))
                                            break
                                except:
                                    continue
                            
                            # Look for bid count
                            bid_count_selectors = [
                                '.bid-count',
                                '.total-bids',
                                '.bids',
                                '[data-testid="bid-count"]'
                            ]
                            
                            bid_count = None
                            for selector in bid_count_selectors:
                                try:
                                    count_elem = await page.query_selector(selector)
                                    if count_elem:
                                        count_text = await count_elem.inner_text()
                                        print(f"   Found bid count ({selector}): {count_text}")
                                        
                                        count_match = re.search(r'(\d+)', count_text)
                                        if count_match:
                                            bid_count = int(count_match.group(1))
                                            break
                                except:
                                    continue
                            
                            # Look for auction status
                            status_selectors = [
                                '.auction-status',
                                '.lot-status',
                                '.status',
                                '[data-testid="status"]'
                            ]
                            
                            status = None
                            for selector in status_selectors:
                                try:
                                    status_elem = await page.query_selector(selector)
                                    if status_elem:
                                        status = await status_elem.inner_text()
                                        print(f"   Found status ({selector}): {status}")
                                        break
                                except:
                                    continue
                            
                            if current_bid is not None or bid_count is not None or status:
                                print(f"   ✅ Found lot data!")
                                print(f"      Current Bid: ${current_bid if current_bid else 'Unknown'}")
                                print(f"      Bid Count: {bid_count if bid_count else 'Unknown'}")
                                print(f"      Status: {status if status else 'Unknown'}")
                                lot_found = True
                                break
                            else:
                                print(f"   ❌ No bid data found on this page")
                        
                        except Exception as e:
                            print(f"   ❌ Error accessing {url}: {e}")
                            continue
                    
                    if not lot_found:
                        print(f"   ❌ Could not find valid lot page for {lot['lot_id']}")
                    
                    # Small delay between lots
                    await asyncio.sleep(2)
                
            except Exception as e:
                print(f"❌ Browser error: {e}")
            finally:
                await browser.close()
    
    async def try_alternative_lot_access(self):
        """Try alternative methods to access lot information."""
        print("\n🔄 Trying Alternative Lot Access Methods")
        print("=" * 50)
        
        # Try to find lot pages through search
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            print("❌ Playwright not available")
            return
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()
            
            try:
                # Go to main mac.bid site
                print("1. 🏠 Going to main mac.bid site...")
                await page.goto("https://www.mac.bid", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                
                # Try to find any current auctions
                print("2. 🔍 Looking for current auctions...")
                
                # Look for auction links
                auction_links = await page.query_selector_all('a[href*="auction"], a[href*="lot"]')
                
                if auction_links:
                    print(f"   Found {len(auction_links)} potential auction/lot links")
                    
                    for i, link in enumerate(auction_links[:5]):  # Check first 5 links
                        try:
                            href = await link.get_attribute('href')
                            text = await link.inner_text()
                            print(f"   Link {i+1}: {href} - {text[:50]}")
                        except:
                            continue
                else:
                    print("   No auction/lot links found")
                
                # Try searching for a specific product
                print("\n3. 🔍 Trying product search...")
                
                # Look for search box
                search_selectors = [
                    'input[type="search"]',
                    'input[placeholder*="search"]',
                    '.search-input',
                    '#search'
                ]
                
                search_box = None
                for selector in search_selectors:
                    try:
                        search_box = await page.query_selector(selector)
                        if search_box:
                            print(f"   Found search box: {selector}")
                            break
                    except:
                        continue
                
                if search_box:
                    # Try searching for "Sony headphones"
                    await search_box.fill("Sony headphones")
                    await search_box.press("Enter")
                    await asyncio.sleep(3)
                    
                    # Look for search results
                    results = await page.query_selector_all('.hit-box, .product, .item, .result')
                    print(f"   Found {len(results)} search results")
                    
                    if results:
                        # Check first result
                        first_result = results[0]
                        try:
                            result_text = await first_result.inner_text()
                            print(f"   First result: {result_text[:100]}...")
                            
                            # Try clicking on it
                            await first_result.click()
                            await asyncio.sleep(3)
                            
                            # Check what page we're on now
                            current_url = page.url
                            page_title = await page.title()
                            print(f"   Navigated to: {current_url}")
                            print(f"   Page title: {page_title}")
                            
                            # Look for bid information
                            page_content = await page.content()
                            if 'bid' in page_content.lower():
                                print("   ✅ Found bid-related content on page!")
                            else:
                                print("   ❌ No bid content found")
                        
                        except Exception as e:
                            print(f"   ❌ Error checking result: {e}")
                else:
                    print("   ❌ No search box found")
                
            except Exception as e:
                print(f"❌ Error in alternative access: {e}")
            finally:
                await browser.close()
    
    async def run_direct_check(self):
        """Run direct lot checking."""
        print("🚀 Direct Lot Checking")
        print("=" * 40)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Check specific lots directly
        await self.check_specific_lots_directly()
        
        # Try alternative access methods
        await self.try_alternative_lot_access()
        
        print(f"\n✅ Direct check completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    checker = DirectLotChecker()
    await checker.run_direct_check()

if __name__ == "__main__":
    asyncio.run(main()) 