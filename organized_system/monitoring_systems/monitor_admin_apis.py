#!/usr/bin/env python3
"""
Monitor mac.bid admin/seller areas for product addition APIs.
Focus on areas where products would be created/added.
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from playwright.async_api import async_playwright
from src.scraper.auth_handler import create_auth_credentials


async def monitor_admin_areas():
    """Monitor admin/seller areas for product addition APIs."""
    print("🔍 MAC.BID Admin/Seller API Monitor")
    print("=" * 50)
    
    auth_creds = create_auth_credentials(
        username="darvonshops@gmail.com",
        password="^sy3i@NiV14tv7",
        auth_type="form"
    )
    
    product_apis = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Monitor all requests
        async def handle_request(request):
            url = request.url.lower()
            method = request.method
            post_data = request.post_data or ''
            
            # Look for product/auction related APIs
            if any(keyword in url for keyword in ['product', 'auction', 'item', 'listing', 'inventory']):
                if method in ['POST', 'PUT', 'PATCH']:  # Creation/update operations
                    api_call = {
                        'method': method,
                        'url': request.url,
                        'post_data': post_data[:500] if post_data else None,
                        'timestamp': time.time()
                    }
                    product_apis.append(api_call)
                    print(f"🎯 CREATION API: {method} {request.url}")
                    if post_data:
                        print(f"   Data: {post_data[:200]}...")
        
        page.on('request', handle_request)
        
        try:
            # Login first
            print("🔐 Logging in...")
            await page.goto("https://mac.bid", wait_until='domcontentloaded')
            await asyncio.sleep(3)
            
            login_button = await page.query_selector('button:has-text("Log In")')
            if login_button:
                await login_button.click()
                await asyncio.sleep(2)
                
                email_field = await page.query_selector('input[name="email"], #si-email')
                password_field = await page.query_selector('input[name="password"], #si-password')
                
                if email_field and password_field:
                    await email_field.fill(auth_creds.username)
                    await password_field.fill(auth_creds.password)
                    await password_field.press('Enter')
                    await asyncio.sleep(5)
                    print("✅ Login successful!")
            
            # Try to find admin/seller areas
            admin_urls = [
                "https://mac.bid/sell",
                "https://mac.bid/admin",
                "https://mac.bid/dashboard",
                "https://mac.bid/account",
                "https://mac.bid/account/sell",
                "https://mac.bid/account/listings",
                "https://mac.bid/account/inventory",
                "https://mac.bid/seller",
                "https://mac.bid/seller/dashboard",
                "https://mac.bid/add-product",
                "https://mac.bid/create-auction",
                "https://mac.bid/list-item"
            ]
            
            for url in admin_urls:
                try:
                    print(f"\n📍 Trying: {url}")
                    await page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    await asyncio.sleep(3)
                    
                    # Look for forms or buttons that might create products
                    create_buttons = await page.query_selector_all(
                        'button:has-text("Create"), button:has-text("Add"), button:has-text("List"), '
                        'button:has-text("Submit"), button:has-text("Post"), '
                        'input[type="submit"], .create-btn, .add-btn, .submit-btn'
                    )
                    
                    if create_buttons:
                        print(f"   Found {len(create_buttons)} potential creation buttons")
                        # Try clicking the first one to see what API it calls
                        try:
                            await create_buttons[0].click()
                            await asyncio.sleep(2)
                            print("   Clicked creation button")
                        except Exception as e:
                            print(f"   Could not click button: {e}")
                    
                except Exception as e:
                    print(f"   ❌ Could not access: {e}")
                    continue
            
            # Also try looking for API documentation or endpoints
            api_docs_urls = [
                "https://api.macdiscount.com/docs",
                "https://api.macdiscount.com/swagger",
                "https://api.macdiscount.com/",
                "https://mac.bid/api",
                "https://mac.bid/api/docs"
            ]
            
            print("\n🔍 Checking for API documentation...")
            for url in api_docs_urls:
                try:
                    await page.goto(url, wait_until='domcontentloaded', timeout=10000)
                    await asyncio.sleep(2)
                    print(f"✅ Found: {url}")
                    
                    # Take a screenshot of API docs if found
                    await page.screenshot(path=f'api_docs_{int(time.time())}.png')
                    
                except Exception:
                    print(f"❌ Not found: {url}")
            
            print(f"\n📊 Summary:")
            print(f"Found {len(product_apis)} product-related creation APIs")
            
            if product_apis:
                print("\n🎯 Product Creation APIs Found:")
                for api in product_apis:
                    print(f"  {api['method']} {api['url']}")
                    if api['post_data']:
                        print(f"    Data: {api['post_data'][:100]}...")
            else:
                print("\n💡 No product creation APIs found in accessible areas.")
                print("   This suggests:")
                print("   1. Product addition might be restricted to admin users")
                print("   2. APIs might be called from different domains")
                print("   3. Product addition might use different endpoints")
            
            # Save results
            with open('admin_api_analysis.json', 'w') as f:
                json.dump(product_apis, f, indent=2, default=str)
            print(f"\n💾 Results saved to admin_api_analysis.json")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(monitor_admin_areas()) 