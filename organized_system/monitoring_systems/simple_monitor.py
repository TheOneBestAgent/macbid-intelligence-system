#!/usr/bin/env python3
"""
Simplified Real-time Product Monitor for mac.bid
Shows exactly what's happening and detects new products.
Now with location filtering!
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import hashlib
import ssl
import sys

class SimpleProductMonitor:
    def __init__(self, filter_locations=None):
        self.known_products = set()
        self.new_products = []
        self.session = None
        self.filter_locations = filter_locations or []  # List of location IDs to monitor
        
    async def create_session(self):
        """Create a persistent HTTP session with proper SSL handling."""
        # Create SSL context that's more permissive
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=10,
            limit_per_host=5,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
    async def close_session(self):
        """Properly close the session."""
        if self.session:
            await self.session.close()
            # Wait a bit for the underlying connections to close
            await asyncio.sleep(0.1)
        
    def should_include_auction(self, product):
        """Check if auction should be included based on location filter."""
        if not self.filter_locations:
            return True  # No filter = include all
        
        location_id = product.get('location_id')
        if location_id is None:
            return False  # Skip auctions without location
        
        # Convert to string for comparison (API might return int or string)
        return str(location_id) in [str(loc) for loc in self.filter_locations]
        
    async def fetch_products(self, page=1):
        """Fetch products from mac.bid API."""
        if not self.session:
            await self.create_session()
            
        url = f"https://api.macdiscount.com/auctionsummary?pg={page}&ppg=20"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    # Handle different possible response formats
                    if 'data' in data:
                        all_products = data['data']
                    elif 'items' in data:
                        all_products = data['items']
                    elif isinstance(data, list):
                        all_products = data
                    else:
                        print(f"📊 API response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                        return []
                    
                    # Apply location filter
                    if self.filter_locations:
                        filtered_products = [p for p in all_products if self.should_include_auction(p)]
                        return filtered_products
                    else:
                        return all_products
                else:
                    print(f"⚠️  API returned status {response.status}")
                    return []
        except asyncio.TimeoutError:
            print(f"⚠️  Timeout fetching page {page}")
            return []
        except Exception as e:
            print(f"⚠️  Error fetching page {page}: {str(e)[:100]}")
            return []
    
    def get_product_id(self, product):
        """Get unique ID for a product."""
        # Try common ID fields
        for field in ['id', 'auction_id', 'product_id', 'auction_number']:
            if field in product and product[field]:
                return str(product[field])
        
        # Fallback: hash multiple fields
        title = product.get('title', product.get('auction_number', ''))
        date = product.get('date_created', product.get('closing_date', ''))
        if title:
            return hashlib.md5(f"{title}_{date}".encode()).hexdigest()[:12]
        return None
    
    def get_product_title(self, product):
        """Extract a readable title from product data."""
        # Try different title fields
        for field in ['title', 'auction_number', 'external_folder_name']:
            if field in product and product[field]:
                return str(product[field])
        return f"Auction {product.get('id', 'Unknown')}"
    
    async def initialize(self):
        """Initialize with current products."""
        if self.filter_locations:
            print(f"📊 Initializing with current auctions (filtering for locations: {', '.join(map(str, self.filter_locations))})...")
        else:
            print("📊 Initializing with current auctions (all locations)...")
        
        total_products = 0
        total_filtered = 0
        
        for page in range(1, 4):  # Check first 3 pages
            print(f"   Scanning page {page}...")
            products = await self.fetch_products(page)
            
            if products:
                print(f"   ✅ Found {len(products)} matching auctions on page {page}")
                # Show sample product structure only once
                if page == 1 and products:
                    sample = products[0]
                    print(f"   📋 Sample auction keys: {list(sample.keys())[:10]}...")
                    if self.filter_locations:
                        print(f"   📍 Sample location: {sample.get('location_id', 'N/A')}")
            else:
                if self.filter_locations:
                    print(f"   ❌ No matching auctions found on page {page} (location filter applied)")
                else:
                    print(f"   ❌ No auctions found on page {page}")
            
            for product in products:
                product_id = self.get_product_id(product)
                if product_id:
                    self.known_products.add(product_id)
                    total_products += 1
        
        if self.filter_locations:
            print(f"✅ Initialized with {total_products} auctions from your selected locations")
        else:
            print(f"✅ Initialized with {total_products} known auctions")
        return total_products > 0
    
    async def check_for_new_products(self):
        """Check for new products."""
        new_found = []
        
        for page in range(1, 3):  # Check first 2 pages
            products = await self.fetch_products(page)
            
            for product in products:
                product_id = self.get_product_id(product)
                
                if product_id and product_id not in self.known_products:
                    new_found.append(product)
                    self.known_products.add(product_id)
        
        return new_found
    
    async def monitor(self):
        """Main monitoring loop."""
        print("🔥 Simple Real-time Product Monitor")
        if self.filter_locations:
            print(f"📍 Monitoring locations: {', '.join(map(str, self.filter_locations))}")
        print("=" * 50)
        
        try:
            # Initialize
            if not await self.initialize():
                if self.filter_locations:
                    print("❌ No auctions found for your selected locations - they might all be closed or API might be down")
                else:
                    print("❌ Failed to initialize - API might be down")
                return
            
            print(f"🚀 Starting monitoring (checking every 10 seconds)...")
            print(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
            print("💡 Press Ctrl+C to stop monitoring")
            
            check_count = 0
            
            while True:
                try:
                    check_count += 1
                    current_time = datetime.now()
                    
                    # Check for new products
                    new_products = await self.check_for_new_products()
                    
                    if new_products:
                        for product in new_products:
                            product_id = self.get_product_id(product)
                            title = self.get_product_title(product)
                            closing_date = product.get('closing_date', 'Unknown')
                            auction_number = product.get('auction_number', 'Unknown')
                            location_id = product.get('location_id', 'Unknown')
                            
                            print(f"\n🆕 NEW AUCTION DETECTED!")
                            print(f"   🆔 ID: {product_id}")
                            print(f"   📝 Title: {title}")
                            print(f"   🔢 Auction #: {auction_number}")
                            print(f"   📍 Location: {location_id}")
                            print(f"   📅 Closes: {closing_date}")
                            print(f"   ⏰ Detected: {current_time.strftime('%H:%M:%S')}")
                            
                            # Save to file
                            self.new_products.append({
                                'timestamp': current_time.isoformat(),
                                'id': product_id,
                                'title': title,
                                'auction_number': auction_number,
                                'location_id': location_id,
                                'closing_date': closing_date,
                                'full_data': product
                            })
                            
                            with open('new_products_simple.json', 'w') as f:
                                json.dump(self.new_products, f, indent=2, default=str)
                            
                            # Also log to simple file
                            with open('product_alerts_simple.log', 'a') as f:
                                f.write(f"{current_time.isoformat()} - NEW: {title} ({auction_number}) at Location {location_id}\n")
                    
                    # Status update every 6 checks (1 minute)
                    if check_count % 6 == 0:
                        location_info = f" from {len(self.filter_locations)} locations" if self.filter_locations else ""
                        print(f"⏰ {current_time.strftime('%H:%M:%S')} - Monitoring{location_info}... ({len(self.known_products)} auctions tracked, {len(self.new_products)} new found)")
                    
                    await asyncio.sleep(10)  # Check every 10 seconds
                    
                except KeyboardInterrupt:
                    print("\n👋 Monitoring stopped by user")
                    break
                except Exception as e:
                    print(f"⚠️  Error during monitoring: {str(e)[:100]}")
                    await asyncio.sleep(30)  # Wait longer on error
                    
        finally:
            # Always clean up the session
            await self.close_session()

def parse_locations(location_str):
    """Parse location string into list of location IDs."""
    if not location_str:
        return []
    
    locations = []
    for loc in location_str.split(','):
        loc = loc.strip()
        if loc.isdigit():
            locations.append(int(loc))
        else:
            print(f"⚠️  Invalid location ID: {loc} (must be a number)")
    
    return locations

async def main():
    # Check for command line arguments
    filter_locations = []
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("🔥 Simple Real-time Product Monitor for mac.bid")
            print("\nUsage:")
            print("  python3 simple_monitor.py                    # Monitor all locations")
            print("  python3 simple_monitor.py 1,6,13,16,25      # Monitor specific locations")
            print("  python3 simple_monitor.py --help            # Show this help")
            print("\nExamples:")
            print("  python3 simple_monitor.py 1,6,13           # Monitor locations 1, 6, and 13")
            print("  python3 simple_monitor.py 25               # Monitor only location 25")
            return
        else:
            # Parse locations from command line
            filter_locations = parse_locations(sys.argv[1])
            if not filter_locations:
                print("❌ No valid location IDs provided. Use --help for usage info.")
                return
    else:
        # Interactive mode - ask user for locations
        print("🔥 Simple Real-time Product Monitor Setup")
        print("=" * 40)
        print("Which mac.bid warehouse locations can you shop at?")
        print("(Enter location IDs separated by commas, or press Enter for all locations)")
        print("\nExample: 1,6,13,16,25")
        
        user_input = input("Your locations: ").strip()
        if user_input:
            filter_locations = parse_locations(user_input)
            if not filter_locations:
                print("❌ No valid location IDs provided. Monitoring all locations instead.")
        
        print()  # Add spacing
    
    monitor = SimpleProductMonitor(filter_locations=filter_locations)
    await monitor.monitor()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}") 