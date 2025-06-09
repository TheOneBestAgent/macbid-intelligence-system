#!/usr/bin/env python3
"""
🚀 Ultimate Auction Intelligence System
Combines comprehensive warehouse scanning, NextJS real-time data, ML predictions, and live bidding
"""

import asyncio
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import aiohttp
import ssl
import requests
import time
import os
import sys

# Import our subsystems
sys.path.append('.')
from discovery_systems.typesense_all_lots_scanner import TypesenseAllLotsScanner
from core_systems.nextjs_integration_system import NextJSIntegrationSystem
from ml_prediction.enhanced_ml_models import EnhancedMLModels
from core_systems.real_bidding_system import RealBiddingSystem, BidRequest
from core_systems.portfolio_management_system import PortfolioManagementSystem, PortfolioConfig

@dataclass
class UltimateOpportunity:
    # Basic lot info
    lot_id: int
    auction_id: int
    product_name: str
    current_price: float
    instant_win_price: float
    retail_price: float
    
    # Location and condition
    warehouse_location: str
    condition: str
    category: str
    brand: str
    
    # Real-time bidding data
    total_bids: int
    unique_bidders: int
    time_remaining: str
    is_open: bool
    
    # ML predictions
    predicted_final_price: float = 0.0
    ml_confidence: float = 0.0
    optimal_bid: float = 0.0
    win_probability: float = 0.0
    
    # Intelligence scores
    opportunity_score: float = 0.0
    predicted_roi: float = 0.0
    risk_level: str = "MEDIUM"
    investment_recommendation: str = "CONSIDER"
    
    # System tracking
    discovery_method: str = ""
    analysis_timestamp: str = ""
    monitoring_priority: int = 1
    
    def __post_init__(self):
        if not self.analysis_timestamp:
            self.analysis_timestamp = datetime.now().isoformat()

