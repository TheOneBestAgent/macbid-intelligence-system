#!/usr/bin/env python3
"""
Mac.bid Intelligence System - Automated Bidding System
Phase 5: Intelligent Bidding and Portfolio Management
"""

import json
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutomatedBiddingSystem:
    """Intelligent automated bidding system for Mac.bid auctions"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.db_path = self.base_dir / "databases" / "bidding_intelligence.db"
        
        # Ensure database directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Bidding configuration
        self.config = {
            "max_daily_budget": 1000,
            "default_bid_increment": 5,
            "snipe_window_seconds": 30,
            "max_concurrent_bids": 10
        }
    
    def _init_database(self):
        """Initialize bidding intelligence database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Bid strategies table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bid_strategies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        strategy_type TEXT NOT NULL,
                        max_bid_amount REAL NOT NULL,
                        bid_increment REAL DEFAULT 5.0,
                        categories TEXT,
                        active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Active bids table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS active_bids (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id TEXT NOT NULL,
                        item_title TEXT NOT NULL,
                        current_bid REAL NOT NULL,
                        max_bid REAL NOT NULL,
                        strategy_id INTEGER,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (strategy_id) REFERENCES bid_strategies (id)
                    )
                """)
                
                # Bid history table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bid_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id TEXT NOT NULL,
                        item_title TEXT NOT NULL,
                        bid_amount REAL NOT NULL,
                        result TEXT NOT NULL,
                        final_price REAL,
                        profit_loss REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Portfolio tracking table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfolio (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id TEXT NOT NULL,
                        item_title TEXT NOT NULL,
                        purchase_price REAL NOT NULL,
                        estimated_value REAL,
                        category TEXT,
                        purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'owned'
                    )
                """)
                
                conn.commit()
                logger.info("Bidding intelligence database initialized")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    def create_bid_strategy(self, name: str, strategy_type: str, max_bid: float, 
                           increment: float = 5.0, categories: List[str] = None) -> Dict[str, Any]:
        """Create a new bidding strategy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO bid_strategies 
                    (name, strategy_type, max_bid_amount, bid_increment, categories)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, strategy_type, max_bid, increment, json.dumps(categories or [])))
                
                strategy_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Created bid strategy '{name}' with ID {strategy_id}")
                return {"success": True, "id": strategy_id}
                
        except Exception as e:
            logger.error(f"Error creating bid strategy: {e}")
            return {"success": False, "error": str(e)}
    
    def get_bid_strategies(self) -> List[Dict[str, Any]]:
        """Get all bid strategies"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, name, strategy_type, max_bid_amount, 
                           bid_increment, categories, active, created_at
                    FROM bid_strategies
                    ORDER BY created_at DESC
                """)
                
                strategies = []
                for row in cursor.fetchall():
                    strategies.append({
                        "id": row[0],
                        "name": row[1],
                        "strategy_type": row[2],
                        "max_bid_amount": row[3],
                        "bid_increment": row[4],
                        "categories": json.loads(row[5]) if row[5] else [],
                        "active": bool(row[6]),
                        "created_at": row[7]
                    })
                
                return strategies
                
        except Exception as e:
            logger.error(f"Error getting bid strategies: {e}")
            return []
    
    def place_bid(self, item_id: str, item_title: str, bid_amount: float, 
                  strategy_id: int = None) -> Dict[str, Any]:
        """Place a bid on an item"""
        try:
            # Check daily budget
            if not self._check_daily_budget(bid_amount):
                return {"success": False, "error": "Daily budget exceeded"}
            
            # Check concurrent bids limit
            if not self._check_concurrent_bids():
                return {"success": False, "error": "Too many concurrent bids"}
            
            # Simulate bid placement (would integrate with Mac.bid API)
            success = self._simulate_bid_placement(item_id, bid_amount)
            
            if success:
                # Record active bid
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                        INSERT INTO active_bids 
                        (item_id, item_title, current_bid, max_bid, strategy_id)
                        VALUES (?, ?, ?, ?, ?)
                    """, (item_id, item_title, bid_amount, bid_amount, strategy_id))
                    
                    conn.commit()
                
                logger.info(f"Placed bid of ${bid_amount} on '{item_title}'")
                return {"success": True, "bid_amount": bid_amount}
            else:
                return {"success": False, "error": "Bid placement failed"}
                
        except Exception as e:
            logger.error(f"Error placing bid: {e}")
            return {"success": False, "error": str(e)}
    
    def get_active_bids(self) -> List[Dict[str, Any]]:
        """Get all active bids"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT ab.id, ab.item_id, ab.item_title, ab.current_bid, 
                           ab.max_bid, ab.status, ab.created_at, bs.name as strategy_name
                    FROM active_bids ab
                    LEFT JOIN bid_strategies bs ON ab.strategy_id = bs.id
                    WHERE ab.status = 'active'
                    ORDER BY ab.created_at DESC
                """)
                
                bids = []
                for row in cursor.fetchall():
                    bids.append({
                        "id": row[0],
                        "item_id": row[1],
                        "item_title": row[2],
                        "current_bid": row[3],
                        "max_bid": row[4],
                        "status": row[5],
                        "created_at": row[6],
                        "strategy_name": row[7] or "Manual"
                    })
                
                return bids
                
        except Exception as e:
            logger.error(f"Error getting active bids: {e}")
            return []
    
    def get_portfolio_stats(self) -> Dict[str, Any]:
        """Get portfolio statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get basic stats
                cursor.execute("SELECT COUNT(*) FROM active_bids WHERE status = 'active'")
                active_bids = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM portfolio WHERE status = 'owned'")
                items_owned = cursor.fetchone()[0]
                
                cursor.execute("SELECT AVG(profit_loss) FROM bid_history WHERE result = 'won'")
                avg_profit = cursor.fetchone()[0] or 0
                
                cursor.execute("""
                    SELECT COUNT(*) as total, 
                           SUM(CASE WHEN result = 'won' THEN 1 ELSE 0 END) as won
                    FROM bid_history
                """)
                row = cursor.fetchone()
                total_bids = row[0]
                won_bids = row[1]
                win_rate = (won_bids / total_bids * 100) if total_bids > 0 else 0
                
                return {
                    "active_bids": active_bids,
                    "items_owned": items_owned,
                    "win_rate": round(win_rate, 1),
                    "avg_profit": round(avg_profit, 2),
                    "total_bids": total_bids
                }
                
        except Exception as e:
            logger.error(f"Error getting portfolio stats: {e}")
            return {
                "active_bids": 0,
                "items_owned": 0,
                "win_rate": 0,
                "avg_profit": 0,
                "total_bids": 0
            }
    
    def _check_daily_budget(self, bid_amount: float) -> bool:
        """Check if bid amount is within daily budget"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                today = datetime.now().date()
                cursor.execute("""
                    SELECT SUM(current_bid) FROM active_bids 
                    WHERE DATE(created_at) = ?
                """, (today,))
                
                daily_spent = cursor.fetchone()[0] or 0
                return (daily_spent + bid_amount) <= self.config["max_daily_budget"]
                
        except Exception as e:
            logger.error(f"Error checking daily budget: {e}")
            return False
    
    def _check_concurrent_bids(self) -> bool:
        """Check if concurrent bids limit is reached"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM active_bids WHERE status = 'active'")
                active_count = cursor.fetchone()[0]
                
                return active_count < self.config["max_concurrent_bids"]
                
        except Exception as e:
            logger.error(f"Error checking concurrent bids: {e}")
            return False
    
    def _simulate_bid_placement(self, item_id: str, bid_amount: float) -> bool:
        """Simulate bid placement (would integrate with Mac.bid API)"""
        # For now, simulate success
        time.sleep(0.5)  # Simulate API call delay
        return True
    
    def execute_snipe_strategy(self, item_id: str, max_bid: float) -> Dict[str, Any]:
        """Execute snipe bidding strategy"""
        try:
            # This would monitor auction end time and place bid in final seconds
            logger.info(f"Executing snipe strategy for item {item_id} with max bid ${max_bid}")
            
            # Simulate snipe execution
            success = self._simulate_bid_placement(item_id, max_bid)
            
            if success:
                return {"success": True, "message": "Snipe bid executed successfully"}
            else:
                return {"success": False, "error": "Snipe bid failed"}
                
        except Exception as e:
            logger.error(f"Error executing snipe strategy: {e}")
            return {"success": False, "error": str(e)}
    
    def update_bid_status(self, bid_id: int, status: str, final_price: float = None):
        """Update bid status (won/lost)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get bid details
                cursor.execute("""
                    SELECT item_id, item_title, current_bid 
                    FROM active_bids WHERE id = ?
                """, (bid_id,))
                
                bid_data = cursor.fetchone()
                if not bid_data:
                    return
                
                item_id, item_title, bid_amount = bid_data
                
                # Update active bid status
                cursor.execute("""
                    UPDATE active_bids SET status = ? WHERE id = ?
                """, (status, bid_id))
                
                # Add to bid history
                profit_loss = 0
                if status == "won" and final_price:
                    profit_loss = bid_amount - final_price
                
                cursor.execute("""
                    INSERT INTO bid_history 
                    (item_id, item_title, bid_amount, result, final_price, profit_loss)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (item_id, item_title, bid_amount, status, final_price, profit_loss))
                
                # If won, add to portfolio
                if status == "won" and final_price:
                    cursor.execute("""
                        INSERT INTO portfolio 
                        (item_id, item_title, purchase_price)
                        VALUES (?, ?, ?)
                    """, (item_id, item_title, final_price))
                
                conn.commit()
                logger.info(f"Updated bid {bid_id} status to {status}")
                
        except Exception as e:
            logger.error(f"Error updating bid status: {e}")

def main():
    """Test the automated bidding system"""
    bidding_system = AutomatedBiddingSystem()
    
    print("🤖 Testing Automated Bidding System...")
    
    # Create a test strategy
    strategy = bidding_system.create_bid_strategy(
        "Conservative Electronics",
        "incremental",
        500.0,
        5.0,
        ["electronics"]
    )
    print(f"📋 Created strategy: {strategy}")
    
    # Get portfolio stats
    stats = bidding_system.get_portfolio_stats()
    print(f"📊 Portfolio stats: {stats}")

if __name__ == "__main__":
    main()
