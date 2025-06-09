#!/usr/bin/env python3
"""
🎯 Add Single Bid - Quick bid entry
"""

import sys
from portfolio_tracker import PortfolioTracker

def add_bid_1631F():
    """Add bid for lot 1631F with user input."""
    print("🎯 Adding Bid for Lot 1631F")
    print("=" * 30)
    
    tracker = PortfolioTracker()
    
    # Get details for lot 1631F
    print("Please provide details for Lot 1631F:")
    print()
    
    product_name = input("Product name: ").strip()
    if not product_name:
        product_name = "Unknown Product"
    
    brand = input("Brand (optional): ").strip() or "Unknown"
    category = input("Category (optional): ").strip() or "Other"
    location = input("Location (optional): ").strip() or "Unknown"
    
    try:
        retail_price = float(input("Retail price ($): ").strip() or "0")
        instant_win = float(input("Instant win price ($): ").strip() or "0")
        my_bid = float(input("Your bid amount ($): ").strip())
    except ValueError:
        print("❌ Please enter valid numbers for prices!")
        return False
    
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
    
    # Add the bid
    success = tracker.add_bid(
        lot_id="1631F",
        product_name=product_name,
        brand=brand,
        category=category,
        auction_location=location,
        retail_price=retail_price,
        instant_win_price=instant_win,
        my_bid_amount=my_bid,
        notes="Added manually"
    )
    
    if success and won_auction is not None:
        tracker.update_bid_result("1631F", won_auction, winning_bid)
    
    if success:
        print("✅ Successfully added bid for lot 1631F!")
        print("\n📊 Your updated portfolio:")
        tracker.show_portfolio_dashboard()
        return True
    else:
        print("❌ Failed to add bid")
        return False

if __name__ == "__main__":
    add_bid_1631F() 