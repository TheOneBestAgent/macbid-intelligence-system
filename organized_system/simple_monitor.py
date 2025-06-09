#!/usr/bin/env python3
"""
Simple Auction Monitor - Non-freezing version
Monitors auctions with timeouts and error handling
"""

import requests
import time
import json
from datetime import datetime
import sys
import signal

class SimpleAuctionMonitor:
    def __init__(self):
        self.running = False
        self.session = requests.Session()
        self.session.timeout = 10  # 10 second timeout
        
        # Mac.bid API configuration
        self.base_url = "https://www.mac.bid/_next/data/AslxUFb4wF5GgYRFXlpoC"
        
        # Sample auction data for monitoring
        self.sample_lots = [
            {"auction_id": 35863830, "lot_id": "1"},
            {"auction_id": 35863831, "lot_id": "1"},
            {"auction_id": 35863832, "lot_id": "1"},
            {"auction_id": 35863833, "lot_id": "1"},
            {"auction_id": 35863834, "lot_id": "1"}
        ]
        
        # Setup signal handler for graceful exit
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n🛑 Monitoring stopped by user")
        self.running = False
        sys.exit(0)
    
    def fetch_lot_data(self, auction_id, lot_id):
        """Fetch lot data with timeout and error handling"""
        try:
            url = f"{self.base_url}/index.json"
            params = {'aid': auction_id, 'lid': lot_id}
            
            response = self.session.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                lot_data = data.get('pageProps', {}).get('activeLot', {})
                return lot_data
            else:
                print(f"⚠️  HTTP {response.status_code} for lot {auction_id}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⏰ Timeout fetching lot {auction_id}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error for lot {auction_id}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error fetching lot {auction_id}: {e}")
            return None
    
    def analyze_opportunity(self, lot_data):
        """Quick opportunity analysis"""
        if not lot_data:
            return None
            
        try:
            product_name = lot_data.get('product_name', 'Unknown Item')
            current_bid = float(lot_data.get('winning_bid_amount', 0))
            instant_win = float(lot_data.get('instant_win_price', 0))
            retail_price = float(lot_data.get('retail_price', 0))
            bidder_count = int(lot_data.get('unique_bidders', 0))
            bid_count = int(lot_data.get('total_bids', 0))
            
            # Calculate basic metrics
            if retail_price > 0 and current_bid > 0:
                potential_roi = ((retail_price - current_bid) / current_bid) * 100
            else:
                potential_roi = 0
                
            # Simple scoring
            score = 0
            if potential_roi > 100:
                score += 30
            elif potential_roi > 50:
                score += 20
            elif potential_roi > 25:
                score += 10
                
            if bidder_count < 5:
                score += 20
            elif bidder_count < 10:
                score += 10
                
            if current_bid < 50:
                score += 15
                
            return {
                'product_name': product_name,
                'current_bid': current_bid,
                'instant_win': instant_win,
                'retail_price': retail_price,
                'bidder_count': bidder_count,
                'bid_count': bid_count,
                'potential_roi': potential_roi,
                'opportunity_score': score
            }
            
        except Exception as e:
            print(f"❌ Error analyzing lot: {e}")
            return None
    
    def display_opportunities(self, opportunities):
        """Display current opportunities"""
        print(f"\n📊 AUCTION OPPORTUNITIES - {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 80)
        
        if not opportunities:
            print("⚠️  No opportunities found this cycle")
            return
            
        # Sort by opportunity score
        sorted_opps = sorted(opportunities, key=lambda x: x['opportunity_score'], reverse=True)
        
        for i, opp in enumerate(sorted_opps[:5], 1):
            print(f"\n{i}. {opp['product_name'][:50]}")
            print(f"   💰 Current Bid: ${opp['current_bid']:.2f}")
            print(f"   🏷️  Retail Price: ${opp['retail_price']:.2f}")
            print(f"   📈 Potential ROI: {opp['potential_roi']:.1f}%")
            print(f"   👥 Bidders: {opp['bidder_count']} | Bids: {opp['bid_count']}")
            print(f"   🎯 Score: {opp['opportunity_score']}/100")
            
            # Highlight good opportunities
            if opp['opportunity_score'] >= 60:
                print("   ⭐ STRONG OPPORTUNITY!")
            elif opp['opportunity_score'] >= 40:
                print("   ✅ Good opportunity")
    
    def monitor_cycle(self):
        """Single monitoring cycle"""
        print(f"🔍 Scanning {len(self.sample_lots)} auctions...")
        
        opportunities = []
        
        for lot in self.sample_lots:
            if not self.running:
                break
                
            lot_data = self.fetch_lot_data(lot['auction_id'], lot['lot_id'])
            
            if lot_data:
                opportunity = self.analyze_opportunity(lot_data)
                if opportunity:
                    opportunities.append(opportunity)
            
            # Small delay between requests
            time.sleep(0.5)
        
        self.display_opportunities(opportunities)
        return opportunities
    
    def start_monitoring(self, interval=60):
        """Start monitoring with specified interval"""
        print("🚀 SIMPLE AUCTION MONITOR STARTED")
        print("=" * 50)
        print(f"⏱️  Monitoring every {interval} seconds")
        print("🛑 Press Ctrl+C to stop")
        print()
        
        self.running = True
        cycle_count = 0
        
        try:
            while self.running:
                cycle_count += 1
                print(f"\n🔄 MONITORING CYCLE #{cycle_count}")
                
                opportunities = self.monitor_cycle()
                
                if not self.running:
                    break
                
                # Show next update time
                next_update = datetime.now().strftime('%H:%M:%S')
                print(f"\n⏰ Next update in {interval} seconds (at {next_update})")
                
                # Wait for next cycle
                for i in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")
        finally:
            self.running = False
            print("👋 Monitor shutdown complete")

def main():
    """Main function"""
    print("🎯 SIMPLE AUCTION MONITOR")
    print("=" * 50)
    print("This is a lightweight, stable monitoring solution")
    print("that won't freeze or hang.")
    print()
    
    monitor = SimpleAuctionMonitor()
    
    # Ask for monitoring interval
    try:
        interval = input("Enter monitoring interval in seconds [60]: ").strip()
        if interval:
            interval = int(interval)
        else:
            interval = 60
            
        if interval < 10:
            print("⚠️  Minimum interval is 10 seconds")
            interval = 10
            
    except ValueError:
        print("⚠️  Invalid interval, using 60 seconds")
        interval = 60
    
    monitor.start_monitoring(interval)

if __name__ == "__main__":
    main() 