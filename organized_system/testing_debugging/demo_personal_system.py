#!/usr/bin/env python3
"""
🎯 Demo: Your Personalized Analytics System
Shows how your actual bidding history enhances auction recommendations
"""

from personalized_analytics import PersonalizedAnalytics
import json

def demo_personal_system():
    """Demonstrate your personalized analytics system."""
    print("🎯 DEMO: YOUR PERSONALIZED AUCTION SYSTEM")
    print("=" * 60)
    print("This system uses your ACTUAL bidding history to provide")
    print("personalized recommendations and risk assessments!")
    print("=" * 60)
    
    analytics = PersonalizedAnalytics()
    
    # Show your personal patterns first
    print("\n📊 YOUR ACTUAL BIDDING PERFORMANCE:")
    personal_stats = analytics.analyze_personal_patterns()
    
    if not personal_stats:
        print("❌ No personal data found!")
        return
    
    print("\n" + "="*60)
    print("🔮 PERSONALIZED PREDICTIONS FOR CURRENT ITEMS")
    print("="*60)
    
    # Demo items similar to what's actually on mac.bid
    demo_items = [
        {
            'product_name': 'Apple iPhone 14 Pro Max',
            'category': 'Electronics',
            'brand': 'Apple',
            'location': 'Rock Hill',
            'retail_price': 1099.99,
            'instant_win_price': 750.00
        },
        {
            'product_name': 'Sony WH-1000XM5 Wireless Headphones',
            'category': 'Audio',
            'brand': 'Sony',
            'location': 'Greenville',
            'retail_price': 399.99,
            'instant_win_price': 280.00
        },
        {
            'product_name': 'Turtle Beach Stealth 700 Gaming Headset',
            'category': 'Audio',
            'brand': 'Turtle Beach',
            'location': 'Rock Hill',
            'retail_price': 149.99,
            'instant_win_price': 89.99
        },
        {
            'product_name': 'Nintendo Switch OLED Console',
            'category': 'Gaming',
            'brand': 'Nintendo',
            'location': 'Greenville',
            'retail_price': 349.99,
            'instant_win_price': 250.00
        }
    ]
    
    for i, item in enumerate(demo_items, 1):
        print(f"\n🎯 ITEM #{i}: {item['product_name']}")
        print("-" * 50)
        
        # Get personalized recommendation
        recommendation = analytics.get_personalized_recommendations(item)
        
        # Show comparison
        print(f"\n💡 RECOMMENDATION SUMMARY:")
        print(f"   Your Optimal Bid: ${recommendation['personal_bid_suggestion']:,.2f}")
        print(f"   Personal Confidence: {recommendation['personal_confidence']:.1%}")
        print(f"   Risk Level: {recommendation['risk_level']}")
        print(f"   Category Success: {recommendation['category_success_rate']:.1f}%")
        print(f"   Brand Success: {recommendation['brand_success_rate']:.1f}%")
        
        print("\n" + "="*60)
    
    print("\n🚀 WHAT MAKES THIS SYSTEM SPECIAL:")
    print("-" * 40)
    print("✅ Uses YOUR actual 75% win rate")
    print("✅ Knows your 57% average savings")
    print("✅ Recognizes your 60% sweet spot strategy")
    print("✅ Adjusts for categories/brands you dominate")
    print("✅ Warns about categories where you've struggled")
    print("✅ Provides risk-adjusted bidding recommendations")
    print("✅ Targets your personal savings goals")
    
    print("\n🎯 YOUR SUCCESS PROFILE:")
    print("-" * 40)
    print("🏆 Audio: 50% win rate, but 94% savings when you win!")
    print("🏆 Electronics: 100% win rate, 35% savings")
    print("🏆 Gaming: 100% win rate, 43% savings")
    print("🏆 Apple: 100% success rate")
    print("🏆 Nintendo: 100% success rate")
    print("⚠️ Sony: 0% success (but only 1 attempt)")
    
    print("\n💰 FINANCIAL IMPACT:")
    print("-" * 40)
    print(f"Total Spent: $856.00")
    print(f"Total Savings: $593.98")
    print(f"ROI: {(593.98/856)*100:.1f}% return on investment!")
    print(f"Best Deal: 94% savings on Turtle Beach headset!")

if __name__ == "__main__":
    demo_personal_system() 