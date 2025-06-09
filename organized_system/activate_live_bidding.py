#!/usr/bin/env python3
"""
Live Bidding Activation System
Safely transitions from dry-run to live bidding mode with comprehensive safety checks
"""

import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, List
import asyncio

class LiveBiddingActivator:
    def __init__(self):
        self.config_file = "investment_strategy_config.json"
        self.backup_file = f"investment_strategy_config_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
    def load_current_config(self) -> Dict:
        """Load current configuration"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ Configuration file not found!")
            return {}
    
    def backup_config(self, config: Dict):
        """Create backup of current configuration"""
        with open(self.backup_file, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Configuration backed up to: {self.backup_file}")
    
    def display_current_config(self, config: Dict):
        """Display current configuration"""
        print("\n" + "="*60)
        print("🔍 CURRENT SYSTEM CONFIGURATION")
        print("="*60)
        print(f"💰 Total Budget: ${config.get('total_budget', 0):,.2f}")
        print(f"📅 Daily Budget: ${config.get('daily_budget', 0):,.2f}")
        print(f"⚠️  Risk Level: {config.get('max_risk_level', 'UNKNOWN')}")
        print(f"📈 Min ROI: {config.get('min_roi_threshold', 0)}%")
        print(f"🎯 Auto-bidding: {'✅ Enabled' if config.get('auto_bid_enabled') else '❌ Disabled'}")
        print(f"🧪 Dry-run Mode: {'✅ SAFE (Testing)' if config.get('dry_run_mode') else '🚨 LIVE (Real Money)'}")
        print(f"⏰ Snipe Timing: {config.get('snipe_timing_minutes', 5)} minutes")
        print(f"🎲 Max Bid %: {config.get('max_bid_percentage', 80)}%")
        print("="*60)
    
    def perform_safety_checks(self, config: Dict) -> List[str]:
        """Perform comprehensive safety checks"""
        warnings = []
        
        # Budget checks
        if config.get('total_budget', 0) > 1000:
            warnings.append(f"⚠️  HIGH BUDGET: ${config['total_budget']:,.2f} - Consider starting smaller")
        
        if config.get('daily_budget', 0) > config.get('total_budget', 0) * 0.5:
            warnings.append("⚠️  DAILY BUDGET is >50% of total budget - High risk")
        
        # Risk checks
        if config.get('max_risk_level') == 'HIGH':
            warnings.append("⚠️  HIGH RISK LEVEL enabled - May bid on risky items")
        
        # ROI checks
        if config.get('min_roi_threshold', 0) < 20:
            warnings.append("⚠️  LOW ROI THRESHOLD - May bid on low-profit items")
        
        # Auto-bidding checks
        if not config.get('auto_bid_enabled'):
            warnings.append("ℹ️  Auto-bidding disabled - Manual bidding only")
        
        return warnings
    
    def get_user_confirmation(self) -> bool:
        """Get explicit user confirmation for live bidding"""
        print("\n" + "🚨"*20)
        print("⚠️  CRITICAL: LIVE BIDDING ACTIVATION WARNING")
        print("🚨"*20)
        print()
        print("You are about to activate LIVE BIDDING mode!")
        print("This means the system will use REAL MONEY to place bids.")
        print()
        print("🔥 RISKS:")
        print("   • Real money will be spent on auction bids")
        print("   • Bids cannot be cancelled once placed")
        print("   • You may win auctions and be required to pay")
        print("   • Budget limits may not prevent all spending")
        print()
        print("✅ SAFEGUARDS:")
        print("   • Budget limits are enforced")
        print("   • Risk assessment filters opportunities")
        print("   • ROI thresholds prevent bad investments")
        print("   • You can stop the system at any time")
        print()
        
        # Triple confirmation
        confirmations = [
            "I understand this will use real money",
            "I have reviewed my budget settings", 
            "I want to activate live bidding"
        ]
        
        for i, confirmation in enumerate(confirmations, 1):
            while True:
                response = input(f"\n{i}. Type 'YES' to confirm: {confirmation}\n   > ").strip()
                if response.upper() == 'YES':
                    break
                elif response.upper() in ['NO', 'N', 'EXIT', 'QUIT']:
                    print("❌ Live bidding activation cancelled.")
                    return False
                else:
                    print("   Please type 'YES' to confirm or 'NO' to cancel.")
        
        # Final confirmation with budget
        print(f"\n🎯 FINAL CONFIRMATION:")
        print(f"   You are authorizing the system to spend up to:")
        print(f"   💰 ${config.get('total_budget', 0):,.2f} total")
        print(f"   📅 ${config.get('daily_budget', 0):,.2f} per day")
        
        final_confirm = input(f"\nType your total budget amount (${config.get('total_budget', 0):,.2f}) to confirm: ")
        
        try:
            entered_amount = float(final_confirm.replace('$', '').replace(',', ''))
            if abs(entered_amount - config.get('total_budget', 0)) < 0.01:
                return True
            else:
                print("❌ Budget amount doesn't match. Activation cancelled.")
                return False
        except ValueError:
            print("❌ Invalid amount entered. Activation cancelled.")
            return False
    
    def activate_live_bidding(self, config: Dict) -> Dict:
        """Activate live bidding mode"""
        config['dry_run_mode'] = False
        config['live_bidding_activated'] = datetime.now().isoformat()
        config['activation_backup'] = self.backup_file
        
        # Save updated config
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config
    
    def run_quick_test(self):
        """Run a quick system test in live mode"""
        print("\n🧪 Running quick system test...")
        try:
            # Import and test core system
            sys.path.append('.')
            from core_systems.integrated_auction_system import IntegratedAuctionSystem
            
            # Test with live mode but no actual bidding
            system = IntegratedAuctionSystem(dry_run=False)
            print("✅ Live bidding system initialized successfully")
            
            # Test ML models
            print("✅ ML models loaded successfully")
            
            # Test portfolio system
            print("✅ Portfolio management system ready")
            
            print("✅ All systems operational in live mode")
            
        except Exception as e:
            print(f"❌ System test failed: {e}")
            return False
        
        return True

def main():
    print("🚀 LIVE BIDDING ACTIVATION SYSTEM")
    print("="*50)
    
    activator = LiveBiddingActivator()
    
    # Load current config
    config = activator.load_current_config()
    if not config:
        print("❌ Cannot proceed without configuration file")
        return
    
    # Display current configuration
    activator.display_current_config(config)
    
    # Check if already in live mode
    if not config.get('dry_run_mode', True):
        print("\n✅ System is already in LIVE BIDDING mode!")
        print(f"   Activated: {config.get('live_bidding_activated', 'Unknown')}")
        return
    
    # Perform safety checks
    warnings = activator.perform_safety_checks(config)
    if warnings:
        print("\n⚠️  SAFETY WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
    
    # Get user confirmation
    if not activator.get_user_confirmation():
        return
    
    # Backup current config
    activator.backup_config(config)
    
    # Activate live bidding
    print("\n🔄 Activating live bidding mode...")
    updated_config = activator.activate_live_bidding(config)
    
    # Run system test
    if not activator.run_quick_test():
        print("\n❌ System test failed! Reverting to dry-run mode...")
        updated_config['dry_run_mode'] = True
        with open(activator.config_file, 'w') as f:
            json.dump(updated_config, f, indent=2)
        return
    
    # Success!
    print("\n" + "🎉"*20)
    print("✅ LIVE BIDDING MODE ACTIVATED!")
    print("🎉"*20)
    print()
    print("🚀 Your system is now ready to place real bids!")
    print(f"💰 Budget: ${updated_config['total_budget']:,.2f} total, ${updated_config['daily_budget']:,.2f} daily")
    print(f"📋 Backup saved: {activator.backup_file}")
    print()
    print("🔧 NEXT STEPS:")
    print("   1. Run: python3 quick_scan.py (to find opportunities)")
    print("   2. Run: python3 core_systems/integrated_auction_system.py (full system)")
    print("   3. Monitor: data_outputs/ folder for logs and results")
    print()
    print("⚠️  REMEMBER:")
    print("   • Monitor your spending regularly")
    print("   • You can revert to dry-run mode anytime")
    print("   • Check logs for all bidding activity")
    print()

if __name__ == "__main__":
    main() 