#!/usr/bin/env python3
"""
🎯 Enhanced Personal Monitor
Uses your REAL purchase history to find matching auction opportunities
"""

import json
import os
import asyncio
import aiohttp
import sqlite3
from datetime import datetime
import re
from collections import Counter

class EnhancedPersonalMonitor:
    def __init__(self):
        self.portfolio_db = "portfolio_tracker.db"
        self.tokens_file = os.path.expanduser("~/.macbid_scraper/api_tokens.json")
        self.load_tokens()
        self.load_purchase_patterns()
        
    def load_tokens(self):
        """Load JWT tokens."""
        try:
            with open(self.tokens_file, 'r') as f:
                token_data = json.load(f)
                self.jwt_token = token_data.get('tokens', {}).get('authorization')
                self.customer_id = token_data.get('customer_id')
                self.username = token_data.get('username')
        except:
            self.jwt_token = None
            self.customer_id = None
            self.username = None
    
    def load_purchase_patterns(self):
        """Analyze your real purchase patterns."""
        print("🔍 ANALYZING YOUR PURCHASE PATTERNS")
        print("=" * 50)
        
        conn = sqlite3.connect(self.portfolio_db)
        cursor = conn.cursor()
        
        # Get your real purchase data
        cursor.execute('''
            SELECT brand, category, product_name, my_bid_amount
            FROM bids 
            WHERE source = 'real_data_import'
        ''')
        
        purchases = cursor.fetchall()
        
        if not purchases:
            print("❌ No real purchase data found!")
            self.favorite_brands = []
            self.favorite_categories = []
            self.price_ranges = {}
            self.keywords = []
            return
        
        # Analyze patterns
        brands = [p[0] for p in purchases if p[0]]
        categories = [p[1] for p in purchases if p[1]]
        prices = [float(p[3]) for p in purchases if p[3]]
        product_names = [p[2] for p in purchases if p[2]]
        
        # Top brands (your favorites)
        brand_counts = Counter(brands)
        self.favorite_brands = [brand for brand, count in brand_counts.most_common(10)]
        
        # Top categories
        category_counts = Counter(categories)
        self.favorite_categories = [cat for cat, count in category_counts.most_common(5)]
        
        # Price ranges by category
        self.price_ranges = {}
        for category in self.favorite_categories:
            cat_prices = [float(p[3]) for p in purchases if p[1] == category]
            if cat_prices:
                self.price_ranges[category] = {
                    'min': min(cat_prices),
                    'max': max(cat_prices),
                    'avg': sum(cat_prices) / len(cat_prices)
                }
        
        # Extract keywords from product names
        all_words = []
        for name in product_names:
            words = re.findall(r'\b[A-Za-z]{3,}\b', name.lower())
            all_words.extend(words)
        
        word_counts = Counter(all_words)
        # Filter out common words
        common_words = {'the', 'and', 'for', 'with', 'pro', 'mini', 'plus', 'new', 'set'}
        self.keywords = [word for word, count in word_counts.most_common(20) 
                        if word not in common_words and count >= 2]
        
        print(f"✅ Analyzed {len(purchases)} real purchases")
        print(f"🏷️ Favorite Brands: {', '.join(self.favorite_brands[:5])}")
        print(f"📂 Favorite Categories: {', '.join(self.favorite_categories)}")
        print(f"🔑 Key Product Words: {', '.join(self.keywords[:10])}")
        
        conn.close()
    
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
    
    async def fetch_current_auctions(self):
        """Fetch current auctions from mac.bid."""
        print("🔍 Fetching current auctions...")
        
        connector = aiohttp.TCPConnector(ssl=False)
        session = aiohttp.ClientSession(connector=connector)
        
        try:
            # Try multiple auction endpoints
            endpoints = [
                "https://api.macdiscount.com/auction/getAuctions?pg=1&ppg=50&loc=17,18",
                "https://api.macdiscount.com/auction/getAuctions?pg=1&ppg=50",
                "https://api.macdiscount.com/auction/search?q=&pg=1&ppg=50"
            ]
            
            for endpoint in endpoints:
                try:
                    async with session.get(endpoint, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and isinstance(data, list):
                                print(f"✅ Found {len(data)} auctions")
                                return data
                except Exception as e:
                    print(f"⚠️ Endpoint failed: {str(e)[:50]}...")
                    continue
            
            print("❌ No auction data available")
            return []
            
        finally:
            await session.close()
    
    def calculate_match_score(self, auction):
        """Calculate how well an auction matches your purchase patterns."""
        score = 0
        reasons = []
        
        title = auction.get('title', '').lower()
        description = auction.get('description', '').lower()
        current_price = float(auction.get('current_bid', 0))
        
        # Brand matching (high weight)
        for brand in self.favorite_brands:
            if brand.lower() in title or brand.lower() in description:
                score += 30
                reasons.append(f"Favorite brand: {brand}")
                break
        
        # Keyword matching
        keyword_matches = 0
        for keyword in self.keywords:
            if keyword in title or keyword in description:
                keyword_matches += 1
                score += 5
        
        if keyword_matches > 0:
            reasons.append(f"{keyword_matches} keyword matches")
        
        # Category-based price range matching
        for category, price_range in self.price_ranges.items():
            category_keywords = {
                'Audio': ['headphone', 'speaker', 'microphone', 'audio', 'sound'],
                'Gaming': ['gaming', 'keyboard', 'mouse', 'controller'],
                'Computing': ['processor', 'cpu', 'computer', 'pc'],
                'Electronics': ['electronic', 'device', 'tech'],
                'Home': ['home', 'kitchen', 'vacuum', 'cleaner']
            }
            
            if category in category_keywords:
                if any(word in title for word in category_keywords[category]):
                    # Check if price is in your typical range for this category
                    if price_range['min'] <= current_price <= price_range['max'] * 1.5:
                        score += 20
                        reasons.append(f"Price fits {category} range (${price_range['min']:.0f}-${price_range['max']:.0f})")
                    break
        
        # Bonus for low current bid (opportunity)
        if current_price < 50:
            score += 10
            reasons.append("Low current bid")
        
        return score, reasons
    
    def find_matching_auctions(self, auctions):
        """Find auctions that match your purchase patterns."""
        print(f"\n🎯 ANALYZING {len(auctions)} AUCTIONS FOR MATCHES")
        print("=" * 50)
        
        matches = []
        
        for auction in auctions:
            score, reasons = self.calculate_match_score(auction)
            
            if score >= 25:  # Minimum threshold for a good match
                match = {
                    'auction': auction,
                    'score': score,
                    'reasons': reasons
                }
                matches.append(match)
        
        # Sort by score
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches
    
    def display_matches(self, matches):
        """Display matching auctions."""
        if not matches:
            print("❌ No auctions match your purchase patterns")
            return
        
        print(f"🎉 FOUND {len(matches)} MATCHING AUCTIONS!")
        print("=" * 60)
        
        for i, match in enumerate(matches[:10], 1):  # Show top 10
            auction = match['auction']
            score = match['score']
            reasons = match['reasons']
            
            title = auction.get('title', 'Unknown')
            current_bid = auction.get('current_bid', 0)
            end_time = auction.get('end_time', 'Unknown')
            lot_id = auction.get('lot_id', 'Unknown')
            
            print(f"\n🏆 MATCH #{i} (Score: {score})")
            print(f"📦 {title}")
            print(f"💰 Current Bid: ${current_bid}")
            print(f"🕒 Ends: {end_time}")
            print(f"🔗 Lot ID: {lot_id}")
            print(f"✨ Why it matches: {', '.join(reasons)}")
            print("-" * 60)
    
    async def run_enhanced_monitor(self):
        """Run the enhanced monitoring system."""
        print("🎯 ENHANCED PERSONAL AUCTION MONITOR")
        print("=" * 60)
        print(f"👤 Monitoring for: {self.username}")
        print(f"🎲 Using your REAL purchase patterns")
        print(f"🏷️ Tracking {len(self.favorite_brands)} favorite brands")
        print(f"📂 Watching {len(self.favorite_categories)} categories")
        print("=" * 60)
        
        if not self.favorite_brands:
            print("❌ No purchase patterns found!")
            print("Run integrate_real_data.py first to import your purchase history")
            return
        
        # Fetch current auctions
        auctions = await self.fetch_current_auctions()
        
        if auctions:
            # Find matches
            matches = self.find_matching_auctions(auctions)
            
            # Display results
            self.display_matches(matches)
            
            # Save results
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"personal_matches_{timestamp}.json"
            
            with open(filename, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'total_auctions': len(auctions),
                    'matches_found': len(matches),
                    'matches': matches
                }, f, indent=2)
            
            print(f"\n💾 Results saved to: {filename}")
            
        else:
            print("❌ No auction data available")

async def main():
    """Main function."""
    monitor = EnhancedPersonalMonitor()
    await monitor.run_enhanced_monitor()

if __name__ == "__main__":
    asyncio.run(main()) 