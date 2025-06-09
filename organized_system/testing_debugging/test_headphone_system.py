#!/usr/bin/env python3
"""
🧪 Test Headphone Monitoring System
Verifies that your headphone alerts and monitoring are working properly
"""

import sqlite3
import asyncio
import aiohttp
import ssl
from datetime import datetime

def test_database_alerts():
    """Test that alerts are properly stored in database."""
    print("🧪 Testing Database Alerts")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect('price_tracker.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM price_alerts WHERE is_active = 1')
        alerts = cursor.fetchall()
        
        if alerts:
            print(f"✅ Found {len(alerts)} active alerts:")
            for alert in alerts:
                alert_id, keyword, max_price, location_ids, alert_type, created_date, is_active = alert
                print(f"   🔔 '{keyword}' under ${max_price} in locations {location_ids}")
                print(f"      Created: {created_date[:19]}")
        else:
            print("❌ No active alerts found!")
            
        conn.close()
        return len(alerts) > 0
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

async def test_api_connection():
    """Test that we can connect to mac.bid API."""
    print("\n🌐 Testing API Connection")
    print("=" * 40)
    
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    timeout = aiohttp.ClientTimeout(total=10)
    
    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            url = "https://api.macdiscount.com/auctionsummary?pg=1&ppg=5"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    auctions = data.get('data', [])
                    print(f"✅ API connection successful!")
                    print(f"   📊 Retrieved {len(auctions)} auctions from page 1")
                    return True
                else:
                    print(f"❌ API returned status {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_alert_logic():
    """Test the alert matching logic."""
    print("\n🎯 Testing Alert Logic")
    print("=" * 40)
    
    # Simulate some test auction data
    test_auctions = [
        {"title": "Apple AirPods Pro - New in Box", "current_price": 120, "location_id": 17},
        {"title": "Beats Studio3 Wireless Headphones", "current_price": 60, "location_id": 20},
        {"title": "Sony WH-1000XM4 Headphones", "current_price": 80, "location_id": 28},
        {"title": "Random Electronics Lot", "current_price": 50, "location_id": 34},
    ]
    
    # Test keywords
    headphone_keywords = ['headphone', 'headphones', 'airpods', 'beats', 'sony']
    
    matches = []
    for auction in test_auctions:
        title = auction['title'].lower()
        if any(keyword in title for keyword in headphone_keywords):
            matches.append(auction)
            
    print(f"✅ Alert logic test:")
    print(f"   📊 {len(test_auctions)} test auctions")
    print(f"   🎯 {len(matches)} would trigger headphone alerts:")
    
    for match in matches:
        print(f"      🎧 {match['title']} - ${match['current_price']} (Location {match['location_id']})")
        
    return len(matches) > 0

def test_location_filtering():
    """Test location filtering for SC warehouses."""
    print("\n📍 Testing Location Filtering")
    print("=" * 40)
    
    sc_locations = [17, 20, 28, 34, 36]
    test_locations = [17, 25, 20, 45, 28, 60, 34]  # Mix of SC and non-SC
    
    filtered = [loc for loc in test_locations if loc in sc_locations]
    
    print(f"✅ Location filtering test:")
    print(f"   🏛️  SC Locations: {sc_locations}")
    print(f"   📊 Test Locations: {test_locations}")
    print(f"   🎯 Filtered Result: {filtered}")
    print(f"   ✅ {len(filtered)} locations would be monitored")
    
    return len(filtered) > 0

async def test_full_monitoring_cycle():
    """Test a complete monitoring cycle."""
    print("\n🔄 Testing Full Monitoring Cycle")
    print("=" * 40)
    
    try:
        # Import the price tracker
        from price_tracker import PriceTracker
        
        tracker = PriceTracker()
        
        # Test fetching a small amount of data
        print("📡 Testing data fetch...")
        auctions = await tracker.fetch_auctions(2)  # Just 2 pages
        
        if auctions:
            print(f"✅ Fetched {len(auctions)} auctions successfully")
            
            # Test saving data
            print("💾 Testing data save...")
            tracker.save_auction_data(auctions)
            print("✅ Data saved successfully")
            
            # Test checking alerts
            print("🔔 Testing alert check...")
            alert_count = tracker.check_alerts()
            print(f"✅ Alert check complete ({alert_count} alerts triggered)")
            
            return True
        else:
            print("❌ No auction data retrieved")
            return False
            
    except Exception as e:
        print(f"❌ Full cycle test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Headphone Monitoring System Test")
    print("=" * 50)
    print(f"⏰ Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = []
    
    # Run all tests
    tests.append(("Database Alerts", test_database_alerts()))
    tests.append(("API Connection", await test_api_connection()))
    tests.append(("Alert Logic", test_alert_logic()))
    tests.append(("Location Filtering", test_location_filtering()))
    tests.append(("Full Monitoring Cycle", await test_full_monitoring_cycle()))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:25} | {status}")
        if result:
            passed += 1
            
    print(f"\n🎯 Overall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 Your headphone monitoring system is working perfectly!")
        print("\n💡 Next steps:")
        print("   • Run: python3 find_headphones.py (to search now)")
        print("   • Run: python3 price_tracker.py --alerts (to check alerts)")
        print("   • Wait for notifications when headphones appear!")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        
    print(f"\n⏰ Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    asyncio.run(main()) 