#!/usr/bin/env python3
"""
🚀 Quick Bid Tracker - Easy Personal Auction History Setup
Add your recent bids quickly to start getting personalized analytics
"""

import sqlite3
import json
from datetime import datetime
from portfolio_tracker import PortfolioTracker

def quick_setup():
    """Quick setup for personal auction tracking."""
    print("🚀 Quick Bid Tracker Setup")
    print("=" * 40)
    print("Let's add your recent bids to start building personalized analytics!")
    print()
    
    tracker = PortfolioTracker()
    
    print("📝 Add Recent Bids (Enter 'done' when finished)")
    print("=" * 50)
    
    bid_count = 0
    
    while True:
        print(f"\n🎯 Bid #{bid_count + 1}")
        print("-" * 20)
        
        # Get basic info
        lot_id = input("Lot ID (or 'done' to finish): ").strip()
        if lot_id.lower() == 'done':
            break
            
        product_name = input("Product name: ").strip()
        if not product_name:
            print("⚠️ Product name required!")
            continue
            
        # Get pricing
        try:
            retail_price = float(input("Retail price ($): ").strip() or "0")
            instant_win = float(input("Instant win price ($): ").strip() or "0")
            my_bid = float(input("Your bid amount ($): ").strip())
        except ValueError:
            print("⚠️ Please enter valid numbers for prices!")
            continue
            
        # Optional details
        brand = input("Brand (optional): ").strip() or "Unknown"
        category = input("Category (optional): ").strip() or "Other"
        location = input("Location (optional): ").strip() or "Unknown"
        
        # Auction result
        result = input("Did you win? (y/n/pending): ").strip().lower()
        
        won_auction = None
        winning_bid = None
        
        if result == 'y':
            won_auction = True
            winning_bid = my_bid
        elif result == 'n':
            won_auction = False
            try:
                winning_bid = float(input("Winning bid amount ($): ").strip())
            except ValueError:
                winning_bid = my_bid + 10  # Estimate
        else:
            print("   📝 Marked as pending")
            
        # Add to tracker
        success = tracker.add_bid(
            lot_id=lot_id,
            product_name=product_name,
            brand=brand,
            category=category,
            auction_location=location,
            retail_price=retail_price,
            instant_win_price=instant_win,
            my_bid_amount=my_bid,
            notes=f"Added via quick setup on {datetime.now().strftime('%Y-%m-%d')}"
        )
        
        if success and won_auction is not None:
            tracker.update_bid_result(lot_id, won_auction, winning_bid)
            
        if success:
            bid_count += 1
            print(f"✅ Added bid #{bid_count}")
        
    print(f"\n🎉 Setup complete! Added {bid_count} bids")
    
    if bid_count > 0:
        print("\n📊 Your Portfolio Dashboard:")
        tracker.show_portfolio_dashboard()
        
        print("\n🚀 Next Steps:")
        print("1. Run analytics with your data:")
        print("   python3 enhanced_new_arrivals.py")
        print("2. View your portfolio anytime:")
        print("   python3 portfolio_tracker.py --dashboard")
        print("3. Add more bids:")
        print("   python3 portfolio_tracker.py --add-bid [options]")

def add_sample_data():
    """Add sample data for testing."""
    print("🧪 Adding sample bid data for testing...")
    
    tracker = PortfolioTracker()
    
    sample_bids = [
        {
            "lot_id": "SAMPLE001",
            "product_name": "Apple iPhone 15 Pro",
            "brand": "Apple",
            "category": "Electronics",
            "auction_location": "Rock Hill",
            "retail_price": 999.99,
            "instant_win_price": 750.00,
            "my_bid_amount": 650.00,
            "won": True,
            "winning_bid": 650.00
        },
        {
            "lot_id": "SAMPLE002", 
            "product_name": "Sony WH-1000XM5 Headphones",
            "brand": "Sony",
            "category": "Audio",
            "auction_location": "Greenville",
            "retail_price": 399.99,
            "instant_win_price": 280.00,
            "my_bid_amount": 220.00,
            "won": False,
            "winning_bid": 245.00
        },
        {
            "lot_id": "SAMPLE003",
            "product_name": "Nintendo Switch OLED",
            "brand": "Nintendo", 
            "category": "Gaming",
            "auction_location": "Spartanburg",
            "retail_price": 349.99,
            "instant_win_price": 250.00,
            "my_bid_amount": 200.00,
            "won": True,
            "winning_bid": 200.00
        }
    ]
    
    for bid in sample_bids:
        tracker.add_bid(
            lot_id=bid["lot_id"],
            product_name=bid["product_name"],
            brand=bid["brand"],
            category=bid["category"],
            auction_location=bid["auction_location"],
            retail_price=bid["retail_price"],
            instant_win_price=bid["instant_win_price"],
            my_bid_amount=bid["my_bid_amount"],
            notes="Sample data for testing"
        )
        
        tracker.update_bid_result(
            lot_id=bid["lot_id"],
            won_auction=bid["won"],
            winning_bid_amount=bid["winning_bid"]
        )
    
    print("✅ Added 3 sample bids")
    print("\n📊 Sample Portfolio Dashboard:")
    tracker.show_portfolio_dashboard()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        add_sample_data()
    else:
        quick_setup() 