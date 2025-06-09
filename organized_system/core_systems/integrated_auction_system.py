#!/usr/bin/env python3
"""
Integrated Auction Intelligence System
Combines real bidding, portfolio management, and enhanced ML models
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import os

# Import our systems
import sys
sys.path.append('.')
from core_systems.real_bidding_system import RealBiddingSystem, BidRequest
from core_systems.portfolio_management_system import PortfolioManagementSystem, PortfolioLot, PortfolioConfig
from ml_prediction.enhanced_ml_models import EnhancedMLModels

@dataclass
class AuctionOpportunity:
    lot_id: int
    auction_id: int
    product_name: str
    current_price: float
    instant_win_price: float
    category: str
    brand: str
    condition: str
    time_remaining: str
    bidder_count: int
    bid_count: int
    
    # ML Predictions
    predicted_final_price: float = 0.0
    ml_confidence: float = 0.0
    optimal_bid: float = 0.0
    win_probability: float = 0.0
    
    # Portfolio Analysis
    opportunity_score: float = 0.0
    predicted_roi: float = 0.0
    risk_level: str = "MEDIUM"
    investment_recommendation: str = "CONSIDER"
    
    # System Status
    analysis_timestamp: str = ""
    
    def __post_init__(self):
        if not self.analysis_timestamp:
            self.analysis_timestamp = datetime.now().isoformat()

class IntegratedAuctionSystem:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data_outputs/integrated_auction_system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize subsystems
        self.logger.info("🚀 Initializing Integrated Auction System...")
        
        # ML Models
        self.ml_system = EnhancedMLModels()
        
        # Portfolio Management
        portfolio_config = PortfolioConfig(
            total_budget=300.0,
            daily_budget=30.0,
            min_roi_threshold=25.0,
            max_risk_level="MEDIUM",
            preferred_categories=["Electronics", "Computers", "Home & Garden"],
            auto_bid_enabled=True
        )
        self.portfolio_system = PortfolioManagementSystem(portfolio_config)
        
        # Real Bidding System
        self.bidding_system = RealBiddingSystem(dry_run=dry_run)
        
        # System state
        self.opportunities: Dict[int, AuctionOpportunity] = {}
        self.session_stats = {
            'session_start': datetime.now().isoformat(),
            'opportunities_analyzed': 0,
            'lots_added_to_portfolio': 0,
            'bids_executed': 0,
            'total_investment': 0.0,
            'predicted_returns': 0.0
        }
        
        self.logger.info("✅ Integrated Auction System initialized")
    
    async def analyze_auction_opportunity(self, lot_data: Dict) -> AuctionOpportunity:
        """Comprehensive analysis of an auction opportunity"""
        
        self.logger.info(f"🔍 Analyzing opportunity: Lot {lot_data.get('lot_id')}")
        
        # Create opportunity object
        opportunity = AuctionOpportunity(
            lot_id=lot_data['lot_id'],
            auction_id=lot_data['auction_id'],
            product_name=lot_data['product_name'],
            current_price=lot_data['current_price'],
            instant_win_price=lot_data['instant_win_price'],
            category=lot_data['category'],
            brand=lot_data['brand'],
            condition=lot_data['condition'],
            time_remaining=lot_data['time_remaining'],
            bidder_count=lot_data['bidder_count'],
            bid_count=lot_data['bid_count']
        )
        
        # Step 1: ML Price Prediction
        self.logger.info("🤖 Running ML price prediction...")
        try:
            ml_prediction = self.ml_system.predict_auction_price(lot_data)
            
            opportunity.predicted_final_price = ml_prediction.predicted_final_price
            opportunity.ml_confidence = ml_prediction.confidence_score
            opportunity.optimal_bid = ml_prediction.optimal_bid
            opportunity.win_probability = ml_prediction.win_probability
            
            self.logger.info(f"   ML Prediction: ${ml_prediction.predicted_final_price} (Confidence: {ml_prediction.confidence_score}%)")
            
        except Exception as e:
            self.logger.warning(f"ML prediction failed: {e}")
            # Fallback prediction
            opportunity.predicted_final_price = opportunity.current_price * 2.0
            opportunity.ml_confidence = 30.0
            opportunity.optimal_bid = opportunity.current_price * 1.5
            opportunity.win_probability = 50.0
        
        # Step 2: ROI and Risk Analysis
        self.logger.info("📊 Calculating ROI and risk...")
        
        # Calculate ROI
        if opportunity.predicted_final_price > 0:
            opportunity.predicted_roi = ((opportunity.instant_win_price - opportunity.predicted_final_price) / opportunity.predicted_final_price) * 100
        else:
            opportunity.predicted_roi = 0.0
        
        # Determine risk level
        opportunity.risk_level = self.calculate_risk_level(opportunity)
        
        # Calculate opportunity score
        opportunity.opportunity_score = self.calculate_opportunity_score(opportunity)
        
        # Generate investment recommendation
        opportunity.investment_recommendation = self.generate_investment_recommendation(opportunity)
        
        self.logger.info(f"   ROI: {opportunity.predicted_roi:.1f}%, Risk: {opportunity.risk_level}, Score: {opportunity.opportunity_score:.1f}")
        
        # Store opportunity
        self.opportunities[opportunity.lot_id] = opportunity
        self.session_stats['opportunities_analyzed'] += 1
        
        return opportunity
    
    def calculate_risk_level(self, opportunity: AuctionOpportunity) -> str:
        """Calculate risk level based on multiple factors"""
        
        risk_score = 0
        
        # Competition risk
        if opportunity.bidder_count > 15:
            risk_score += 2
        elif opportunity.bidder_count > 8:
            risk_score += 1
        
        # Condition risk
        condition_risk = {"New": 0, "Like New": 0, "Good": 1, "Fair": 2, "Poor": 3}
        risk_score += condition_risk.get(opportunity.condition, 1)
        
        # ML confidence risk
        if opportunity.ml_confidence < 50:
            risk_score += 2
        elif opportunity.ml_confidence < 70:
            risk_score += 1
        
        # Time pressure risk
        if 'minute' in opportunity.time_remaining.lower():
            risk_score += 1
        
        # Price volatility risk
        price_ratio = opportunity.current_price / opportunity.instant_win_price
        if price_ratio > 0.5:  # Already expensive
            risk_score += 2
        elif price_ratio > 0.3:
            risk_score += 1
        
        # Determine risk level
        if risk_score <= 2:
            return "LOW"
        elif risk_score <= 5:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def calculate_opportunity_score(self, opportunity: AuctionOpportunity) -> float:
        """Calculate comprehensive opportunity score (0-100)"""
        
        score = 0.0
        
        # ROI component (40% weight)
        roi_score = min(opportunity.predicted_roi / 100 * 40, 40)  # Cap at 40 points
        score += roi_score
        
        # ML confidence component (25% weight)
        confidence_score = opportunity.ml_confidence / 100 * 25
        score += confidence_score
        
        # Win probability component (20% weight)
        win_score = opportunity.win_probability / 100 * 20
        score += win_score
        
        # Risk adjustment (15% weight)
        risk_adjustment = {"LOW": 15, "MEDIUM": 10, "HIGH": 5}
        score += risk_adjustment[opportunity.risk_level]
        
        # Brand premium bonus
        premium_brands = ["Apple", "Samsung", "Sony", "LG", "Dell"]
        if opportunity.brand in premium_brands:
            score += 5
        
        # Category bonus
        preferred_categories = ["Electronics", "Computers"]
        if opportunity.category in preferred_categories:
            score += 3
        
        return min(score, 100.0)  # Cap at 100
    
    def generate_investment_recommendation(self, opportunity: AuctionOpportunity) -> str:
        """Generate investment recommendation"""
        
        if opportunity.opportunity_score >= 80 and opportunity.predicted_roi >= 50:
            return "STRONG_BUY"
        elif opportunity.opportunity_score >= 65 and opportunity.predicted_roi >= 25:
            return "BUY"
        elif opportunity.opportunity_score >= 50 and opportunity.predicted_roi >= 15:
            return "CONSIDER"
        elif opportunity.opportunity_score >= 35:
            return "WATCH"
        else:
            return "AVOID"
    
    async def process_opportunities(self, opportunities_data: List[Dict]) -> List[AuctionOpportunity]:
        """Process multiple auction opportunities"""
        
        self.logger.info(f"🔄 Processing {len(opportunities_data)} auction opportunities...")
        
        analyzed_opportunities = []
        
        for lot_data in opportunities_data:
            try:
                opportunity = await self.analyze_auction_opportunity(lot_data)
                analyzed_opportunities.append(opportunity)
                
                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"Error analyzing lot {lot_data.get('lot_id')}: {e}")
        
        # Sort by opportunity score
        analyzed_opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        self.logger.info(f"✅ Processed {len(analyzed_opportunities)} opportunities")
        return analyzed_opportunities
    
    async def execute_portfolio_strategy(self, opportunities: List[AuctionOpportunity]) -> Dict:
        """Execute comprehensive portfolio strategy"""
        
        self.logger.info("🎯 Executing integrated portfolio strategy...")
        
        # Filter opportunities that meet criteria
        qualified_opportunities = [
            opp for opp in opportunities 
            if opp.investment_recommendation in ["STRONG_BUY", "BUY", "CONSIDER"]
            and opp.predicted_roi >= 25.0
        ]
        
        self.logger.info(f"📋 {len(qualified_opportunities)} opportunities meet investment criteria")
        
        # Convert to portfolio lots
        portfolio_lots = []
        for opp in qualified_opportunities:
            portfolio_lot = PortfolioLot(
                lot_id=opp.lot_id,
                auction_id=opp.auction_id,
                product_name=opp.product_name,
                current_price=opp.current_price,
                instant_win_price=opp.instant_win_price,
                predicted_final_price=opp.predicted_final_price,
                predicted_roi=opp.predicted_roi,
                confidence_score=opp.ml_confidence,
                risk_level=opp.risk_level,
                category=opp.category,
                brand=opp.brand,
                condition=opp.condition,
                time_remaining=opp.time_remaining,
                bidder_count=opp.bidder_count,
                bid_count=opp.bid_count,
                opportunity_score=opp.opportunity_score,
                investment_recommendation=opp.investment_recommendation,
                max_bid_amount=opp.optimal_bid,
                priority="HIGH" if opp.opportunity_score >= 80 else "MEDIUM" if opp.opportunity_score >= 65 else "LOW"
            )
            portfolio_lots.append(portfolio_lot)
        
        # Add lots to portfolio
        added_lots = []
        for lot in portfolio_lots:
            if self.portfolio_system.add_lot_to_portfolio(lot):
                added_lots.append(lot)
                self.session_stats['lots_added_to_portfolio'] += 1
        
        self.logger.info(f"📦 Added {len(added_lots)} lots to portfolio")
        
        # Execute bidding strategy
        if added_lots and not self.dry_run:
            self.logger.info("🎯 Executing bidding strategy...")
            bid_results = await self.portfolio_system.execute_bidding_strategy()
            self.session_stats['bids_executed'] = len(bid_results)
            
            # Calculate investment totals
            successful_bids = [r for r in bid_results if r.success]
            self.session_stats['total_investment'] = sum(r.bid_amount for r in successful_bids)
            
            # Calculate predicted returns
            for result in successful_bids:
                if result.lot_id in self.opportunities:
                    opp = self.opportunities[result.lot_id]
                    predicted_value = opp.instant_win_price
                    self.session_stats['predicted_returns'] += predicted_value
        
        # Generate comprehensive report
        strategy_report = {
            'execution_timestamp': datetime.now().isoformat(),
            'opportunities_analyzed': len(opportunities),
            'qualified_opportunities': len(qualified_opportunities),
            'lots_added_to_portfolio': len(added_lots),
            'portfolio_summary': self.portfolio_system.get_portfolio_summary(),
            'top_opportunities': [asdict(opp) for opp in opportunities[:5]],
            'session_statistics': self.session_stats,
            'performance_projections': self.calculate_performance_projections(added_lots)
        }
        
        return strategy_report
    
    def calculate_performance_projections(self, portfolio_lots: List[PortfolioLot]) -> Dict:
        """Calculate performance projections for the portfolio"""
        
        if not portfolio_lots:
            return {}
        
        total_investment = sum(lot.max_bid_amount for lot in portfolio_lots)
        total_potential_value = sum(lot.instant_win_price for lot in portfolio_lots)
        weighted_roi = sum(lot.predicted_roi * lot.max_bid_amount for lot in portfolio_lots) / total_investment
        weighted_confidence = sum(lot.confidence_score * lot.max_bid_amount for lot in portfolio_lots) / total_investment
        
        return {
            'total_investment': total_investment,
            'total_potential_value': total_potential_value,
            'projected_roi': weighted_roi,
            'average_confidence': weighted_confidence,
            'risk_distribution': {
                'LOW': len([l for l in portfolio_lots if l.risk_level == "LOW"]),
                'MEDIUM': len([l for l in portfolio_lots if l.risk_level == "MEDIUM"]),
                'HIGH': len([l for l in portfolio_lots if l.risk_level == "HIGH"])
            },
            'category_distribution': {
                cat: len([l for l in portfolio_lots if l.category == cat])
                for cat in set(lot.category for lot in portfolio_lots)
            }
        }
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive system performance report"""
        
        report = {
            'report_timestamp': datetime.now().isoformat(),
            'system_overview': {
                'session_duration': str(datetime.now() - datetime.fromisoformat(self.session_stats['session_start'])),
                'opportunities_analyzed': self.session_stats['opportunities_analyzed'],
                'lots_in_portfolio': len(self.portfolio_system.portfolio_lots),
                'ml_models_active': len(self.ml_system.models),
                'dry_run_mode': self.dry_run
            },
            'ml_performance': self.ml_system.get_model_performance_report(),
            'portfolio_performance': {
                'total_lots': len(self.portfolio_system.portfolio_lots),
                'budget_status': self.portfolio_system.budget_tracker
            },
            'session_statistics': self.session_stats,
            'top_opportunities': [
                asdict(opp) for opp in 
                sorted(self.opportunities.values(), key=lambda x: x.opportunity_score, reverse=True)[:10]
            ]
        }
        
        # Save report
        os.makedirs('data_outputs', exist_ok=True)
        report_path = f"data_outputs/integrated_system_report_{int(time.time())}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"📊 COMPREHENSIVE REPORT GENERATED:")
        self.logger.info(f"   Opportunities Analyzed: {report['system_overview']['opportunities_analyzed']}")
        self.logger.info(f"   Portfolio Lots: {report['system_overview']['lots_in_portfolio']}")
        self.logger.info(f"   ML Models Active: {report['system_overview']['ml_models_active']}")
        self.logger.info(f"   Session Duration: {report['system_overview']['session_duration']}")
        self.logger.info(f"   Report: {report_path}")
        
        return report
    
    def cleanup(self):
        """Clean up all subsystems"""
        self.ml_system.cleanup()
        self.portfolio_system.cleanup()
        self.bidding_system.cleanup()
        self.logger.info("🧹 Integrated auction system cleanup complete")

