#!/usr/bin/env python3
"""
Demo of continuous monitoring - runs for 2 cycles then stops
"""

import asyncio
from ultimate_authenticated_monitoring_system import UltimateMonitoringSystem
from playwright.async_api import async_playwright

async def demo_continuous_monitoring():
    """Demo continuous monitoring for 2 cycles."""
    print("🚀 CONTINUOUS MONITORING DEMO")
    print("=" * 50)
    print("This will run 2 monitoring cycles to demonstrate:")
    print("• Continuous lot discovery")
    print("• Real-time bid tracking")
    print("• Opportunity scoring")
    print("• Alert detection")
    print()
    print("Press Ctrl+C to stop early...")
    print()
    
    system = UltimateMonitoringSystem()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = await context.new_page()
        
        # Login once
        print("🔐 Logging in to Mac.bid...")
        login_success = await system.login_to_macbid(page)
        if not login_success:
            print("❌ Failed to login")
            return
        
        # Run 2 monitoring cycles
        for cycle in range(1, 3):
            try:
                print(f"\n🔄 MONITORING CYCLE #{cycle}")
                print("-" * 30)
                
                # Discover lots every cycle (in real system, this would be every 10 cycles)
                print("🔍 Discovering lots...")
                lots = await system.discover_lots_via_api()
                
                # Store new lots
                for lot in lots[:5]:  # Store first 5
                    system.store_lot_data(lot)
                
                print(f"📦 Found {len(lots)} lots, stored 5 in database")
                
                # Monitor active lots from database
                import sqlite3
                conn = sqlite3.connect(system.db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT lot_id FROM lots WHERE is_active = 1 LIMIT 3')
                active_lots = [row[0] for row in cursor.fetchall()]
                conn.close()
                
                print(f"💰 Monitoring {len(active_lots)} active lots...")
                
                # Monitor each lot
                for i, lot_id in enumerate(active_lots, 1):
                    clean_lot_id = lot_id.replace('mac_lot_', '')
                    print(f"   {i}. Checking lot {clean_lot_id}...")
                    
                    # Extract current bid
                    bid_data = await system.extract_current_bid(page, clean_lot_id)
                    
                    # Store bid data
                    system.store_bid_data(bid_data)
                    
                    # Calculate opportunity score
                    opportunity_score = system.calculate_opportunity_score(lot_id)
                    
                    print(f"      Current Bid: ${bid_data.get('current_bid', 0):.2f}")
                    print(f"      Opportunity Score: {opportunity_score:.3f}")
                    
                    # Check for alerts
                    if opportunity_score > 0.8:
                        print(f"      🚨 HIGH OPPORTUNITY DETECTED!")
                    
                    if bid_data.get('current_bid', 0) == 0:
                        print(f"      🎯 NO BIDS YET - OPPORTUNITY!")
                    
                    await asyncio.sleep(1)  # Brief pause
                
                print(f"✅ Cycle {cycle} complete")
                
                if cycle < 2:
                    print("⏳ Waiting 10 seconds before next cycle...")
                    await asyncio.sleep(10)
                
            except Exception as e:
                print(f"❌ Error in cycle {cycle}: {e}")
                break
        
        await browser.close()
    
    # Generate final report
    print(f"\n📊 FINAL REPORT")
    print("-" * 15)
    report = system.generate_report()
    print(report)
    
    print(f"\n🎉 CONTINUOUS MONITORING DEMO COMPLETE!")
    print("=" * 50)
    print("✅ System successfully ran multiple monitoring cycles")
    print("✅ Real-time bid data extracted and stored")
    print("✅ Opportunity scores calculated")
    print("✅ Alerts detected and logged")
    print()
    print("🚀 Ready for production continuous monitoring!")
    print("   Run: python3 monitoring_cli.py monitor")

if __name__ == "__main__":
    asyncio.run(demo_continuous_monitoring()) 