#!/usr/bin/env python3
"""
Test NextJS Integration with Authentication
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_systems.nextjs_integration_system import NextJSIntegrationSystem
import asyncio

async def test_authenticated_nextjs():
    """Test NextJS integration with proper authentication"""
    print("🔐 TESTING AUTHENTICATED NEXTJS INTEGRATION")
    print("=" * 60)
    
    # Initialize system (this will handle authentication)
    print("🔧 Initializing NextJS system with authentication...")
    nextjs_system = NextJSIntegrationSystem()
    
    print(f"   Authentication status: {'✅ Authenticated' if nextjs_system.authenticated else '❌ Not authenticated'}")
    
    # Test with a high-value lot from our Typesense results
    test_lots = [
        35242923,  # Pallet of General Merchandise (REMOVAL) - $17,986.38
        35684618,  # General Merchandise 06-04 #2 - $16,562.34
        35739734,  # General Merchandise 06-05 - $14,730.09
    ]
    
    print(f"\n🧪 Testing {len(test_lots)} high-value lots...")
    
    success_count = 0
    for i, lot_id in enumerate(test_lots, 1):
        print(f"\n[{i}/{len(test_lots)}] Testing lot {lot_id}...")
        
        try:
            # Fetch NextJS data
            result = nextjs_system.fetch_nextjs_lot_data(None, lot_id)
            
            if result and isinstance(result, dict) and result:
                success_count += 1
                print(f"   ✅ SUCCESS! Real-time data retrieved:")
                print(f"      Product: {result.get('product_name', 'Unknown')[:50]}...")
                print(f"      Retail: ${result.get('retail_price', 0):,.2f}")
                print(f"      Current Bid: ${result.get('nextjs_current_bid', 0):,.2f}")
                print(f"      Total Bids: {result.get('nextjs_total_bids', 0)}")
                print(f"      Unique Bidders: {result.get('nextjs_unique_bidders', 0)}")
                print(f"      Is Open: {result.get('nextjs_is_open', False)}")
                print(f"      Timestamp: {result.get('nextjs_timestamp', 'N/A')}")
                
                # Test if this lot has real bidding activity
                if result.get('nextjs_total_bids', 0) > 0:
                    print(f"      🔥 ACTIVE BIDDING DETECTED!")
                    
            else:
                print(f"   ❌ Failed - no data returned")
                
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   Success Rate: {success_count}/{len(test_lots)} ({success_count/len(test_lots)*100:.1f}%)")
    print(f"   Authentication: {'✅ Working' if nextjs_system.authenticated else '❌ Failed'}")
    
    if success_count > 0:
        print(f"\n🎉 NEXTJS INTEGRATION WORKING!")
        print(f"   ✅ Real-time bid data extraction successful")
        print(f"   ✅ Ready for parallel discovery integration")
        
        # Test the integration format
        print(f"\n🔧 Testing integration with parallel discovery format...")
        test_lot = nextjs_system.fetch_nextjs_lot_data(None, test_lots[0])
        if test_lot:
            # Simulate how it would be integrated
            enhanced_lot = {
                'lot_id': test_lots[0],
                'product_name': test_lot.get('product_name', 'Unknown'),
                'retail_price': test_lot.get('retail_price', 0),
                'data_source': 'nextjs_enhanced',
                'has_realtime_data': True,
                'nextjs_current_bid': test_lot.get('nextjs_current_bid', 0),
                'nextjs_total_bids': test_lot.get('nextjs_total_bids', 0),
                'nextjs_unique_bidders': test_lot.get('nextjs_unique_bidders', 0),
                'nextjs_is_open': test_lot.get('nextjs_is_open', False),
                'nextjs_timestamp': test_lot.get('nextjs_timestamp', 'N/A')
            }
            
            print(f"   📦 Enhanced lot format:")
            for key, value in enhanced_lot.items():
                print(f"      {key}: {value}")
                
        return True
    else:
        print(f"\n❌ NEXTJS INTEGRATION FAILED")
        print(f"   Check authentication and lot availability")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_authenticated_nextjs())
    
    if success:
        print(f"\n🚀 READY TO UPDATE PARALLEL DISCOVERY SYSTEM")
        print(f"   The NextJS integration is working and can be enabled")
    else:
        print(f"\n🔧 DEBUGGING NEEDED")
        print(f"   NextJS integration requires further investigation") 