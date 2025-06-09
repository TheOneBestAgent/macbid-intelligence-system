#!/usr/bin/env python3
"""
Update stored credentials with discovered customer ID
"""

import json
from pathlib import Path

def update_customer_id(customer_id):
    """Update the stored credentials with customer ID."""
    config_file = Path.home() / '.macbid_scraper' / 'credentials.json'
    
    try:
        with open(config_file, 'r') as f:
            creds = json.load(f)
        
        creds['customer_id'] = str(customer_id)
        
        with open(config_file, 'w') as f:
            json.dump(creds, f, indent=2)
        
        print(f'✅ Updated credentials with customer ID: {customer_id}')
        return True
        
    except Exception as e:
        print(f'❌ Error updating credentials: {e}')
        return False

if __name__ == "__main__":
    update_customer_id('2710619') 