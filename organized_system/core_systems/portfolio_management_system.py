#!/usr/bin/env python3
"""
Multi-lot Portfolio Management System
Manages bidding across multiple auctions with intelligent resource allocation
"""

import asyncio
import json
import sqlite3
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import os
from collections import defaultdict

# Import our existing systems
import sys
sys.path.append('.')
from core_systems.real_bidding_system import RealBiddingSystem, BidRequest, BidResult

@dataclass
class PortfolioLot:
    lot_id: int
    auction_id: int
    product_name: str
    current_price: float
    instant_win_price: float
    predicted_final_price: float
    predicted_roi: float
    confidence_score: float
    risk_level: str  # LOW, MEDIUM, HIGH
    category: str
    brand: str
    condition: str
    time_remaining: str
    bidder_count: int
    bid_count: int
    opportunity_score: float
    investment_recommendation: str
    max_bid_amount: float
    priority: str  # HIGH, MEDIUM, LOW
    status: str = "ACTIVE"  # ACTIVE, BIDDING, WON, LOST, EXPIRED
    notes: str = ""
    added_at: str = ""
    
    def __post_init__(self):
        if not self.added_at:
            self.added_at = datetime.now().isoformat()

@dataclass
class PortfolioConfig:
    total_budget: float = 5000.0
    daily_budget: float = 1000.0
    max_lots_per_auction: int = 5
    max_concurrent_bids: int = 10
    min_roi_threshold: float = 25.0  # 25% minimum ROI
    max_risk_level: str = "MEDIUM"
    preferred_categories: List[str] = None
    preferred_brands: List[str] = None
    auto_bid_enabled: bool = True
    snipe_timing_minutes: int = 5
    
    def __post_init__(self):
        if self.preferred_categories is None:
            self.preferred_categories = ["Electronics", "Computers", "Home & Garden"]
        if self.preferred_brands is None:
            self.preferred_brands = ["Apple", "Samsung", "Sony", "LG", "Dell"]

@dataclass
class PortfolioMetrics:
    total_lots: int = 0
    active_lots: int = 0
    won_lots: int = 0
    lost_lots: int = 0
    total_invested: float = 0.0
    total_value: float = 0.0
    realized_roi: float = 0.0
    unrealized_roi: float = 0.0
    success_rate: float = 0.0
    average_roi: float = 0.0
    budget_utilization: float = 0.0

