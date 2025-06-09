#!/usr/bin/env python3
"""
Simple Mac.bid Login Test
========================
Test if we can successfully log into Mac.bid with credentials
"""

import asyncio
import json
from pathlib import Path

async def test_macbid_login():
    """Test Mac.bid login process"""
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("❌ Playwright not installed. Run: pip install playwright && playwright install chromium")
        return False
    
    # Load credentials
    home_creds = Path.home() / ".macbid_scraper" / "credentials.json"
    if not home_creds.exists():
        print("❌ No credentials found")
        return False
    
    with open(home_creds, 'r') as f:
        creds = json.load(f)
    
    email = creds.get('username', '')
    password = creds.get('password', '')
    
    if not email or not password:
        print("❌ Invalid credentials")
        return False
    
    print(f"🔐 Testing login for: {email}")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, timeout=30000)
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # Navigate to Mac.bid
            print("🌐 Navigating to Mac.bid...")
            await page.goto('https://www.mac.bid', timeout=30000)
            await page.wait_for_load_state('domcontentloaded')
            print("✅ Page loaded successfully")
            
            # Take screenshot for debugging
            await page.screenshot(path='macbid_homepage.png')
            print("📸 Screenshot saved: macbid_homepage.png")
            
            # Look for login elements
            print("🔍 Looking for login elements...")
            
            # Check if already logged in
            if await page.locator('text=Sign Out').count() > 0:
                print("✅ Already logged in!")
                await browser.close()
                return True
            
            # Try to find login button
            login_selectors = [
                'text=Sign In',
                'text=Login', 
                'a[href*="login"]',
                'a[href*="sign-in"]',
                'button:has-text("Sign In")',
                '[data-testid="login"]'
            ]
            
            login_found = False
            for selector in login_selectors:
                if await page.locator(selector).count() > 0:
                    print(f"✅ Found login element: {selector}")
                    await page.locator(selector).first.click()
                    login_found = True
                    break
            
            if not login_found:
                print("❌ No login button found")
                await page.screenshot(path='no_login_found.png')
                await browser.close()
                return False
            
            # Wait for login form
            await page.wait_for_timeout(2000)
            
            # Fill in credentials
            print("📝 Filling in credentials...")
            
            # Try different email field selectors
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="email"]',
                'input[id*="email"]'
            ]
            
            email_filled = False
            for selector in email_selectors:
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, email)
                    email_filled = True
                    print(f"✅ Email filled with selector: {selector}")
                    break
            
            if not email_filled:
                print("❌ Email field not found")
                await page.screenshot(path='no_email_field.png')
                await browser.close()
                return False
            
            # Try different password field selectors
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="password"]',
                'input[id*="password"]'
            ]
            
            password_filled = False
            for selector in password_selectors:
                if await page.locator(selector).count() > 0:
                    await page.fill(selector, password)
                    password_filled = True
                    print(f"✅ Password filled with selector: {selector}")
                    break
            
            if not password_filled:
                print("❌ Password field not found")
                await page.screenshot(path='no_password_field.png')
                await browser.close()
                return False
            
            # Submit the form
            print("🚀 Submitting login form...")
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Sign In")',
                'button:has-text("Login")',
                'button:has-text("Submit")'
            ]
            
            submit_clicked = False
            for selector in submit_selectors:
                if await page.locator(selector).count() > 0:
                    await page.click(selector)
                    submit_clicked = True
                    print(f"✅ Submit clicked with selector: {selector}")
                    break
            
            if not submit_clicked:
                # Try pressing Enter
                await page.keyboard.press('Enter')
                print("✅ Pressed Enter to submit")
            
            # Wait for login to complete
            await page.wait_for_timeout(5000)
            
            # Check if login was successful
            current_url = page.url
            print(f"🌐 Current URL: {current_url}")
            
            # Take screenshot after login attempt
            await page.screenshot(path='after_login.png')
            print("📸 Screenshot saved: after_login.png")
            
            # Check for success indicators
            success_indicators = [
                'text=Sign Out',
                'text=My Account',
                'text=Dashboard',
                'text=Profile'
            ]
            
            login_successful = False
            for indicator in success_indicators:
                if await page.locator(indicator).count() > 0:
                    print(f"✅ Login successful! Found: {indicator}")
                    login_successful = True
                    break
            
            # Check for error messages
            error_indicators = [
                'text=Invalid',
                'text=Error',
                'text=Failed',
                'text=Incorrect'
            ]
            
            for error in error_indicators:
                if await page.locator(error).count() > 0:
                    print(f"❌ Login error found: {error}")
            
            await browser.close()
            return login_successful
            
        except Exception as e:
            print(f"❌ Login test failed: {e}")
            await page.screenshot(path='login_error.png')
            await browser.close()
            return False

if __name__ == "__main__":
    result = asyncio.run(test_macbid_login())
    print(f"\n🎯 LOGIN TEST RESULT: {'SUCCESS' if result else 'FAILED'}") 