#!/usr/bin/env python3
"""
🔍 Bid Data Verification Script
Checks current bid status of top opportunities in real-time
🔐 REQUIRES AUTHENTICATION BEFORE ANY OPERATIONS
"""

import requests
import json
import time
import asyncio
import sys
from typing import Dict, List

# Import authentication manager (REQUIRED FIRST)
sys.path.append('.')
sys.path.append('..')
from core_systems.authentication_manager import require_authentication, get_authenticated_headers, get_customer_id

class BidDataVerifier:
    def __init__(self):
        self.session = requests.Session()
        self.authenticated_headers = None
        self.auth_manager = None
        
        # Basic headers (will be updated with auth)
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://mac.bid/',
            'Origin': 'https://mac.bid'
        })
    
    async def setup_authentication(self):
        """Setup authentication before any operations"""
        print("🔐 Setting up authentication...")
        try:
            self.auth_manager = await require_authentication()
            self.authenticated_headers = get_authenticated_headers()
            customer_id = get_customer_id()
            
            # Update session headers with authentication
            self.session.headers.update(self.authenticated_headers)
            
            print(f"✅ Authenticated as Customer ID: {customer_id}")
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def setup_top_lots(self):
        """Setup the top lots to verify"""
        # Top opportunities to verify
        self.top_lots = [
            {
                'name': 'Pallet of General Merchandise (REMOVAL)',
                'mac_lot_id': 'mac_lot_35242923',
                'reported_retail': 17986.38,
                'reported_bid': 0.00,
                'link': 'https://mac.bid/lot/mac_lot_35242923'
            },
            {
                'name': 'General Merchandise 06-04 #2',
                'mac_lot_id': 'mac_lot_35684618',
                'reported_retail': 16562.34,
                'reported_bid': 0.00,
                'link': 'https://mac.bid/lot/mac_lot_35684618'
            },
            {
                'name': 'General Merchandise 06-05',
                'mac_lot_id': 'mac_lot_35739734',
                'reported_retail': 14730.09,
                'reported_bid': 0.00,
                'link': 'https://mac.bid/lot/mac_lot_35739734'
            },
            {
                'name': 'GIGABYTE GeForce RTX 4090 AERO OC Graphics Card',
                'mac_lot_id': 'mac_lot_35764632',
                'reported_retail': 3399.00,
                'reported_bid': 0.00,
                'link': 'https://mac.bid/lot/mac_lot_35764632'
            },
            {
                'name': 'LG Electric Washer/Dryer Combo',
                'mac_lot_id': 'mac_lot_35812259',
                'reported_retail': 3299.00,
                'reported_bid': 0.00,
                'link': 'https://mac.bid/lot/mac_lot_35812259'
            }
        ]
    
    def extract_lot_details_from_id(self, mac_lot_id: str) -> Dict:
        """Extract auction_id and lot_id from mac_lot_id"""
        try:
            # mac_lot_id format: mac_lot_35242923
            lot_number = mac_lot_id.replace('mac_lot_', '')
            
            # Try to get lot details from NextJS API
            nextjs_url = f"https://mac.bid/_next/data/BUILD_ID/lot/{mac_lot_id}.json"
            
            # Also try direct lot page to extract IDs
            lot_page_url = f"https://mac.bid/lot/{mac_lot_id}"
            
            response = self.session.get(lot_page_url, timeout=10)
            if response.status_code == 200:
                # Extract auction_id and lot_id from page content
                content = response.text
                
                # Look for auction and lot IDs in the page
                import re
                auction_match = re.search(r'"auction_id":(\d+)', content)
                lot_match = re.search(r'"lot_id":(\d+)', content)
                
                if auction_match and lot_match:
                    return {
                        'auction_id': int(auction_match.group(1)),
                        'lot_id': int(lot_match.group(1)),
                        'mac_lot_id': mac_lot_id
                    }
            
            return None
            
        except Exception as e:
            print(f"❌ Error extracting lot details for {mac_lot_id}: {e}")
            return None
    
    def get_current_bid_data(self, auction_id: int, lot_id: int) -> Dict:
        """Get current bid data from NextJS API"""
        try:
            # Try NextJS API endpoint
            api_url = f"https://mac.bid/api/auctions/{auction_id}/lots/{lot_id}"
            
            response = self.session.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'current_bid': data.get('current_bid', 0),
                    'total_bids': data.get('total_bids', 0),
                    'retail_price': data.get('retail_price', 0),
                    'is_open': data.get('is_open', False),
                    'status': 'success'
                }
            else:
                return {'status': 'api_failed', 'status_code': response.status_code}
                
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def verify_lot(self, lot_info: Dict) -> Dict:
        """Verify a single lot's current bid status"""
        print(f"\n🔍 Verifying: {lot_info['name']}")
        print(f"🔗 Link: {lot_info['link']}")
        
        # Extract lot details
        lot_details = self.extract_lot_details_from_id(lot_info['mac_lot_id'])
        
        if not lot_details:
            return {
                'lot': lot_info['name'],
                'status': 'failed_to_extract_ids',
                'link': lot_info['link']
            }
        
        # Get current bid data
        bid_data = self.get_current_bid_data(lot_details['auction_id'], lot_details['lot_id'])
        
        if bid_data.get('status') == 'success':
            current_bid = bid_data.get('current_bid', 0)
            reported_bid = lot_info['reported_bid']
            
            verification_result = {
                'lot': lot_info['name'],
                'link': lot_info['link'],
                'reported_bid': reported_bid,
                'actual_bid': current_bid,
                'bid_match': abs(current_bid - reported_bid) < 0.01,
                'retail_price': bid_data.get('retail_price', 0),
                'total_bids': bid_data.get('total_bids', 0),
                'is_open': bid_data.get('is_open', False),
                'status': 'verified'
            }
            
            # Print verification results
            if verification_result['bid_match']:
                print(f"✅ BID VERIFIED: ${current_bid:.2f} (matches reported ${reported_bid:.2f})")
            else:
                print(f"⚠️  BID MISMATCH: Actual ${current_bid:.2f} vs Reported ${reported_bid:.2f}")
            
            print(f"📊 Total Bids: {bid_data.get('total_bids', 0)}")
            print(f"💰 Retail Price: ${bid_data.get('retail_price', 0):.2f}")
            print(f"🔓 Is Open: {bid_data.get('is_open', 'Unknown')}")
            
            return verification_result
        else:
            print(f"❌ Failed to get current bid data: {bid_data}")
            return {
                'lot': lot_info['name'],
                'link': lot_info['link'],
                'status': 'api_failed',
                'error': bid_data
            }
    
    async def verify_all_lots(self) -> List[Dict]:
        """Verify all top lots"""
        print("🔍 BID DATA VERIFICATION REPORT")
        print("=" * 60)
        
        # STEP 1: AUTHENTICATE FIRST (MANDATORY)
        if not await self.setup_authentication():
            print("❌ Cannot proceed without authentication")
            return []
        
        # STEP 2: Setup lots to verify
        self.setup_top_lots()
        
        print(f"Verifying {len(self.top_lots)} top opportunities...")
        
        results = []
        
        for i, lot in enumerate(self.top_lots, 1):
            print(f"\n[{i}/{len(self.top_lots)}]", end=" ")
            result = self.verify_lot(lot)
            results.append(result)
            time.sleep(1)  # Be respectful to the API
        
        # Summary
        print(f"\n\n📊 VERIFICATION SUMMARY")
        print("=" * 40)
        
        verified_count = len([r for r in results if r.get('status') == 'verified'])
        matched_count = len([r for r in results if r.get('bid_match') == True])
        
        print(f"✅ Successfully Verified: {verified_count}/{len(results)}")
        print(f"🎯 Bid Data Matches: {matched_count}/{verified_count}")
        
        if matched_count == verified_count and verified_count > 0:
            print(f"🏆 PERFECT ACCURACY: All bid data is correct!")
        elif matched_count > 0:
            print(f"⚠️  PARTIAL ACCURACY: {matched_count}/{verified_count} bids match")
        else:
            print(f"❌ ACCURACY ISSUES: Bid data may be outdated")
        
        return results

async def main():
    """Run bid verification"""
    verifier = BidDataVerifier()
    results = await verifier.verify_all_lots()
    
    print(f"\n🔗 DIRECT LINKS FOR MANUAL VERIFICATION:")
    print("-" * 50)
    for lot in verifier.top_lots:
        print(f"• {lot['name']}")
        print(f"  {lot['link']}")
        print()

if __name__ == "__main__":
    asyncio.run(main()) 