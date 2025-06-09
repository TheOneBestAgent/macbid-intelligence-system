#!/usr/bin/env python3
"""
CLI Interface for Ultimate Monitoring System
"""

import asyncio
import argparse
import sys
from ultimate_authenticated_monitoring_system import UltimateMonitoringSystem

async def run_test():
    """Run system tests."""
    from test_ultimate_system import test_system
    await test_system()

async def run_monitoring():
    """Start continuous monitoring."""
    system = UltimateMonitoringSystem()
    await system.start_monitoring()

async def generate_report():
    """Generate and display current report."""
    from datetime import datetime
    system = UltimateMonitoringSystem()
    report = system.generate_report()
    print(report)
    
    # Also save to file
    with open(f'monitoring_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt', 'w') as f:
        f.write(report)
    print(f"\n📄 Report saved to file")

async def discover_lots():
    """Discover and display new lots."""
    system = UltimateMonitoringSystem()
    lots = await system.discover_lots_via_api()
    
    print(f"🔍 DISCOVERED {len(lots)} LOTS")
    print("=" * 40)
    
    for i, lot in enumerate(lots[:10], 1):  # Show first 10
        title = lot.get('auction_title', lot.get('title', 'Unknown'))
        lot_id = lot.get('id', lot.get('mac_lot_id', 'Unknown'))
        retail_price = lot.get('retail_price', lot.get('discount', 0))
        location = lot.get('auction_location', lot.get('location_name', 'Unknown'))
        
        print(f"{i:2d}. {title[:50]}")
        print(f"    ID: {lot_id} | Retail: ${retail_price:.2f}")
        print(f"    Location: {location}")
        print()
    
    if len(lots) > 10:
        print(f"... and {len(lots) - 10} more lots")

def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description='Ultimate Mac.bid Monitoring System')
    parser.add_argument('command', choices=['test', 'monitor', 'report', 'discover'], 
                       help='Command to run')
    
    args = parser.parse_args()
    
    print("🎯 ULTIMATE MAC.BID MONITORING SYSTEM")
    print("=" * 50)
    
    try:
        if args.command == 'test':
            print("Running system tests...")
            asyncio.run(run_test())
        elif args.command == 'monitor':
            print("Starting continuous monitoring...")
            print("Press Ctrl+C to stop")
            asyncio.run(run_monitoring())
        elif args.command == 'report':
            print("Generating current report...")
            asyncio.run(generate_report())
        elif args.command == 'discover':
            print("Discovering new lots...")
            asyncio.run(discover_lots())
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 