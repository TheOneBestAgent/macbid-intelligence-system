#!/usr/bin/env python3
"""
Debug script to inspect the mac.bid login page structure.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from playwright.async_api import async_playwright


async def debug_login_page():
    """Debug the mac.bid login page to understand its structure."""
    print("🔍 Debugging mac.bid login page...")
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False)  # Set to False to see what's happening
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            print("📡 Navigating to login page...")
            await page.goto("https://www.mac.bid/login", wait_until='domcontentloaded', timeout=60000)
            
            print("⏳ Waiting for page to load...")
            await asyncio.sleep(10)  # Give time for JavaScript to load
            
            print("📄 Page title:", await page.title())
            print("🌐 Current URL:", page.url)
            
            # Get page content
            content = await page.content()
            print(f"📝 Page content length: {len(content)} characters")
            
            # Look for all input fields
            print("\n🔍 Looking for input fields...")
            inputs = await page.query_selector_all('input')
            print(f"Found {len(inputs)} input fields:")
            
            for i, input_elem in enumerate(inputs):
                input_type = await input_elem.get_attribute('type') or 'text'
                input_name = await input_elem.get_attribute('name') or 'no-name'
                input_id = await input_elem.get_attribute('id') or 'no-id'
                input_placeholder = await input_elem.get_attribute('placeholder') or 'no-placeholder'
                input_class = await input_elem.get_attribute('class') or 'no-class'
                
                print(f"  {i+1}. Type: {input_type}, Name: {input_name}, ID: {input_id}")
                print(f"      Placeholder: {input_placeholder}")
                print(f"      Class: {input_class}")
                print()
            
            # Look for buttons
            print("🔍 Looking for buttons...")
            buttons = await page.query_selector_all('button')
            print(f"Found {len(buttons)} buttons:")
            
            for i, button in enumerate(buttons):
                button_type = await button.get_attribute('type') or 'button'
                button_text = await button.inner_text()
                button_class = await button.get_attribute('class') or 'no-class'
                button_id = await button.get_attribute('id') or 'no-id'
                
                print(f"  {i+1}. Type: {button_type}, Text: '{button_text}'")
                print(f"      Class: {button_class}, ID: {button_id}")
                print()
            
            # Look for forms
            print("🔍 Looking for forms...")
            forms = await page.query_selector_all('form')
            print(f"Found {len(forms)} forms:")
            
            for i, form in enumerate(forms):
                form_action = await form.get_attribute('action') or 'no-action'
                form_method = await form.get_attribute('method') or 'GET'
                form_class = await form.get_attribute('class') or 'no-class'
                
                print(f"  {i+1}. Action: {form_action}, Method: {form_method}")
                print(f"      Class: {form_class}")
                print()
            
            # Check if there are any React/Vue components
            print("🔍 Looking for JavaScript frameworks...")
            react_elements = await page.query_selector_all('[data-reactroot], [data-react-class], .react-component')
            vue_elements = await page.query_selector_all('[data-v-], .vue-component')
            angular_elements = await page.query_selector_all('[ng-app], [ng-controller], .ng-scope')
            
            print(f"React elements: {len(react_elements)}")
            print(f"Vue elements: {len(vue_elements)}")
            print(f"Angular elements: {len(angular_elements)}")
            
            # Save page content for inspection
            with open('mac_bid_login_debug.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("\n💾 Saved page content to 'mac_bid_login_debug.html'")
            
            # Take a screenshot
            await page.screenshot(path='mac_bid_login_debug.png')
            print("📸 Saved screenshot to 'mac_bid_login_debug.png'")
            
            print("\n✅ Debug complete! Check the saved files for more details.")
            
        except Exception as e:
            print(f"❌ Error during debug: {e}")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(debug_login_page()) 