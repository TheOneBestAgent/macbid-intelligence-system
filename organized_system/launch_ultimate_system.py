1#!/usr/bin/env python3
"""
🚀 Ultimate Auction Intelligence System Launcher
Quick launcher for the comprehensive auction intelligence system
"""

import asyncio
import json
import sys
import os
from datetime import datetime

def display_system_info():
    """Display system information and capabilities"""
    print("🚀 ULTIMATE AUCTION INTELLIGENCE SYSTEM")
    print("=" * 60)
    print()
    print("🔍 SYSTEM CAPABILITIES:")
    print("   • Comprehensive warehouse scanning (5 SC locations)")
    print("   • Real-time NextJS bid data integration")
    print("   • ML-powered opportunity analysis")
    print("   • Intelligent bidding execution")
    print("   • Continuous real-time monitoring")
    print("   • Portfolio management integration")
    print()
    
def check_configuration():
    """Check current system configuration"""
    try:
        with open('investment_strategy_config.json', 'r') as f:
            config = json.load(f)
        
        print("⚙️  CURRENT CONFIGURATION:")
        print(f"   💰 Total Budget: ${config.get('total_budget', 0):,.2f}")
        print(f"   📅 Daily Budget: ${config.get('daily_budget', 0):,.2f}")
        print(f"   ⚠️  Risk Level: {config.get('max_risk_level', 'UNKNOWN')}")
        print(f"   📈 Min ROI: {config.get('min_roi_threshold', 0)}%")
        print(f"   🎯 Auto-bidding: {'✅ Enabled' if config.get('auto_bid_enabled') else '❌ Disabled'}")
        
        dry_run = config.get('dry_run_mode', True)
        mode_text = "🧪 DRY RUN (Safe Testing)" if dry_run else "🚨 LIVE BIDDING (Real Money)"
        print(f"   🎮 Mode: {mode_text}")
        print()
        
        return config
        
    except FileNotFoundError:
        print("❌ Configuration file not found!")
        print("   Please run: python3 configure_budget.py")
        return None

def get_monitoring_duration():
    """Get monitoring duration from user"""
    print("⏰ MONITORING DURATION:")
    print("   1. Quick scan (5 minutes)")
    print("   2. Standard monitoring (30 minutes)")
    print("   3. Extended monitoring (60 minutes)")
    print("   4. Custom duration")
    
    while True:
        try:
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                return 5
            elif choice == "2":
                return 30
            elif choice == "3":
                return 60
            elif choice == "4":
                duration = int(input("Enter duration in minutes: "))
                if 1 <= duration <= 480:  # Max 8 hours
                    return duration
                else:
                    print("❌ Duration must be between 1-480 minutes")
            else:
                print("❌ Please select 1, 2, 3, or 4")
                
        except ValueError:
            print("❌ Please enter a valid number")
        except KeyboardInterrupt:
            print("\n🛑 Cancelled by user")
            sys.exit(0)

async def run_ultimate_system(monitoring_duration):
    """Run the ultimate auction intelligence system"""
    try:
        # Import and run the ultimate system
        from core_systems.ultimate_auction_intelligence_system import UltimateAuctionIntelligenceSystem
        
        # Load configuration
        with open('investment_strategy_config.json', 'r') as f:
            config = json.load(f)
        
        dry_run = config.get('dry_run_mode', True)
        
        print(f"🚀 Launching Ultimate Auction Intelligence System...")
        print(f"⏱️  Monitoring Duration: {monitoring_duration} minutes")
        print(f"💡 Mode: {'DRY RUN' if dry_run else 'LIVE BIDDING'}")
        print()
        
        # Initialize system
        system = UltimateAuctionIntelligenceSystem(dry_run=dry_run)
        
        # Run complete system
        report = await system.run_complete_system(monitoring_duration=monitoring_duration)
        
        # Display results
        print("\n🎉 ULTIMATE SYSTEM EXECUTION COMPLETE!")
        print("=" * 50)
        print(f"📦 Total lots discovered: {report['session_stats']['total_lots_discovered']:,}")
        print(f"🎯 SC warehouse lots: {report['session_stats']['sc_lots_found']:,}")
        print(f"🤖 Opportunities analyzed: {report['session_stats']['opportunities_analyzed']:,}")
        print(f"🏆 Top opportunities selected: {report['session_stats']['top_opportunities_selected']}")
        print(f"💰 Bids executed: {report['session_stats']['bids_executed']}")
        print(f"💵 Total investment: ${report['session_stats']['total_investment']:.2f}")
        
        if report['session_stats']['top_opportunities_selected'] > 0:
            print(f"\n🎯 TOP OPPORTUNITIES:")
            for i, opp in enumerate(report['top_opportunities'][:3], 1):
                print(f"   {i}. {opp['product_name'][:50]}")
                print(f"      Score: {opp['opportunity_score']:.1f}/100, ROI: {opp['predicted_roi']:.1f}%")
        
        print(f"\n📊 Full report saved to: data_outputs/ultimate_system_report_*.json")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Please ensure all system files are present")
    except Exception as e:
        print(f"❌ System error: {e}")
        raise

def main():
    """Main launcher function"""
    print(f"🕐 Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Display system info
    display_system_info()
    
    # Check configuration
    config = check_configuration()
    if not config:
        return
    
    # Get monitoring duration
    monitoring_duration = get_monitoring_duration()
    
    # Confirm execution
    print(f"\n🚀 READY TO LAUNCH")
    print("=" * 30)
    print(f"⏱️  Duration: {monitoring_duration} minutes")
    print(f"💰 Budget: ${config.get('total_budget', 0):,.2f}")
    print(f"🎮 Mode: {'DRY RUN' if config.get('dry_run_mode') else 'LIVE BIDDING'}")
    
    confirm = input(f"\nProceed with ultimate system launch? (y/N): ").strip().lower()
    
    if confirm in ['y', 'yes']:
        print(f"\n🚀 Launching in 3 seconds...")
        import time
        for i in range(3, 0, -1):
            print(f"   {i}...")
            time.sleep(1)
        
        # Run the system
        try:
            asyncio.run(run_ultimate_system(monitoring_duration))
        except KeyboardInterrupt:
            print(f"\n🛑 System stopped by user")
        except Exception as e:
            print(f"\n❌ Launch error: {e}")
    else:
        print(f"🛑 Launch cancelled")

if __name__ == "__main__":
    main() 