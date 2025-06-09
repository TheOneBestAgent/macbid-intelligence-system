#!/usr/bin/env python3
"""
Test NextJS Integration System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_systems.nextjs_integration_system import NextJSIntegrationSystem

def test_nextjs_integration():
    """Test NextJS integration with a known lot"""
    print("🧪 TESTING NEXTJS INTEGRATION")
    print("=" * 50)
    
    # Initialize system
    nextjs_system = NextJSIntegrationSystem()
    
    # Test with a known lot ID (from the Typesense results)
    test_lot_id = 35242923  # Pallet of General Merchandise (REMOVAL)
    test_auction_id = None  # We'll try without auction_id first
    
    print(f"🔍 Testing lot ID: {test_lot_id}")
    
    # Try to fetch NextJS data
    result = nextjs_system.fetch_nextjs_lot_data(test_auction_id, test_lot_id)
    
    if result:
        print("✅ SUCCESS! NextJS data retrieved:")
        print(f"   Product: {result.get('product_name', 'Unknown')}")
        print(f"   Retail Price: ${result.get('retail_price', 0):,.2f}")
        print(f"   Current Bid: ${result.get('nextjs_current_bid', 0):,.2f}")
        print(f"   Total Bids: {result.get('nextjs_total_bids', 0)}")
        print(f"   Is Open: {result.get('nextjs_is_open', False)}")
        print(f"   Timestamp: {result.get('nextjs_timestamp', 'N/A')}")
        
        # Show all available fields
        print(f"\n📋 Available fields ({len(result)} total):")
        for key, value in sorted(result.items()):
            if isinstance(value, (str, int, float, bool)) and value is not None:
                print(f"   {key}: {value}")
    else:
        print("❌ FAILED! No NextJS data retrieved")
        print("   This could be due to:")
        print("   - Incorrect URL format")
        print("   - Authentication issues")
        print("   - Lot not available via NextJS API")
        print("   - Network connectivity issues")
    
    # Test with a few more lot IDs
    test_lots = [35684618, 35739734, 35777466]  # Other high-value lots
    
    print(f"\n🔄 Testing {len(test_lots)} additional lots...")
    success_count = 0
    
    for lot_id in test_lots:
        result = nextjs_system.fetch_nextjs_lot_data(None, lot_id)
        if result:
            success_count += 1
            print(f"   ✅ Lot {lot_id}: {result.get('product_name', 'Unknown')[:30]}...")
        else:
            print(f"   ❌ Lot {lot_id}: Failed")
    
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   Success Rate: {success_count}/{len(test_lots)} ({success_count/len(test_lots)*100:.1f}%)")
    
    if success_count > 0:
        print("   ✅ NextJS integration is working!")
        print("   🔧 The parallel discovery system should be enhanced")
    else:
        print("   ❌ NextJS integration needs debugging")
        print("   🔧 Check authentication, URL format, or API availability")

if __name__ == "__main__":
    test_nextjs_integration() 