class UltimateAuctionIntelligenceSystem:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data_outputs/ultimate_auction_intelligence.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize subsystems
        self.logger.info("🚀 Initializing Ultimate Auction Intelligence System...")
        
        # Typesense scanner for comprehensive discovery (finds 1000s of lots)
        self.typesense_scanner = TypesenseAllLotsScanner()
        
        # NextJS integration for real-time data
        self.nextjs_system = NextJSIntegrationSystem()
        
        # ML models for predictions
        self.ml_system = EnhancedMLModels()
        
        # Portfolio management
        portfolio_config = PortfolioConfig(
            total_budget=300.0,
            daily_budget=30.0,
            min_roi_threshold=25.0,
            max_risk_level="MEDIUM",
            preferred_categories=["Electronics", "Computers", "Home & Garden"],
            auto_bid_enabled=True
        )
        self.portfolio_system = PortfolioManagementSystem(portfolio_config)
        
        # Real bidding system
        self.bidding_system = RealBiddingSystem(dry_run=dry_run)
        
        # System state
        self.all_discovered_lots: List[Dict] = []
        self.top_opportunities: List[UltimateOpportunity] = []
        self.monitored_lots: Dict[int, UltimateOpportunity] = {}
        
        # Performance tracking
        self.session_stats = {
            'session_start': datetime.now().isoformat(),
            'total_lots_discovered': 0,
            'sc_lots_found': 0,
            'opportunities_analyzed': 0,
            'top_opportunities_selected': 0,
            'bids_executed': 0,
            'total_investment': 0.0,
            'predicted_returns': 0.0
        }
        
        self.setup_database()
        self.logger.info("✅ Ultimate Auction Intelligence System initialized")
    
    def setup_database(self):
        """Setup comprehensive database for ultimate system"""
        self.db_path = "databases/ultimate_auction_intelligence.db"
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ultimate opportunities table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ultimate_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER UNIQUE,
                auction_id INTEGER,
                product_name TEXT,
                current_price REAL,
                instant_win_price REAL,
                retail_price REAL,
                warehouse_location TEXT,
                condition_name TEXT,
                category TEXT,
                brand TEXT,
                total_bids INTEGER,
                unique_bidders INTEGER,
                time_remaining TEXT,
                is_open INTEGER,
                predicted_final_price REAL,
                ml_confidence REAL,
                optimal_bid REAL,
                win_probability REAL,
                opportunity_score REAL,
                predicted_roi REAL,
                risk_level TEXT,
                investment_recommendation TEXT,
                discovery_method TEXT,
                monitoring_priority INTEGER,
                analysis_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Monitoring queue for real-time tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitoring_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER,
                auction_id INTEGER,
                product_name TEXT,
                priority INTEGER,
                status TEXT DEFAULT 'ACTIVE',
                last_check DATETIME,
                bid_count_last INTEGER,
                price_last REAL,
                alerts_sent INTEGER DEFAULT 0,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Bidding execution log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bidding_execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id INTEGER,
                auction_id INTEGER,
                bid_amount REAL,
                bid_type TEXT,
                execution_status TEXT,
                response_data TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info("✅ Ultimate database initialized")
    
    async def comprehensive_warehouse_discovery(self) -> List[Dict]:
        """Phase 1: Comprehensive discovery across all 5 SC warehouses using Typesense"""
        self.logger.info("🔍 PHASE 1: Comprehensive Typesense Discovery")
        self.logger.info("=" * 60)
        
        # Use Typesense scanner to find ALL lots (thousands)
        await self.typesense_scanner.run_typesense_discovery()
        
        # Get discovered lots from the scanner
        all_lots = list(self.typesense_scanner.discovered_lots.values())
        
        self.session_stats['total_lots_discovered'] = len(all_lots)
        self.session_stats['sc_lots_found'] = len(all_lots)  # All are already SC lots
        self.all_discovered_lots = all_lots
        
        self.logger.info(f"✅ Typesense discovery complete: {len(all_lots)} lots in SC warehouses")
        return all_lots
    
    async def enhance_with_nextjs_data(self, lots: List[Dict]) -> List[Dict]:
        """Phase 2: Enhance with real-time NextJS data"""
        self.logger.info("🔄 PHASE 2: Enhancing with Real-time NextJS Data")
        self.logger.info("=" * 60)
        
        enhanced_lots = []
        
        for i, lot in enumerate(lots[:100], 1):  # Limit to top 100 for performance
            try:
                auction_id = lot.get('auction_id')
                lot_id = lot.get('lot_id') or lot.get('id')
                
                if auction_id and lot_id:
                    # Get real-time data from NextJS
                    nextjs_data = self.nextjs_system.fetch_nextjs_lot_data(auction_id, lot_id)
                    
                    if nextjs_data:
                        # Merge data
                        enhanced_lot = {**lot, **nextjs_data}
                        enhanced_lots.append(enhanced_lot)
                        
                        if i % 10 == 0:
                            self.logger.info(f"   Enhanced {i}/100 lots with real-time data")
                    
                    # Rate limiting
                    await asyncio.sleep(0.1)
                
            except Exception as e:
                self.logger.warning(f"   ❌ Error enhancing lot {lot_id}: {e}")
                continue
        
        self.logger.info(f"✅ Enhanced {len(enhanced_lots)} lots with real-time data")
        return enhanced_lots
    
    async def ml_opportunity_analysis(self, lots: List[Dict]) -> List[UltimateOpportunity]:
        """Phase 3: ML-powered opportunity analysis"""
        self.logger.info("🤖 PHASE 3: ML-Powered Opportunity Analysis")
        self.logger.info("=" * 60)
        
        opportunities = []
        
        for lot in lots:
            try:
                # Create opportunity object (handle both Typesense and NextJS field names)
                opportunity = UltimateOpportunity(
                    lot_id=int(lot.get('lot_id') or lot.get('id', 0)),
                    auction_id=int(lot.get('auction_id', 0)),
                    product_name=lot.get('product_name') or lot.get('title', ''),
                    current_price=float(lot.get('current_bid', 0)),
                    instant_win_price=float(lot.get('instant_win_price') or lot.get('retail_price', 0)),
                    retail_price=float(lot.get('retail_price', 0)),
                    warehouse_location=lot.get('auction_location', ''),
                    condition=lot.get('condition_name') or lot.get('condition', 'Unknown'),
                    category=lot.get('category', 'General'),
                    brand=self.extract_brand(lot.get('product_name') or lot.get('title', '')),
                    total_bids=int(lot.get('total_bids', 0)),
                    unique_bidders=int(lot.get('unique_bidders', 0)),
                    time_remaining=lot.get('time_remaining', ''),
                    is_open=bool(lot.get('is_open', True)),
                    discovery_method="typesense_comprehensive_scan"
                )
                
                # ML prediction
                ml_prediction = self.ml_system.predict_auction_price(lot)
                opportunity.predicted_final_price = ml_prediction.predicted_final_price
                opportunity.ml_confidence = ml_prediction.confidence_score
                opportunity.optimal_bid = ml_prediction.optimal_bid
                opportunity.win_probability = ml_prediction.win_probability
                
                # Calculate scores
                opportunity.predicted_roi = self.calculate_roi(opportunity)
                opportunity.risk_level = self.calculate_risk_level(opportunity)
                opportunity.opportunity_score = self.calculate_opportunity_score(opportunity)
                opportunity.investment_recommendation = self.generate_recommendation(opportunity)
                
                opportunities.append(opportunity)
                
            except Exception as e:
                self.logger.warning(f"   ❌ Error analyzing lot {lot.get('lot_id')}: {e}")
                continue
        
        self.session_stats['opportunities_analyzed'] = len(opportunities)
        self.logger.info(f"✅ Analyzed {len(opportunities)} opportunities with ML")
        return opportunities
    
    def select_top_opportunities(self, opportunities: List[UltimateOpportunity], top_n: int = 5) -> List[UltimateOpportunity]:
        """Phase 4: Select top N opportunities for monitoring"""
        self.logger.info(f"🎯 PHASE 4: Selecting Top {top_n} Opportunities")
        self.logger.info("=" * 60)
        
        # Filter by investment criteria
        qualified_opportunities = []
        for opp in opportunities:
            if (opp.predicted_roi >= 25.0 and 
                opp.risk_level in ['LOW', 'MEDIUM'] and 
                opp.opportunity_score >= 50.0 and
                opp.is_open):
                qualified_opportunities.append(opp)
        
        # Sort by opportunity score
        qualified_opportunities.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        # Select top N
        top_opportunities = qualified_opportunities[:top_n]
        
        self.logger.info(f"✅ Selected {len(top_opportunities)} top opportunities:")
        for i, opp in enumerate(top_opportunities, 1):
            self.logger.info(f"   {i}. {opp.product_name[:50]} (Score: {opp.opportunity_score:.1f}, ROI: {opp.predicted_roi:.1f}%)")
        
        self.session_stats['top_opportunities_selected'] = len(top_opportunities)
        self.top_opportunities = top_opportunities
        return top_opportunities
    
    async def setup_real_time_monitoring(self, opportunities: List[UltimateOpportunity]):
        """Phase 5: Setup real-time monitoring for top opportunities"""
        self.logger.info("📡 PHASE 5: Setting up Real-time Monitoring")
        self.logger.info("=" * 60)
        
        # Add to monitoring queue
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for opp in opportunities:
            # Set monitoring priority based on opportunity score
            priority = 1 if opp.opportunity_score >= 80 else 2 if opp.opportunity_score >= 60 else 3
            opp.monitoring_priority = priority
            
            cursor.execute('''
                INSERT OR REPLACE INTO monitoring_queue 
                (lot_id, auction_id, product_name, priority, last_check, bid_count_last, price_last)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (opp.lot_id, opp.auction_id, opp.product_name, priority, 
                  datetime.now(), opp.total_bids, opp.current_price))
            
            self.monitored_lots[opp.lot_id] = opp
        
        conn.commit()
        conn.close()
        
        self.logger.info(f"✅ Monitoring setup complete for {len(opportunities)} opportunities")
    
    async def execute_intelligent_bidding(self, opportunities: List[UltimateOpportunity]):
        """Phase 6: Execute intelligent bidding on top opportunities"""
        self.logger.info("💰 PHASE 6: Executing Intelligent Bidding")
        self.logger.info("=" * 60)
        
        bids_executed = 0
        total_investment = 0.0
        
        for opp in opportunities:
            try:
                # Check if we should bid
                if (opp.investment_recommendation in ['STRONG_BUY', 'BUY'] and
                    opp.opportunity_score >= 70.0 and
                    opp.predicted_roi >= 50.0):
                    
                    # Create bid request
                    bid_request = BidRequest(
                        auction_id=opp.auction_id,
                        lot_id=opp.lot_id,
                        bid_amount=opp.optimal_bid,
                        max_bid=min(opp.optimal_bid * 1.2, opp.instant_win_price * 0.8),
                        notes=f"AI bid for {opp.product_name[:50]}"
                    )
                    
                    # Execute bid
                    result = await self.bidding_system.place_bid(bid_request)
                    
                    if result.get('success'):
                        bids_executed += 1
                        total_investment += opp.optimal_bid
                        
                        self.logger.info(f"   ✅ Bid placed: {opp.product_name[:40]} - ${opp.optimal_bid}")
                        
                        # Log to database
                        self.log_bid_execution(opp, bid_request, result)
                    else:
                        self.logger.warning(f"   ❌ Bid failed: {opp.product_name[:40]} - {result.get('error')}")
                
                # Rate limiting
                await asyncio.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"   ❌ Bidding error for {opp.product_name}: {e}")
                continue
        
        self.session_stats['bids_executed'] = bids_executed
        self.session_stats['total_investment'] = total_investment
        
        self.logger.info(f"✅ Bidding complete: {bids_executed} bids, ${total_investment:.2f} invested")
    
    async def continuous_monitoring_loop(self, duration_minutes: int = 60):
        """Phase 7: Continuous monitoring and adaptive bidding"""
        self.logger.info(f"🔄 PHASE 7: Continuous Monitoring ({duration_minutes} minutes)")
        self.logger.info("=" * 60)
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        while datetime.now() < end_time:
            try:
                # Check each monitored lot
                for lot_id, opportunity in self.monitored_lots.items():
                    await self.check_lot_status(opportunity)
                
                # Sleep between monitoring cycles
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Monitoring stopped by user")
                break
            except Exception as e:
                self.logger.error(f"❌ Monitoring error: {e}")
                await asyncio.sleep(10)
        
        self.logger.info("✅ Continuous monitoring complete")
    
    async def check_lot_status(self, opportunity: UltimateOpportunity):
        """Check real-time status of a monitored lot"""
        try:
            # Get updated data from NextJS
            updated_data = self.nextjs_system.fetch_nextjs_lot_data(
                opportunity.auction_id, opportunity.lot_id
            )
            
            if updated_data:
                new_bid_count = updated_data.get('total_bids', opportunity.total_bids)
                new_price = updated_data.get('current_bid', opportunity.current_price)
                
                # Check for changes
                if new_bid_count > opportunity.total_bids:
                    self.logger.info(f"🔔 New bid on {opportunity.product_name[:40]}: ${new_price}")
                    
                    # Update opportunity
                    opportunity.total_bids = new_bid_count
                    opportunity.current_price = new_price
                    
                    # Check if we need to counter-bid
                    await self.consider_counter_bid(opportunity, updated_data)
        
        except Exception as e:
            self.logger.warning(f"❌ Status check error for lot {opportunity.lot_id}: {e}")
    
    async def consider_counter_bid(self, opportunity: UltimateOpportunity, updated_data: Dict):
        """Consider placing a counter-bid based on new activity"""
        try:
            # Re-run ML prediction with updated data
            ml_prediction = self.ml_system.predict_auction_price(updated_data)
            
            # Check if still profitable
            if ml_prediction.predicted_final_price > 0:
                new_roi = ((opportunity.instant_win_price - ml_prediction.predicted_final_price) / 
                          ml_prediction.predicted_final_price) * 100
            else:
                new_roi = 0.0
            
            if (new_roi >= 25.0 and 
                ml_prediction.predicted_final_price < opportunity.optimal_bid * 1.5):
                
                # Place counter-bid
                counter_bid = min(ml_prediction.optimal_bid, opportunity.optimal_bid * 1.3)
                
                bid_request = BidRequest(
                    auction_id=opportunity.auction_id,
                    lot_id=opportunity.lot_id,
                    bid_amount=counter_bid,
                    max_bid=opportunity.optimal_bid * 1.5,
                    notes=f"Counter-bid for {opportunity.product_name[:50]}"
                )
                
                result = await self.bidding_system.place_bid(bid_request)
                
                if result.get('success'):
                    self.logger.info(f"   ✅ Counter-bid placed: ${counter_bid}")
                    self.log_bid_execution(opportunity, bid_request, result)
        
        except Exception as e:
            self.logger.warning(f"❌ Counter-bid error: {e}")
    
    # Helper methods
    def extract_brand(self, product_name: str) -> str:
        """Extract brand from product name"""
        brands = ['Apple', 'Samsung', 'Sony', 'LG', 'Dell', 'HP', 'Nintendo', 'Xbox', 'PlayStation', 
                 'Dyson', 'Bose', 'Beats', 'JBL', 'Canon', 'Nikon', 'DeWalt', 'Milwaukee']
        
        for brand in brands:
            if brand.lower() in product_name.lower():
                return brand
        return "Unknown"
    
    def calculate_roi(self, opportunity: UltimateOpportunity) -> float:
        """Calculate predicted ROI"""
        if opportunity.predicted_final_price > 0 and opportunity.instant_win_price > 0:
            return ((opportunity.instant_win_price - opportunity.predicted_final_price) / 
                   opportunity.predicted_final_price) * 100
        elif opportunity.current_price > 0 and opportunity.instant_win_price > 0:
            # Fallback to current price if predicted price is 0
            return ((opportunity.instant_win_price - opportunity.current_price) / 
                   opportunity.current_price) * 100
        return 0.0
    
    def calculate_risk_level(self, opportunity: UltimateOpportunity) -> str:
        """Calculate risk level"""
        risk_score = 0
        
        # Competition risk
        if opportunity.unique_bidders > 10:
            risk_score += 2
        elif opportunity.unique_bidders > 5:
            risk_score += 1
        
        # Condition risk
        if opportunity.condition in ['Poor', 'Damaged']:
            risk_score += 3
        elif opportunity.condition in ['Fair', 'Used']:
            risk_score += 1
        
        # ML confidence risk
        if opportunity.ml_confidence < 50:
            risk_score += 2
        elif opportunity.ml_confidence < 70:
            risk_score += 1
        
        if risk_score >= 4:
            return "HIGH"
        elif risk_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def calculate_opportunity_score(self, opportunity: UltimateOpportunity) -> float:
        """Calculate comprehensive opportunity score"""
        score = 0.0
        
        # ROI component (40%)
        roi_score = min(opportunity.predicted_roi / 100.0, 1.0) * 40
        score += roi_score
        
        # ML confidence component (20%)
        confidence_score = (opportunity.ml_confidence / 100.0) * 20
        score += confidence_score
        
        # Win probability component (20%)
        win_score = (opportunity.win_probability / 100.0) * 20
        score += win_score
        
        # Risk adjustment (20%)
        risk_multiplier = {'LOW': 1.0, 'MEDIUM': 0.8, 'HIGH': 0.5}
        risk_score = 20 * risk_multiplier.get(opportunity.risk_level, 0.5)
        score += risk_score
        
        return min(score, 100.0)
    
    def generate_recommendation(self, opportunity: UltimateOpportunity) -> str:
        """Generate investment recommendation"""
        if opportunity.opportunity_score >= 80 and opportunity.predicted_roi >= 100:
            return "STRONG_BUY"
        elif opportunity.opportunity_score >= 60 and opportunity.predicted_roi >= 50:
            return "BUY"
        elif opportunity.opportunity_score >= 40 and opportunity.predicted_roi >= 25:
            return "CONSIDER"
        elif opportunity.opportunity_score >= 20:
            return "WATCH"
        else:
            return "AVOID"
    
    def log_bid_execution(self, opportunity: UltimateOpportunity, bid_request: BidRequest, result: Dict):
        """Log bid execution to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bidding_execution_log 
            (lot_id, auction_id, bid_amount, bid_type, execution_status, response_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (opportunity.lot_id, opportunity.auction_id, bid_request.bid_amount,
              'intelligent_bid', 'success' if result.get('success') else 'failed',
              json.dumps(result)))
        
        conn.commit()
        conn.close()
    
    def generate_comprehensive_report(self) -> Dict:
        """Generate comprehensive system report"""
        return {
            'session_stats': self.session_stats,
            'top_opportunities': [asdict(opp) for opp in self.top_opportunities],
            'monitoring_status': len(self.monitored_lots),
            'system_mode': 'DRY_RUN' if self.dry_run else 'LIVE_BIDDING',
            'timestamp': datetime.now().isoformat()
        }
    
    async def run_complete_system(self, monitoring_duration: int = 60):
        """Run the complete ultimate auction intelligence system"""
        self.logger.info("🚀 ULTIMATE AUCTION INTELLIGENCE SYSTEM - FULL EXECUTION")
        self.logger.info("=" * 80)
        
        try:
            # Phase 1: Comprehensive warehouse discovery
            discovered_lots = await self.comprehensive_warehouse_discovery()
            
            # Phase 2: Enhance with NextJS real-time data
            enhanced_lots = await self.enhance_with_nextjs_data(discovered_lots)
            
            # Phase 3: ML opportunity analysis
            opportunities = await self.ml_opportunity_analysis(enhanced_lots)
            
            # Phase 4: Select top opportunities
            top_opportunities = self.select_top_opportunities(opportunities, top_n=5)
            
            # Phase 5: Setup real-time monitoring
            await self.setup_real_time_monitoring(top_opportunities)
            
            # Phase 6: Execute intelligent bidding
            await self.execute_intelligent_bidding(top_opportunities)
            
            # Phase 7: Continuous monitoring
            await self.continuous_monitoring_loop(monitoring_duration)
            
            # Generate final report
            report = self.generate_comprehensive_report()
            
            # Save report
            report_file = f"data_outputs/ultimate_system_report_{int(time.time())}.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.logger.info(f"✅ ULTIMATE SYSTEM COMPLETE - Report: {report_file}")
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Ultimate system error: {e}")
            raise

async def main():
    """Main execution function"""
    # Load configuration
    try:
        with open('investment_strategy_config.json', 'r') as f:
            config = json.load(f)
        dry_run = config.get('dry_run_mode', True)
    except:
        dry_run = True
    
    print(f"🚀 Starting Ultimate Auction Intelligence System")
    print(f"💡 Mode: {'DRY RUN (Safe Testing)' if dry_run else 'LIVE BIDDING (Real Money)'}")
    
    # Initialize and run system
    system = UltimateAuctionIntelligenceSystem(dry_run=dry_run)
    
    try:
        report = await system.run_complete_system(monitoring_duration=30)
        
        print("\n🎯 ULTIMATE SYSTEM RESULTS:")
        print(f"   📦 Total lots discovered: {report['session_stats']['total_lots_discovered']}")
        print(f"   🎯 SC warehouse lots: {report['session_stats']['sc_lots_found']}")
        print(f"   🤖 Opportunities analyzed: {report['session_stats']['opportunities_analyzed']}")
        print(f"   🏆 Top opportunities: {report['session_stats']['top_opportunities_selected']}")
        print(f"   💰 Bids executed: {report['session_stats']['bids_executed']}")
        print(f"   💵 Total investment: ${report['session_stats']['total_investment']:.2f}")
        
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 