class PortfolioManagementSystem:
    def __init__(self, config: PortfolioConfig = None):
        self.config = config or PortfolioConfig()
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data_outputs/portfolio_management.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize systems
        self.bidding_system = RealBiddingSystem(dry_run=True)  # Start in dry-run mode
        
        # Initialize database
        self.init_database()
        
        # Portfolio state
        self.portfolio_lots: Dict[int, PortfolioLot] = {}
        self.active_bids: Dict[int, BidRequest] = {}
        self.budget_tracker = {
            'daily_spent': 0.0,
            'total_spent': 0.0,
            'reserved_funds': 0.0,
            'available_budget': self.config.total_budget
        }
        
        # Performance tracking
        self.session_start = datetime.now()
        self.performance_metrics = PortfolioMetrics()
        
    def init_database(self):
        """Initialize portfolio management database"""
        os.makedirs('databases', exist_ok=True)
        
        self.conn = sqlite3.connect('databases/portfolio_management.db')
        cursor = self.conn.cursor()
        
        # Portfolio lots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_lots (
                lot_id INTEGER PRIMARY KEY,
                auction_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                current_price REAL NOT NULL,
                instant_win_price REAL NOT NULL,
                predicted_final_price REAL NOT NULL,
                predicted_roi REAL NOT NULL,
                confidence_score REAL NOT NULL,
                risk_level TEXT NOT NULL,
                category TEXT NOT NULL,
                brand TEXT NOT NULL,
                condition TEXT NOT NULL,
                time_remaining TEXT NOT NULL,
                bidder_count INTEGER NOT NULL,
                bid_count INTEGER NOT NULL,
                opportunity_score REAL NOT NULL,
                investment_recommendation TEXT NOT NULL,
                max_bid_amount REAL NOT NULL,
                priority TEXT NOT NULL,
                status TEXT DEFAULT 'ACTIVE',
                notes TEXT,
                added_at TEXT NOT NULL,
                updated_at TEXT
            )
        ''')
        
        # Portfolio performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_lots INTEGER NOT NULL,
                active_lots INTEGER NOT NULL,
                won_lots INTEGER NOT NULL,
                lost_lots INTEGER NOT NULL,
                total_invested REAL NOT NULL,
                total_value REAL NOT NULL,
                realized_roi REAL NOT NULL,
                unrealized_roi REAL NOT NULL,
                success_rate REAL NOT NULL,
                budget_utilization REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        # Budget tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budget_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                daily_budget REAL NOT NULL,
                daily_spent REAL NOT NULL,
                total_budget REAL NOT NULL,
                total_spent REAL NOT NULL,
                available_budget REAL NOT NULL,
                reserved_funds REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')
        
        self.conn.commit()
        self.logger.info("✅ Portfolio database initialized")
    
    def add_lot_to_portfolio(self, lot: PortfolioLot) -> bool:
        """Add a lot to the portfolio with validation"""
        
        try:
            # Validate lot meets criteria
            if not self.validate_lot_criteria(lot):
                self.logger.warning(f"❌ Lot {lot.lot_id} doesn't meet portfolio criteria")
                return False
            
            # Check budget availability
            if not self.check_budget_availability(lot.max_bid_amount):
                self.logger.warning(f"❌ Insufficient budget for lot {lot.lot_id}")
                return False
            
            # Add to portfolio
            self.portfolio_lots[lot.lot_id] = lot
            
            # Reserve funds
            self.budget_tracker['reserved_funds'] += lot.max_bid_amount
            self.budget_tracker['available_budget'] -= lot.max_bid_amount
            
            # Store in database
            self.store_portfolio_lot(lot)
            
            self.logger.info(f"✅ Added lot {lot.lot_id} to portfolio: {lot.product_name}")
            self.logger.info(f"   ROI: {lot.predicted_roi:.1f}%, Score: {lot.opportunity_score:.1f}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error adding lot {lot.lot_id}: {e}")
            return False
    
    def validate_lot_criteria(self, lot: PortfolioLot) -> bool:
        """Validate if lot meets portfolio investment criteria"""
        
        # ROI threshold
        if lot.predicted_roi < self.config.min_roi_threshold:
            return False
        
        # Risk level
        risk_levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        if risk_levels[lot.risk_level] > risk_levels[self.config.max_risk_level]:
            return False
        
        # Category preference
        if self.config.preferred_categories and lot.category not in self.config.preferred_categories:
            return False
        
        # Brand preference (optional)
        if self.config.preferred_brands and lot.brand not in self.config.preferred_brands:
            # Allow if ROI is exceptionally high
            if lot.predicted_roi < 50.0:
                return False
        
        # Investment recommendation
        if lot.investment_recommendation in ["AVOID"]:
            return False
        
        return True
    
    def check_budget_availability(self, amount: float) -> bool:
        """Check if budget is available for the amount"""
        return self.budget_tracker['available_budget'] >= amount
    
    def store_portfolio_lot(self, lot: PortfolioLot):
        """Store portfolio lot in database"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO portfolio_lots 
            (lot_id, auction_id, product_name, current_price, instant_win_price, 
             predicted_final_price, predicted_roi, confidence_score, risk_level, 
             category, brand, condition, time_remaining, bidder_count, bid_count, 
             opportunity_score, investment_recommendation, max_bid_amount, priority, 
             status, notes, added_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            lot.lot_id, lot.auction_id, lot.product_name, lot.current_price,
            lot.instant_win_price, lot.predicted_final_price, lot.predicted_roi,
            lot.confidence_score, lot.risk_level, lot.category, lot.brand,
            lot.condition, lot.time_remaining, lot.bidder_count, lot.bid_count,
            lot.opportunity_score, lot.investment_recommendation, lot.max_bid_amount,
            lot.priority, lot.status, lot.notes, lot.added_at, datetime.now().isoformat()
        ))
        self.conn.commit()
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        
        active_lots = [lot for lot in self.portfolio_lots.values() if lot.status == "ACTIVE"]
        won_lots = [lot for lot in self.portfolio_lots.values() if lot.status == "WON"]
        lost_lots = [lot for lot in self.portfolio_lots.values() if lot.status == "LOST"]
        
        # Calculate metrics
        total_invested = sum(lot.max_bid_amount for lot in won_lots)
        total_value = sum(lot.instant_win_price for lot in won_lots)
        unrealized_value = sum(lot.instant_win_price for lot in active_lots)
        
        summary = {
            'portfolio_overview': {
                'total_lots': len(self.portfolio_lots),
                'active_lots': len(active_lots),
                'won_lots': len(won_lots),
                'lost_lots': len(lost_lots),
                'success_rate': (len(won_lots) / len(self.portfolio_lots) * 100) if self.portfolio_lots else 0
            },
            'financial_metrics': {
                'total_invested': total_invested,
                'total_value': total_value,
                'unrealized_value': unrealized_value,
                'realized_roi': ((total_value - total_invested) / total_invested * 100) if total_invested > 0 else 0,
                'potential_roi': sum(lot.predicted_roi for lot in active_lots) / len(active_lots) if active_lots else 0
            },
            'budget_status': self.budget_tracker.copy(),
            'top_opportunities': sorted(active_lots, key=lambda x: x.opportunity_score, reverse=True)[:5],
            'risk_distribution': self.get_risk_distribution(),
            'category_distribution': self.get_category_distribution()
        }
        
        return summary
    
    def get_risk_distribution(self) -> Dict[str, int]:
        """Get distribution of lots by risk level"""
        distribution = defaultdict(int)
        for lot in self.portfolio_lots.values():
            if lot.status == "ACTIVE":
                distribution[lot.risk_level] += 1
        return dict(distribution)
    
    def get_category_distribution(self) -> Dict[str, int]:
        """Get distribution of lots by category"""
        distribution = defaultdict(int)
        for lot in self.portfolio_lots.values():
            if lot.status == "ACTIVE":
                distribution[lot.category] += 1
        return dict(distribution)
    
    def optimize_portfolio(self) -> List[Dict]:
        """Optimize portfolio allocation and suggest actions"""
        
        self.logger.info("🔧 Optimizing portfolio allocation...")
        
        recommendations = []
        active_lots = [lot for lot in self.portfolio_lots.values() if lot.status == "ACTIVE"]
        
        # 1. Budget optimization
        if self.budget_tracker['available_budget'] < self.config.total_budget * 0.1:
            recommendations.append({
                'type': 'BUDGET_WARNING',
                'priority': 'HIGH',
                'message': 'Low available budget - consider reducing reserved funds or increasing budget',
                'action': 'Review low-priority lots for removal'
            })
        
        # 2. Risk diversification
        risk_dist = self.get_risk_distribution()
        high_risk_ratio = risk_dist.get('HIGH', 0) / len(active_lots) if active_lots else 0
        
        if high_risk_ratio > 0.3:
            recommendations.append({
                'type': 'RISK_BALANCE',
                'priority': 'MEDIUM',
                'message': f'High-risk lots comprise {high_risk_ratio*100:.1f}% of portfolio',
                'action': 'Consider adding more low-risk opportunities'
            })
        
        # 3. Category diversification
        cat_dist = self.get_category_distribution()
        if len(cat_dist) < 3 and len(active_lots) > 5:
            recommendations.append({
                'type': 'DIVERSIFICATION',
                'priority': 'LOW',
                'message': 'Portfolio concentrated in few categories',
                'action': 'Consider diversifying across more categories'
            })
        
        # 4. Opportunity scoring
        low_score_lots = [lot for lot in active_lots if lot.opportunity_score < 50]
        if len(low_score_lots) > len(active_lots) * 0.3:
            recommendations.append({
                'type': 'OPPORTUNITY_QUALITY',
                'priority': 'MEDIUM',
                'message': f'{len(low_score_lots)} lots have low opportunity scores',
                'action': 'Review and consider removing low-scoring lots'
            })
        
        # 5. Timing optimization
        ending_soon = [lot for lot in active_lots if 'hour' in lot.time_remaining.lower()]
        if len(ending_soon) > self.config.max_concurrent_bids:
            recommendations.append({
                'type': 'TIMING_CONFLICT',
                'priority': 'HIGH',
                'message': f'{len(ending_soon)} auctions ending soon - may exceed concurrent bid limit',
                'action': 'Prioritize highest-value opportunities'
            })
        
        self.logger.info(f"🔧 Portfolio optimization complete: {len(recommendations)} recommendations")
        return recommendations
    
    async def execute_bidding_strategy(self) -> List[BidResult]:
        """Execute intelligent bidding strategy across portfolio"""
        
        self.logger.info("🎯 Executing portfolio bidding strategy...")
        
        active_lots = [lot for lot in self.portfolio_lots.values() if lot.status == "ACTIVE"]
        
        if not active_lots:
            self.logger.info("No active lots in portfolio")
            return []
        
        # Prioritize lots for bidding
        prioritized_lots = self.prioritize_bidding_opportunities(active_lots)
        
        # Create bid requests
        bid_requests = []
        for lot in prioritized_lots[:self.config.max_concurrent_bids]:
            
            # Calculate optimal bid amount
            optimal_bid = self.calculate_optimal_bid(lot)
            
            bid_request = BidRequest(
                lot_id=lot.lot_id,
                auction_id=lot.auction_id,
                bid_amount=optimal_bid,
                max_bid=lot.max_bid_amount,
                priority=lot.priority,
                timing_strategy=self.determine_timing_strategy(lot),
                notes=f"Portfolio bid - Score: {lot.opportunity_score:.1f}, ROI: {lot.predicted_roi:.1f}%"
            )
            
            bid_requests.append(bid_request)
            
            # Mark as bidding
            lot.status = "BIDDING"
            self.active_bids[lot.lot_id] = bid_request
        
        # Execute bids
        results = await self.bidding_system.execute_bidding_queue(bid_requests)
        
        # Update portfolio based on results
        self.update_portfolio_from_results(results)
        
        return results
    
    def prioritize_bidding_opportunities(self, lots: List[PortfolioLot]) -> List[PortfolioLot]:
        """Prioritize lots for bidding based on multiple factors"""
        
        def priority_score(lot: PortfolioLot) -> float:
            score = 0.0
            
            # Opportunity score (40% weight)
            score += lot.opportunity_score * 0.4
            
            # ROI potential (30% weight)
            score += min(lot.predicted_roi, 100) * 0.3
            
            # Confidence score (20% weight)
            score += lot.confidence_score * 0.2
            
            # Time urgency (10% weight)
            if 'hour' in lot.time_remaining.lower():
                score += 10  # Ending soon bonus
            elif 'minute' in lot.time_remaining.lower():
                score += 20  # Ending very soon bonus
            
            # Risk penalty
            risk_penalty = {"LOW": 0, "MEDIUM": -5, "HIGH": -10}
            score += risk_penalty.get(lot.risk_level, 0)
            
            # Priority bonus
            priority_bonus = {"HIGH": 10, "MEDIUM": 5, "LOW": 0}
            score += priority_bonus.get(lot.priority, 0)
            
            return score
        
        return sorted(lots, key=priority_score, reverse=True)
    
    def calculate_optimal_bid(self, lot: PortfolioLot) -> float:
        """Calculate optimal bid amount for a lot"""
        
        # Base bid: current price + small increment
        base_bid = lot.current_price + 1.0
        
        # Factor in predicted final price
        predicted_bid = lot.predicted_final_price * 0.8  # Bid 80% of predicted final
        
        # Factor in confidence
        confidence_adjusted = predicted_bid * (lot.confidence_score / 100)
        
        # Choose conservative approach
        optimal_bid = min(base_bid, predicted_bid, confidence_adjusted, lot.max_bid_amount)
        
        # Ensure minimum increment
        optimal_bid = max(optimal_bid, lot.current_price + 0.50)
        
        return round(optimal_bid, 2)
    
    def determine_timing_strategy(self, lot: PortfolioLot) -> str:
        """Determine optimal timing strategy for a lot"""
        
        time_remaining = lot.time_remaining.lower()
        
        if 'minute' in time_remaining:
            return "SNIPE"  # Last-second bidding
        elif 'hour' in time_remaining:
            return "LAST_MINUTE"  # Wait until final minutes
        else:
            return "IMMEDIATE"  # Bid now
    
    def update_portfolio_from_results(self, results: List[BidResult]):
        """Update portfolio status based on bidding results"""
        
        for result in results:
            if result.lot_id in self.portfolio_lots:
                lot = self.portfolio_lots[result.lot_id]
                
                if result.success:
                    lot.status = "BIDDING"  # Still in auction, but we have a bid
                    self.logger.info(f"✅ Bid placed on lot {result.lot_id}: ${result.bid_amount}")
                else:
                    lot.status = "ACTIVE"  # Return to active status
                    self.logger.warning(f"❌ Bid failed on lot {result.lot_id}: {result.message}")
                
                # Update database
                self.store_portfolio_lot(lot)
    
    def generate_portfolio_report(self) -> Dict:
        """Generate comprehensive portfolio performance report"""
        
        summary = self.get_portfolio_summary()
        recommendations = self.optimize_portfolio()
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'session_duration': str(datetime.now() - self.session_start),
            'portfolio_summary': summary,
            'optimization_recommendations': recommendations,
            'performance_metrics': {
                'total_opportunities_evaluated': len(self.portfolio_lots),
                'active_investments': len([l for l in self.portfolio_lots.values() if l.status == "ACTIVE"]),
                'budget_efficiency': (self.budget_tracker['reserved_funds'] / self.config.total_budget * 100),
                'average_opportunity_score': sum(l.opportunity_score for l in self.portfolio_lots.values()) / len(self.portfolio_lots) if self.portfolio_lots else 0,
                'risk_weighted_return': self.calculate_risk_weighted_return()
            },
            'top_performers': self.get_top_performing_lots(),
            'alerts': self.generate_portfolio_alerts()
        }
        
        # Save report
        os.makedirs('data_outputs', exist_ok=True)
        report_path = f"data_outputs/portfolio_report_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"📊 PORTFOLIO REPORT GENERATED:")
        self.logger.info(f"   Total Lots: {summary['portfolio_overview']['total_lots']}")
        self.logger.info(f"   Active: {summary['portfolio_overview']['active_lots']}")
        self.logger.info(f"   Success Rate: {summary['portfolio_overview']['success_rate']:.1f}%")
        self.logger.info(f"   Budget Utilization: {report['performance_metrics']['budget_efficiency']:.1f}%")
        self.logger.info(f"   Report: {report_path}")
        
        return report
    
    def calculate_risk_weighted_return(self) -> float:
        """Calculate risk-weighted return for the portfolio"""
        
        total_weighted_return = 0.0
        total_weight = 0.0
        
        for lot in self.portfolio_lots.values():
            if lot.status in ["ACTIVE", "BIDDING"]:
                # Weight by inverse of risk
                risk_weight = {"LOW": 1.0, "MEDIUM": 0.7, "HIGH": 0.4}[lot.risk_level]
                weighted_return = lot.predicted_roi * risk_weight
                
                total_weighted_return += weighted_return
                total_weight += risk_weight
        
        return total_weighted_return / total_weight if total_weight > 0 else 0.0
    
    def get_top_performing_lots(self) -> List[Dict]:
        """Get top performing lots by various metrics"""
        
        active_lots = [lot for lot in self.portfolio_lots.values() if lot.status == "ACTIVE"]
        
        return {
            'highest_roi': sorted(active_lots, key=lambda x: x.predicted_roi, reverse=True)[:3],
            'highest_confidence': sorted(active_lots, key=lambda x: x.confidence_score, reverse=True)[:3],
            'best_opportunities': sorted(active_lots, key=lambda x: x.opportunity_score, reverse=True)[:3],
            'lowest_risk': sorted([l for l in active_lots if l.risk_level == "LOW"], key=lambda x: x.predicted_roi, reverse=True)[:3]
        }
    
    def generate_portfolio_alerts(self) -> List[Dict]:
        """Generate important portfolio alerts"""
        
        alerts = []
        
        # Budget alerts
        if self.budget_tracker['available_budget'] < self.config.total_budget * 0.1:
            alerts.append({
                'type': 'BUDGET_LOW',
                'severity': 'HIGH',
                'message': f"Available budget low: ${self.budget_tracker['available_budget']:.2f}"
            })
        
        # Ending soon alerts
        ending_soon = [l for l in self.portfolio_lots.values() 
                      if l.status == "ACTIVE" and 'hour' in l.time_remaining.lower()]
        
        if len(ending_soon) > 5:
            alerts.append({
                'type': 'TIMING_CONFLICT',
                'severity': 'MEDIUM',
                'message': f"{len(ending_soon)} auctions ending soon - prepare for concurrent bidding"
            })
        
        # High-value opportunities
        high_value = [l for l in self.portfolio_lots.values() 
                     if l.status == "ACTIVE" and l.opportunity_score > 80]
        
        if high_value:
            alerts.append({
                'type': 'HIGH_VALUE_OPPORTUNITY',
                'severity': 'INFO',
                'message': f"{len(high_value)} high-value opportunities available"
            })
        
        return alerts
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'conn'):
            self.conn.close()
        if hasattr(self, 'bidding_system'):
            self.bidding_system.cleanup()
        self.logger.info("🧹 Portfolio management system cleanup complete")

async def main():
    """Test the portfolio management system"""
    
    print("🎯 PORTFOLIO MANAGEMENT SYSTEM TEST")
    print("="*50)
    
    # Create test portfolio configuration
    config = PortfolioConfig(
        total_budget=300.0,
        daily_budget=30.0,
        min_roi_threshold=30.0,
        max_risk_level="MEDIUM",
        preferred_categories=["Electronics", "Computers"],
        auto_bid_enabled=True
    )
    
    # Initialize portfolio system
    portfolio = PortfolioManagementSystem(config)
    
    try:
        # Create test lots
        test_lots = [
            PortfolioLot(
                lot_id=35863830,
                auction_id=48796,
                product_name="ECOVACS DEEBOT X8 PRO OMNI Robot Vacuum",
                current_price=1.00,
                instant_win_price=1299.99,
                predicted_final_price=200.00,
                predicted_roi=550.0,
                confidence_score=85.0,
                risk_level="MEDIUM",
                category="Electronics",
                brand="ECOVACS",
                condition="New",
                time_remaining="2 hours",
                bidder_count=6,
                bid_count=0,
                opportunity_score=70.0,
                investment_recommendation="BUY",
                max_bid_amount=250.00,
                priority="HIGH"
            ),
            PortfolioLot(
                lot_id=35863831,
                auction_id=48797,
                product_name="Apple MacBook Pro 16-inch",
                current_price=50.00,
                instant_win_price=2499.99,
                predicted_final_price=800.00,
                predicted_roi=212.0,
                confidence_score=75.0,
                risk_level="LOW",
                category="Computers",
                brand="Apple",
                condition="Refurbished",
                time_remaining="1 day",
                bidder_count=12,
                bid_count=5,
                opportunity_score=85.0,
                investment_recommendation="STRONG_BUY",
                max_bid_amount=1000.00,
                priority="HIGH"
            ),
            PortfolioLot(
                lot_id=35863832,
                auction_id=48798,
                product_name="Samsung 65-inch QLED TV",
                current_price=25.00,
                instant_win_price=1799.99,
                predicted_final_price=400.00,
                predicted_roi=1500.0,
                confidence_score=60.0,
                risk_level="HIGH",
                category="Electronics",
                brand="Samsung",
                condition="Used",
                time_remaining="30 minutes",
                bidder_count=20,
                bid_count=15,
                opportunity_score=65.0,
                investment_recommendation="CONSIDER",
                max_bid_amount=500.00,
                priority="MEDIUM"
            )
        ]
        
        # Add lots to portfolio
        print("\n📦 Adding lots to portfolio...")
        for lot in test_lots:
            success = portfolio.add_lot_to_portfolio(lot)
            print(f"   {'✅' if success else '❌'} {lot.product_name}: ROI {lot.predicted_roi:.1f}%")
        
        # Get portfolio summary
        print("\n📊 Portfolio Summary:")
        summary = portfolio.get_portfolio_summary()
        print(f"   Total Lots: {summary['portfolio_overview']['total_lots']}")
        print(f"   Active Lots: {summary['portfolio_overview']['active_lots']}")
        print(f"   Budget Available: ${summary['budget_status']['available_budget']:.2f}")
        print(f"   Reserved Funds: ${summary['budget_status']['reserved_funds']:.2f}")
        
        # Optimize portfolio
        print("\n🔧 Portfolio Optimization:")
        recommendations = portfolio.optimize_portfolio()
        for rec in recommendations:
            print(f"   {rec['priority']}: {rec['message']}")
        
        # Execute bidding strategy
        print("\n🎯 Executing Bidding Strategy:")
        results = await portfolio.execute_bidding_strategy()
        print(f"   Executed {len(results)} bids")
        for result in results:
            print(f"   {'✅' if result.success else '❌'} Lot {result.lot_id}: ${result.bid_amount}")
        
        # Generate final report
        print("\n📋 Generating Portfolio Report:")
        report = portfolio.generate_portfolio_report()
        print(f"   Report generated with {len(report['optimization_recommendations'])} recommendations")
        print(f"   Budget Efficiency: {report['performance_metrics']['budget_efficiency']:.1f}%")
        
    finally:
        portfolio.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 