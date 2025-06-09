#!/usr/bin/env python3
"""
Test script for Ultimate Monitoring System
"""

import asyncio
from ultimate_authenticated_monitoring_system import UltimateMonitoringSystem

async def test_system():
    """Test the monitoring system components."""
    print("🧪 TESTING ULTIMATE MONITORING SYSTEM")
    print("=" * 40)
    
    system = UltimateMonitoringSystem()
    
    # Test 1: Database setup
    print("1️⃣ Testing database setup...")
    system.setup_database()
    print("   ✅ Database setup complete")
    
    # Test 2: API discovery
    print("\n2️⃣ Testing API lot discovery...")
    lots = await system.discover_lots_via_api()
    print(f"   📦 Found {len(lots)} lots")
    
    if lots:
        # Store first few lots
        for lot in lots[:5]:
            system.store_lot_data(lot)
        print("   ✅ Sample lots stored")
    
    # Test 3: Generate report
    print("\n3️⃣ Testing report generation...")
    report = system.generate_report()
    print(report)
    
    # Test 4: Opportunity scoring
    if lots:
        print("\n4️⃣ Testing opportunity scoring...")
        test_lot_id = lots[0].get('id')
        if test_lot_id:
            score = system.calculate_opportunity_score(test_lot_id)
            print(f"   🎯 Opportunity score for lot {test_lot_id}: {score:.3f}")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(test_system()) 