#!/usr/bin/env python3
"""
🎯 Personal Data Access System
Access your actual mac.bid auction data using JWT authentication
"""

import json
import os
import asyncio
import aiohttp
from datetime import datetime
import pandas as pd

class PersonalDataAccess:
    def __init__(self):
        self.tokens_file = os.path.expanduser("~/.macbid_scraper/api_tokens.json")
        self.load_tokens()
        
    def load_tokens(self):
        """Load JWT tokens."""
        try:
            with open(self.tokens_file, 'r') as f:
                token_data = json.load(f)
                self.jwt_token = token_data.get('tokens', {}).get('authorization')
                self.customer_id = token_data.get('customer_id')
                self.username = token_data.get('username')
                self.working_endpoints = token_data.get('working_endpoints', [])
        except:
            print("❌ No JWT tokens found! Run process_captured_token.py first!")
            self.jwt_token = None
            self.customer_id = None
            self.username = None
            self.working_endpoints = []
    
    def get_headers(self):
        """Get authenticated headers."""
        return {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.6',
            'authorization': self.jwt_token,
            'content-type': 'application/json',
            'origin': 'https://www.mac.bid',
            'referer': 'https://www.mac.bid/',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
    
    async def get_invoices(self, pages=5):
        """Get your invoice history."""
        print("📋 FETCHING YOUR INVOICE HISTORY")
        print("=" * 50)
        
        if 'Invoices' not in self.working_endpoints:
            print("❌ Invoices endpoint not available")
            return None
        
        all_invoices = []
        connector = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(connector=connector)
        
        try:
            for page in range(1, pages + 1):
                url = f"https://api.macdiscount.com/user/{self.customer_id}/invoices?pg={page}"
                print(f"📄 Fetching page {page}...")
                
                async with session.get(url, headers=self.get_headers(), timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            all_invoices.extend(data)
                            print(f"   ✅ Got {len(data)} invoices")
                            if len(data) < 20:  # Likely last page
                                break
                        else:
                            break
                    else:
                        print(f"   ❌ Error: Status {response.status}")
                        break
        
        finally:
            await session.close()
        
        print(f"\n📊 TOTAL INVOICES FOUND: {len(all_invoices)}")
        return all_invoices
    
    async def get_invoice_items(self, pages=10):
        """Get your detailed invoice items."""
        print("\n📦 FETCHING YOUR INVOICE ITEMS")
        print("=" * 50)
        
        if 'Invoice Items' not in self.working_endpoints:
            print("❌ Invoice Items endpoint not available")
            return None
        
        all_items = []
        connector = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(connector=connector)
        
        try:
            for page in range(1, pages + 1):
                url = f"https://api.macdiscount.com/user/{self.customer_id}/invoices-items?pg={page}&ppg=30"
                print(f"📦 Fetching page {page}...")
                
                async with session.get(url, headers=self.get_headers(), timeout=15) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            all_items.extend(data)
                            print(f"   ✅ Got {len(data)} items")
                            if len(data) < 30:  # Likely last page
                                break
                        else:
                            break
                    else:
                        print(f"   ❌ Error: Status {response.status}")
                        break
        
        finally:
            await session.close()
        
        print(f"\n📊 TOTAL ITEMS FOUND: {len(all_items)}")
        return all_items
    
    async def get_alerts(self):
        """Get your keyword alerts."""
        print("\n🚨 FETCHING YOUR ALERTS")
        print("=" * 30)
        
        if 'Alerts' not in self.working_endpoints:
            print("❌ Alerts endpoint not available")
            return None
        
        connector = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(connector=connector)
        
        try:
            url = f"https://api.macdiscount.com/user/{self.customer_id}/getAlertsAndKeywordsHitsForCustomer?loc=17,18&pg=1&ppg=25"
            
            async with session.get(url, headers=self.get_headers(), timeout=15) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Got alerts data")
                    return data
                else:
                    print(f"❌ Error: Status {response.status}")
                    return None
        
        finally:
            await session.close()
    
    def analyze_purchase_history(self, invoices, items):
        """Analyze your purchase history."""
        print("\n📊 ANALYZING YOUR PURCHASE HISTORY")
        print("=" * 50)
        
        if not invoices or not items:
            print("❌ No data to analyze")
            return
        
        # Basic stats
        total_invoices = len(invoices)
        total_items = len(items)
        
        # Financial analysis
        total_spent = sum(float(inv.get('grand_total', 0)) for inv in invoices)
        total_item_value = sum(float(inv.get('total_price', 0)) for inv in invoices)
        total_fees = total_spent - total_item_value
        
        print(f"🏆 PURCHASE SUMMARY:")
        print(f"   Total Invoices: {total_invoices}")
        print(f"   Total Items: {total_items}")
        print(f"   Total Spent: ${total_spent:,.2f}")
        print(f"   Item Value: ${total_item_value:,.2f}")
        print(f"   Fees & Taxes: ${total_fees:,.2f}")
        print(f"   Average per Invoice: ${total_spent/total_invoices:,.2f}")
        
        # Recent activity
        recent_invoices = sorted(invoices, key=lambda x: x.get('date_created', ''), reverse=True)[:5]
        print(f"\n📅 RECENT PURCHASES:")
        for i, inv in enumerate(recent_invoices, 1):
            date = inv.get('date_created', 'Unknown')[:10]
            total = inv.get('grand_total', 0)
            print(f"   {i}. {date}: ${total}")
        
        # Item analysis
        if items:
            print(f"\n📦 ITEM ANALYSIS:")
            
            # Most expensive items
            expensive_items = sorted(items, key=lambda x: float(x.get('total', 0)), reverse=True)[:5]
            print(f"💰 Most Expensive Items:")
            for i, item in enumerate(expensive_items, 1):
                desc = item.get('description', 'Unknown')[:50]
                total = item.get('total', 0)
                print(f"   {i}. ${total} - {desc}")
            
            # Recent items
            recent_items = sorted(items, key=lambda x: x.get('date_created', ''), reverse=True)[:5]
            print(f"\n📅 Recent Items:")
            for i, item in enumerate(recent_items, 1):
                desc = item.get('description', 'Unknown')[:50]
                date = item.get('date_created', 'Unknown')[:10]
                total = item.get('total', 0)
                print(f"   {i}. {date}: ${total} - {desc}")
    
    def save_data_to_files(self, invoices, items, alerts):
        """Save data to JSON files for further analysis."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if invoices:
            filename = f"personal_invoices_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(invoices, f, indent=2)
            print(f"💾 Invoices saved to: {filename}")
        
        if items:
            filename = f"personal_items_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(items, f, indent=2)
            print(f"💾 Items saved to: {filename}")
        
        if alerts:
            filename = f"personal_alerts_{timestamp}.json"
            with open(filename, 'w') as f:
                json.dump(alerts, f, indent=2)
            print(f"💾 Alerts saved to: {filename}")

async def main():
    """Main function to access personal data."""
    access = PersonalDataAccess()
    
    print("🎯 PERSONAL MAC.BID DATA ACCESS")
    print("=" * 50)
    
    if not access.jwt_token:
        print("❌ No JWT token found!")
        print("Run process_captured_token.py first to capture your browser token")
        return
    
    print(f"👤 Customer ID: {access.customer_id}")
    print(f"📧 Username: {access.username}")
    print(f"🔑 JWT Token: {access.jwt_token[:30]}...")
    print(f"✅ Working Endpoints: {', '.join(access.working_endpoints)}")
    print()
    
    # Fetch all your data
    invoices = await access.get_invoices(pages=10)  # Get up to 10 pages
    items = await access.get_invoice_items(pages=20)  # Get up to 20 pages
    alerts = await access.get_alerts()
    
    # Analyze the data
    if invoices or items:
        access.analyze_purchase_history(invoices, items)
        
        # Save data for future use
        print(f"\n💾 SAVING DATA FOR FUTURE ANALYSIS")
        print("=" * 40)
        access.save_data_to_files(invoices, items, alerts)
        
        print(f"\n🚀 NEXT STEPS:")
        print("1. Your personal data is now saved locally")
        print("2. You can integrate this with your portfolio tracker")
        print("3. Use this data to enhance your bidding analytics")
        print("4. Run personalized_analytics.py with this real data")
    
    else:
        print("❌ No personal data could be retrieved")

if __name__ == "__main__":
    asyncio.run(main()) 