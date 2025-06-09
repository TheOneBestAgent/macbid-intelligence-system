#!/usr/bin/env python3
"""
Mac.bid Page Debug Tool
======================
Analyze the Mac.bid page to understand login status and available elements
"""

import asyncio
import json
from pathlib import Path

async def debug_macbid_page():
    """Debug what's on the Mac.bid page"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed")
        return False
    
    # Load credentials
    home_creds = Path.home() / ".macbid_scraper" / "credentials.json"
    with open(home_creds, 'r') as f:
        creds = json.load(f)
    
    print(f"🔐 Debugging Mac.bid page for: {creds.get('username', 'unknown')}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, timeout=30000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to Mac.bid
            print("🌐 Navigating to Mac.bid...")
            await page.goto('https://www.mac.bid', timeout=30000)
            await page.wait_for_load_state('domcontentloaded')
            print("✅ Page loaded successfully")
            
            # Get page title and URL
            title = await page.title()
            url = page.url
            print(f"📄 Page Title: {title}")
            print(f"🌐 Current URL: {url}")
            
            # Check for login status indicators
            print("\n🔍 CHECKING LOGIN STATUS...")
            
            # Check for signed-in indicators
            signed_in_indicators = [
                'text=Sign Out',
                'text=Logout', 
                'text=My Account',
                'text=Dashboard',
                'text=Profile',
                'text=Welcome',
                '[data-testid="user-menu"]',
                '.user-menu',
                'button:has-text("Account")'
            ]
            
            is_signed_in = False
            for indicator in signed_in_indicators:
                count = await page.locator(indicator).count()
                if count > 0:
                    print(f"✅ Found signed-in indicator: {indicator} ({count} elements)")
                    is_signed_in = True
                else:
                    print(f"❌ Not found: {indicator}")
            
            print(f"\n🎯 LOGIN STATUS: {'ALREADY SIGNED IN' if is_signed_in else 'NOT SIGNED IN'}")
            
            # If not signed in, look for login elements
            if not is_signed_in:
                print("\n🔍 LOOKING FOR LOGIN ELEMENTS...")
                
                login_indicators = [
                    'text=Sign In',
                    'text=Login',
                    'text=Log In',
                    'a[href*="login"]',
                    'a[href*="sign-in"]',
                    'button:has-text("Sign In")',
                    'button:has-text("Login")',
                    '[data-testid="login"]',
                    '.login-btn'
                ]
                
                for indicator in login_indicators:
                    count = await page.locator(indicator).count()
                    if count > 0:
                        print(f"✅ Found login element: {indicator} ({count} elements)")
                    else:
                        print(f"❌ Not found: {indicator}")
            
            # Get all links on the page
            print("\n🔗 ALL LINKS ON PAGE:")
            links = await page.locator('a').all()
            for i, link in enumerate(links[:10]):  # Show first 10 links
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href and text:
                        print(f"   {i+1}. {text.strip()[:30]} -> {href}")
                except:
                    pass
            
            # Get all buttons on the page
            print("\n🔘 ALL BUTTONS ON PAGE:")
            buttons = await page.locator('button').all()
            for i, button in enumerate(buttons[:10]):  # Show first 10 buttons
                try:
                    text = await button.inner_text()
                    if text:
                        print(f"   {i+1}. {text.strip()[:30]}")
                except:
                    pass
            
            # Take detailed screenshot
            await page.screenshot(path='macbid_debug.png', full_page=True)
            print("\n📸 Full page screenshot saved: macbid_debug.png")
            
            # Check page content for specific words
            print("\n📝 PAGE CONTENT ANALYSIS:")
            page_content = await page.content()
            
            keywords = ['sign in', 'login', 'sign up', 'register', 'account', 'profile', 'dashboard']
            for keyword in keywords:
                if keyword.lower() in page_content.lower():
                    print(f"✅ Found keyword: {keyword}")
                else:
                    print(f"❌ Missing keyword: {keyword}")
            
            # Keep browser open for manual inspection
            print("\n⏸️ Browser will stay open for 30 seconds for manual inspection...")
            await page.wait_for_timeout(30000)
            
            await browser.close()
            return is_signed_in
            
        except Exception as e:
            print(f"❌ Debug failed: {e}")
            await browser.close()
            return False

if __name__ == "__main__":
    result = asyncio.run(debug_macbid_page())
    print(f"\n🎯 FINAL RESULT: {'USER IS LOGGED IN' if result else 'USER NEEDS TO LOG IN'}") 