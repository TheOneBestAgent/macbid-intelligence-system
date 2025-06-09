#!/usr/bin/env python3
"""
Test Typesense Scanner
"""

import sys
import asyncio
sys.path.append('.')

from discovery_systems.typesense_all_lots_scanner import TypesenseAllLotsScanner

async def test_typesense():
    print("🔍 Testing Typesense All Lots Scanner...")
    
    scanner = TypesenseAllLotsScanner()
    
    # Run discovery
    await scanner.run_typesense_discovery()
    
    total_lots = len(scanner.discovered_lots)
    print(f"✅ Typesense found {total_lots:,} lots!")
    
    if total_lots > 1000:
        print("🎉 SUCCESS: Found 1000+ lots (much better than 154!)")
    elif total_lots > 500:
        print("✅ GOOD: Found 500+ lots")
    else:
        print("⚠️  WARNING: Only found {total_lots} lots")
    
    return total_lots

if __name__ == "__main__":
    result = asyncio.run(test_typesense())
    print(f"🎯 Final result: {result:,} lots discovered") 