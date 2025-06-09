#!/usr/bin/env python3
"""
⏰ Auction Timing Analyzer - Optimize Your Bidding Strategy
Track auction closing times, identify low-competition slots, and analyze bid patterns
"""

import asyncio
import aiohttp
import ssl
import json
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

class AuctionTimingAnalyzer:
    def __init__(self):
        self.session = None
        self.sc_locations = ["Spartanburg", "Greenville", "Rock Hill", "Gastonia", "Anderson"]
        self.db_file = "timing_analysis.db"
        self.init_database()
        
        # Time slots for analysis (24-hour format)
        self.time_slots = {
            'Early Morning': (6, 9),    # 6 AM - 9 AM
            'Morning': (9, 12),         # 9 AM - 12 PM
            'Afternoon': (12, 17),      # 12 PM - 5 PM
            'Evening': (17, 21),        # 5 PM - 9 PM
            'Night': (21, 24),          # 9 PM - 12 AM
            'Late Night': (0, 6)        # 12 AM - 6 AM
        }
        
        # Days of week analysis
        self.weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
    def init_database(self):
        """Initialize timing analysis database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Auction timing data
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS auction_timing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_id TEXT,
                product_name TEXT,
                auction_location TEXT,
                retail_price REAL,
                instant_win_price REAL,
                current_bid REAL,
                expected_close_date TEXT,
                close_hour INTEGER,
                close_day_of_week TEXT,
                time_slot TEXT,
                competition_score REAL,
                discount_percent REAL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Time slot analysis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_slot_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time_slot TEXT,
                day_of_week TEXT,
                avg_competition REAL,
                avg_discount REAL,
                total_auctions INTEGER,
                avg_retail_value REAL,
                opportunity_score REAL,
                analysis_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def create_session(self):
        """Create HTTP session."""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context, limit=15)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
        )
        
    async def close_session(self):
        if self.session:
            await self.session.close()
            await asyncio.sleep(0.25)
            
    async def search_for_term(self, term, limit=100):
        """Search for a specific term."""
        url = f"https://api.macdiscount.com/search?q={term}&limit={limit}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    hits = data.get('hits', [])
                    
                    sc_hits = []
                    for hit in hits:
                        if hit.get('auction_location') in self.sc_locations:
                            sc_hits.append(hit)
                            
                    return sc_hits
                else:
                    return []
        except Exception as e:
            return []
            
    def parse_closing_time(self, close_date_str):
        """Parse closing date and extract timing info."""
        if not close_date_str or close_date_str == 'Unknown':
            return None, None, None
            
        try:
            # Handle different date formats
            if 'T' in close_date_str:
                close_date = datetime.fromisoformat(close_date_str.replace('Z', ''))
            else:
                close_date = datetime.strptime(close_date_str, '%Y-%m-%d')
                
            hour = close_date.hour
            day_of_week = self.weekdays[close_date.weekday()]
            
            # Determine time slot
            time_slot = None
            for slot_name, (start_hour, end_hour) in self.time_slots.items():
                if start_hour <= hour < end_hour:
                    time_slot = slot_name
                    break
                    
            return hour, day_of_week, time_slot
            
        except Exception as e:
            return None, None, None
            
    def calculate_competition_score(self, item):
        """Calculate competition score based on various factors."""
        retail_price = item.get('retail_price', 0)
        instant_win_price = item.get('instant_win_price', 0)
        current_bid = item.get('current_bid', 0)
        
        # Base competition score
        score = 50  # Neutral score
        
        # High-value items typically have more competition
        if retail_price > 1000:
            score += 20
        elif retail_price > 500:
            score += 10
            
        # Current bid activity indicates competition
        if current_bid > 0:
            if retail_price > 0:
                bid_ratio = current_bid / retail_price
                if bid_ratio > 0.7:  # High bidding activity
                    score += 25
                elif bid_ratio > 0.5:
                    score += 15
                elif bid_ratio > 0.3:
                    score += 10
                    
        # Discount level affects competition
        if retail_price > 0 and instant_win_price > 0:
            discount = ((retail_price - instant_win_price) / retail_price) * 100
            if discount > 50:  # High discounts attract more bidders
                score += 15
            elif discount > 30:
                score += 10
                
        return min(score, 100)  # Cap at 100
        
    async def collect_timing_data(self):
        """Collect auction timing data."""
        print("⏰ AUCTION TIMING ANALYZER")
        print("📊 Analyzing auction timing patterns...")
        print()
        
        # Search terms for diverse auction data
        search_terms = [
            'electronics', 'laptop', 'phone', 'tv', 'appliance',
            'tool', 'furniture', 'jewelry', 'watch', 'camera'
        ]
        
        all_items = []
        seen_lot_ids = set()
        
        for term in search_terms:
            print(f"🔍 Searching {term}...")
            
            results = await self.search_for_term(term)
            
            for result in results:
                lot_id = result.get('lot_id')
                if lot_id and lot_id not in seen_lot_ids:
                    close_date_str = result.get('expected_close_date', '')
                    hour, day_of_week, time_slot = self.parse_closing_time(close_date_str)
                    
                    if hour is not None and time_slot:
                        # Calculate metrics
                        competition_score = self.calculate_competition_score(result)
                        
                        retail_price = result.get('retail_price', 0)
                        instant_win_price = result.get('instant_win_price', 0)
                        discount_percent = 0
                        
                        if retail_price > 0 and instant_win_price > 0:
                            discount_percent = ((retail_price - instant_win_price) / retail_price) * 100
                            
                        # Enhance result with timing data
                        result['close_hour'] = hour
                        result['close_day_of_week'] = day_of_week
                        result['time_slot'] = time_slot
                        result['competition_score'] = competition_score
                        result['discount_percent'] = discount_percent
                        
                        all_items.append(result)
                        seen_lot_ids.add(lot_id)
                        
            await asyncio.sleep(0.2)
            
        print(f"📈 Collected timing data for {len(all_items)} auctions")
        return all_items
        
    def analyze_time_patterns(self, items):
        """Analyze timing patterns and opportunities."""
        # Group by time slot and day
        by_time_slot = defaultdict(list)
        by_day = defaultdict(list)
        by_hour = defaultdict(list)
        
        for item in items:
            time_slot = item.get('time_slot')
            day = item.get('close_day_of_week')
            hour = item.get('close_hour')
            
            if time_slot:
                by_time_slot[time_slot].append(item)
            if day:
                by_day[day].append(item)
            if hour is not None:
                by_hour[hour].append(item)
                
        # Analyze time slots
        time_slot_analysis = {}
        for slot, slot_items in by_time_slot.items():
            if len(slot_items) >= 3:  # Minimum sample size
                avg_competition = statistics.mean([item.get('competition_score', 50) for item in slot_items])
                avg_discount = statistics.mean([item.get('discount_percent', 0) for item in slot_items])
                avg_retail = statistics.mean([item.get('retail_price', 0) for item in slot_items])
                
                # Calculate opportunity score (lower competition + higher discounts = better)
                opportunity_score = (100 - avg_competition) + (avg_discount / 2)
                
                time_slot_analysis[slot] = {
                    'avg_competition': avg_competition,
                    'avg_discount': avg_discount,
                    'avg_retail_value': avg_retail,
                    'total_auctions': len(slot_items),
                    'opportunity_score': opportunity_score
                }
                
        # Analyze days of week
        day_analysis = {}
        for day, day_items in by_day.items():
            if len(day_items) >= 3:
                avg_competition = statistics.mean([item.get('competition_score', 50) for item in day_items])
                avg_discount = statistics.mean([item.get('discount_percent', 0) for item in day_items])
                avg_retail = statistics.mean([item.get('retail_price', 0) for item in day_items])
                
                opportunity_score = (100 - avg_competition) + (avg_discount / 2)
                
                day_analysis[day] = {
                    'avg_competition': avg_competition,
                    'avg_discount': avg_discount,
                    'avg_retail_value': avg_retail,
                    'total_auctions': len(day_items),
                    'opportunity_score': opportunity_score
                }
                
        return time_slot_analysis, day_analysis, by_hour
        
    def identify_optimal_times(self, time_slot_analysis, day_analysis):
        """Identify optimal bidding times."""
        optimal_times = []
        
        # Best time slots (highest opportunity scores)
        if time_slot_analysis:
            best_slots = sorted(time_slot_analysis.items(), 
                              key=lambda x: x[1]['opportunity_score'], reverse=True)
            
            for slot, data in best_slots[:3]:  # Top 3 time slots
                optimal_times.append({
                    'type': 'TIME_SLOT',
                    'period': slot,
                    'opportunity_score': data['opportunity_score'],
                    'avg_competition': data['avg_competition'],
                    'avg_discount': data['avg_discount'],
                    'sample_size': data['total_auctions']
                })
                
        # Best days (highest opportunity scores)
        if day_analysis:
            best_days = sorted(day_analysis.items(), 
                             key=lambda x: x[1]['opportunity_score'], reverse=True)
            
            for day, data in best_days[:3]:  # Top 3 days
                optimal_times.append({
                    'type': 'DAY_OF_WEEK',
                    'period': day,
                    'opportunity_score': data['opportunity_score'],
                    'avg_competition': data['avg_competition'],
                    'avg_discount': data['avg_discount'],
                    'sample_size': data['total_auctions']
                })
                
        return optimal_times
        
    def display_timing_report(self, items, time_slot_analysis, day_analysis, optimal_times):
        """Display comprehensive timing analysis report."""
        print(f"\n⏰ AUCTION TIMING ANALYSIS REPORT")
        print("=" * 80)
        
        if not items:
            print("❌ No timing data collected")
            return
            
        print(f"📊 Analyzed {len(items)} auctions with timing data")
        print()
        
        # Overall statistics
        avg_competition = statistics.mean([item.get('competition_score', 50) for item in items])
        avg_discount = statistics.mean([item.get('discount_percent', 0) for item in items])
        total_retail_value = sum(item.get('retail_price', 0) for item in items)
        
        print(f"📈 OVERALL MARKET TIMING")
        print("-" * 50)
        print(f"🎯 Average Competition Score: {avg_competition:.1f}/100")
        print(f"💰 Average Discount: {avg_discount:.1f}%")
        print(f"💵 Total Retail Value: ${total_retail_value:,.2f}")
        
        # Time slot analysis
        if time_slot_analysis:
            print(f"\n🕐 TIME SLOT ANALYSIS")
            print("-" * 70)
            print(f"{'Time Slot':15s} | {'Opportunity':11s} | {'Competition':11s} | {'Avg Discount':12s} | {'Auctions':8s}")
            print("-" * 70)
            
            for slot, data in sorted(time_slot_analysis.items(), 
                                   key=lambda x: x[1]['opportunity_score'], reverse=True):
                opportunity = data['opportunity_score']
                competition = data['avg_competition']
                discount = data['avg_discount']
                count = data['total_auctions']
                
                # Color coding for opportunity
                if opportunity >= 60:
                    icon = "🟢"  # High opportunity
                elif opportunity >= 45:
                    icon = "🟡"  # Medium opportunity
                else:
                    icon = "🔴"  # Low opportunity
                    
                print(f"{icon} {slot:13s} | {opportunity:9.1f} | {competition:9.1f} | {discount:10.1f}% | {count:6d}")
                
        # Day of week analysis
        if day_analysis:
            print(f"\n📅 DAY OF WEEK ANALYSIS")
            print("-" * 70)
            print(f"{'Day':12s} | {'Opportunity':11s} | {'Competition':11s} | {'Avg Discount':12s} | {'Auctions':8s}")
            print("-" * 70)
            
            for day, data in sorted(day_analysis.items(), 
                                  key=lambda x: x[1]['opportunity_score'], reverse=True):
                opportunity = data['opportunity_score']
                competition = data['avg_competition']
                discount = data['avg_discount']
                count = data['total_auctions']
                
                if opportunity >= 60:
                    icon = "🟢"
                elif opportunity >= 45:
                    icon = "🟡"
                else:
                    icon = "🔴"
                    
                print(f"{icon} {day:10s} | {opportunity:9.1f} | {competition:9.1f} | {discount:10.1f}% | {count:6d}")
                
        # Optimal timing recommendations
        if optimal_times:
            print(f"\n🎯 OPTIMAL BIDDING TIMES")
            print("-" * 60)
            
            time_slots = [ot for ot in optimal_times if ot['type'] == 'TIME_SLOT']
            days = [ot for ot in optimal_times if ot['type'] == 'DAY_OF_WEEK']
            
            if time_slots:
                print("⏰ Best Time Slots:")
                for i, slot_data in enumerate(time_slots, 1):
                    period = slot_data['period']
                    opportunity = slot_data['opportunity_score']
                    competition = slot_data['avg_competition']
                    discount = slot_data['avg_discount']
                    
                    print(f"  {i}. {period} - Opportunity: {opportunity:.1f}, Competition: {competition:.1f}, Discount: {discount:.1f}%")
                    
            if days:
                print("\n📅 Best Days:")
                for i, day_data in enumerate(days, 1):
                    period = day_data['period']
                    opportunity = day_data['opportunity_score']
                    competition = day_data['avg_competition']
                    discount = day_data['avg_discount']
                    
                    print(f"  {i}. {period} - Opportunity: {opportunity:.1f}, Competition: {competition:.1f}, Discount: {discount:.1f}%")
                    
        # Strategy recommendations
        print(f"\n💡 BIDDING STRATEGY RECOMMENDATIONS")
        print("-" * 60)
        
        if time_slot_analysis:
            best_slot = max(time_slot_analysis.items(), key=lambda x: x[1]['opportunity_score'])
            worst_slot = min(time_slot_analysis.items(), key=lambda x: x[1]['opportunity_score'])
            
            print(f"✅ BEST TIME TO BID: {best_slot[0]}")
            print(f"   • Lower competition ({best_slot[1]['avg_competition']:.1f}/100)")
            print(f"   • Better discounts ({best_slot[1]['avg_discount']:.1f}%)")
            print()
            print(f"❌ AVOID BIDDING: {worst_slot[0]}")
            print(f"   • Higher competition ({worst_slot[1]['avg_competition']:.1f}/100)")
            print(f"   • Lower discounts ({worst_slot[1]['avg_discount']:.1f}%)")
            
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"timing_analysis_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'timestamp': timestamp,
                'summary': {
                    'total_auctions': len(items),
                    'avg_competition': avg_competition,
                    'avg_discount': avg_discount
                },
                'time_slot_analysis': time_slot_analysis,
                'day_analysis': day_analysis,
                'optimal_times': optimal_times
            }, f, indent=2)
            
        print(f"\n💾 Timing analysis report saved to: {filename}")

async def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Auction Timing Analyzer')
    parser.add_argument('--time-slot', type=str, help='Analyze specific time slot only')
    parser.add_argument('--day', type=str, help='Analyze specific day only')
    
    args = parser.parse_args()
    
    analyzer = AuctionTimingAnalyzer()
    await analyzer.create_session()
    
    try:
        items = await analyzer.collect_timing_data()
        
        # Apply filters
        if args.time_slot:
            items = [item for item in items if item.get('time_slot', '').lower() == args.time_slot.lower()]
            
        if args.day:
            items = [item for item in items if item.get('close_day_of_week', '').lower() == args.day.lower()]
            
        time_slot_analysis, day_analysis, by_hour = analyzer.analyze_time_patterns(items)
        optimal_times = analyzer.identify_optimal_times(time_slot_analysis, day_analysis)
        
        analyzer.display_timing_report(items, time_slot_analysis, day_analysis, optimal_times)
        
    finally:
        await analyzer.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 