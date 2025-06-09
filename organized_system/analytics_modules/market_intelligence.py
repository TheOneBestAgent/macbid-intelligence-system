#!/usr/bin/env python3
"""
🎯 ADVANCED MARKET INTELLIGENCE - Competitor & Trend Analysis
Analyze bidding patterns, identify power bidders, track market trends, and provide strategic insights
"""

import asyncio
import aiohttp
import ssl
import sqlite3
import json
from datetime import datetime, timedelta
import statistics
from collections import defaultdict, Counter
import argparse

class MarketIntelligence:
    def __init__(self, db_path="market_intelligence.db"):
        self.db_path = db_path
        self.session = None
        self.ssl_context = self.create_ssl_context()
        self.setup_database()
        
        # Analysis parameters
        self.competitor_threshold = 5  # Minimum bids to be considered active competitor
        self.trend_analysis_days = 30
        self.seasonal_analysis_months = 12
        
    def create_ssl_context(self):
        """Create SSL context for API requests."""
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
        
    def setup_database(self):
        """Setup market intelligence database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collection_date DATE DEFAULT CURRENT_DATE,
                lot_id TEXT,
                product_name TEXT,
                brand TEXT,
                category TEXT,
                auction_location TEXT,
                retail_price REAL,
                instant_win_price REAL,
                current_bid REAL,
                total_bids INTEGER,
                unique_bidders INTEGER,
                auction_start_date TIMESTAMP,
                auction_end_date TIMESTAMP,
                final_winning_bid REAL,
                winner_id TEXT,
                bid_history TEXT,  -- JSON string of bid progression
                market_conditions TEXT,  -- JSON string of market state
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS competitor_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bidder_id TEXT UNIQUE,
                bidder_type TEXT,  -- POWER_BIDDER, CASUAL, SNIPER, etc.
                total_bids INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0,
                avg_bid_amount REAL DEFAULT 0,
                preferred_categories TEXT,  -- JSON array
                preferred_locations TEXT,  -- JSON array
                bidding_patterns TEXT,  -- JSON object with patterns
                activity_score REAL DEFAULT 0,
                threat_level TEXT DEFAULT 'LOW',  -- LOW, MEDIUM, HIGH, CRITICAL
                last_seen TIMESTAMP,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_trends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                trend_date DATE DEFAULT CURRENT_DATE,
                category TEXT,
                brand TEXT,
                location TEXT,
                
                -- Price Trends
                avg_retail_price REAL,
                avg_winning_bid REAL,
                avg_discount_percent REAL,
                price_volatility REAL,
                
                -- Competition Trends
                avg_bidders_per_auction REAL,
                avg_bids_per_auction REAL,
                competition_intensity REAL,
                
                -- Volume Trends
                total_auctions INTEGER,
                total_volume REAL,
                inventory_turnover REAL,
                
                -- Market Conditions
                market_sentiment TEXT,  -- BULLISH, BEARISH, NEUTRAL
                demand_level TEXT,      -- HIGH, MEDIUM, LOW
                supply_level TEXT,      -- HIGH, MEDIUM, LOW
                
                -- Predictions
                predicted_trend TEXT,   -- RISING, FALLING, STABLE
                confidence_score REAL,
                
                analysis_period_days INTEGER DEFAULT 30,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seasonal_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,  -- WEEKLY, MONTHLY, QUARTERLY, YEARLY
                category TEXT,
                brand TEXT,
                
                -- Pattern Data
                pattern_data TEXT,  -- JSON object with pattern details
                peak_periods TEXT,  -- JSON array of peak periods
                low_periods TEXT,   -- JSON array of low periods
                
                -- Metrics
                pattern_strength REAL,  -- How strong the pattern is (0-100)
                reliability_score REAL, -- How reliable the pattern is (0-100)
                
                -- Recommendations
                optimal_buy_periods TEXT,  -- JSON array
                optimal_sell_periods TEXT, -- JSON array
                
                last_calculated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_points_used INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS strategic_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_date DATE DEFAULT CURRENT_DATE,
                insight_type TEXT,  -- OPPORTUNITY, THREAT, TREND, RECOMMENDATION
                category TEXT,
                brand TEXT,
                location TEXT,
                
                -- Insight Details
                title TEXT,
                description TEXT,
                impact_level TEXT,  -- HIGH, MEDIUM, LOW
                confidence_level TEXT,  -- HIGH, MEDIUM, LOW
                time_sensitivity TEXT,  -- URGENT, MODERATE, LOW
                
                -- Supporting Data
                supporting_data TEXT,  -- JSON object with data
                related_lots TEXT,     -- JSON array of related lot IDs
                
                -- Action Items
                recommended_actions TEXT,  -- JSON array of actions
                expected_outcome TEXT,
                
                -- Status
                status TEXT DEFAULT 'ACTIVE',  -- ACTIVE, RESOLVED, EXPIRED
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def create_session(self):
        """Create HTTP session for API requests."""
        connector = aiohttp.TCPConnector(
            ssl=self.ssl_context,
            limit=10,
            limit_per_host=5
        )
        
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
        )
        
    async def close_session(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            
    async def collect_market_data(self, pages=10):
        """Collect comprehensive market data for analysis."""
        print("📊 Collecting market data for intelligence analysis...")
        
        all_items = []
        
        for page in range(1, pages + 1):
            print(f"   Scanning page {page}/{pages}...")
            
            try:
                url = "https://api.macdiscount.com/search"
                params = {'q': '', 'limit': 100, 'page': page}
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get('items', []) if isinstance(data, dict) else data
                        all_items.extend(items)
                        
                await asyncio.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                print(f"⚠️ Error collecting page {page}: {e}")
                
        print(f"✅ Collected {len(all_items)} items for analysis")
        
        # Store market data
        self.store_market_data(all_items)
        
        return all_items
        
    def store_market_data(self, items):
        """Store collected market data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in items:
            # Extract and clean data
            lot_id = item.get('lot_id')
            product_name = item.get('product_name', '')
            brand = self.extract_brand(product_name)
            category = self.extract_category(product_name)
            
            cursor.execute('''
                INSERT OR REPLACE INTO market_data (
                    lot_id, product_name, brand, category, auction_location,
                    retail_price, instant_win_price, current_bid, total_bids,
                    unique_bidders, auction_end_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                lot_id, product_name, brand, category,
                item.get('auction_location', ''),
                item.get('retail_price', 0),
                item.get('instant_win_price', 0),
                item.get('current_bid', 0),
                item.get('total_bids', 0),
                item.get('unique_bidders', 0),
                item.get('expected_close_date', '')
            ))
            
        conn.commit()
        conn.close()
        
    def extract_brand(self, product_name):
        """Extract brand from product name."""
        if not product_name:
            return 'Unknown'
            
        brands = ['apple', 'sony', 'samsung', 'nintendo', 'dyson', 'bose', 
                 'lg', 'canon', 'nikon', 'dewalt', 'milwaukee', 'makita']
        
        product_lower = product_name.lower()
        for brand in brands:
            if brand in product_lower:
                return brand.title()
                
        return 'Unknown'
        
    def extract_category(self, product_name):
        """Extract category from product name."""
        if not product_name:
            return 'Unknown'
            
        categories = {
            'Electronics': ['laptop', 'computer', 'tablet', 'phone', 'iphone', 'ipad'],
            'Audio': ['headphones', 'speaker', 'audio', 'sound', 'airpods'],
            'Gaming': ['gaming', 'game', 'console', 'xbox', 'playstation', 'nintendo'],
            'Appliances': ['vacuum', 'kitchen', 'appliance', 'dyson'],
            'Tools': ['drill', 'saw', 'tool', 'dewalt', 'milwaukee'],
            'Photography': ['camera', 'lens', 'canon', 'nikon']
        }
        
        product_lower = product_name.lower()
        for category, keywords in categories.items():
            if any(keyword in product_lower for keyword in keywords):
                return category
                
        return 'Other'
        
    def analyze_competitor_patterns(self):
        """Analyze competitor bidding patterns."""
        print("🕵️ Analyzing competitor patterns...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get bidding data (simulated - would need actual bid history)
        cursor.execute('''
            SELECT category, brand, auction_location, total_bids, unique_bidders,
                   retail_price, current_bid, instant_win_price
            FROM market_data 
            WHERE total_bids > 0
        ''')
        
        data = cursor.fetchall()
        
        # Analyze competition patterns
        competition_analysis = {
            'high_competition_categories': [],
            'low_competition_opportunities': [],
            'power_bidder_territories': [],
            'optimal_bidding_times': []
        }
        
        # Group by category for competition analysis
        by_category = defaultdict(list)
        for row in data:
            category = row[0]
            by_category[category].append(row)
            
        # Analyze each category
        for category, items in by_category.items():
            if len(items) < 5:  # Need minimum sample size
                continue
                
            avg_bidders = statistics.mean([item[4] for item in items if item[4] > 0])
            avg_bids = statistics.mean([item[3] for item in items if item[3] > 0])
            
            competition_score = (avg_bidders * 0.6) + (avg_bids * 0.4)
            
            if competition_score > 8:
                competition_analysis['high_competition_categories'].append({
                    'category': category,
                    'avg_bidders': avg_bidders,
                    'avg_bids': avg_bids,
                    'competition_score': competition_score
                })
            elif competition_score < 3:
                competition_analysis['low_competition_opportunities'].append({
                    'category': category,
                    'avg_bidders': avg_bidders,
                    'avg_bids': avg_bids,
                    'competition_score': competition_score
                })
                
        conn.close()
        return competition_analysis
        
    def analyze_market_trends(self, days=30):
        """Analyze market trends over specified period."""
        print(f"📈 Analyzing market trends over {days} days...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since_date = datetime.now() - timedelta(days=days)
        
        # Get trend data by category
        cursor.execute('''
            SELECT category, brand, 
                   AVG(retail_price) as avg_retail,
                   AVG(current_bid) as avg_bid,
                   AVG(CASE WHEN retail_price > 0 THEN 
                       ((retail_price - instant_win_price) / retail_price * 100) 
                       ELSE 0 END) as avg_discount,
                   COUNT(*) as total_auctions,
                   AVG(total_bids) as avg_bids_per_auction,
                   AVG(unique_bidders) as avg_bidders_per_auction
            FROM market_data 
            WHERE recorded_at > ?
            GROUP BY category, brand
            HAVING COUNT(*) >= 5
            ORDER BY total_auctions DESC
        ''', (since_date.isoformat(),))
        
        trends = cursor.fetchall()
        
        # Analyze trends
        trend_analysis = {
            'hot_categories': [],
            'declining_categories': [],
            'emerging_brands': [],
            'price_trends': [],
            'competition_trends': []
        }
        
        for trend in trends:
            category, brand, avg_retail, avg_bid, avg_discount, total_auctions, avg_bids, avg_bidders = trend
            
            # Calculate trend indicators
            activity_score = total_auctions * 0.4 + avg_bids * 0.3 + avg_bidders * 0.3
            value_score = avg_discount if avg_discount else 0
            
            trend_data = {
                'category': category,
                'brand': brand,
                'avg_retail_price': avg_retail,
                'avg_current_bid': avg_bid,
                'avg_discount': avg_discount,
                'total_auctions': total_auctions,
                'activity_score': activity_score,
                'value_score': value_score
            }
            
            # Categorize trends
            if activity_score > 50:
                trend_analysis['hot_categories'].append(trend_data)
            elif activity_score < 10:
                trend_analysis['declining_categories'].append(trend_data)
                
            if brand != 'Unknown' and total_auctions > 10:
                trend_analysis['emerging_brands'].append(trend_data)
                
        # Sort by relevance
        trend_analysis['hot_categories'].sort(key=lambda x: x['activity_score'], reverse=True)
        trend_analysis['emerging_brands'].sort(key=lambda x: x['total_auctions'], reverse=True)
        
        conn.close()
        return trend_analysis
        
    def identify_strategic_opportunities(self):
        """Identify strategic market opportunities."""
        print("🎯 Identifying strategic opportunities...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        opportunities = []
        
        # Low competition, high value opportunities
        cursor.execute('''
            SELECT category, brand, auction_location,
                   AVG(retail_price) as avg_retail,
                   AVG(instant_win_price) as avg_instant_win,
                   AVG(total_bids) as avg_bids,
                   AVG(unique_bidders) as avg_bidders,
                   COUNT(*) as total_items,
                   AVG(CASE WHEN retail_price > 0 THEN 
                       ((retail_price - instant_win_price) / retail_price * 100) 
                       ELSE 0 END) as avg_discount
            FROM market_data 
            WHERE recorded_at > datetime('now', '-7 days')
            GROUP BY category, brand, auction_location
            HAVING COUNT(*) >= 3 AND AVG(total_bids) < 5 AND AVG(retail_price) > 200
            ORDER BY avg_discount DESC
        ''')
        
        low_competition_opps = cursor.fetchall()
        
        for opp in low_competition_opps:
            category, brand, location, avg_retail, avg_instant_win, avg_bids, avg_bidders, total_items, avg_discount = opp
            
            opportunity = {
                'type': 'LOW_COMPETITION_HIGH_VALUE',
                'category': category,
                'brand': brand,
                'location': location,
                'avg_retail_price': avg_retail,
                'avg_discount': avg_discount,
                'avg_competition': avg_bids,
                'total_items': total_items,
                'opportunity_score': (avg_discount * 0.6) + ((10 - avg_bids) * 4),
                'description': f"Low competition {category} items in {location} with {avg_discount:.1f}% average discount"
            }
            
            opportunities.append(opportunity)
            
        # Price anomaly opportunities
        cursor.execute('''
            SELECT lot_id, product_name, category, brand, auction_location,
                   retail_price, instant_win_price, current_bid,
                   ((retail_price - instant_win_price) / retail_price * 100) as discount
            FROM market_data 
            WHERE retail_price > 0 AND instant_win_price > 0
            AND ((retail_price - instant_win_price) / retail_price * 100) > 70
            AND recorded_at > datetime('now', '-3 days')
            ORDER BY discount DESC
            LIMIT 20
        ''')
        
        price_anomalies = cursor.fetchall()
        
        for anomaly in price_anomalies:
            lot_id, product_name, category, brand, location, retail_price, instant_win_price, current_bid, discount = anomaly
            
            opportunity = {
                'type': 'PRICE_ANOMALY',
                'lot_id': lot_id,
                'product_name': product_name,
                'category': category,
                'brand': brand,
                'location': location,
                'retail_price': retail_price,
                'instant_win_price': instant_win_price,
                'discount': discount,
                'opportunity_score': min(discount, 100),
                'description': f"Price anomaly: {product_name} at {discount:.1f}% discount"
            }
            
            opportunities.append(opportunity)
            
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x['opportunity_score'], reverse=True)
        
        conn.close()
        return opportunities
        
    def generate_strategic_insights(self):
        """Generate strategic insights and recommendations."""
        print("🧠 Generating strategic insights...")
        
        # Collect analysis data
        competitor_analysis = self.analyze_competitor_patterns()
        trend_analysis = self.analyze_market_trends()
        opportunities = self.identify_strategic_opportunities()
        
        insights = []
        
        # Generate insights from competitor analysis
        if competitor_analysis['low_competition_opportunities']:
            for opp in competitor_analysis['low_competition_opportunities'][:3]:
                insight = {
                    'type': 'OPPORTUNITY',
                    'title': f"Low Competition in {opp['category']}",
                    'description': f"Category shows low competition with only {opp['avg_bidders']:.1f} average bidders per auction",
                    'impact_level': 'HIGH',
                    'confidence_level': 'HIGH',
                    'recommended_actions': [
                        f"Focus bidding efforts on {opp['category']} items",
                        "Set aggressive bid targets in this category",
                        "Monitor for new arrivals in this category"
                    ],
                    'category': opp['category']
                }
                insights.append(insight)
                
        # Generate insights from trends
        if trend_analysis['hot_categories']:
            hot_cat = trend_analysis['hot_categories'][0]
            insight = {
                'type': 'TREND',
                'title': f"High Activity in {hot_cat['category']}",
                'description': f"Category showing high activity with {hot_cat['total_auctions']} auctions and {hot_cat['avg_discount']:.1f}% average discount",
                'impact_level': 'MEDIUM',
                'confidence_level': 'HIGH',
                'recommended_actions': [
                    "Monitor pricing trends closely",
                    "Consider higher bid amounts due to competition",
                    "Look for off-peak bidding opportunities"
                ],
                'category': hot_cat['category']
            }
            insights.append(insight)
            
        # Generate insights from opportunities
        top_opportunities = opportunities[:5]
        for opp in top_opportunities:
            if opp['type'] == 'PRICE_ANOMALY':
                insight = {
                    'type': 'OPPORTUNITY',
                    'title': f"Price Anomaly Alert",
                    'description': f"Potential pricing error: {opp['product_name']} at {opp['discount']:.1f}% discount",
                    'impact_level': 'CRITICAL',
                    'confidence_level': 'HIGH',
                    'time_sensitivity': 'URGENT',
                    'recommended_actions': [
                        "Investigate item immediately",
                        "Place bid if legitimate opportunity",
                        "Monitor for similar anomalies"
                    ],
                    'lot_id': opp['lot_id']
                }
                insights.append(insight)
                
        return insights
        
    def show_market_intelligence_dashboard(self):
        """Display comprehensive market intelligence dashboard."""
        print("\n🎯 MARKET INTELLIGENCE DASHBOARD")
        print("="*70)
        
        # Generate all analyses
        competitor_analysis = self.analyze_competitor_patterns()
        trend_analysis = self.analyze_market_trends()
        opportunities = self.identify_strategic_opportunities()
        insights = self.generate_strategic_insights()
        
        # Competitor Analysis
        print(f"\n🕵️ COMPETITOR ANALYSIS")
        print("-" * 50)
        
        if competitor_analysis['high_competition_categories']:
            print("⚔️ High Competition Categories:")
            for cat in competitor_analysis['high_competition_categories'][:3]:
                print(f"   • {cat['category']}: {cat['avg_bidders']:.1f} avg bidders, {cat['avg_bids']:.1f} avg bids")
                
        if competitor_analysis['low_competition_opportunities']:
            print("\n🎯 Low Competition Opportunities:")
            for cat in competitor_analysis['low_competition_opportunities'][:3]:
                print(f"   • {cat['category']}: {cat['avg_bidders']:.1f} avg bidders, {cat['avg_bids']:.1f} avg bids")
                
        # Market Trends
        print(f"\n📈 MARKET TRENDS")
        print("-" * 50)
        
        if trend_analysis['hot_categories']:
            print("🔥 Hot Categories:")
            for trend in trend_analysis['hot_categories'][:3]:
                print(f"   • {trend['category']} ({trend['brand']}): {trend['total_auctions']} auctions, {trend['avg_discount']:.1f}% avg discount")
                
        if trend_analysis['emerging_brands']:
            print("\n🌟 Emerging Brands:")
            for brand in trend_analysis['emerging_brands'][:3]:
                print(f"   • {brand['brand']} in {brand['category']}: {brand['total_auctions']} auctions")
                
        # Strategic Opportunities
        print(f"\n💎 STRATEGIC OPPORTUNITIES")
        print("-" * 50)
        
        top_opportunities = opportunities[:5]
        for i, opp in enumerate(top_opportunities, 1):
            print(f"{i}. {opp['type']}: {opp['description']}")
            print(f"   Score: {opp['opportunity_score']:.1f} | Category: {opp.get('category', 'N/A')}")
            
        # Strategic Insights
        print(f"\n🧠 STRATEGIC INSIGHTS")
        print("-" * 50)
        
        for i, insight in enumerate(insights[:3], 1):
            impact_icon = {"CRITICAL": "🚨", "HIGH": "⚡", "MEDIUM": "📢", "LOW": "ℹ️"}
            icon = impact_icon.get(insight['impact_level'], "📢")
            
            print(f"{icon} {insight['title']}")
            print(f"   {insight['description']}")
            print(f"   Impact: {insight['impact_level']} | Confidence: {insight['confidence_level']}")
            
            if insight.get('recommended_actions'):
                print("   Actions:")
                for action in insight['recommended_actions'][:2]:
                    print(f"     • {action}")
            print()

async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="🎯 Market Intelligence")
    parser.add_argument("--collect", action="store_true", help="Collect market data")
    parser.add_argument("--dashboard", action="store_true", help="Show intelligence dashboard")
    parser.add_argument("--competitors", action="store_true", help="Analyze competitors")
    parser.add_argument("--trends", action="store_true", help="Analyze market trends")
    parser.add_argument("--opportunities", action="store_true", help="Find opportunities")
    parser.add_argument("--pages", type=int, default=10, help="Pages to scan for data collection")
    parser.add_argument("--days", type=int, default=30, help="Days for trend analysis")
    
    args = parser.parse_args()
    
    intelligence = MarketIntelligence()
    
    if args.collect:
        await intelligence.create_session()
        try:
            await intelligence.collect_market_data(args.pages)
        finally:
            await intelligence.close_session()
            
    elif args.competitors:
        analysis = intelligence.analyze_competitor_patterns()
        print("\n🕵️ COMPETITOR ANALYSIS")
        print("="*50)
        print(json.dumps(analysis, indent=2, default=str))
        
    elif args.trends:
        analysis = intelligence.analyze_market_trends(args.days)
        print(f"\n📈 MARKET TRENDS ({args.days} days)")
        print("="*50)
        print(json.dumps(analysis, indent=2, default=str))
        
    elif args.opportunities:
        opportunities = intelligence.identify_strategic_opportunities()
        print("\n💎 STRATEGIC OPPORTUNITIES")
        print("="*50)
        for i, opp in enumerate(opportunities[:10], 1):
            print(f"{i}. {opp['description']} (Score: {opp['opportunity_score']:.1f})")
            
    else:
        intelligence.show_market_intelligence_dashboard()

if __name__ == "__main__":
    asyncio.run(main()) 