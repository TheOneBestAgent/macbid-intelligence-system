#!/usr/bin/env python3
"""
🎯 Accurate Bid Scraper for Mac.bid
Precisely identifies current bid vs other dollar amounts
"""

import asyncio
import aiohttp
import ssl
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import re

class AccurateBidScraper:
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
    
    async def extract_bid_by_label_context(self, page) -> dict:
        """Extract bid by looking for 'current bid' labels and nearby dollar amounts."""
        try:
            page_text = await page.text_content('body')
            page_text_lower = page_text.lower()
            
            patterns = [
                r'current\s+bid[:\s]*\$?([\d,]+\.?\d*)',
                r'bid[:\s]*\$?([\d,]+\.?\d*)',
                r'\$?([\d,]+\.?\d*)\s*current\s+bid',
            ]
            
            results = []
            for pattern in patterns:
                matches = re.finditer(pattern, page_text_lower, re.IGNORECASE)
                for match in matches:
                    try:
                        bid_amount = float(match.group(1).replace(',', ''))
                        results.append({
                            'amount': bid_amount,
                            'pattern': pattern,
                            'match_text': match.group(0)
                        })
                    except:
                        continue
            
            return {
                'method': 'label_context',
                'success': len(results) > 0,
                'results': results,
                'best_match': results[0] if results else None
            }
            
        except Exception as e:
            return {
                'method': 'label_context',
                'success': False,
                'error': str(e)
            }
    
    async def extract_bid_by_js_variables(self, page) -> dict:
        """Extract bid from JavaScript variables."""
        try:
            js_data = await page.evaluate("""
                () => {
                    const data = {};
                    
                    // Check __NEXT_DATA__
                    if (window.__NEXT_DATA__) {
                        const nextData = window.__NEXT_DATA__;
                        if (nextData.props?.pageProps?.currentLot) {
                            const lot = nextData.props.pageProps.currentLot;
                            data.nextData_current_bid = lot.current_bid;
                            data.nextData_winning_bid_amount = lot.winning_bid_amount;
                            data.nextData_total_bids = lot.total_bids;
                        }
                    }
                    
                    return data;
                }
            """)
            
            potential_bids = []
            for key, value in js_data.items():
                if isinstance(value, (int, float)) and value >= 0:
                    potential_bids.append({
                        'amount': float(value),
                        'source': key,
                        'confidence': 'high' if 'current_bid' in key else 'medium'
                    })
            
            return {
                'method': 'js_variables',
                'success': len(potential_bids) > 0,
                'js_data': js_data,
                'potential_bids': potential_bids,
                'best_match': potential_bids[0] if potential_bids else None
            }
            
        except Exception as e:
            return {
                'method': 'js_variables',
                'success': False,
                'error': str(e)
            }
    
    async def extract_bid_by_dom_analysis(self, page) -> dict:
        """Analyze DOM structure to find bid elements."""
        try:
            dom_analysis = await page.evaluate("""
                () => {
                    const results = [];
                    const allElements = document.querySelectorAll('*');
                    
                    for (const el of allElements) {
                        const text = el.textContent?.trim();
                        if (!text) continue;
                        
                        const dollarMatches = text.match(/\$[\d,]+\.?\d*/g);
                        if (dollarMatches) {
                            const parent = el.parentElement;
                            const parentText = parent?.textContent?.trim() || '';
                            
                            const contextLower = (text + ' ' + parentText).toLowerCase();
                            const isBidContext = contextLower.includes('current') || 
                                                contextLower.includes('bid') ||
                                                contextLower.includes('winning');
                            
                            for (const match of dollarMatches) {
                                const amount = parseFloat(match.replace(/[$,]/g, ''));
                                if (amount > 0) {
                                    results.push({
                                        amount: amount,
                                        text: text,
                                        parentText: parentText,
                                        className: el.className,
                                        tagName: el.tagName,
                                        isBidContext: isBidContext,
                                        contextScore: isBidContext ? 10 : 0
                                    });
                                }
                            }
                        }
                    }
                    
                    results.sort((a, b) => {
                        if (a.contextScore !== b.contextScore) {
                            return b.contextScore - a.contextScore;
                        }
                        return a.amount - b.amount;
                    });
                    
                    return results.slice(0, 10);
                }
            """)
            
            return {
                'method': 'dom_analysis',
                'success': len(dom_analysis) > 0,
                'candidates': dom_analysis,
                'best_match': dom_analysis[0] if dom_analysis else None
            }
            
        except Exception as e:
            return {
                'method': 'dom_analysis',
                'success': False,
                'error': str(e)
            }
    
    async def scrape_accurate_bid(self, lot_id: str, retail_price: float) -> dict:
        """Scrape accurate bid using multiple strategies."""
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
                await page.wait_for_timeout(3000)
                
                results = {}
                
                print("   🔍 Trying label context method...")
                results['label_context'] = await self.extract_bid_by_label_context(page)
                
                print("   🔍 Trying JavaScript variables method...")
                results['js_variables'] = await self.extract_bid_by_js_variables(page)
                
                print("   🔍 Trying DOM analysis method...")
                results['dom_analysis'] = await self.extract_bid_by_dom_analysis(page)
                
                await browser.close()
                
                best_result = self.determine_best_bid(results, retail_price)
                
                return {
                    'lot_id': lot_id,
                    'url': url,
                    'retail_price': retail_price,
                    'all_results': results,
                    'best_result': best_result,
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            print(f"❌ Error scraping lot {lot_id}: {e}")
            return {
                'lot_id': lot_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def determine_best_bid(self, results: dict, retail_price: float) -> dict:
        """Determine the most likely correct bid from all methods."""
        candidates = []
        
        for method, result in results.items():
            if not result.get('success'):
                continue
            
            if method == 'label_context' and result.get('best_match'):
                candidates.append({
                    'amount': result['best_match']['amount'],
                    'method': method,
                    'confidence': 90,
                    'details': result['best_match']
                })
            
            elif method == 'js_variables' and result.get('best_match'):
                confidence = 85 if 'current_bid' in result['best_match']['source'] else 60
                candidates.append({
                    'amount': result['best_match']['amount'],
                    'method': method,
                    'confidence': confidence,
                    'details': result['best_match']
                })
            
            elif method == 'dom_analysis' and result.get('best_match'):
                confidence = 80 if result['best_match'].get('isBidContext') else 50
                candidates.append({
                    'amount': result['best_match']['amount'],
                    'method': method,
                    'confidence': confidence,
                    'details': result['best_match']
                })
        
        if not candidates:
            return {
                'current_bid': 0.0,
                'confidence': 0,
                'method': 'none',
                'message': 'No valid bid found'
            }
        
        # Filter out unreasonable bids
        reasonable_candidates = [
            c for c in candidates 
            if 0 <= c['amount'] <= retail_price * 1.5
        ]
        
        if not reasonable_candidates:
            return {
                'current_bid': 0.0,
                'confidence': 0,
                'method': 'filtered_out',
                'message': 'All candidates filtered out as unreasonable',
                'all_candidates': candidates
            }
        
        reasonable_candidates.sort(key=lambda x: (-x['confidence'], x['amount']))
        
        best = reasonable_candidates[0]
        
        return {
            'current_bid': best['amount'],
            'confidence': best['confidence'],
            'method': best['method'],
            'details': best['details'],
            'all_candidates': candidates
        }
    
    async def test_known_lot(self, lot_id: str, retail_price: float, expected_bid: float):
        """Test scraping on a known lot with expected bid."""
        print(f"🎯 TESTING ACCURATE BID SCRAPER")
        print("=" * 50)
        print(f"Lot ID: {lot_id}")
        print(f"Retail Price: ${retail_price:.2f}")
        print(f"Expected Bid: ${expected_bid:.2f}")
        print()
        
        result = await self.scrape_accurate_bid(lot_id, retail_price)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        best = result['best_result']
        found_bid = best['current_bid']
        
        print(f"🎯 RESULTS")
        print("=" * 30)
        print(f"Found Bid: ${found_bid:.2f}")
        print(f"Expected: ${expected_bid:.2f}")
        print(f"Method: {best['method']}")
        print(f"Confidence: {best['confidence']}%")
        
        accuracy = abs(found_bid - expected_bid)
        if accuracy < 1.0:
            print(f"✅ ACCURATE! (difference: ${accuracy:.2f})")
        else:
            print(f"❌ INACCURATE! (difference: ${accuracy:.2f})")
        
        print(f"\n📊 ALL METHODS TRIED:")
        for method, method_result in result['all_results'].items():
            status = "✅" if method_result.get('success') else "❌"
            print(f"   {status} {method}")
            if method_result.get('success') and method_result.get('best_match'):
                amount = method_result['best_match'].get('amount', 'N/A')
                print(f"      Found: ${amount}")
        
        if best.get('all_candidates'):
            print(f"\n🔍 ALL CANDIDATES FOUND:")
            for candidate in best['all_candidates']:
                print(f"   ${candidate['amount']:.2f} - {candidate['method']} (confidence: {candidate['confidence']}%)")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"accurate_bid_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\n💾 Detailed results saved: {filename}")

async def main():
    """Test the accurate bid scraper on the known MacBook Pro lot."""
    scraper = AccurateBidScraper()
    
    # Test on the MacBook Pro lot we know has $560 bid
    await scraper.test_known_lot(
        lot_id="35383973",
        retail_price=1534.95,
        expected_bid=560.0
    )

if __name__ == "__main__":
    asyncio.run(main()) 