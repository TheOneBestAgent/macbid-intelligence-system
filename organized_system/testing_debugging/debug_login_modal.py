#!/usr/bin/env python3
"""
Debug script to click the Log In button and inspect the modal.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from playwright.async_api import async_playwright


async def debug_login_modal():
    """Debug the mac.bid login modal."""
    print("🔍 Debugging mac.bid login modal...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to False to see what's happening
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("📡 Navigating to main page...")
            await page.goto("https://mac.bid", wait_until='domcontentloaded', timeout=60000)
            
            print("⏳ Waiting for page to load...")
            await asyncio.sleep(5)
            
            print("📄 Page title:", await page.title())
            print("🌐 Current URL:", page.url)
            
            # Look for the Log In button
            print("\n🔍 Looking for Log In button...")
            login_buttons = await page.query_selector_all('button:has-text("Log In")')
            print(f"Found {len(login_buttons)} Log In buttons")
            
            if login_buttons:
                print("🖱️ Clicking the Log In button...")
                await login_buttons[0].click()
                
                # Wait for modal to appear
                print("⏳ Waiting for login modal to appear...")
                await asyncio.sleep(3)
                
                # Look for modal or popup
                print("\n🔍 Looking for modal elements...")
                modals = await page.query_selector_all('.modal, [role="dialog"], .popup, .login-modal')
                print(f"Found {len(modals)} modal elements")
                
                # Look for input fields again
                print("\n🔍 Looking for input fields after clicking login...")
                inputs = await page.query_selector_all('input')
                print(f"Found {len(inputs)} input fields:")
                
                for i, input_elem in enumerate(inputs):
                    input_type = await input_elem.get_attribute('type') or 'text'
                    input_name = await input_elem.get_attribute('name') or 'no-name'
                    input_id = await input_elem.get_attribute('id') or 'no-id'
                    input_placeholder = await input_elem.get_attribute('placeholder') or 'no-placeholder'
                    input_class = await input_elem.get_attribute('class') or 'no-class'
                    
                    # Check if the input is visible
                    is_visible = await input_elem.is_visible()
                    
                    print(f"  {i+1}. Type: {input_type}, Name: {input_name}, ID: {input_id}")
                    print(f"      Placeholder: {input_placeholder}")
                    print(f"      Class: {input_class}")
                    print(f"      Visible: {is_visible}")
                    print()
                
                # Look for forms again
                print("🔍 Looking for forms after clicking login...")
                forms = await page.query_selector_all('form')
                print(f"Found {len(forms)} forms:")
                
                for i, form in enumerate(forms):
                    form_action = await form.get_attribute('action') or 'no-action'
                    form_method = await form.get_attribute('method') or 'GET'
                    form_class = await form.get_attribute('class') or 'no-class'
                    is_visible = await form.is_visible()
                    
                    print(f"  {i+1}. Action: {form_action}, Method: {form_method}")
                    print(f"      Class: {form_class}")
                    print(f"      Visible: {is_visible}")
                    print()
                
                # Take a screenshot after clicking login
                await page.screenshot(path='mac_bid_after_login_click.png')
                print("📸 Saved screenshot to 'mac_bid_after_login_click.png'")
                
                # Save page content after clicking login
                content = await page.content()
                with open('mac_bid_after_login_click.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print("💾 Saved page content to 'mac_bid_after_login_click.html'")
                
                # Wait a bit more to see if anything else loads
                print("⏳ Waiting a bit more for any dynamic content...")
                await asyncio.sleep(5)
                
                # Check for any iframes (login might be in an iframe)
                print("\n🔍 Looking for iframes...")
                iframes = await page.query_selector_all('iframe')
                print(f"Found {len(iframes)} iframes:")
                
                for i, iframe in enumerate(iframes):
                    iframe_src = await iframe.get_attribute('src') or 'no-src'
                    iframe_name = await iframe.get_attribute('name') or 'no-name'
                    iframe_id = await iframe.get_attribute('id') or 'no-id'
                    
                    print(f"  {i+1}. Src: {iframe_src}")
                    print(f"      Name: {iframe_name}, ID: {iframe_id}")
                    print()
            
            else:
                print("❌ No Log In button found!")
            
            print("\n✅ Debug complete!")
            
        except Exception as e:
            print(f"❌ Error during debug: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_login_modal()) 