#!/usr/bin/env python3
"""
Quick Custom Budget Configuration
"""

from configure_budget import BudgetConfigurator

def quick_custom_config():
    configurator = BudgetConfigurator()
    
    print("🔧 CUSTOM BUDGET CONFIGURATION")
    print("=" * 60)
    print("Let's set up your personalized investment strategy...")
    print("(Press Enter to keep current value)")
    print()
    
    try:
        # Budget Settings
        print("💰 BUDGET SETTINGS:")
        total = input(f"Total Budget [${configurator.strategy.total_budget:,.2f}]: ").strip()
        if total:
            configurator.strategy.total_budget = float(total)
        
        daily = input(f"Daily Budget [${configurator.strategy.daily_budget:,.2f}]: ").strip()
        if daily:
            configurator.strategy.daily_budget = float(daily)
        
        # Risk Settings
        print(f"\n📊 RISK & ROI SETTINGS:")
        roi = input(f"Minimum ROI Threshold [{configurator.strategy.min_roi_threshold}%]: ").strip()
        if roi:
            configurator.strategy.min_roi_threshold = float(roi)
        
        print("Risk Levels: LOW (safest), MEDIUM (balanced), HIGH (aggressive)")
        risk = input(f"Maximum Risk Level [{configurator.strategy.max_risk_level}]: ").strip().upper()
        if risk in ["LOW", "MEDIUM", "HIGH"]:
            configurator.strategy.max_risk_level = risk
        
        # Bidding Strategy
        print(f"\n🎯 BIDDING STRATEGY:")
        auto_bid = input(f"Enable Auto-Bidding? [{'Y' if configurator.strategy.auto_bid_enabled else 'N'}]: ").strip().upper()
        if auto_bid in ["Y", "YES"]:
            configurator.strategy.auto_bid_enabled = True
        elif auto_bid in ["N", "NO"]:
            configurator.strategy.auto_bid_enabled = False
        
        dry_run = input(f"Start in Dry-Run Mode (recommended)? [{'Y' if configurator.strategy.dry_run_mode else 'N'}]: ").strip().upper()
        if dry_run in ["Y", "YES"]:
            configurator.strategy.dry_run_mode = True
        elif dry_run in ["N", "NO"]:
            configurator.strategy.dry_run_mode = False
            print("⚠️  WARNING: Live bidding mode enabled!")
        
        print("\n✅ Custom configuration complete!")
        print()
        
        # Display the new configuration
        configurator.display_current_config()
        print()
        configurator.generate_strategy_summary()
        
        # Save configuration
        configurator.save_configuration()
        print()
        
        # Ask about updating system files
        update = input("💾 Update system files with new configuration? (Y/N): ").strip().upper()
        if update in ["Y", "YES"]:
            configurator.update_system_files()
            print("\n🚀 Ready to test? Run the integrated system? (Y/N): ", end="")
            test = input().strip().upper()
            if test in ["Y", "YES"]:
                import os
                print("\n🚀 Testing configuration with integrated system...")
                os.system("python3 core_systems/integrated_auction_system.py")
        
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        print("Please enter valid numbers for budget amounts.")
    except KeyboardInterrupt:
        print("\n👋 Configuration canceled.")

if __name__ == "__main__":
    quick_custom_config() 