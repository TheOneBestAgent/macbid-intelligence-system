#!/usr/bin/env python3
"""
⚙️ ENHANCEMENT SETUP - Configure All Advanced Features
Set up continuous monitoring, notifications, and ML predictions
"""

import json
import os
import getpass
from datetime import datetime

class EnhancementSetup:
    def __init__(self):
        self.config_files = {
            "notification_config.json": self.create_notification_config,
            "bid_model.json": self.create_ml_config,
            "monitoring_config.json": self.create_monitoring_config
        }
        
    def create_notification_config(self):
        """Create notification configuration"""
        print("\n📱 NOTIFICATION SETUP")
        print("="*50)
        
        config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "",
                "to_emails": [],
                "use_tls": True
            },
            "webhook": {
                "enabled": False,
                "discord_url": "",
                "slack_url": "",
                "headers": {"Content-Type": "application/json"}
            },
            "preferences": {
                "quiet_hours_enabled": True,
                "quiet_start": "22:00",
                "quiet_end": "07:00",
                "max_alerts_per_hour": 10
            }
        }
        
        # Email setup
        setup_email = input("📧 Set up email notifications? (y/n): ").lower() == 'y'
        if setup_email:
            config["email"]["enabled"] = True
            config["email"]["username"] = input("Gmail username: ")
            config["email"]["password"] = getpass.getpass("Gmail app password (hidden): ")
            config["email"]["from_email"] = config["email"]["username"]
            
            to_emails = input("Notification email(s) (comma-separated): ").split(',')
            config["email"]["to_emails"] = [email.strip() for email in to_emails if email.strip()]
            
            print("✅ Email notifications configured!")
            
        # Discord webhook setup
        setup_discord = input("🎮 Set up Discord webhook? (y/n): ").lower() == 'y'
        if setup_discord:
            config["webhook"]["enabled"] = True
            config["webhook"]["discord_url"] = input("Discord webhook URL: ")
            print("✅ Discord webhook configured!")
            
        # Slack webhook setup
        setup_slack = input("💬 Set up Slack webhook? (y/n): ").lower() == 'y'
        if setup_slack:
            config["webhook"]["enabled"] = True
            config["webhook"]["slack_url"] = input("Slack webhook URL: ")
            print("✅ Slack webhook configured!")
            
        return config
        
    def create_ml_config(self):
        """Create ML model configuration"""
        print("\n🤖 MACHINE LEARNING SETUP")
        print("="*50)
        
        config = {
            "category_multipliers": {
                "Electronics": 0.65,
                "Audio": 0.70,
                "Appliances": 0.60,
                "Tools": 0.55,
                "Gaming": 0.75,
                "Luxury": 0.80,
                "Default": 0.65
            },
            "brand_premiums": {
                "apple": 1.2,
                "sony": 1.1,
                "samsung": 1.1,
                "nintendo": 1.15,
                "dyson": 1.1,
                "bose": 1.1,
                "default": 1.0
            },
            "location_factors": {
                "Rock Hill": 1.05,
                "Greenville": 1.0,
                "Gastonia": 0.95,
                "Anderson": 0.90,
                "Spartanburg": 0.85,
                "default": 1.0
            },
            "competition_adjustments": {
                "low": 0.85,
                "medium": 1.0,
                "high": 1.25
            },
            "time_factors": {
                "weekday_evening": 1.1,
                "weekend": 1.15,
                "late_night": 0.9,
                "business_hours": 1.0
            }
        }
        
        # Ask for customization
        customize = input("🎯 Customize ML model parameters? (y/n): ").lower() == 'y'
        if customize:
            print("\n📊 Current category multipliers:")
            for category, mult in config["category_multipliers"].items():
                if category != "Default":
                    print(f"   {category}: {mult}")
                    
            print("\n💡 Lower values = more aggressive bidding")
            print("💡 Higher values = more conservative bidding")
            
            # Allow adjustment of key categories
            for category in ["Electronics", "Audio", "Gaming"]:
                new_mult = input(f"New multiplier for {category} (current: {config['category_multipliers'][category]}): ")
                if new_mult:
                    try:
                        config["category_multipliers"][category] = float(new_mult)
                    except ValueError:
                        print(f"Invalid value, keeping {config['category_multipliers'][category]}")
                        
        print("✅ ML model configured!")
        return config
        
    def create_monitoring_config(self):
        """Create monitoring configuration"""
        print("\n🔄 CONTINUOUS MONITORING SETUP")
        print("="*50)
        
        config = {
            "monitoring": {
                "interval_minutes": 5,
                "enabled_modules": [
                    "enhanced_new_arrivals",
                    "deal_hunter", 
                    "no_bid_tracker",
                    "price_analytics_tracker",
                    "advanced_product_search"
                ],
                "alert_thresholds": {
                    "min_savings": 500,
                    "min_discount_percent": 50,
                    "min_confidence": 0.7
                }
            },
            "portfolio": {
                "auto_track_bids": True,
                "track_recommendations": True,
                "calculate_roi": True
            }
        }
        
        # Monitoring interval
        interval = input(f"Monitoring interval in minutes (current: {config['monitoring']['interval_minutes']}): ")
        if interval:
            try:
                config["monitoring"]["interval_minutes"] = int(interval)
            except ValueError:
                print("Invalid value, keeping default")
                
        # Alert thresholds
        min_savings = input(f"Minimum savings for alerts (current: ${config['monitoring']['alert_thresholds']['min_savings']}): ")
        if min_savings:
            try:
                config["monitoring"]["alert_thresholds"]["min_savings"] = float(min_savings)
            except ValueError:
                print("Invalid value, keeping default")
                
        print("✅ Monitoring configured!")
        return config
        
    def save_config(self, filename, config):
        """Save configuration to file"""
        try:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✅ Saved {filename}")
            return True
        except Exception as e:
            print(f"❌ Error saving {filename}: {e}")
            return False
            
    def create_startup_script(self):
        """Create startup script for easy launching"""
        script_content = '''#!/bin/bash
# 🚀 AUCTION INTELLIGENCE STARTUP SCRIPT

echo "🚀 Starting Auction Intelligence System..."

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# Function to start monitoring
start_monitoring() {
    echo "🔄 Starting continuous monitoring..."
    python3 enhanced_continuous_monitor.py --interval 5 &
    MONITOR_PID=$!
    echo "✅ Monitoring started (PID: $MONITOR_PID)"
}

# Function to test system
test_system() {
    echo "🧪 Testing system components..."
    
    echo "Testing bid predictor..."
    python3 bid_predictor.py --test
    
    echo "Testing portfolio tracker..."
    python3 portfolio_tracker.py --dashboard
    
    echo "Testing enhanced monitor..."
    python3 enhanced_continuous_monitor.py --test
    
    echo "✅ System test complete!"
}

# Function to show dashboard
show_dashboard() {
    echo "📊 Launching master dashboard..."
    python3 master_dashboard.py --comprehensive
}

# Main menu
echo ""
echo "Choose an option:"
echo "1) Start continuous monitoring"
echo "2) Test system components"
echo "3) Show master dashboard"
echo "4) View portfolio"
echo "5) Exit"
echo ""

read -p "Enter choice (1-5): " choice

case $choice in
    1)
        start_monitoring
        echo "Press Ctrl+C to stop monitoring"
        wait $MONITOR_PID
        ;;
    2)
        test_system
        ;;
    3)
        show_dashboard
        ;;
    4)
        python3 portfolio_tracker.py --dashboard
        ;;
    5)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac
'''
        
        try:
            with open('start_auction_intelligence.sh', 'w') as f:
                f.write(script_content)
            os.chmod('start_auction_intelligence.sh', 0o755)
            print("✅ Created startup script: start_auction_intelligence.sh")
            return True
        except Exception as e:
            print(f"❌ Error creating startup script: {e}")
            return False
            
    def create_quick_commands(self):
        """Create quick command aliases"""
        commands = {
            "monitor": "python3 enhanced_continuous_monitor.py",
            "dashboard": "python3 master_dashboard.py --comprehensive",
            "portfolio": "python3 portfolio_tracker.py --dashboard",
            "predict": "python3 bid_predictor.py --test",
            "test": "python3 enhanced_continuous_monitor.py --test"
        }
        
        aliases_content = "# 🚀 Auction Intelligence Quick Commands\n"
        aliases_content += "# Add these to your ~/.bashrc or ~/.zshrc\n\n"
        
        for alias, command in commands.items():
            aliases_content += f"alias auction-{alias}='{command}'\n"
            
        try:
            with open('auction_aliases.sh', 'w') as f:
                f.write(aliases_content)
            print("✅ Created aliases file: auction_aliases.sh")
            print("💡 Add to your shell: source auction_aliases.sh")
            return True
        except Exception as e:
            print(f"❌ Error creating aliases: {e}")
            return False
            
    def run_setup(self):
        """Run complete setup process"""
        print("⚙️ AUCTION INTELLIGENCE ENHANCEMENT SETUP")
        print("="*60)
        print("This will configure:")
        print("1. 🔄 Continuous monitoring with real-time alerts")
        print("2. 📱 Multi-channel notifications (email, Discord, Slack)")
        print("3. 🤖 Machine learning bid predictions")
        print("4. 📊 Portfolio tracking and analytics")
        print("")
        
        proceed = input("Continue with setup? (y/n): ").lower() == 'y'
        if not proceed:
            print("Setup cancelled.")
            return
            
        # Create all configuration files
        configs_created = 0
        for filename, create_func in self.config_files.items():
            try:
                config = create_func()
                if self.save_config(filename, config):
                    configs_created += 1
            except KeyboardInterrupt:
                print("\nSetup interrupted.")
                return
            except Exception as e:
                print(f"Error creating {filename}: {e}")
                
        # Create startup script
        self.create_startup_script()
        
        # Create quick commands
        self.create_quick_commands()
        
        # Final summary
        print(f"\n🎉 SETUP COMPLETE!")
        print("="*60)
        print(f"✅ {configs_created}/{len(self.config_files)} configuration files created")
        print("✅ Startup script created")
        print("✅ Quick command aliases created")
        
        print(f"\n🚀 QUICK START:")
        print("1. Start monitoring: ./start_auction_intelligence.sh")
        print("2. View dashboard: python3 master_dashboard.py --comprehensive")
        print("3. Test ML predictions: python3 bid_predictor.py --test")
        print("4. Check portfolio: python3 portfolio_tracker.py --dashboard")
        
        print(f"\n📱 NOTIFICATION SETUP:")
        if os.path.exists("notification_config.json"):
            print("✅ Edit notification_config.json to enable email/webhook alerts")
        else:
            print("⚠️ Notification config not created - run setup again if needed")
            
        print(f"\n🤖 MACHINE LEARNING:")
        print("✅ ML model configured and ready for bid predictions")
        print("💡 The system learns from your bidding patterns over time")
        
        print(f"\n🔄 CONTINUOUS MONITORING:")
        print("✅ Enhanced monitoring ready with all analytics modules")
        print("💡 Runs every 5 minutes by default (configurable)")
        
        print(f"\n📊 PORTFOLIO TRACKING:")
        print("✅ Track your bids and measure success rates")
        print("💡 Use --add-bid to start tracking your auction activity")

def main():
    setup = EnhancementSetup()
    setup.run_setup()

if __name__ == "__main__":
    main() 