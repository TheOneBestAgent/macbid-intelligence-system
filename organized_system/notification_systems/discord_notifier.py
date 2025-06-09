#!/usr/bin/env python3
"""
Discord Notification System for Mac.bid Opportunities
Sends real-time alerts for high-value auction opportunities.
"""

import asyncio
import aiohttp
import json
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional

class DiscordNotifier:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL', '')
        self.setup_logging()
        
        # Notification thresholds
        self.high_value_threshold = 1500  # $1500+ retail value
        self.min_opportunity_score = 0.8  # 80%+ opportunity score
        self.max_notifications_per_run = 10  # Limit spam
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def format_opportunity_message(self, opportunities: List[Dict]) -> str:
        """Format opportunities into Discord message"""
        if not opportunities:
            return ""
            
        # Filter high-priority opportunities
        high_priority = [
            opp for opp in opportunities[:20]
            if (opp['retail_price'] >= self.high_value_threshold and 
                opp['opportunity_score'] >= self.min_opportunity_score)
        ]
        
        if not high_priority:
            return ""
            
        # Create message
        message = f"🚨 **{len(high_priority)} HIGH-VALUE OPPORTUNITIES FOUND!**\n\n"
        
        for i, opp in enumerate(high_priority[:self.max_notifications_per_run], 1):
            message += f"**{i}. {opp['title']}**\n"
            message += f"💰 Retail: ${opp['retail_price']:,.2f} | Current Bid: ${opp['current_bid']:,.2f}\n"
            message += f"📊 Discount: {opp['discount']:.1f}% | Score: {opp['opportunity_score']:.3f}\n"
            message += f"📍 {opp['location']} | 🔗 {opp['url']}\n\n"
            
        message += f"⏰ Alert sent at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
        
    async def send_notification(self, message: str) -> bool:
        """Send Discord notification"""
        if not self.webhook_url:
            self.logger.warning("⚠️ No Discord webhook URL configured")
            return False
            
        if not message.strip():
            self.logger.info("ℹ️ No high-priority opportunities to notify")
            return True
            
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "content": message[:2000],  # Discord 2000 char limit
                    "username": "Mac.bid Opportunity Bot",
                    "avatar_url": "https://mac.bid/favicon.ico"
                }
                
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 204:
                        self.logger.info("✅ Discord notification sent successfully")
                        return True
                    else:
                        self.logger.error(f"❌ Discord notification failed: {response.status}")
                        return False
                        
        except Exception as e:
            self.logger.error(f"❌ Discord notification error: {e}")
            return False
            
    async def send_opportunities(self, opportunities: List[Dict]) -> bool:
        """Send opportunities notification"""
        message = self.format_opportunity_message(opportunities)
        return await self.send_notification(message)
        
    async def send_daily_summary(self, stats: Dict) -> bool:
        """Send daily summary notification"""
        message = f"""📊 **DAILY MAC.BID SUMMARY - {datetime.now().strftime('%Y-%m-%d')}**

🔄 Discovery Runs: {stats.get('runs', 0)}
🎯 Total Opportunities: {stats.get('total_opportunities', 0)}
🔍 Lots Scanned: {stats.get('total_lots', 0):,}
✅ Success Rate: {stats.get('success_rate', 0):.1f}%
⏱️ Avg Runtime: {stats.get('avg_runtime', 0):.1f}s

🏆 **Top Categories Today:**
{stats.get('top_categories', 'No data available')}
        """
        
        return await self.send_notification(message)
        
    async def send_system_alert(self, alert_type: str, message: str) -> bool:
        """Send system alert notification"""
        alert_message = f"🔔 **SYSTEM ALERT - {alert_type.upper()}**\n\n{message}\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return await self.send_notification(alert_message)

def main():
    """Test the Discord notifier"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python discord_notifier.py <webhook_url>")
        sys.exit(1)
        
    webhook_url = sys.argv[1]
    notifier = DiscordNotifier(webhook_url)
    
    # Test notification
    test_opportunities = [
        {
            'title': 'Apple MacBook Pro 16"',
            'retail_price': 2499.00,
            'current_bid': 0.00,
            'discount': 100.0,
            'opportunity_score': 1.0,
            'location': 'Anderson',
            'url': 'https://mac.bid/lot/test123'
        }
    ]
    
    async def test():
        success = await notifier.send_opportunities(test_opportunities)
        print(f"Test notification {'sent' if success else 'failed'}")
        
    asyncio.run(test())

if __name__ == "__main__":
    main() 