#!/usr/bin/env python3
"""
Monitor mac.bid for product-related API endpoints during normal browsing.
This script will login and browse the site to capture API calls related to products.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import re

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from playwright.async_api import async_playwright
from src.scraper.auth_handler import create_auth_credentials


class ProductAPIMonitor:
    """Monitor for product-related API calls on mac.bid."""
    
    def __init__(self):
        self.api_calls = []
        self.product_related_calls = []
        
    def is_product_related(self, request_data):
        """Check if an API call is related to products."""
        url = request_data['url'].lower()
        method = request_data['method']
        post_data = request_data.get('post_data', '') or ''
        
        # Keywords that suggest product-related operations
        product_keywords = [
            'product', 'item', 'listing', 'auction', 'bid', 'inventory',
            'catalog', 'goods', 'merchandise', 'stock', 'sku', 'price',
            'category', 'brand', 'model', 'description', 'image', 'photo'
        ]
        
        # API patterns that suggest CRUD operations
        crud_patterns = [
            r'/api/.*/(products?|items?|listings?|auctions?)',
            r'/(products?|items?|listings?|auctions?)/\d+',
            r'/v\d+/(products?|items?|listings?|auctions?)',
            r'/(create|add|new|update|edit|delete|remove).*product',
            r'/product.*(create|add|new|update|edit|delete|remove)',
        ]
        
        # Check URL for product keywords
        for keyword in product_keywords:
            if keyword in url:
                return True
        
        # Check URL for CRUD patterns
        for pattern in crud_patterns:
            if re.search(pattern, url):
                return True
        
        # Check POST data for product-related content
        if method == 'POST' and post_data:
            post_data_lower = post_data.lower()
            for keyword in product_keywords:
                if keyword in post_data_lower:
                    return True
        
        # Check for GraphQL queries related to products
        if 'graphql' in url and post_data:
            graphql_keywords = [
                'createproduct', 'updateproduct', 'deleteproduct',
                'addproduct', 'removeproduct', 'productmutation',
                'productquery', 'getproducts', 'listproducts'
            ]
            post_data_lower = post_data.lower()
            for keyword in graphql_keywords:
                if keyword in post_data_lower:
                    return True
        
        return False
    
    async def monitor_requests(self, page):
        """Set up request monitoring on a page."""
        async def handle_request(request):
            request_data = {
                'timestamp': time.time(),
                'url': request.url,
                'method': request.method,
                'headers': dict(request.headers),
                'post_data': request.post_data,
                'resource_type': request.resource_type
            }
            
            self.api_calls.append(request_data)
            
            # Check if this is product-related
            if self.is_product_related(request_data):
                self.product_related_calls.append(request_data)
                print(f"🔍 Product API detected: {request.method} {request.url}")
        
        page.on('request', handle_request)
    
    async def browse_site_sections(self, page):
        """Browse different sections of mac.bid to trigger API calls."""
        sections_to_visit = [
            ('Home Page', 'https://mac.bid'),
            ('Browse Products', 'https://mac.bid/browse'),
            ('Categories', 'https://mac.bid/categories'),
            ('Search Results', 'https://mac.bid/search?q=laptop'),
        ]
        
        for section_name, url in sections_to_visit:
            try:
                print(f"\n📍 Visiting: {section_name} ({url})")
                await page.goto(url, wait_until='domcontentloaded', timeout=30000)
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"⚠️  Could not visit {section_name}: {e}")
                continue
    
    def analyze_product_apis(self):
        """Analyze the captured product-related API calls."""
        if not self.product_related_calls:
            print("❌ No product-related API calls found")
            return
        
        print(f"\n🎯 Found {len(self.product_related_calls)} product-related API calls:")
        print("=" * 80)
        
        for i, call in enumerate(self.product_related_calls, 1):
            print(f"\n{i}. {call['method']} {call['url']}")
            if call.get('post_data'):
                print(f"   POST Data: {call['post_data'][:200]}...")


async def main():
    """Main monitoring function."""
    print("🔍 MAC.BID Product API Monitor")
    print("=" * 50)
    
    auth_creds = create_auth_credentials(
        username="darvonshops@gmail.com",
        password="^sy3i@NiV14tv7",
        auth_type="form"
    )
    
    monitor = ProductAPIMonitor()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await monitor.monitor_requests(page)
            
            print("🔐 Logging in to mac.bid...")
            await page.goto("https://mac.bid", wait_until='domcontentloaded')
            await asyncio.sleep(5)
            
            # Login process
            login_button = await page.query_selector('button:has-text("Log In")')
            if login_button:
                await login_button.click()
                await asyncio.sleep(3)
                
                email_field = await page.query_selector('input[name="email"], #si-email')
                password_field = await page.query_selector('input[name="password"], #si-password')
                
                if email_field and password_field:
                    await email_field.fill(auth_creds.username)
                    await password_field.fill(auth_creds.password)
                    await password_field.press('Enter')
                    await asyncio.sleep(5)
                    print("✅ Login successful!")
            
            print("\n🌐 Browsing site sections to capture API calls...")
            await monitor.browse_site_sections(page)
            
            print(f"\n📊 Monitoring complete!")
            print(f"Total API calls captured: {len(monitor.api_calls)}")
            
            monitor.analyze_product_apis()
            
        except Exception as e:
            print(f"❌ Error during monitoring: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main()) 