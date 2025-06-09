#!/usr/bin/env python3
"""
🎯 Real-Time Next.js API System for Mac.bid
Using discovered Next.js data endpoints for ACCURATE bid data
"""

import asyncio
import aiohttp
import ssl
import json
import urllib.parse
from datetime import datetime
from pathlib import Path

class RealtimeNextJSAPISystem:
    def __init__(self):
        self.load_credentials()
        self.setup_session_config()
        self.sc_locations = ['Spartanburg', 'Greenville', 'Rock Hill', 'Gastonia', 'Anderson']
        self.premium_brands = ['Apple', 'Sony', 'Samsung', 'Nintendo', 'Dyson', 'Bose', 'DeWalt', 'Milwaukee']
        
        # Next.js build ID (extracted from your curl)
        self.nextjs_build_id = "AslxUFb4wF5GgYRFXlpoC"
        
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
        
        # Headers based on your curl commands
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.6',
            'Referer': 'https://www.mac.bid/',
            'Origin': 'https://www.mac.bid',
            'sec-ch-ua': '"Brave";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'sec-gpc': '1',
            'x-nextjs-data': '1'
        }
        
        # Cookies from your curl (simplified)
        self.cookies = {
            'lat_lon': '{"lat":35.1293,"lon":-80.864}',
            'CookieConsent': 'true',
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
                async with session.get(url, timeout=15) as response:
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
    
    async def get_nextjs_lot_data(self, session: aiohttp.ClientSession, auction_id: str, lot_number: str) -> dict:
        """Get accurate lot data from Next.js data endpoint."""
        try:
            # Construct Next.js data URL
            url = f"https://www.mac.bid/_next/data/{self.nextjs_build_id}/search.json"
            params = {
                'aid': auction_id,
                'lid': lot_number
            }
            
            # Use cookies and proper headers
            async with session.get(
                url, 
                params=params,
                headers=self.headers,
                cookies=self.cookies,
                timeout=15
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    print(f"      ❌ Next.js API returned status {response.status}")
                    
        except Exception as e:
            print(f"      ❌ Error getting Next.js data: {e}")
        
        return {}
    
    async def extract_auction_and_lot_info(self, lot: dict) -> tuple:
        """Extract auction ID and lot number from lot data."""
        auction_number = lot.get('auction_number', '')
        lot_number = lot.get('lot_number', '')
        
        # Try to extract auction ID from auction number
        # Format appears to be like "RHA2506-11-A1"
        auction_id = None
        if auction_number:
            # Look for patterns that might indicate auction ID
            parts = auction_number.split('-')
            if len(parts) >= 2:
                # Try different combinations
                potential_ids = [
                    parts[1],  # "2506" from "RHA2506-11-A1"
                    ''.join(parts[1:3]),  # "250611" 
                    auction_number.replace('-', ''),  # Full number without dashes
                ]
                
                # For now, let's try a simple approach
                auction_id = parts[1] if parts[1].isdigit() else None
        
        return auction_id, lot_number
    
    async def enhance_lots_with_nextjs_data(self, session: aiohttp.ClientSession, lots: list) -> list:
        """Enhance lots with accurate data from Next.js endpoints."""
        print(f"\n🎯 Enhancing {len(lots)} lots with Next.js data...")
        
        enhanced_lots = []
        
        for i, lot in enumerate(lots[:10], 1):  # Limit to first 10 for testing
            lot_id = lot.get('lot_id')
            if not lot_id:
                continue
            
            print(f"   📊 {i}/{min(len(lots), 10)}: Lot {lot_id}")
            
            # Extract auction and lot info
            auction_id, lot_number = await self.extract_auction_and_lot_info(lot)
            
            if auction_id and lot_number:
                print(f"      🔍 Trying Next.js API: auction={auction_id}, lot={lot_number}")
                
                # Get Next.js data
                nextjs_data = await self.get_nextjs_lot_data(session, auction_id, lot_number)
                
                if nextjs_data:
                    print(f"      ✅ Got Next.js data!")
                    
                    # Extract accurate bid data from Next.js response
                    pageProps = nextjs_data.get('pageProps', {})
                    lot_data = pageProps.get('lot', {})
                    
                    if lot_data:
                        enhanced_lot = lot.copy()
                        enhanced_lot.update({
                            # Accurate data from Next.js
                            'nextjs_current_bid': lot_data.get('current_bid', 0),
                            'nextjs_total_bids': lot_data.get('total_bids', 0),
                            'nextjs_unique_bidders': lot_data.get('unique_bidders', 0),
                            'nextjs_is_open': lot_data.get('is_open', False),
                            'nextjs_winning_bid': lot_data.get('winning_bid_amount', 0),
                            
                            # Original API data for comparison
                            'api_current_bid': float(lot.get('current_bid', 0)),
                            'api_total_bids': lot.get('total_bids', 0),
                            
                            # Data source tracking
                            'data_source': 'nextjs_api',
                            'nextjs_success': True,
                            'auction_id_used': auction_id,
                            'lot_number_used': lot_number,
                        })
                        
                        # Calculate discrepancy
                        api_bid = enhanced_lot['api_current_bid']
                        nextjs_bid = enhanced_lot['nextjs_current_bid']
                        enhanced_lot['bid_discrepancy'] = abs(api_bid - nextjs_bid) > 0.01
                        
                        enhanced_lots.append(enhanced_lot)
                    else:
                        print(f"      ⚠️ No lot data in Next.js response")
                        # Fallback to original data
                        enhanced_lot = lot.copy()
                        enhanced_lot.update({
                            'data_source': 'search_api_fallback',
                            'nextjs_success': False
                        })
                        enhanced_lots.append(enhanced_lot)
                else:
                    print(f"      ❌ No Next.js data received")
                    # Fallback to original data
                    enhanced_lot = lot.copy()
                    enhanced_lot.update({
                        'data_source': 'search_api_fallback',
                        'nextjs_success': False
                    })
                    enhanced_lots.append(enhanced_lot)
            else:
                print(f"      ⚠️ Could not extract auction ID or lot number")
                # Fallback to original data
                enhanced_lot = lot.copy()
                enhanced_lot.update({
                    'data_source': 'search_api_fallback',
                    'nextjs_success': False
                })
                enhanced_lots.append(enhanced_lot)
            
            # Rate limiting
            await asyncio.sleep(0.5)
        
        print(f"✅ Enhanced {len(enhanced_lots)} lots with Next.js data")
        return enhanced_lots
    
    def calculate_opportunity_score(self, lot: dict) -> float:
        """Calculate opportunity score using accurate data."""
        score = 0.0
        
        # Use Next.js data if available, otherwise fall back to API data
        if lot.get('nextjs_success', False):
            current_bid = lot.get('nextjs_current_bid', 0)
            total_bids = lot.get('nextjs_total_bids', 0)
            is_open = lot.get('nextjs_is_open', False)
        else:
            current_bid = float(lot.get('current_bid', 0))
            total_bids = lot.get('total_bids', 0)
            is_open = lot.get('is_open', False)
        
        retail_price = float(lot.get('retail_price', 0))
        
        # Only score open auctions
        if not is_open:
            return 0.0
        
        # Price factor (40% of score)
        if retail_price > 0:
            if current_bid == 0:
                price_score = 1.0  # No bids = maximum opportunity
            else:
                discount = (retail_price - current_bid) / retail_price
                price_score = min(discount * 1.5, 1.0)  # Cap at 1.0
        else:
            price_score = 0.0
        
        score += price_score * 0.4
        
        # Bid activity factor (25% of score)
        if total_bids == 0:
            bid_score = 1.0  # No competition
        elif total_bids <= 3:
            bid_score = 0.8  # Low competition
        elif total_bids <= 8:
            bid_score = 0.6  # Moderate competition
        else:
            bid_score = 0.3  # High competition
        
        score += bid_score * 0.25
        
        # Brand factor (20% of score)
        product_name = lot.get('product_name', '').lower()
        brand_score = 0.5  # Default
        for brand in self.premium_brands:
            if brand.lower() in product_name:
                brand_score = 1.0
                break
        
        score += brand_score * 0.2
        
        # Data accuracy factor (10% of score)
        nextjs_success = lot.get('nextjs_success', False)
        accuracy_score = 1.0 if nextjs_success else 0.5
        
        score += accuracy_score * 0.1
        
        # Location factor (5% of score)
        location = lot.get('auction_location', '')
        location_score = 1.0 if any(sc_loc in location for sc_loc in self.sc_locations) else 0.5
        
        score += location_score * 0.05
        
        return min(score, 1.0)  # Cap at 1.0
    
    def get_bid_activity_indicator(self, lot: dict) -> str:
        """Get bid activity indicator using accurate data."""
        if lot.get('nextjs_success', False):
            total_bids = lot.get('nextjs_total_bids', 0)
            is_open = lot.get('nextjs_is_open', False)
        else:
            total_bids = lot.get('total_bids', 0)
            is_open = lot.get('is_open', False)
        
        if not is_open:
            return "🔒 CLOSED"
        elif total_bids == 0:
            return "🟢 NO BIDS"
        elif total_bids <= 3:
            return "🟡 LOW ACTIVITY"
        elif total_bids <= 8:
            return "🟠 MODERATE ACTIVITY"
        else:
            return "🔴 HIGH ACTIVITY"
    
    def display_nextjs_results(self, lots: list):
        """Display results with Next.js vs API comparison."""
        if not lots:
            print("❌ No lots found")
            return
        
        # Sort by opportunity score
        sorted_lots = sorted(lots, key=lambda x: self.calculate_opportunity_score(x), reverse=True)
        
        print(f"\n🎯 NEXT.JS API RESULTS: ACCURATE REAL-TIME BID DATA")
        print("=" * 80)
        
        for i, lot in enumerate(sorted_lots[:15], 1):
            score = self.calculate_opportunity_score(lot)
            activity = self.get_bid_activity_indicator(lot)
            
            # Get accurate data
            if lot.get('nextjs_success', False):
                current_bid = lot.get('nextjs_current_bid', 0)
                total_bids = lot.get('nextjs_total_bids', 0)
                unique_bidders = lot.get('nextjs_unique_bidders', 0)
                data_source = "Next.js API"
            else:
                current_bid = float(lot.get('current_bid', 0))
                total_bids = lot.get('total_bids', 0)
                unique_bidders = lot.get('unique_bidders', 0)
                data_source = "Search API (fallback)"
            
            # API data for comparison
            api_bid = lot.get('api_current_bid', 0)
            api_bids = lot.get('api_total_bids', 0)
            
            retail_price = float(lot.get('retail_price', 0))
            
            # Calculate discount
            if retail_price > 0 and current_bid > 0:
                discount = ((retail_price - current_bid) / retail_price) * 100
            elif retail_price > 0:
                discount = 100  # No bids
            else:
                discount = 0
            
            print(f"\n{i:2d}. {lot.get('product_name', 'Unknown Product')}")
            print(f"    🎯 Opportunity Score: {score:.2f}")
            print(f"    {activity} | Bidders: {unique_bidders}")
            print(f"    ✅ {data_source}: ${current_bid:.2f} | Bids: {total_bids}")
            
            # Show comparison if we have both data sources
            if lot.get('nextjs_success', False) and (api_bid != current_bid or api_bids != total_bids):
                print(f"    ⚠️ Search API showed: ${api_bid:.2f} | Bids: {api_bids} (DIFFERENT)")
            
            print(f"    💰 Retail: ${retail_price:.2f}")
            if discount > 0:
                print(f"    📊 Potential Discount: {discount:.1f}%")
            
            print(f"    📍 {lot.get('auction_location', 'Unknown')} | Lot #{lot.get('lot_number', 'N/A')}")
            print(f"    🔗 https://mac.bid/lot/{lot.get('lot_id')}")
        
        # Summary statistics
        print(f"\n📊 NEXT.JS API SYSTEM SUMMARY")
        print("=" * 50)
        
        total_lots = len(lots)
        nextjs_success = len([l for l in lots if l.get('nextjs_success', False)])
        discrepancies = len([l for l in lots if l.get('bid_discrepancy', False)])
        no_bid_lots = len([l for l in lots if (l.get('nextjs_current_bid', 0) if l.get('nextjs_success') else l.get('current_bid', 0)) == 0])
        
        print(f"📈 Total lots analyzed: {total_lots}")
        print(f"✅ Next.js API success: {nextjs_success}")
        print(f"⚠️ API vs Next.js discrepancies: {discrepancies}")
        print(f"🟢 No-bid opportunities: {no_bid_lots}")
        print(f"📊 Next.js success rate: {(nextjs_success/total_lots)*100:.1f}%")
    
    async def run_nextjs_scan(self):
        """Run scan using Next.js API for accurate bid data."""
        print("🚀 REAL-TIME NEXT.JS API SYSTEM")
        print("=" * 60)
        print("✅ Using discovered Next.js data endpoints for accurate bids")
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
            
            # Step 2: Enhance with Next.js data
            enhanced_lots = await self.enhance_lots_with_nextjs_data(session, lots)
            
            # Step 3: Display results
            self.display_nextjs_results(enhanced_lots)
            
            # Step 4: Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"nextjs_realtime_bids_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'customer_id': self.customer_id,
                    'nextjs_build_id': self.nextjs_build_id,
                    'total_lots': len(enhanced_lots),
                    'nextjs_success_count': len([l for l in enhanced_lots if l.get('nextjs_success', False)]),
                    'lots': enhanced_lots
                }, f, indent=2)
            
            print(f"\n💾 Results saved: {filename}")
            print(f"✅ Next.js scan completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

async def main():
    """Main function."""
    system = RealtimeNextJSAPISystem()
    await system.run_nextjs_scan()

if __name__ == "__main__":
    asyncio.run(main()) 