#!/usr/bin/env python3
"""
🎯 Targeted Bid Scraper for Mac.bid
Looks specifically for the current bid display element
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import re

class TargetedBidScraper:
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
                print(f"📧 Using account: {self.username} (ID: {self.customer_id})")
        except FileNotFoundError:
            print("⚠️ No credentials found, using defaults")
            self.customer_id = '2710619'
            self.username = 'darvonmedia@gmail.com'
    
    async def find_current_bid_element(self, page) -> dict:
        """Find the specific element that displays the current bid."""
        try:
            # Wait for the page to fully load
            await page.wait_for_load_state('networkidle')
            
            # Look for the specific current bid element using multiple strategies
            strategies = [
                {
                    'name': 'CSS Selector - Text Accent',
                    'selector': '.text-accent',
                    'description': 'Looking for elements with text-accent class'
                },
                {
                    'name': 'CSS Selector - H1 Font Weight',
                    'selector': '.h1.font-weight-normal',
                    'description': 'Looking for h1 elements with font-weight-normal'
                },
                {
                    'name': 'CSS Selector - Bid Display Area',
                    'selector': '[class*="bid"], [class*="current"], [class*="amount"]',
                    'description': 'Looking for elements with bid-related classes'
                },
                {
                    'name': 'Text Content Search',
                    'selector': '*',
                    'description': 'Searching all elements for current bid text'
                }
            ]
            
            results = []
            
            for strategy in strategies:
                print(f"   🔍 {strategy['name']}: {strategy['description']}")
                
                try:
                    elements = await page.query_selector_all(strategy['selector'])
                    
                    for element in elements:
                        try:
                            text = await element.text_content()
                            if not text:
                                continue
                            
                            text = text.strip()
                            
                            # Skip if text is too long (likely not a bid amount)
                            if len(text) > 50:
                                continue
                            
                            # Look for dollar amounts
                            dollar_matches = re.findall(r'\$[\d,]+\.?\d*', text)
                            
                            if dollar_matches:
                                # Get element attributes for context
                                class_name = await element.get_attribute('class') or ''
                                tag_name = await element.evaluate('el => el.tagName')
                                
                                # Get parent context
                                parent = await element.query_selector('xpath=..')
                                parent_text = await parent.text_content() if parent else ''
                                parent_class = await parent.get_attribute('class') if parent else ''
                                
                                for match in dollar_matches:
                                    try:
                                        amount = float(match.replace('$', '').replace(',', ''))
                                        
                                        # Calculate confidence based on context
                                        confidence = 0
                                        
                                        # Higher confidence for specific classes
                                        if 'accent' in class_name.lower():
                                            confidence += 30
                                        if 'bid' in class_name.lower():
                                            confidence += 40
                                        if 'current' in class_name.lower():
                                            confidence += 40
                                        if 'amount' in class_name.lower():
                                            confidence += 30
                                        
                                        # Higher confidence for specific text context
                                        text_lower = text.lower()
                                        if 'current' in text_lower and 'bid' in text_lower:
                                            confidence += 50
                                        elif 'bid' in text_lower:
                                            confidence += 30
                                        elif 'current' in text_lower:
                                            confidence += 20
                                        
                                        # Higher confidence for h1 tags
                                        if tag_name.lower() == 'h1':
                                            confidence += 20
                                        
                                        # Lower confidence for very small amounts (likely starting bid)
                                        if amount <= 5:
                                            confidence -= 20
                                        
                                        # Higher confidence for reasonable bid amounts
                                        if 50 <= amount <= 2000:
                                            confidence += 20
                                        
                                        results.append({
                                            'amount': amount,
                                            'text': text,
                                            'strategy': strategy['name'],
                                            'selector': strategy['selector'],
                                            'class_name': class_name,
                                            'tag_name': tag_name,
                                            'parent_text': parent_text[:100] if parent_text else '',
                                            'parent_class': parent_class,
                                            'confidence': max(0, min(100, confidence)),
                                            'raw_match': match
                                        })
                                    except:
                                        continue
                        except:
                            continue
                except Exception as e:
                    print(f"      ❌ Error with {strategy['name']}: {e}")
                    continue
            
            # Sort by confidence
            results.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {
                'success': len(results) > 0,
                'total_candidates': len(results),
                'candidates': results[:10],  # Top 10 candidates
                'best_candidate': results[0] if results else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def scrape_current_bid(self, lot_id: str) -> dict:
        """Scrape the current bid for a specific lot."""
        try:
            url = f"https://mac.bid/lot/{lot_id}"
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                page = await context.new_page()
                
                print(f"🌐 Loading: {url}")
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                
                # Wait a bit for dynamic content to load
                await page.wait_for_timeout(5000)
                
                print("🔍 Searching for current bid element...")
                bid_result = await self.find_current_bid_element(page)
                
                await browser.close()
                
                return {
                    'lot_id': lot_id,
                    'url': url,
                    'bid_result': bid_result,
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
        """Test scraping on a specific lot."""
        print(f"🎯 TESTING TARGETED BID SCRAPER")
        print("=" * 50)
        print(f"Lot ID: {lot_id}")
        print(f"Expected Bid: ${expected_bid:.2f}")
        print()
        
        result = await self.scrape_current_bid(lot_id)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        bid_result = result['bid_result']
        
        if not bid_result['success']:
            print("❌ No bid candidates found")
            if 'error' in bid_result:
                print(f"Error: {bid_result['error']}")
            return
        
        print(f"🎯 RESULTS")
        print("=" * 30)
        print(f"Total Candidates Found: {bid_result['total_candidates']}")
        
        if bid_result['best_candidate']:
            best = bid_result['best_candidate']
            found_bid = best['amount']
            
            print(f"\n🏆 BEST CANDIDATE:")
            print(f"Amount: ${found_bid:.2f}")
            print(f"Expected: ${expected_bid:.2f}")
            print(f"Confidence: {best['confidence']}%")
            print(f"Strategy: {best['strategy']}")
            print(f"Text: '{best['text']}'")
            print(f"Class: {best['class_name']}")
            print(f"Tag: {best['tag_name']}")
            
            accuracy = abs(found_bid - expected_bid)
            if accuracy < 1.0:
                print(f"✅ ACCURATE! (difference: ${accuracy:.2f})")
            else:
                print(f"❌ INACCURATE! (difference: ${accuracy:.2f})")
        
        print(f"\n📊 ALL CANDIDATES:")
        for i, candidate in enumerate(bid_result['candidates'], 1):
            print(f"{i:2d}. ${candidate['amount']:8.2f} - {candidate['confidence']:3d}% - {candidate['strategy']}")
            print(f"     Text: '{candidate['text'][:50]}{'...' if len(candidate['text']) > 50 else ''}'")
            print(f"     Class: {candidate['class_name']}")
            print()
        
        # Save detailed results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"targeted_bid_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"💾 Detailed results saved: {filename}")

async def main():
    """Test the targeted bid scraper on the known MacBook Pro lot."""
    scraper = TargetedBidScraper()
    
    # Test on the MacBook Pro lot we know has $560 bid
    await scraper.test_lot(
        lot_id="35383973",
        expected_bid=560.0
    )

if __name__ == "__main__":
    asyncio.run(main()) 