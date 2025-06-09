#!/usr/bin/env python3
"""
🎧 Updated High-Volume Headphone Monitor
Uses optimal scanning parameters for maximum coverage
"""

import asyncio
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from optimized_scanner import OptimizedScanner
from price_tracker import PriceTracker
import sqlite3
from datetime import datetime

class HighVolumeHeadphoneMonitor:
    def __init__(self):
        self.sc_locations = [17, 20, 28, 34, 36]
        self.headphone_keywords = [
            'headphone', 'headphones', 'earphone', 'earphones', 'earbud', 'earbuds',
            'beats', 'airpods', 'sony', 'bose', 'sennheiser', 'audio-technica',
            'wireless headset', 'bluetooth headset', 'gaming headset', 'skullcandy',
            'jbl', 'plantronics', 'jabra', 'anker', 'soundcore'
        ]
        
    async def scan_all_for_headphones(self):
        """Scan ALL 546 auctions for headphones in your locations."""
        print("🎧 High-Volume Headphone Scanner")
        print("=" * 50)
        print("🎯 Scanning ALL 546 auctions on mac.bid")
        print("📍 Filtering to your 5 SC locations")
        print("🔍 Searching for 20+ headphone brands/keywords")
        print()
        
        # Create optimized scanner
        scanner = OptimizedScanner(
            max_concurrent=3,  # Conservative to avoid errors
            delay_between_requests=0.4  # Slightly faster than test
        )
        
        try:
            # Scan all auctions (28 pages = all available)
            auctions = await scanner.scan_all_auctions(
                max_pages=28,  # We know there are 28 pages
                location_filter=self.sc_locations
            )
            
            # Search for headphones
            headphone_matches = []
            for auction in auctions:
                title = auction.get('title', auction.get('external_folder_name', ''))
                if title and any(keyword.lower() in title.lower() for keyword in self.headphone_keywords):
                    headphone_matches.append(auction)
                    
            # Display results
            if headphone_matches:
                print(f"\n🎉 FOUND {len(headphone_matches)} HEADPHONE AUCTIONS!")
                print("=" * 60)
                
                for match in headphone_matches:
                    title = match.get('title', match.get('external_folder_name', 'No title'))
                    location_id = match.get('location_id')
                    location_name = match.get('location_name', f'Location {location_id}')
                    auction_number = match.get('auction_number', 'Unknown')
                    closing_date = match.get('closing_date', '')
                    
                    print(f"🎧 {title}")
                    print(f"   📋 Auction: {auction_number}")
                    print(f"   📍 Location: {location_name} (ID: {location_id})")
                    if closing_date:
                        try:
                            closing_dt = datetime.fromisoformat(closing_date.replace('Z', '+00:00'))
                            print(f"   ⏰ Closes: {closing_dt.strftime('%Y-%m-%d %H:%M')}")
                        except:
                            print(f"   ⏰ Closes: {closing_date}")
                    print()
                    
                # Update price tracker with found items
                await self.update_price_tracker(headphone_matches)
                
            else:
                print(f"\n❌ No headphones found in current {len(auctions)} auctions")
                print("💡 But your alerts are still active for when they appear!")
                
            return headphone_matches
            
        finally:
            await scanner.close_session()
            
    async def update_price_tracker(self, headphone_auctions):
        """Update price tracker with found headphone auctions."""
        print("💾 Updating price tracker with headphone data...")
        
        try:
            tracker = PriceTracker()
            
            # Convert to price tracker format
            tracker_auctions = []
            for auction in headphone_auctions:
                tracker_auctions.append({
                    'id': auction.get('id'),
                    'auction_number': auction.get('auction_number', ''),
                    'title': auction.get('title', auction.get('external_folder_name', '')),
                    'location_id': auction.get('location_id'),
                    'location_name': auction.get('location_name', ''),
                    'closing_date': auction.get('closing_date', ''),
                    'opening_date': auction.get('opening_date', '')
                })
                
            # Save to price tracker database
            tracker.save_auction_data(tracker_auctions)
            
            # Check if any trigger existing alerts
            alert_count = tracker.check_alerts()
            
            if alert_count > 0:
                print(f"🚨 {alert_count} PRICE ALERTS TRIGGERED!")
            else:
                print("✅ Headphone data saved, no alerts triggered yet")
                
        except Exception as e:
            print(f"⚠️  Error updating price tracker: {e}")
            
    def show_monitoring_status(self):
        """Show current monitoring status."""
        print("📊 Headphone Monitoring Status")
        print("=" * 40)
        
        try:
            conn = sqlite3.connect('price_tracker.db')
            cursor = conn.cursor()
            
            # Show active alerts
            cursor.execute('SELECT * FROM price_alerts WHERE is_active = 1')
            alerts = cursor.fetchall()
            
            print(f"🔔 Active Alerts: {len(alerts)}")
            for alert in alerts:
                keyword, max_price, location_ids = alert[1], alert[2], alert[4]
                print(f"   • '{keyword}' under ${max_price} in locations {location_ids}")
                
            # Show recent auction data
            cursor.execute('SELECT COUNT(*) FROM auctions WHERE last_updated > datetime("now", "-1 day")')
            recent_count = cursor.fetchone()[0]
            
            print(f"📊 Recent Data: {recent_count} auctions in last 24 hours")
            
            conn.close()
            
        except Exception as e:
            print(f"⚠️  Error checking status: {e}")
            
        print(f"\n🎯 Coverage: ALL 546 auctions → {sum([19,18,16,14,10])} in your SC locations")
        print(f"🔍 Keywords: {len(self.headphone_keywords)} headphone brands/types")
        print(f"📍 Locations: {len(self.sc_locations)} SC warehouses")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='High-Volume Headphone Monitor')
    parser.add_argument('--scan', action='store_true', help='Scan all auctions for headphones')
    parser.add_argument('--status', action='store_true', help='Show monitoring status')
    parser.add_argument('--quick', action='store_true', help='Quick scan (first 10 pages only)')
    
    args = parser.parse_args()
    
    monitor = HighVolumeHeadphoneMonitor()
    
    if args.scan:
        await monitor.scan_all_for_headphones()
    elif args.status:
        monitor.show_monitoring_status()
    elif args.quick:
        # Quick scan for testing
        scanner = OptimizedScanner(max_concurrent=3, delay_between_requests=0.5)
        try:
            auctions = await scanner.scan_all_auctions(
                max_pages=10,
                location_filter=monitor.sc_locations
            )
            scanner.analyze_auctions(auctions, monitor.headphone_keywords)
        finally:
            await scanner.close_session()
    else:
        print("🎧 High-Volume Headphone Monitor")
        print("=" * 40)
        print("Commands:")
        print("  --scan     Scan ALL 546 auctions for headphones")
        print("  --status   Show current monitoring status")
        print("  --quick    Quick scan (10 pages for testing)")
        print()
        print("Examples:")
        print("  python3 update_headphone_monitor.py --scan")
        print("  python3 update_headphone_monitor.py --status")

if __name__ == "__main__":
    asyncio.run(main()) 