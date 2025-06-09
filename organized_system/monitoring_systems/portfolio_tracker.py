#!/usr/bin/env python3
"""
📊 PORTFOLIO TRACKER - Bid Performance & ROI Analysis
Track your auction bids, measure success rates, and validate analytics recommendations
"""

import sqlite3
import json
from datetime import datetime, timedelta
import statistics
from collections import defaultdict
import argparse

class PortfolioTracker:
    def __init__(self, db_path="portfolio_tracker.db"):
        self.db_path = db_path
        self.setup_database()
        
    def setup_database(self):
        """Setup portfolio tracking database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bids (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                product_name TEXT,
                brand TEXT,
                category TEXT,
                auction_location TEXT,
                
                -- Pricing Information
                retail_price REAL,
                instant_win_price REAL,
                my_bid_amount REAL,
                winning_bid_amount REAL,
                final_price_paid REAL,
                
                -- Analytics Predictions
                predicted_winning_bid REAL,
                suggested_bid_min REAL,
                suggested_bid_max REAL,
                opportunity_score REAL,
                confidence_score REAL,
                
                -- Bid Outcome
                bid_status TEXT,  -- WON, LOST, OUTBID, PENDING
                won_auction INTEGER DEFAULT 0,
                
                -- Performance Metrics
                savings_amount REAL,
                savings_percent REAL,
                roi_percent REAL,
                
                -- Tracking
                bid_placed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                auction_end_date TIMESTAMP,
                result_recorded_date TIMESTAMP,
                
                -- Strategy Validation
                followed_recommendation INTEGER DEFAULT 0,
                recommendation_accuracy REAL,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary_date DATE DEFAULT CURRENT_DATE,
                
                -- Overall Performance
                total_bids INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                total_losses INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0,
                
                -- Financial Performance
                total_spent REAL DEFAULT 0,
                total_retail_value REAL DEFAULT 0,
                total_savings REAL DEFAULT 0,
                avg_savings_percent REAL DEFAULT 0,
                roi_percent REAL DEFAULT 0,
                
                -- Strategy Performance
                recommendations_followed INTEGER DEFAULT 0,
                recommendations_successful INTEGER DEFAULT 0,
                recommendation_accuracy REAL DEFAULT 0,
                
                -- Category Breakdown
                best_category TEXT,
                worst_category TEXT,
                
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT UNIQUE,
                product_name TEXT,
                brand TEXT,
                category TEXT,
                auction_location TEXT,
                retail_price REAL,
                instant_win_price REAL,
                predicted_winning_bid REAL,
                opportunity_score REAL,
                target_bid_amount REAL,
                max_bid_amount REAL,
                auto_bid_enabled INTEGER DEFAULT 0,
                alert_enabled INTEGER DEFAULT 1,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                auction_end_date TIMESTAMP,
                status TEXT DEFAULT 'WATCHING',
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def add_bid(self, lot_id, product_name, brand, category, auction_location,
                retail_price, instant_win_price, my_bid_amount, 
                predicted_winning_bid=None, suggested_bid_min=None, suggested_bid_max=None,
                opportunity_score=None, confidence_score=None, notes=None):
        """Add a new bid to the portfolio."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if bid already exists
        cursor.execute('SELECT id FROM bids WHERE lot_id = ?', (lot_id,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"⚠️ Bid for lot {lot_id} already exists")
            conn.close()
            return False
            
        # Determine if recommendation was followed
        followed_recommendation = 0
        if suggested_bid_min and suggested_bid_max:
            if suggested_bid_min <= my_bid_amount <= suggested_bid_max:
                followed_recommendation = 1
                
        cursor.execute('''
            INSERT INTO bids (
                lot_id, product_name, brand, category, auction_location,
                retail_price, instant_win_price, my_bid_amount,
                predicted_winning_bid, suggested_bid_min, suggested_bid_max,
                opportunity_score, confidence_score, followed_recommendation,
                bid_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lot_id, product_name, brand, category, auction_location,
            retail_price, instant_win_price, my_bid_amount,
            predicted_winning_bid, suggested_bid_min, suggested_bid_max,
            opportunity_score, confidence_score, followed_recommendation,
            'PENDING', notes
        ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Added bid for {product_name} - ${my_bid_amount}")
        return True
        
    def update_bid_result(self, lot_id, won_auction, winning_bid_amount, final_price_paid=None):
        """Update bid result after auction ends."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get bid details
        cursor.execute('''
            SELECT retail_price, instant_win_price, my_bid_amount, 
                   predicted_winning_bid, followed_recommendation
            FROM bids WHERE lot_id = ?
        ''', (lot_id,))
        
        result = cursor.fetchone()
        if not result:
            print(f"⚠️ No bid found for lot {lot_id}")
            conn.close()
            return False
            
        retail_price, instant_win_price, my_bid_amount, predicted_winning_bid, followed_recommendation = result
        
        # Calculate performance metrics
        if final_price_paid is None:
            final_price_paid = winning_bid_amount if won_auction else 0
            
        savings_amount = 0
        savings_percent = 0
        roi_percent = 0
        
        if won_auction and final_price_paid > 0:
            if retail_price > 0:
                savings_amount = retail_price - final_price_paid
                savings_percent = (savings_amount / retail_price) * 100
                roi_percent = ((retail_price - final_price_paid) / final_price_paid) * 100
                
        # Calculate recommendation accuracy
        recommendation_accuracy = None
        if predicted_winning_bid and winning_bid_amount:
            accuracy = 100 - abs((predicted_winning_bid - winning_bid_amount) / winning_bid_amount * 100)
            recommendation_accuracy = max(0, accuracy)
            
        # Determine bid status
        if won_auction:
            bid_status = 'WON'
        elif my_bid_amount < winning_bid_amount:
            bid_status = 'OUTBID'
        else:
            bid_status = 'LOST'
            
        # Update bid record
        cursor.execute('''
            UPDATE bids SET
                winning_bid_amount = ?,
                final_price_paid = ?,
                won_auction = ?,
                bid_status = ?,
                savings_amount = ?,
                savings_percent = ?,
                roi_percent = ?,
                recommendation_accuracy = ?,
                result_recorded_date = CURRENT_TIMESTAMP
            WHERE lot_id = ?
        ''', (
            winning_bid_amount, final_price_paid, 1 if won_auction else 0,
            bid_status, savings_amount, savings_percent, roi_percent,
            recommendation_accuracy, lot_id
        ))
        
        conn.commit()
        conn.close()
        
        if won_auction:
            print(f"🎉 Won auction for lot {lot_id}! Paid ${final_price_paid}, saved ${savings_amount:.2f} ({savings_percent:.1f}%)")
        else:
            print(f"😞 Lost auction for lot {lot_id}. Winning bid: ${winning_bid_amount}")
            
        return True
        
    def add_to_watchlist(self, lot_id, product_name, brand, category, auction_location,
                        retail_price, instant_win_price, predicted_winning_bid=None,
                        opportunity_score=None, target_bid_amount=None, max_bid_amount=None,
                        auto_bid_enabled=False, notes=None):
        """Add item to watchlist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO watchlist (
                    lot_id, product_name, brand, category, auction_location,
                    retail_price, instant_win_price, predicted_winning_bid,
                    opportunity_score, target_bid_amount, max_bid_amount,
                    auto_bid_enabled, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lot_id, product_name, brand, category, auction_location,
                retail_price, instant_win_price, predicted_winning_bid,
                opportunity_score, target_bid_amount, max_bid_amount,
                1 if auto_bid_enabled else 0, notes
            ))
            
            conn.commit()
            print(f"👁️ Added {product_name} to watchlist")
            return True
            
        except sqlite3.IntegrityError:
            print(f"⚠️ Item {lot_id} already in watchlist")
            return False
        finally:
            conn.close()
            
    def get_portfolio_performance(self, days=30):
        """Get portfolio performance summary."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = datetime.now() - timedelta(days=days)
        
        # Overall statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_bids,
                0 as total_wins,
                0 as avg_savings_percent,
                0 as total_spent,
                0 as total_retail_value,
                0 as total_savings,
                0 as avg_recommendation_accuracy,
                0 as recommendations_followed
            FROM bids 
            WHERE bid_placed_date > ?
        ''', (since_date.isoformat(),))
        
        stats = cursor.fetchone()
        
        # Category performance
        cursor.execute('''
            SELECT 
                category,
                COUNT(*) as bids,
                0 as wins,
                0 as avg_savings
            FROM bids 
            WHERE bid_placed_date > ?
            GROUP BY category
            ORDER BY bids DESC
        ''', (since_date.isoformat(),))
        
        category_stats = cursor.fetchall()
        
        # Brand performance
        cursor.execute('''
            SELECT 
                brand,
                COUNT(*) as bids,
                0 as wins,
                0 as avg_savings
            FROM bids 
            WHERE bid_placed_date > ? AND brand != 'Unknown'
            GROUP BY brand
            ORDER BY bids DESC
        ''', (since_date.isoformat(),))
        
        brand_stats = cursor.fetchall()
        
        conn.close()
        
        # Calculate derived metrics
        total_bids, total_wins, avg_savings_percent, total_spent, total_retail_value, total_savings, avg_recommendation_accuracy, recommendations_followed = stats
        
        win_rate = (total_wins / total_bids * 100) if total_bids > 0 else 0
        roi_percent = (total_savings / total_spent * 100) if total_spent > 0 else 0
        
        return {
            'period_days': days,
            'total_bids': total_bids or 0,
            'total_wins': total_wins or 0,
            'win_rate': win_rate,
            'total_spent': total_spent or 0,
            'total_retail_value': total_retail_value or 0,
            'total_savings': total_savings or 0,
            'avg_savings_percent': avg_savings_percent or 0,
            'roi_percent': roi_percent,
            'avg_recommendation_accuracy': avg_recommendation_accuracy or 0,
            'recommendations_followed': recommendations_followed or 0,
            'category_performance': category_stats,
            'brand_performance': brand_stats
        }
        
    def show_portfolio_dashboard(self, days=30):
        """Display comprehensive portfolio dashboard."""
        performance = self.get_portfolio_performance(days)
        
        print(f"\n📊 PORTFOLIO PERFORMANCE DASHBOARD ({days} days)")
        print("="*60)
        
        # Overall Performance
        print(f"🎯 OVERALL PERFORMANCE")
        print(f"   Total Bids: {performance['total_bids']}")
        print(f"   Wins: {performance['total_wins']}")
        print(f"   Win Rate: {performance['win_rate']:.1f}%")
        print()
        
        # Financial Performance
        print(f"💰 FINANCIAL PERFORMANCE")
        print(f"   Total Spent: ${performance['total_spent']:,.2f}")
        print(f"   Total Retail Value: ${performance['total_retail_value']:,.2f}")
        print(f"   Total Savings: ${performance['total_savings']:,.2f}")
        print(f"   Average Savings: {performance['avg_savings_percent']:.1f}%")
        print(f"   ROI: {performance['roi_percent']:.1f}%")
        print()
        
        # Strategy Performance
        print(f"🎲 STRATEGY PERFORMANCE")
        print(f"   Recommendations Followed: {performance['recommendations_followed']}")
        print(f"   Prediction Accuracy: {performance['avg_recommendation_accuracy']:.1f}%")
        print()
        
        # Category Performance
        if performance['category_performance']:
            print(f"📂 TOP CATEGORIES")
            for category, bids, wins, avg_savings in performance['category_performance'][:5]:
                win_rate = (wins / bids * 100) if bids > 0 else 0
                savings_text = f"{avg_savings:.1f}%" if avg_savings else "N/A"
                print(f"   {category}: {wins}/{bids} wins ({win_rate:.1f}%) | Avg Savings: {savings_text}")
            print()
            
        # Brand Performance
        if performance['brand_performance']:
            print(f"🏷️ TOP BRANDS")
            for brand, bids, wins, avg_savings in performance['brand_performance'][:5]:
                win_rate = (wins / bids * 100) if bids > 0 else 0
                savings_text = f"{avg_savings:.1f}%" if avg_savings else "N/A"
                print(f"   {brand.title()}: {wins}/{bids} wins ({win_rate:.1f}%) | Avg Savings: {savings_text}")
                
    def show_recent_bids(self, limit=10):
        """Show recent bid activity."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT product_name, brand, my_bid_amount, bid_status, 
                   savings_amount, savings_percent, bid_placed_date
            FROM bids 
            ORDER BY bid_placed_date DESC 
            LIMIT ?
        ''', (limit,))
        
        bids = cursor.fetchall()
        conn.close()
        
        if not bids:
            print("📭 No bids found")
            return
            
        print(f"\n📋 RECENT BIDS (Last {limit})")
        print("="*60)
        
        for product_name, brand, my_bid_amount, bid_status, savings_amount, savings_percent, bid_date in bids:
            brand_text = f"({brand.title()}) " if brand and brand != 'Unknown' else ""
            status_icon = {"WON": "🎉", "LOST": "😞", "OUTBID": "📈", "PENDING": "⏳"}.get(bid_status, "❓")
            
            print(f"{status_icon} {brand_text}{product_name[:40]}")
            print(f"   Bid: ${my_bid_amount} | Status: {bid_status}")
            
            if bid_status == "WON" and savings_amount:
                print(f"   Saved: ${savings_amount:.2f} ({savings_percent:.1f}%)")
                
            print(f"   Date: {bid_date[:16]}")
            print()
            
    def show_watchlist(self):
        """Show current watchlist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT product_name, brand, retail_price, instant_win_price,
                   opportunity_score, target_bid_amount, status, added_date
            FROM watchlist 
            WHERE status = 'WATCHING'
            ORDER BY opportunity_score DESC, added_date DESC
        ''')
        
        items = cursor.fetchall()
        conn.close()
        
        if not items:
            print("👁️ Watchlist is empty")
            return
            
        print(f"\n👁️ WATCHLIST ({len(items)} items)")
        print("="*60)
        
        for product_name, brand, retail_price, instant_win_price, opportunity_score, target_bid_amount, status, added_date in items:
            brand_text = f"({brand.title()}) " if brand and brand != 'Unknown' else ""
            discount = ((retail_price - instant_win_price) / retail_price * 100) if retail_price > 0 and instant_win_price > 0 else 0
            
            print(f"🎯 {brand_text}{product_name[:40]}")
            print(f"   Retail: ${retail_price} | Instant Win: ${instant_win_price} | {discount:.0f}% off")
            
            if opportunity_score:
                print(f"   Opportunity Score: {opportunity_score:.0f}")
                
            if target_bid_amount:
                print(f"   Target Bid: ${target_bid_amount}")
                
            print(f"   Added: {added_date[:16]}")
            print()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="📊 Portfolio Tracker")
    parser.add_argument("--dashboard", action="store_true", help="Show portfolio dashboard")
    parser.add_argument("--recent", type=int, default=10, help="Show recent bids")
    parser.add_argument("--watchlist", action="store_true", help="Show watchlist")
    parser.add_argument("--days", type=int, default=30, help="Days for performance analysis")
    
    # Add bid arguments
    parser.add_argument("--add-bid", action="store_true", help="Add a new bid")
    parser.add_argument("--lot-id", help="Lot ID")
    parser.add_argument("--product-name", help="Product name")
    parser.add_argument("--brand", help="Brand")
    parser.add_argument("--category", help="Category")
    parser.add_argument("--location", help="Auction location")
    parser.add_argument("--retail-price", type=float, help="Retail price")
    parser.add_argument("--instant-win", type=float, help="Instant win price")
    parser.add_argument("--my-bid", type=float, help="Your bid amount")
    
    # Update bid result arguments
    parser.add_argument("--update-result", action="store_true", help="Update bid result")
    parser.add_argument("--won", action="store_true", help="Won the auction")
    parser.add_argument("--winning-bid", type=float, help="Winning bid amount")
    
    args = parser.parse_args()
    
    tracker = PortfolioTracker()
    
    if args.add_bid:
        if not all([args.lot_id, args.product_name, args.my_bid]):
            print("❌ Required: --lot-id, --product-name, --my-bid")
            return
            
        tracker.add_bid(
            lot_id=args.lot_id,
            product_name=args.product_name,
            brand=args.brand or 'Unknown',
            category=args.category or 'Unknown',
            auction_location=args.location or 'Unknown',
            retail_price=args.retail_price or 0,
            instant_win_price=args.instant_win or 0,
            my_bid_amount=args.my_bid
        )
        
    elif args.update_result:
        if not all([args.lot_id, args.winning_bid]):
            print("❌ Required: --lot-id, --winning-bid")
            return
            
        tracker.update_bid_result(
            lot_id=args.lot_id,
            won_auction=args.won,
            winning_bid_amount=args.winning_bid
        )
        
    elif args.dashboard:
        tracker.show_portfolio_dashboard(args.days)
        
    elif args.watchlist:
        tracker.show_watchlist()
        
    else:
        tracker.show_recent_bids(args.recent)

if __name__ == "__main__":
    main() 