#!/usr/bin/env python3
"""
🚀 Optimized High-Volume Scanner for mac.bid
Safely scans large numbers of auctions with rate limiting and error handling
"""

import asyncio
import aiohttp
import ssl
import json
import time
from datetime import datetime
from collections import defaultdict

class OptimizedScanner:
    def __init__(self, max_concurrent=3, delay_between_requests=0.5):
        self.max_concurrent = max_concurrent
        self.delay_between_requests = delay_between_requests
        self.session = None
        self.total_scanned = 0
        self.errors = 0
        
    async def create_session(self):
        """Create optimized HTTP session with connection pooling."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Optimized connector settings
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=10,  # Total connection pool size
            limit_per_host=5,  # Max connections per host
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(
            total=30,
            connect=10,
            sock_read=10
        )
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Connection': 'keep-alive'
            }
        )
        
    async def close_session(self):
        """Properly close session and connections."""
        if self.session:
            await self.session.close()
            # Give time for connections to close
            await asyncio.sleep(0.25)
            
    async def fetch_page_safe(self, page, semaphore):
        """Safely fetch a single page with rate limiting."""
        async with semaphore:
            url = f"https://api.macdiscount.com/auctionsummary?pg={page}&ppg=20"
            
            try:
                # Rate limiting delay
                await asyncio.sleep(self.delay_between_requests)
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        auctions = data.get('data', [])
                        self.total_scanned += len(auctions)
                        
                        print(f"📄 Page {page:3d}: {len(auctions):2d} auctions | Total: {self.total_scanned:4d}")
                        return auctions
                    else:
                        print(f"⚠️  Page {page}: HTTP {response.status}")
                        self.errors += 1
                        return []
                        
            except asyncio.TimeoutError:
                print(f"⏰ Page {page}: Timeout")
                self.errors += 1
                return []
            except Exception as e:
                print(f"❌ Page {page}: {str(e)[:50]}...")
                self.errors += 1
                return []
                
    async def find_total_pages(self):
        """Discover how many pages of auctions exist."""
        print("🔍 Discovering total auction pages...")
        
        # Binary search to find the last page
        low, high = 1, 1000  # Start with reasonable upper bound
        last_valid_page = 1
        
        while low <= high:
            mid = (low + high) // 2
            url = f"https://api.macdiscount.com/auctionsummary?pg={mid}&ppg=20"
            
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
                        
                await asyncio.sleep(0.2)  # Small delay between discovery requests
                
            except Exception as e:
                print(f"📊 Page {mid}: Error - {str(e)[:30]}...")
                high = mid - 1
                
        print(f"✅ Found {last_valid_page} total pages of auctions")
        return last_valid_page
        
    async def scan_all_auctions(self, max_pages=None, location_filter=None):
        """Scan all available auctions with optimizations."""
        print("🚀 Starting Optimized High-Volume Auction Scan")
        print("=" * 60)
        start_time = time.time()
        
        if not self.session:
            await self.create_session()
            
        # Discover total pages if not specified
        if max_pages is None:
            total_pages = await self.find_total_pages()
        else:
            total_pages = max_pages
            print(f"📊 Scanning first {total_pages} pages")
            
        print(f"🎯 Target: {total_pages} pages (~{total_pages * 20} auctions)")
        print(f"⚙️  Settings: {self.max_concurrent} concurrent, {self.delay_between_requests}s delay")
        print()
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        # Create tasks for all pages
        tasks = []
        for page in range(1, total_pages + 1):
            task = self.fetch_page_safe(page, semaphore)
            tasks.append(task)
            
        # Execute all tasks with progress tracking
        all_auctions = []
        completed = 0
        
        # Process in batches to avoid overwhelming the system
        batch_size = 50
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, list):
                    all_auctions.extend(result)
                completed += 1
                
            # Progress update
            progress = (completed / len(tasks)) * 100
            print(f"📈 Progress: {completed}/{len(tasks)} pages ({progress:.1f}%)")
            
        # Filter by location if specified
        if location_filter:
            filtered_auctions = []
            for auction in all_auctions:
                if auction.get('location_id') in location_filter:
                    filtered_auctions.append(auction)
            print(f"📍 Filtered to {len(filtered_auctions)} auctions in your locations")
            all_auctions = filtered_auctions
            
        # Summary
        elapsed = time.time() - start_time
        print(f"\n✅ Scan Complete!")
        print(f"📊 Total Auctions: {len(all_auctions)}")
        print(f"⏰ Time Taken: {elapsed:.1f} seconds")
        print(f"📈 Rate: {len(all_auctions)/elapsed:.1f} auctions/second")
        print(f"❌ Errors: {self.errors}")
        
        return all_auctions
        
    def analyze_auctions(self, auctions, search_keywords=None):
        """Analyze the scanned auctions."""
        print(f"\n📊 Auction Analysis")
        print("=" * 40)
        
        # Location distribution
        by_location = defaultdict(int)
        for auction in auctions:
            location_id = auction.get('location_id', 'Unknown')
            by_location[location_id] += 1
            
        print(f"📍 Top Locations:")
        sorted_locations = sorted(by_location.items(), key=lambda x: x[1], reverse=True)
        for location_id, count in sorted_locations[:10]:
            print(f"   Location {location_id}: {count} auctions")
            
        # Search for specific items
        if search_keywords:
            print(f"\n🔍 Searching for: {', '.join(search_keywords)}")
            matches = []
            
            for auction in auctions:
                title = auction.get('title', auction.get('external_folder_name', ''))
                if title and any(keyword.lower() in title.lower() for keyword in search_keywords):
                    matches.append(auction)
                    
            print(f"🎯 Found {len(matches)} matching auctions:")
            for match in matches[:10]:  # Show first 10
                title = match.get('title', match.get('external_folder_name', 'No title'))
                location = match.get('location_id', 'Unknown')
                auction_num = match.get('auction_number', 'Unknown')
                print(f"   🎧 {title[:60]}... (Location {location}, {auction_num})")
                
            if len(matches) > 10:
                print(f"   ... and {len(matches) - 10} more")
                
        return auctions

async def main():
    """Main function with different scanning options."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Optimized mac.bid Scanner')
    parser.add_argument('--max-pages', type=int, help='Maximum pages to scan (default: auto-discover)')
    parser.add_argument('--locations', type=str, help='Comma-separated location IDs to filter')
    parser.add_argument('--search', nargs='+', help='Keywords to search for')
    parser.add_argument('--concurrent', type=int, default=3, help='Max concurrent requests')
    parser.add_argument('--delay', type=float, default=0.5, help='Delay between requests (seconds)')
    parser.add_argument('--test', action='store_true', help='Test mode (scan only 10 pages)')
    
    args = parser.parse_args()
    
    # Parse location filter
    location_filter = None
    if args.locations:
        location_filter = [int(x.strip()) for x in args.locations.split(',') if x.strip().isdigit()]
        print(f"📍 Filtering to locations: {location_filter}")
        
    # Test mode
    if args.test:
        args.max_pages = 10
        print("🧪 Test mode: Scanning only 10 pages")
        
    # Create scanner
    scanner = OptimizedScanner(
        max_concurrent=args.concurrent,
        delay_between_requests=args.delay
    )
    
    try:
        # Scan auctions
        auctions = await scanner.scan_all_auctions(
            max_pages=args.max_pages,
            location_filter=location_filter
        )
        
        # Analyze results
        scanner.analyze_auctions(auctions, args.search)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"auction_scan_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(auctions, f, indent=2)
            
        print(f"\n💾 Results saved to: {filename}")
        
    finally:
        await scanner.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 