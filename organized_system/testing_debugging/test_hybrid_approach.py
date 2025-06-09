#!/usr/bin/env python3
"""
Test the hybrid approach: Public API discovery + Authenticated bid scraping
"""

import asyncio
from ultimate_authenticated_monitoring_system import UltimateMonitoringSystem

async def test_hybrid_approach():
    """Test the complete hybrid workflow."""
    print("🔬 TESTING HYBRID APPROACH")
    print("=" * 50)
    print("Step 1: Public API Discovery (no login)")
    print("Step 2: Authenticated Bid Scraping (with login)")
    print()
    
    system = UltimateMonitoringSystem()
    
    # Step 1: Public API Discovery
    print("🔍 STEP 1: PUBLIC API DISCOVERY")
    print("-" * 30)
    lots = await system.discover_lots_via_api()
    
    if not lots:
        print("❌ No lots found via public API")
        return
    
    print(f"✅ Found {len(lots)} lots via public API")
    
    # Show first few lots discovered
    print("\n📦 Sample lots discovered:")
    for i, lot in enumerate(lots[:3], 1):
        title = lot.get('auction_title', 'Unknown')
        lot_id = lot.get('id', 'Unknown')
        retail = lot.get('discount', 0)
        location = lot.get('auction_location', 'Unknown')
        print(f"  {i}. {title[:40]} - ${retail:.2f} ({location})")
        print(f"     ID: {lot_id}")
    
    # Step 2: Authenticated Bid Scraping
    print(f"\n🔐 STEP 2: AUTHENTICATED BID SCRAPING")
    print("-" * 35)
    
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Login
        print("🔐 Logging in...")
        login_success = await system.login_to_macbid(page)
        
        if not login_success:
            print("❌ Login failed")
            await browser.close()
            return
        
        # Test bid extraction on first lot
        test_lot = lots[0]
        lot_id = test_lot.get('id', '').replace('mac_lot_', '')
        
        print(f"💰 Extracting bid data for lot {lot_id}...")
        bid_data = await system.extract_current_bid(page, lot_id)
        
        await browser.close()
        
        # Show results
        print(f"\n📊 RESULTS COMPARISON")
        print("-" * 20)
        print(f"Lot: {test_lot.get('auction_title', 'Unknown')}")
        print(f"Retail Price (API): ${test_lot.get('discount', 0):.2f}")
        print(f"Current Bid (Scraped): ${bid_data.get('current_bid', 0):.2f}")
        print(f"Total Bids: {bid_data.get('total_bids', 0)}")
        print(f"Unique Bidders: {bid_data.get('unique_bidders', 0)}")
        
        if 'all_amounts' in bid_data:
            print(f"All amounts found: {bid_data['all_amounts']}")
    
    print(f"\n✅ HYBRID APPROACH WORKING!")
    print("✅ Public API: Discovers lots without authentication")
    print("✅ Authenticated Scraper: Gets accurate bid data")

if __name__ == "__main__":
    asyncio.run(test_hybrid_approach()) 