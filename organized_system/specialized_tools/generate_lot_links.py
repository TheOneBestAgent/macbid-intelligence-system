#!/usr/bin/env python3
"""
Generate verification links for all discovered lots
"""

import asyncio
from ultimate_authenticated_monitoring_system import UltimateMonitoringSystem

async def generate_verification_links():
    """Generate links for all discovered lots."""
    print("🔗 GENERATING VERIFICATION LINKS")
    print("=" * 40)
    
    system = UltimateMonitoringSystem()
    
    # Discover current lots
    lots = await system.discover_lots_via_api()
    
    print(f"📦 Found {len(lots)} lots in SC warehouses")
    print("\n🔗 VERIFICATION LINKS:")
    print("-" * 25)
    
    for i, lot in enumerate(lots, 1):
        title = lot.get('auction_title', 'Unknown')
        lot_id = lot.get('id', '').replace('mac_lot_', '')
        retail = lot.get('discount', 0)
        location = lot.get('auction_location', 'Unknown')
        
        print(f"\n{i:2d}. {title[:50]}")
        print(f"    Retail: ${retail:.2f} | Location: {location}")
        print(f"    🔗 Link: https://mac.bid/lot/{lot_id}")
        
        if i >= 15:  # Show first 15 lots
            print(f"\n... and {len(lots) - 15} more lots")
            break
    
    print(f"\n📋 QUICK VERIFICATION CHECKLIST:")
    print("-" * 30)
    print("✅ Click each link above")
    print("✅ Check the current bid amount shown on the page")
    print("✅ Compare with our system's detected bid")
    print("✅ Verify the retail price matches")
    print("✅ Confirm the location is in South Carolina")

if __name__ == "__main__":
    asyncio.run(generate_verification_links()) 