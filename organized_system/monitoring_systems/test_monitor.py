#!/usr/bin/env python3
import asyncio
import sys
sys.path.insert(0, 'src')

async def test_monitor():
    from realtime_product_monitor import RealtimeProductMonitor
    monitor = RealtimeProductMonitor()
    
    print('🔥 Testing Real-time Monitor')
    print('=' * 40)
    
    # Test fetching products
    products = await monitor.fetch_products_page(1)
    print(f'✅ Fetched {len(products)} products from page 1')
    
    if products:
        sample = products[0]
        product_id = monitor.get_product_id(sample)
        print(f'📝 Sample product ID: {product_id}')
        print(f'📝 Sample title: {sample.get("title", "Unknown")[:50]}...')
    
    print('🎯 Monitor is working! Run full version with: python3 realtime_product_monitor.py')

if __name__ == "__main__":
    asyncio.run(test_monitor()) 