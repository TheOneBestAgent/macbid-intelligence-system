#!/usr/bin/env python3
"""
Advanced Auction Intelligence System
Integrates real-time monitoring, predictive pricing, and automated bidding
"""

import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Import our custom modules
import sys
sys.path.append('.')
from core_systems.realtime_auction_monitor import RealTimeAuctionMonitor
from ml_prediction.predictive_pricing_model import PredictivePricingModel
from core_systems.automated_bidding_system import AutomatedBiddingSystem

class AdvancedAuctionIntelligence:
    def __init__(self):
        self.setup_logging()
        
        # Initialize core components
        self.monitor = RealTimeAuctionMonitor()
        self.pricing_model = PredictivePricingModel()
        self.bidding_system = AutomatedBiddingSystem()
        
        # System configuration
        self.intelligence_config = {
            'monitoring_enabled': True,
            'predictive_pricing_enabled': True,
            'automated_bidding_enabled': False,  # Start disabled for safety
            'dry_run_mode': True,
            'max_daily_budget': 2000.00,
            'min_roi_threshold': 25.0,
            'max_risk_level': 'MEDIUM',
            'preferred_categories': ['ELECTRONICS', 'APPLIANCES', 'TOOLS'],
            'excluded_conditions': ['DAMAGED', 'PARTS_ONLY']
        }
        
        # Performance tracking
        self.session_stats = {
            'start_time': datetime.now(),
            'lots_analyzed': 0,
            'opportunities_found': 0,
            'bids_placed': 0,
            'alerts_triggered': 0
        }
        
        # Active opportunities
        self.opportunities = {}  # lot_id -> opportunity_data
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data_outputs/auction_intelligence.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def analyze_lot_opportunity(self, lot_data: Dict) -> Dict:
        """Comprehensive analysis of a lot's investment opportunity"""
        
        # Get ML prediction
        prediction = self.pricing_model.predict_price(lot_data)
        
        # Generate bidding strategy
        strategy = self.pricing_model.generate_bidding_strategy(
            lot_data, 
            max_budget=self.intelligence_config['max_daily_budget'] * 0.1  # Max 10% of daily budget per lot
        )
        
        # Calculate opportunity score
        opportunity_score = self.calculate_opportunity_score(lot_data, prediction, strategy)
        
        # Determine recommendation
        recommendation = self.generate_recommendation(lot_data, strategy, opportunity_score)
        
        # Check if lot meets our criteria
        meets_criteria = self.meets_investment_criteria(lot_data, strategy, opportunity_score)
        
        opportunity = {
            'lot_data': lot_data,
            'prediction': prediction,
            'strategy': strategy,
            'opportunity_score': opportunity_score,
            'recommendation': recommendation,
            'meets_criteria': meets_criteria,
            'analysis_timestamp': datetime.now().isoformat(),
            'priority_level': self.calculate_priority_level(opportunity_score, strategy)
        }
        
        self.session_stats['lots_analyzed'] += 1
        
        if meets_criteria:
            self.session_stats['opportunities_found'] += 1
            self.opportunities[lot_data.get('id')] = opportunity
            
            self.logger.info(f"🎯 OPPORTUNITY FOUND: {lot_data.get('lot_number')} - "
                           f"Score: {opportunity_score:.1f} - "
                           f"ROI: {strategy.get('expected_roi', 0):.1f}% - "
                           f"Strategy: {strategy.get('strategy_type')}")
        
        return opportunity
    
    def calculate_opportunity_score(self, lot_data: Dict, prediction: Dict, strategy: Dict) -> float:
        """Calculate overall opportunity score (0-100)"""
        score = 0.0
        
        # ROI component (40% weight)
        roi = strategy.get('expected_roi', 0)
        roi_score = min(roi / 100.0, 1.0) * 40
        score += roi_score
        
        # Confidence component (20% weight)
        confidence = prediction.get('confidence_score', 0)
        confidence_score = confidence * 20
        score += confidence_score
        
        # Win probability component (15% weight)
        win_prob = strategy.get('win_probability', 0)
        win_score = win_prob * 15
        score += win_score
        
        # Risk adjustment (15% weight)
        risk_level = strategy.get('risk_level', 'HIGH')
        risk_scores = {'LOW': 15, 'MEDIUM': 10, 'HIGH': 5}
        risk_score = risk_scores.get(risk_level, 5)
        score += risk_score
        
        # Brand premium (10% weight)
        product_name = lot_data.get('product_name', '').upper()
        premium_brands = ['APPLE', 'SONY', 'SAMSUNG', 'NINTENDO', 'DYSON', 'BOSE']
        if any(brand in product_name for brand in premium_brands):
            score += 10
        
        return min(score, 100.0)
    
    def generate_recommendation(self, lot_data: Dict, strategy: Dict, opportunity_score: float) -> str:
        """Generate investment recommendation"""
        
        roi = strategy.get('expected_roi', 0)
        risk_level = strategy.get('risk_level', 'HIGH')
        
        if opportunity_score >= 80 and roi >= 50 and risk_level == 'LOW':
            return 'STRONG_BUY'
        elif opportunity_score >= 60 and roi >= 30:
            return 'BUY'
        elif opportunity_score >= 40 and roi >= 15:
            return 'CONSIDER'
        elif opportunity_score >= 20:
            return 'WATCH'
        else:
            return 'AVOID'
    
    def meets_investment_criteria(self, lot_data: Dict, strategy: Dict, opportunity_score: float) -> bool:
        """Check if lot meets our investment criteria"""
        
        # Check minimum ROI threshold
        if strategy.get('expected_roi', 0) < self.intelligence_config['min_roi_threshold']:
            return False
        
        # Check risk level
        risk_level = strategy.get('risk_level', 'HIGH')
        max_risk = self.intelligence_config['max_risk_level']
        risk_levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        if risk_levels.get(risk_level, 3) > risk_levels.get(max_risk, 2):
            return False
        
        # Check category preference
        product_name = lot_data.get('product_name', '').upper()
        preferred_categories = self.intelligence_config['preferred_categories']
        
        category_match = False
        for category in preferred_categories:
            category_keywords = {
                'ELECTRONICS': ['IPHONE', 'IPAD', 'MACBOOK', 'TV', 'SPEAKER', 'HEADPHONE'],
                'APPLIANCES': ['VACUUM', 'CLEANER', 'ROBOT', 'DYSON', 'SHARK'],
                'TOOLS': ['DEWALT', 'MILWAUKEE', 'DRILL', 'SAW', 'TOOL']
            }
            
            if any(keyword in product_name for keyword in category_keywords.get(category, [])):
                category_match = True
                break
        
        if not category_match:
            return False
        
        # Check excluded conditions
        condition_name = lot_data.get('condition_name', '').upper()
        excluded_conditions = self.intelligence_config['excluded_conditions']
        
        if any(excluded in condition_name for excluded in excluded_conditions):
            return False
        
        # Check opportunity score threshold
        if opportunity_score < 40:
            return False
        
        return True
    
    def calculate_priority_level(self, opportunity_score: float, strategy: Dict) -> str:
        """Calculate priority level for opportunity"""
        
        roi = strategy.get('expected_roi', 0)
        
        if opportunity_score >= 80 and roi >= 75:
            return 'CRITICAL'
        elif opportunity_score >= 60 and roi >= 50:
            return 'HIGH'
        elif opportunity_score >= 40 and roi >= 25:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    async def scan_for_opportunities(self, auction_ids: List[int] = None) -> List[Dict]:
        """Scan auctions for investment opportunities"""
        
        if not auction_ids:
            auction_ids = [48796]  # Default to test auction
        
        opportunities = []
        
        for auction_id in auction_ids:
            self.logger.info(f"🔍 Scanning auction {auction_id} for opportunities...")
            
            try:
                # Test lot for demonstration
                test_lots = [
                    {
                        'id': 35863830,
                        'auction_id': auction_id,
                        'lot_number': '3912D',
                        'product_name': 'ECOVACS DEEBOT X8 PRO OMNI Robot Vacuum and Mop',
                        'retail_price': 1299.99,
                        'instant_win_price': 1040.00,
                        'unique_bidders': 6,
                        'total_bids': 0,
                        'condition_name': 'OPEN BOX',
                        'is_tested': True,
                        'damaged_note': 'Very dirty - lots of moisture',
                        'expected_close_date': '2025-06-15T18:30:20.000Z'
                    }
                ]
                
                for lot_data in test_lots:
                    opportunity = self.analyze_lot_opportunity(lot_data)
                    
                    if opportunity['meets_criteria']:
                        opportunities.append(opportunity)
                        
                        # Add to monitoring if enabled
                        if self.intelligence_config['monitoring_enabled']:
                            self.monitor.add_lot_to_monitor(auction_id, lot_data['id'])
                        
                        # Add to bidding targets if enabled
                        if self.intelligence_config['automated_bidding_enabled']:
                            self.bidding_system.add_bidding_target(lot_data)
                
            except Exception as e:
                self.logger.error(f"Error scanning auction {auction_id}: {e}")
        
        return opportunities
    
    def start_intelligence_system(self):
        """Start the complete auction intelligence system"""
        
        self.logger.info("🚀 STARTING ADVANCED AUCTION INTELLIGENCE SYSTEM")
        self.logger.info("="*60)
        
        # Display configuration
        self.logger.info(f"📊 SYSTEM CONFIGURATION:")
        for key, value in self.intelligence_config.items():
            self.logger.info(f"  {key}: {value}")
        
        # Start monitoring if enabled
        if self.intelligence_config['monitoring_enabled']:
            self.monitor.start_monitoring()
            self.logger.info("✅ Real-time monitoring started")
        
        # Start bidding system if enabled
        if self.intelligence_config['automated_bidding_enabled']:
            self.bidding_system.set_dry_run_mode(self.intelligence_config['dry_run_mode'])
            self.bidding_system.start_automated_bidding()
            self.logger.info(f"✅ Automated bidding started ({'DRY RUN' if self.intelligence_config['dry_run_mode'] else 'LIVE'})")
        
        self.logger.info("🎯 System ready for opportunity detection")
    
    def stop_intelligence_system(self):
        """Stop the auction intelligence system"""
        
        self.logger.info("🛑 STOPPING AUCTION INTELLIGENCE SYSTEM")
        
        # Stop monitoring
        if self.intelligence_config['monitoring_enabled']:
            self.monitor.stop_monitoring()
            self.logger.info("✅ Real-time monitoring stopped")
        
        # Stop bidding
        if self.intelligence_config['automated_bidding_enabled']:
            self.bidding_system.stop_automated_bidding()
            self.logger.info("✅ Automated bidding stopped")
        
        # Generate final report
        self.generate_session_report()
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        
        status = {
            'timestamp': datetime.now().isoformat(),
            'session_stats': self.session_stats.copy(),
            'active_opportunities': len(self.opportunities),
            'system_config': self.intelligence_config.copy()
        }
        
        # Add component statuses
        if self.intelligence_config['monitoring_enabled']:
            status['monitoring_status'] = self.monitor.get_monitoring_status()
        
        if self.intelligence_config['automated_bidding_enabled']:
            status['bidding_status'] = self.bidding_system.get_bidding_status()
        
        # Calculate session duration
        session_duration = datetime.now() - self.session_stats['start_time']
        status['session_duration_minutes'] = session_duration.total_seconds() / 60
        
        return status
    
    def generate_session_report(self) -> Dict:
        """Generate comprehensive session report"""
        
        status = self.get_system_status()
        
        # Calculate performance metrics
        session_duration = status['session_duration_minutes']
        lots_per_minute = status['session_stats']['lots_analyzed'] / max(session_duration, 1)
        opportunity_rate = (status['session_stats']['opportunities_found'] / 
                          max(status['session_stats']['lots_analyzed'], 1)) * 100
        
        # Get top opportunities
        top_opportunities = sorted(
            self.opportunities.values(),
            key=lambda x: x['opportunity_score'],
            reverse=True
        )[:5]
        
        report = {
            'session_summary': {
                'duration_minutes': session_duration,
                'lots_analyzed': status['session_stats']['lots_analyzed'],
                'opportunities_found': status['session_stats']['opportunities_found'],
                'opportunity_rate_percent': opportunity_rate,
                'analysis_rate_per_minute': lots_per_minute
            },
            'top_opportunities': [
                {
                    'lot_number': opp['lot_data'].get('lot_number'),
                    'product_name': opp['lot_data'].get('product_name'),
                    'opportunity_score': opp['opportunity_score'],
                    'expected_roi': opp['strategy'].get('expected_roi', 0),
                    'recommendation': opp['recommendation'],
                    'priority_level': opp['priority_level']
                }
                for opp in top_opportunities
            ],
            'system_performance': status
        }
        
        # Log report
        self.logger.info("📈 SESSION REPORT:")
        self.logger.info(f"  Duration: {session_duration:.1f} minutes")
        self.logger.info(f"  Lots Analyzed: {status['session_stats']['lots_analyzed']}")
        self.logger.info(f"  Opportunities Found: {status['session_stats']['opportunities_found']}")
        self.logger.info(f"  Opportunity Rate: {opportunity_rate:.1f}%")
        
        if top_opportunities:
            self.logger.info("🏆 TOP OPPORTUNITIES:")
            for i, opp in enumerate(top_opportunities, 1):
                self.logger.info(f"  {i}. {opp['lot_data'].get('lot_number')} - "
                               f"Score: {opp['opportunity_score']:.1f} - "
                               f"ROI: {opp['strategy'].get('expected_roi', 0):.1f}%")
        
        return report

