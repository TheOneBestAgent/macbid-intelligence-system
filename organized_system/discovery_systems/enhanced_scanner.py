#!/usr/bin/env python3
"""
🔍 Enhanced High-Volume Scanner
Explores different API parameters to find ALL auctions
"""

import asyncio
import aiohttp
import ssl
import json
import time
from datetime import datetime
from collections import defaultdict

class EnhancedScanner:
    def __init__(self):
        self.session = None
        self.total_found = 0
        
    async def create_session(self):
        """Create HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=10)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        )
        
    async def close_session(self):
        if self.session:
            await self.session.close()
            await asyncio.sleep(0.25)
            
    async def test_api_parameters(self):
        """Test different API parameters to find more auctions."""
        print("🔍 Testing Different API Parameters")
        print("=" * 50)
        
        test_params = [
            {},  # Default
            {"status": "all"},
            {"status": "open"},
            {"status": "closed"},
            {"include_closed": "1"},
            {"include_inactive": "1"},
            {"show_all": "1"},
            {"active": "1"},
            {"active": "0"},
            {"type": "all"},
        ]
        
        results = {}
        
        for i, params in enumerate(test_params):
            param_str = "&".join([f"{k}={v}" for k, v in params.items()]) if params else "default"
            
            try:
                url = "https://api.macdiscount.com/auctionsummary?pg=1&ppg=100"
                if params:
                    url += "&" + "&".join([f"{k}={v}" for k, v in params.items()])
                    
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        auctions = data.get('data', [])
                        results[param_str] = len(auctions)
                        print(f"  {i+1:2d}. {param_str:20s}: {len(auctions):3d} auctions")
                    else:
                        print(f"  {i+1:2d}. {param_str:20s}: HTTP {response.status}")
                        
                await asyncio.sleep(0.2)
                
            except Exception as e:
                print(f"  {i+1:2d}. {param_str:20s}: Error - {str(e)[:30]}...")
                
        return results
        
    async def discover_max_pages_with_params(self, params=None):
        """Binary search to find max pages with specific parameters."""
        base_url = "https://api.macdiscount.com/auctionsummary"
        
        low, high = 1, 10000  # Much higher upper bound
        last_valid_page = 1
        
        while low <= high:
            mid = (low + high) // 2
            
            url = f"{base_url}?pg={mid}&ppg=100"
            if params:
                url += "&" + "&".join([f"{k}={v}" for k, v in params.items()])
                
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        auctions = data.get('data', [])
                        
                        if auctions:
                            last_valid_page = mid
                            low = mid + 1
                            print(f"📊 Page {mid}: {len(auctions)} auctions (searching higher)")
                        else:
                            high = mid - 1
                            print(f"📊 Page {mid}: Empty (searching lower)")
                    else:
                        high = mid - 1
                        print(f"📊 Page {mid}: HTTP {response.status} (searching lower)")
                        
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"📊 Page {mid}: Error - {str(e)[:30]}...")
                high = mid - 1
                
        return last_valid_page
        
    async def scan_with_large_pages(self, location_filter=None, params=None):
        """Scan using 100 auctions per page."""
        print("🚀 Enhanced High-Volume Scan (100 per page)")
        print("=" * 60)
        
        # Discover total pages
        max_pages = await self.discover_max_pages_with_params(params)
        print(f"✅ Found {max_pages} total pages")
        print(f"🎯 Estimated total auctions: ~{max_pages * 100}")
        print()
        
        base_url = "https://api.macdiscount.com/auctionsummary"
        all_auctions = []
        
        # Scan all pages
        for page in range(1, max_pages + 1):
            url = f"{base_url}?pg={page}&ppg=100"
            if params:
                url += "&" + "&".join([f"{k}={v}" for k, v in params.items()])
                
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        auctions = data.get('data', [])
                        all_auctions.extend(auctions)
                        
                        print(f"📄 Page {page:3d}: {len(auctions):3d} auctions | Total: {len(all_auctions):5d}")
                    else:
                        print(f"⚠️  Page {page}: HTTP {response.status}")
                        
                await asyncio.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Page {page}: {str(e)[:50]}...")
                
        # Filter by location if specified
        if location_filter:
            filtered_auctions = []
            for auction in all_auctions:
                if auction.get('location_id') in location_filter:
                    filtered_auctions.append(auction)
            print(f"\n📍 Filtered to {len(filtered_auctions)} auctions in your locations")
            all_auctions = filtered_auctions
            
        return all_auctions
        
    def analyze_locations(self, auctions):
        """Analyze auction distribution by location."""
        by_location = defaultdict(int)
        for auction in auctions:
            location_id = auction.get('location_id', 'Unknown')
            by_location[location_id] += 1
            
        print(f"\n📊 Location Distribution (Top 20):")
        sorted_locations = sorted(by_location.items(), key=lambda x: x[1], reverse=True)
        for location_id, count in sorted_locations[:20]:
            print(f"   Location {location_id}: {count:4d} auctions")
            
        # Highlight SC locations
        sc_locations = [17, 20, 28, 34, 36]
        sc_total = sum(by_location.get(loc, 0) for loc in sc_locations)
        print(f"\n🎯 Your SC Locations Total: {sc_total} auctions")
        for loc in sc_locations:
            count = by_location.get(loc, 0)
            if count > 0:
                print(f"   Location {loc}: {count} auctions")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Scanner')
    parser.add_argument('--test-params', action='store_true', help='Test different API parameters')
    parser.add_argument('--scan-all', action='store_true', help='Scan all auctions with best parameters')
    parser.add_argument('--locations', type=str, help='Comma-separated location IDs')
    
    args = parser.parse_args()
    
    scanner = EnhancedScanner()
    await scanner.create_session()
    
    try:
        if args.test_params:
            await scanner.test_api_parameters()
            
        elif args.scan_all:
            location_filter = None
            if args.locations:
                location_filter = [int(x.strip()) for x in args.locations.split(',')]
                
            # Try different parameter combinations
            param_sets = [
                None,  # Default
                {"status": "all"},
                {"include_closed": "1"},
                {"show_all": "1"}
            ]
            
            best_count = 0
            best_auctions = []
            
            for params in param_sets:
                param_name = str(params) if params else "default"
                print(f"\n🧪 Testing with parameters: {param_name}")
                
                auctions = await scanner.scan_with_large_pages(location_filter, params)
                
                if len(auctions) > best_count:
                    best_count = len(auctions)
                    best_auctions = auctions
                    
                print(f"✅ Found {len(auctions)} auctions with {param_name}")
                
            print(f"\n🏆 BEST RESULT: {best_count} auctions")
            scanner.analyze_locations(best_auctions)
            
            # Save best results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"enhanced_scan_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(best_auctions, f, indent=2)
            print(f"\n💾 Best results saved to: {filename}")
            
        else:
            print("🔍 Enhanced Scanner")
            print("Use --test-params to test API parameters")
            print("Use --scan-all to scan with all methods")
            
    finally:
        await scanner.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 