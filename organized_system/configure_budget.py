#!/usr/bin/env python3
"""
🎯 BUDGET CONFIGURATION TOOL
Advanced Auction Intelligence System - Investment Strategy Setup

This tool helps you configure budget parameters and investment strategy
for optimal auction bidding performance.
"""

import json
import os
from typing import Dict, List
from dataclasses import dataclass, asdict

@dataclass
class InvestmentStrategy:
    # Budget Settings
    total_budget: float = 10000.0
    daily_budget: float = 2000.0
    max_lots_per_auction: int = 5
    max_concurrent_bids: int = 10
    
    # Risk & ROI Settings
    min_roi_threshold: float = 25.0  # Minimum 25% ROI
    max_risk_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    
    # Category Preferences
    preferred_categories: List[str] = None
    preferred_brands: List[str] = None
    
    # Bidding Strategy
    auto_bid_enabled: bool = True
    snipe_timing_minutes: int = 5
    dry_run_mode: bool = True  # Safety first!
    
    # Advanced Settings
    max_bid_percentage: float = 80.0  # Max % of predicted final price
    confidence_threshold: float = 40.0  # Minimum ML confidence
    
    def __post_init__(self):
        if self.preferred_categories is None:
            self.preferred_categories = ["Electronics", "Computers", "Home & Garden", "Collectibles"]
        if self.preferred_brands is None:
            self.preferred_brands = ["Apple", "Samsung", "Sony", "LG", "Dell", "HP", "Canon", "Nikon"]

