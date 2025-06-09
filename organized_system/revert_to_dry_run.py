#!/usr/bin/env python3
"""
Emergency Revert to Dry-Run Mode
Quickly switches back to safe testing mode
"""

import json
from datetime import datetime

def revert_to_dry_run():
    config_file = "investment_strategy_config.json"
    
    try:
        # Load current config
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Check current mode
        if config.get('dry_run_mode', True):
            print("✅ System is already in DRY-RUN mode (safe)")
            return
        
        # Revert to dry-run
        config['dry_run_mode'] = True
        config['reverted_to_dry_run'] = datetime.now().isoformat()
        
        # Save updated config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print("🛡️  REVERTED TO DRY-RUN MODE")
        print("✅ System is now in SAFE testing mode")
        print("💡 No real money will be spent")
        
    except Exception as e:
        print(f"❌ Error reverting to dry-run: {e}")

if __name__ == "__main__":
    revert_to_dry_run() 