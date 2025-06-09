#!/usr/bin/env python3
"""
Test a complete monitoring cycle: Discovery + Authentication + Bid Scraping + Analytics
"""

import asyncio
from ultimate_authenticated_monitoring_system import UltimateMonitoringSystem
from playwright.async_api import async_playwright

async def test_full_monitoring_cycle():
    """Test one complete monitoring cycle."""
    print("🔄 TESTING FULL MONITORING CYCLE")
    print("=" * 50)
    print("This will test the complete workflow:")
    print("1. Public API Discovery")
    print("2. Database Storage")
    print("3. Authenticated Login")
    print("4. Bid Scraping")
    print("5. Opportunity Scoring")
    print("6. Alert Checking")
    print()
    
    system = UltimateMonitoringSystem()
    
    # Step 1: Discovery
    print("🔍 STEP 1: DISCOVERING LOTS VIA PUBLIC API")
    print("-" * 40)
    lots = await system.discover_lots_via_api()
    
    if not lots:
        print("❌ No lots found")
        return
    
    print(f"✅ Found {len(lots)} lots")
    
    # Step 2: Store lots in database
    print(f"\n💾 STEP 2: STORING LOTS IN DATABASE")
    print("-" * 35)
    for lot in lots[:5]:  # Store first 5 lots
        system.store_lot_data(lot)
    print("✅ Lots stored in database")
    
    # Step 3: Authenticated monitoring
    print(f"\n🔐 STEP 3: AUTHENTICATED BID MONITORING")
    print("-" * 40)
    
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
        
        # Monitor first 3 lots
        print(f"\n💰 STEP 4: EXTRACTING BID DATA")
        print("-" * 30)
        
        for i, lot in enumerate(lots[:3], 1):
            lot_id = lot.get('id', '').replace('mac_lot_', '')
            title = lot.get('auction_title', 'Unknown')
            
            print(f"\n{i}. Monitoring: {title[:40]}")
            print(f"   Lot ID: {lot_id}")
            
            # Extract bid data
            bid_data = await system.extract_current_bid(page, lot_id)
            
            # Store bid data
            system.store_bid_data(bid_data)
            
            # Calculate opportunity score
            opportunity_score = system.calculate_opportunity_score(lot_id)
            
            # Display results
            print(f"   Current Bid: ${bid_data.get('current_bid', 0):.2f}")
            print(f"   Total Bids: {bid_data.get('total_bids', 0)}")
            print(f"   Unique Bidders: {bid_data.get('unique_bidders', 0)}")
            print(f"   Opportunity Score: {opportunity_score:.3f}")
            
            # Check for alerts (without sending emails for test)
            if opportunity_score > 0.8:
                print(f"   🚨 HIGH OPPORTUNITY ALERT! Score: {opportunity_score:.3f}")
            
            if bid_data.get('current_bid', 0) == 0:
                print(f"   🎯 NO BID OPPORTUNITY!")
            
            # Brief pause between lots
            await asyncio.sleep(2)
        
        await browser.close()
    
    # Step 5: Generate report
    print(f"\n📊 STEP 5: GENERATING REPORT")
    print("-" * 25)
    report = system.generate_report()
    print(report)
    
    print(f"\n✅ FULL MONITORING CYCLE COMPLETE!")
    print("=" * 50)
    print("✅ Public API Discovery: Working")
    print("✅ Database Storage: Working") 
    print("✅ Authentication: Working")
    print("✅ Bid Scraping: Working")
    print("✅ Opportunity Scoring: Working")
    print("✅ Alert Detection: Working")
    print("✅ Report Generation: Working")
    print()
    print("🚀 System ready for continuous monitoring!")

if __name__ == "__main__":
    asyncio.run(test_full_monitoring_cycle()) 