class BudgetConfigurator:
    def __init__(self):
        self.strategy = InvestmentStrategy()
        self.config_file = "investment_strategy_config.json"
    
    def display_current_config(self):
        """Display current configuration"""
        print("🎯 CURRENT INVESTMENT STRATEGY CONFIGURATION")
        print("=" * 60)
        
        print(f"\n💰 BUDGET SETTINGS:")
        print(f"   Total Budget: ${self.strategy.total_budget:,.2f}")
        print(f"   Daily Budget: ${self.strategy.daily_budget:,.2f}")
        print(f"   Max Lots per Auction: {self.strategy.max_lots_per_auction}")
        print(f"   Max Concurrent Bids: {self.strategy.max_concurrent_bids}")
        
        print(f"\n📊 RISK & ROI SETTINGS:")
        print(f"   Minimum ROI Threshold: {self.strategy.min_roi_threshold}%")
        print(f"   Maximum Risk Level: {self.strategy.max_risk_level}")
        print(f"   Max Bid Percentage: {self.strategy.max_bid_percentage}%")
        print(f"   Confidence Threshold: {self.strategy.confidence_threshold}%")
        
        print(f"\n🎯 BIDDING STRATEGY:")
        print(f"   Auto-Bidding: {'✅ Enabled' if self.strategy.auto_bid_enabled else '❌ Disabled'}")
        print(f"   Snipe Timing: {self.strategy.snipe_timing_minutes} minutes before end")
        print(f"   Dry Run Mode: {'✅ Safe Mode' if self.strategy.dry_run_mode else '⚠️ LIVE BIDDING'}")
        
        print(f"\n📂 CATEGORY PREFERENCES:")
        for category in self.strategy.preferred_categories:
            print(f"   ✅ {category}")
        
        print(f"\n🏷️ BRAND PREFERENCES:")
        brands_per_line = 4
        for i in range(0, len(self.strategy.preferred_brands), brands_per_line):
            brands = self.strategy.preferred_brands[i:i+brands_per_line]
            print(f"   {' | '.join(brands)}")
    
    def get_budget_recommendations(self):
        """Provide budget recommendations based on risk tolerance"""
        print("\n💡 BUDGET RECOMMENDATIONS BY RISK PROFILE:")
        print("=" * 60)
        
        recommendations = {
            "Conservative": {
                "total_budget": 5000.0,
                "daily_budget": 500.0,
                "min_roi": 50.0,
                "max_risk": "LOW",
                "description": "Safe, steady returns with minimal risk"
            },
            "Moderate": {
                "total_budget": 10000.0,
                "daily_budget": 1500.0,
                "min_roi": 25.0,
                "max_risk": "MEDIUM",
                "description": "Balanced approach with good growth potential"
            },
            "Aggressive": {
                "total_budget": 20000.0,
                "daily_budget": 3000.0,
                "min_roi": 15.0,
                "max_risk": "HIGH",
                "description": "High growth potential with higher risk"
            }
        }
        
        for profile, config in recommendations.items():
            print(f"\n🎯 {profile.upper()} STRATEGY:")
            print(f"   Total Budget: ${config['total_budget']:,.2f}")
            print(f"   Daily Budget: ${config['daily_budget']:,.2f}")
            print(f"   Min ROI: {config['min_roi']}%")
            print(f"   Max Risk: {config['max_risk']}")
            print(f"   📝 {config['description']}")
    
    def interactive_configuration(self):
        """Interactive configuration setup"""
        print("\n🔧 INTERACTIVE BUDGET CONFIGURATION")
        print("=" * 60)
        print("Let's set up your investment strategy step by step...")
        
        try:
            # Budget Settings
            print(f"\n💰 BUDGET SETTINGS:")
            total = input(f"Total Budget [${self.strategy.total_budget:,.2f}]: ").strip()
            if total:
                self.strategy.total_budget = float(total)
            
            daily = input(f"Daily Budget [${self.strategy.daily_budget:,.2f}]: ").strip()
            if daily:
                self.strategy.daily_budget = float(daily)
            
            # Risk Settings
            print(f"\n📊 RISK & ROI SETTINGS:")
            roi = input(f"Minimum ROI Threshold [{self.strategy.min_roi_threshold}%]: ").strip()
            if roi:
                self.strategy.min_roi_threshold = float(roi)
            
            print(f"Risk Levels: LOW (safest), MEDIUM (balanced), HIGH (aggressive)")
            risk = input(f"Maximum Risk Level [{self.strategy.max_risk_level}]: ").strip().upper()
            if risk in ["LOW", "MEDIUM", "HIGH"]:
                self.strategy.max_risk_level = risk
            
            # Bidding Strategy
            print(f"\n🎯 BIDDING STRATEGY:")
            auto_bid = input(f"Enable Auto-Bidding? [{'Y' if self.strategy.auto_bid_enabled else 'N'}]: ").strip().upper()
            if auto_bid in ["Y", "YES"]:
                self.strategy.auto_bid_enabled = True
            elif auto_bid in ["N", "NO"]:
                self.strategy.auto_bid_enabled = False
            
            dry_run = input(f"Start in Dry-Run Mode (recommended)? [{'Y' if self.strategy.dry_run_mode else 'N'}]: ").strip().upper()
            if dry_run in ["Y", "YES"]:
                self.strategy.dry_run_mode = True
            elif dry_run in ["N", "NO"]:
                self.strategy.dry_run_mode = False
                print("⚠️  WARNING: Live bidding mode enabled!")
            
            print("\n✅ Configuration updated successfully!")
            
        except ValueError as e:
            print(f"❌ Invalid input: {e}")
            print("Please enter valid numbers for budget amounts.")
    
    def apply_preset_strategy(self, strategy_name: str):
        """Apply a preset investment strategy"""
        presets = {
            "conservative": {
                "total_budget": 5000.0,
                "daily_budget": 500.0,
                "min_roi_threshold": 50.0,
                "max_risk_level": "LOW",
                "max_concurrent_bids": 5,
                "preferred_categories": ["Electronics", "Computers"]
            },
            "moderate": {
                "total_budget": 10000.0,
                "daily_budget": 1500.0,
                "min_roi_threshold": 25.0,
                "max_risk_level": "MEDIUM",
                "max_concurrent_bids": 10,
                "preferred_categories": ["Electronics", "Computers", "Home & Garden"]
            },
            "aggressive": {
                "total_budget": 20000.0,
                "daily_budget": 3000.0,
                "min_roi_threshold": 15.0,
                "max_risk_level": "HIGH",
                "max_concurrent_bids": 15,
                "preferred_categories": ["Electronics", "Computers", "Home & Garden", "Collectibles", "Jewelry"]
            }
        }
        
        if strategy_name.lower() in presets:
            preset = presets[strategy_name.lower()]
            for key, value in preset.items():
                setattr(self.strategy, key, value)
            print(f"✅ Applied {strategy_name.upper()} strategy preset")
        else:
            print(f"❌ Unknown strategy: {strategy_name}")
    
    def save_configuration(self):
        """Save configuration to file"""
        config_data = asdict(self.strategy)
        
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        print(f"✅ Configuration saved to {self.config_file}")
    
    def load_configuration(self):
        """Load configuration from file"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
            
            # Update strategy with loaded data
            for key, value in config_data.items():
                if hasattr(self.strategy, key):
                    setattr(self.strategy, key, value)
            
            print(f"✅ Configuration loaded from {self.config_file}")
        else:
            print(f"⚠️  No saved configuration found. Using defaults.")
    
    def update_system_files(self):
        """Update the actual system files with new configuration"""
        print("\n🔄 UPDATING SYSTEM CONFIGURATION FILES...")
        
        # Files to update
        files_to_update = [
            "core_systems/integrated_auction_system.py",
            "core_systems/portfolio_management_system.py",
            "core_systems/automated_bidding_system.py"
        ]
        
        updates_made = 0
        
        for file_path in files_to_update:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Update configuration values
                    replacements = [
                        (f"total_budget=10000.0", f"total_budget={self.strategy.total_budget}"),
                        (f"daily_budget=2000.0", f"daily_budget={self.strategy.daily_budget}"),
                        (f"min_roi_threshold=25.0", f"min_roi_threshold={self.strategy.min_roi_threshold}"),
                        (f"max_risk_level=\"MEDIUM\"", f"max_risk_level=\"{self.strategy.max_risk_level}\""),
                        (f"self.max_daily_budget = 5000.00", f"self.max_daily_budget = {self.strategy.daily_budget}"),
                        (f"dry_run=True", f"dry_run={self.strategy.dry_run_mode}")
                    ]
                    
                    for old, new in replacements:
                        if old in content:
                            content = content.replace(old, new)
                            updates_made += 1
                    
                    with open(file_path, 'w') as f:
                        f.write(content)
                    
                    print(f"   ✅ Updated {file_path}")
                    
                except Exception as e:
                    print(f"   ❌ Error updating {file_path}: {e}")
            else:
                print(f"   ⚠️  File not found: {file_path}")
        
        print(f"\n✅ Configuration update complete! {updates_made} values updated.")
        print("🔄 Restart the system to apply changes.")
    
    def generate_strategy_summary(self):
        """Generate a summary of the investment strategy"""
        print("\n📋 INVESTMENT STRATEGY SUMMARY")
        print("=" * 60)
        
        # Calculate key metrics
        daily_percentage = (self.strategy.daily_budget / self.strategy.total_budget) * 100
        days_to_exhaust = self.strategy.total_budget / self.strategy.daily_budget
        
        print(f"💰 FINANCIAL PARAMETERS:")
        print(f"   Total Investment Capital: ${self.strategy.total_budget:,.2f}")
        print(f"   Daily Spending Limit: ${self.strategy.daily_budget:,.2f} ({daily_percentage:.1f}% of total)")
        print(f"   Days to Exhaust Budget: {days_to_exhaust:.1f} days (at max daily spend)")
        
        print(f"\n🎯 STRATEGY PROFILE:")
        risk_profile = {
            "LOW": "Conservative - Focus on safe, predictable returns",
            "MEDIUM": "Moderate - Balanced risk/reward approach", 
            "HIGH": "Aggressive - High growth potential with higher risk"
        }
        print(f"   Risk Tolerance: {self.strategy.max_risk_level} ({risk_profile.get(self.strategy.max_risk_level, 'Unknown')})")
        print(f"   Minimum ROI Target: {self.strategy.min_roi_threshold}%")
        print(f"   Operating Mode: {'🛡️ Dry Run (Safe)' if self.strategy.dry_run_mode else '⚡ Live Bidding'}")
        
        print(f"\n📊 EXPECTED PERFORMANCE:")
        if self.strategy.min_roi_threshold > 0:
            min_daily_profit = self.strategy.daily_budget * (self.strategy.min_roi_threshold / 100)
            min_monthly_profit = min_daily_profit * 30
            print(f"   Minimum Daily Profit Target: ${min_daily_profit:,.2f}")
            print(f"   Minimum Monthly Profit Target: ${min_monthly_profit:,.2f}")
        
        print(f"\n🎲 RISK ASSESSMENT:")
        if self.strategy.max_risk_level == "LOW":
            print("   ✅ Conservative approach - Lower returns but safer investments")
        elif self.strategy.max_risk_level == "MEDIUM":
            print("   ⚖️ Balanced approach - Moderate risk for good returns")
        else:
            print("   ⚠️ Aggressive approach - Higher risk but potential for large returns")

def main():
    """Main configuration interface"""
    print("🎯 ADVANCED AUCTION INTELLIGENCE SYSTEM")
    print("💰 BUDGET & INVESTMENT STRATEGY CONFIGURATOR")
    print("=" * 60)
    
    configurator = BudgetConfigurator()
    configurator.load_configuration()
    
    while True:
        print(f"\n📋 CONFIGURATION MENU:")
        print("1. 📊 View Current Configuration")
        print("2. 💡 View Budget Recommendations")
        print("3. 🔧 Interactive Configuration")
        print("4. 🎯 Apply Preset Strategy")
        print("5. 💾 Save Configuration")
        print("6. 🔄 Update System Files")
        print("7. 📋 Generate Strategy Summary")
        print("8. 🚀 Test Configuration")
        print("9. ❌ Exit")
        
        choice = input("\nSelect option [1-9]: ").strip()
        
        if choice == "1":
            configurator.display_current_config()
        elif choice == "2":
            configurator.get_budget_recommendations()
        elif choice == "3":
            configurator.interactive_configuration()
        elif choice == "4":
            print("\nAvailable presets: conservative, moderate, aggressive")
            preset = input("Enter preset name: ").strip()
            configurator.apply_preset_strategy(preset)
        elif choice == "5":
            configurator.save_configuration()
        elif choice == "6":
            configurator.update_system_files()
        elif choice == "7":
            configurator.generate_strategy_summary()
        elif choice == "8":
            print("\n🚀 Testing configuration with integrated system...")
            os.system("python3 core_systems/integrated_auction_system.py")
        elif choice == "9":
            print("👋 Configuration complete! Happy bidding!")
            break
        else:
            print("❌ Invalid option. Please select 1-9.")

if __name__ == "__main__":
    main() 