def main():
    """Main function for testing the complete system"""
    
    print("🧠 ADVANCED AUCTION INTELLIGENCE SYSTEM")
    print("="*60)
    
    # Initialize system
    intelligence = AdvancedAuctionIntelligence()
    
    try:
        # Start the system
        intelligence.start_intelligence_system()
        
        # Scan for opportunities
        print("\n🔍 Scanning for investment opportunities...")
        opportunities = asyncio.run(intelligence.scan_for_opportunities([48796]))
        
        print(f"\n📊 SCAN RESULTS:")
        print(f"Opportunities Found: {len(opportunities)}")
        
        for opp in opportunities:
            lot_data = opp['lot_data']
            print(f"\n🎯 OPPORTUNITY: {lot_data.get('lot_number')}")
            print(f"  Product: {lot_data.get('product_name')}")
            print(f"  Score: {opp['opportunity_score']:.1f}/100")
            print(f"  ROI: {opp['strategy'].get('expected_roi', 0):.1f}%")
            print(f"  Recommendation: {opp['recommendation']}")
            print(f"  Priority: {opp['priority_level']}")
        
        # Show system status
        status = intelligence.get_system_status()
        print(f"\n📈 SYSTEM STATUS:")
        print(f"  Session Duration: {status['session_duration_minutes']:.1f} minutes")
        print(f"  Lots Analyzed: {status['session_stats']['lots_analyzed']}")
        print(f"  Opportunities Found: {status['session_stats']['opportunities_found']}")
        
        # Wait for user input
        input("\nPress Enter to stop the system...")
        
    except KeyboardInterrupt:
        print("\n🛑 System interrupted by user")
    
    finally:
        # Stop the system
        intelligence.stop_intelligence_system()
        print("✅ System shutdown complete")

if __name__ == "__main__":
    main() 