async def main():
    """Test the integrated auction system"""
    
    print("🚀 INTEGRATED AUCTION INTELLIGENCE SYSTEM")
    print("="*60)
    
    # Initialize integrated system
    system = IntegratedAuctionSystem(dry_run=True)
    
    try:
        # Create test auction opportunities
        test_opportunities = [
            {
                'lot_id': 35863830,
                'auction_id': 48796,
                'product_name': 'ECOVACS DEEBOT X8 PRO OMNI Robot Vacuum',
                'current_price': 1.00,
                'instant_win_price': 1299.99,
                'category': 'Electronics',
                'brand': 'ECOVACS',
                'condition': 'New',
                'time_remaining': '2 hours',
                'bidder_count': 6,
                'bid_count': 0
            },
            {
                'lot_id': 35863831,
                'auction_id': 48797,
                'product_name': 'Apple MacBook Pro 16-inch M1 Max',
                'current_price': 50.00,
                'instant_win_price': 2499.99,
                'category': 'Computers',
                'brand': 'Apple',
                'condition': 'Like New',
                'time_remaining': '1 day',
                'bidder_count': 12,
                'bid_count': 5
            },
            {
                'lot_id': 35863832,
                'auction_id': 48798,
                'product_name': 'Samsung 65" QLED 4K Smart TV',
                'current_price': 25.00,
                'instant_win_price': 1799.99,
                'category': 'Electronics',
                'brand': 'Samsung',
                'condition': 'Good',
                'time_remaining': '30 minutes',
                'bidder_count': 20,
                'bid_count': 15
            },
            {
                'lot_id': 35863833,
                'auction_id': 48799,
                'product_name': 'Sony WH-1000XM5 Wireless Headphones',
                'current_price': 15.00,
                'instant_win_price': 399.99,
                'category': 'Electronics',
                'brand': 'Sony',
                'condition': 'New',
                'time_remaining': '6 hours',
                'bidder_count': 8,
                'bid_count': 3
            },
            {
                'lot_id': 35863834,
                'auction_id': 48800,
                'product_name': 'Generic Bluetooth Speaker',
                'current_price': 5.00,
                'instant_win_price': 49.99,
                'category': 'Electronics',
                'brand': 'Generic',
                'condition': 'Fair',
                'time_remaining': '3 days',
                'bidder_count': 3,
                'bid_count': 1
            }
        ]
        
        print(f"\n🔍 ANALYZING {len(test_opportunities)} AUCTION OPPORTUNITIES")
        print("-" * 60)
        
        # Process opportunities
        analyzed_opportunities = await system.process_opportunities(test_opportunities)
        
        # Display analysis results
        print(f"\n📊 OPPORTUNITY ANALYSIS RESULTS:")
        for i, opp in enumerate(analyzed_opportunities, 1):
            print(f"\n{i}. {opp.product_name}")
            print(f"   Current Price: ${opp.current_price}")
            print(f"   Predicted Final: ${opp.predicted_final_price}")
            print(f"   Predicted ROI: {opp.predicted_roi:.1f}%")
            print(f"   Opportunity Score: {opp.opportunity_score:.1f}/100")
            print(f"   Risk Level: {opp.risk_level}")
            print(f"   Recommendation: {opp.investment_recommendation}")
            print(f"   ML Confidence: {opp.ml_confidence:.1f}%")
        
        print(f"\n🎯 EXECUTING PORTFOLIO STRATEGY")
        print("-" * 40)
        
        # Execute portfolio strategy
        strategy_report = await system.execute_portfolio_strategy(analyzed_opportunities)
        
        print(f"\n📋 STRATEGY EXECUTION RESULTS:")
        print(f"   Opportunities Analyzed: {strategy_report['opportunities_analyzed']}")
        print(f"   Qualified Opportunities: {strategy_report['qualified_opportunities']}")
        print(f"   Added to Portfolio: {strategy_report['lots_added_to_portfolio']}")
        
        if 'performance_projections' in strategy_report:
            projections = strategy_report['performance_projections']
            print(f"   Total Investment: ${projections.get('total_investment', 0):.2f}")
            print(f"   Projected ROI: {projections.get('projected_roi', 0):.1f}%")
            print(f"   Average Confidence: {projections.get('average_confidence', 0):.1f}%")
        
        print(f"\n📊 GENERATING COMPREHENSIVE REPORT")
        print("-" * 40)
        
        # Generate final report
        final_report = system.generate_comprehensive_report()
        
        print(f"\n✅ INTEGRATION TEST COMPLETE!")
        print(f"   🤖 ML Models: {final_report['system_overview']['ml_models_active']} active")
        print(f"   📦 Portfolio: {final_report['system_overview']['lots_in_portfolio']} lots")
        print(f"   🎯 Opportunities: {final_report['system_overview']['opportunities_analyzed']} analyzed")
        print(f"   ⏱️  Duration: {final_report['system_overview']['session_duration']}")
        
        # Show top opportunity
        if final_report['top_opportunities']:
            top_opp = final_report['top_opportunities'][0]
            print(f"\n🏆 TOP OPPORTUNITY:")
            print(f"   {top_opp['product_name']}")
            print(f"   Score: {top_opp['opportunity_score']:.1f}/100")
            print(f"   ROI: {top_opp['predicted_roi']:.1f}%")
            print(f"   Recommendation: {top_opp['investment_recommendation']}")
        
    finally:
        system.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 